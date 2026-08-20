"""Crosswalk circuito electoral -> localidad geolocalizada, vía join espacial
contra el catálogo validado (`geolocalizacion.catalogo`,
`data/geolocalizacion/localidades_la_plata.csv`, 36 filas, fuente Ministerio
de Obras Públicas + Georef-AR). Escribe `data/geolocalizacion/circuitos_por_localidad.csv`.

A diferencia de `data/geolocalizacion/fuentes_extra/circuito_localidad.csv` (crosswalk
hand-curated contra nombres de barrio de una resolución de 1990/2007 y un
relevamiento periodístico, ver skill `laplata-elecciones`), este archivo es
**derivado**, recalculable en segundos: `data/geolocalizacion/localidades_la_plata.csv`
no trae polígono por localidad, solo un punto (centroide/asentamiento), así
que la asignación es *nearest-neighbor* -- centroide de cada circuito
(`data/socioeconomia/circuitos_electorales_la_plata.geojson`, 68 polígonos)
contra el punto de localidad más cercano, ambos reproyectados a la UTM
estimada de los circuitos para que la distancia se calcule en metros (mismo
patrón que `socioeconomia.geo.calcular_correspondencia`). Cada circuito queda
con exactamente una localidad -- nunca `SIN_DETERMINAR`, a diferencia del
crosswalk por nombre, porque el nearest-neighbor siempre encuentra un punto
más cercano.

No todas las 36 localidades terminan usadas: varias comparten zona urbana
con otra localidad más próxima al centroide de cualquier circuito que las
rodea (ver `data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md`) -- no es un
error, es la consecuencia esperada de tener más circuitos (68) que
localidades (36) y un solo punto de referencia por localidad. La distancia
del match queda en la columna `distancia_metros`: circuitos grandes y
rurales (ej. 498, ~208 km²) quedan con distancias grandes porque su
centroide cae lejos de cualquier área poblada -- eso tampoco se recorta ni
se ajusta, se documenta.

Uso:
    PYTHONPATH=src python -m geolocalizacion.circuitos_por_localidad
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd

from constantes import (
    CIRCUITOS_GEOJSON_PATH,
    CIRCUITOS_POR_LOCALIDAD_PATH,
    LOCALIDADES_LA_PLATA_PATH,
)
from socioeconomia.geo import cargar_circuitos_electorales


@dataclass(frozen=True)
class ReporteAsignacion:
    total_circuitos: int
    localidades_utilizadas: int
    localidades_totales: int
    localidades_sin_circuito: tuple[str, ...]
    distancia_media_m: float
    distancia_maxima_m: float
    distancia_maxima_circuito: str
    distancia_maxima_localidad: str


def cargar_localidades(path: Path | str = LOCALIDADES_LA_PLATA_PATH) -> gpd.GeoDataFrame:
    """Lee el catálogo validado y arma un `GeoDataFrame` de puntos (`nombre`
    + `geometry`) en EPSG:4326."""
    df = pd.read_csv(path)
    return gpd.GeoDataFrame(
        df[["nombre"]],
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )


def asignar_localidad_mas_cercana(
    circuitos: gpd.GeoDataFrame, localidades: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Pura -- no hace red ni lee archivos. `circuitos` viene de
    `socioeconomia.geo.cargar_circuitos_electorales` (columnas `circuito_id`
    + `geometry`, polígonos); `localidades` de `cargar_localidades` (columnas
    `nombre` + `geometry`, puntos). Devuelve una fila por circuito con
    `circuito_id`, `localidad`, `distancia_metros` (centroide del circuito
    al punto de localidad más cercano), ordenada por `circuito_id`.

    Reproyecta ambas capas a la UTM estimada a partir de `circuitos` para
    que la distancia salga en metros, no en grados (mismo criterio que
    `socioeconomia.geo.calcular_correspondencia`).
    """
    crs_metrico = circuitos.estimate_utm_crs()
    circuitos_m = circuitos.to_crs(crs_metrico)
    localidades_m = localidades.to_crs(crs_metrico)

    centroides = circuitos_m.copy()
    centroides["geometry"] = centroides.geometry.centroid

    unido = gpd.sjoin_nearest(
        centroides[["circuito_id", "geometry"]],
        localidades_m[["nombre", "geometry"]],
        how="left",
        distance_col="distancia_metros",
    )
    unido = unido.rename(columns={"nombre": "localidad"})
    unido["distancia_metros"] = unido["distancia_metros"].round(1)

    return (
        unido[["circuito_id", "localidad", "distancia_metros"]]
        .sort_values("circuito_id")
        .reset_index(drop=True)
    )


def generar_reporte(asignacion: pd.DataFrame, nombres_localidades: set[str]) -> ReporteAsignacion:
    """Pura. `nombres_localidades` es el universo completo (`set(localidades["nombre"])`),
    para poder reportar cuáles quedaron sin ningún circuito asignado."""
    peor = asignacion.loc[asignacion["distancia_metros"].idxmax()]
    utilizadas = set(asignacion["localidad"])
    return ReporteAsignacion(
        total_circuitos=len(asignacion),
        localidades_utilizadas=len(utilizadas),
        localidades_totales=len(nombres_localidades),
        localidades_sin_circuito=tuple(sorted(nombres_localidades - utilizadas)),
        distancia_media_m=round(asignacion["distancia_metros"].mean(), 1),
        distancia_maxima_m=peor["distancia_metros"],
        distancia_maxima_circuito=peor["circuito_id"],
        distancia_maxima_localidad=peor["localidad"],
    )


def generar_csv(
    geojson_path: Path | str = CIRCUITOS_GEOJSON_PATH,
    localidades_path: Path | str = LOCALIDADES_LA_PLATA_PATH,
    destino: Path | str = CIRCUITOS_POR_LOCALIDAD_PATH,
) -> tuple[Path, ReporteAsignacion]:
    circuitos = cargar_circuitos_electorales(geojson_path)
    localidades = cargar_localidades(localidades_path)

    asignacion = asignar_localidad_mas_cercana(circuitos, localidades)
    reporte = generar_reporte(asignacion, set(localidades["nombre"]))

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    with destino_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["circuito", "localidad", "distancia_metros"])
        for _, fila in asignacion.iterrows():
            writer.writerow([fila["circuito_id"], fila["localidad"], fila["distancia_metros"]])

    return destino_path, reporte


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--geojson", default=CIRCUITOS_GEOJSON_PATH)
    parser.add_argument("--localidades", default=LOCALIDADES_LA_PLATA_PATH)
    parser.add_argument("--destino", default=CIRCUITOS_POR_LOCALIDAD_PATH)
    args = parser.parse_args()

    destino, reporte = generar_csv(
        geojson_path=args.geojson, localidades_path=args.localidades, destino=args.destino
    )

    print(
        f"{destino} -- {reporte.total_circuitos} circuitos, "
        f"{reporte.localidades_utilizadas}/{reporte.localidades_totales} localidades utilizadas "
        f"(distancia media {reporte.distancia_media_m:.0f} m, máx {reporte.distancia_maxima_m:.0f} m "
        f"en circuito {reporte.distancia_maxima_circuito!r} -> {reporte.distancia_maxima_localidad!r})"
    )
    if reporte.localidades_sin_circuito:
        print(f"localidades sin ningún circuito asignado: {', '.join(reporte.localidades_sin_circuito)}")


if __name__ == "__main__":
    main()
