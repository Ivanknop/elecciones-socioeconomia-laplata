"""Catálogo validado de localidades geolocalizadas de La Plata: cruza
Georef-AR contra la fuente del Ministerio de Obras Públicas, escribe
`localidades_la_plata.csv`. Metodología en `data/geolocalizacion/LOCALIDADES.md`.

Uso:
    PYTHONPATH=src python -m geolocalizacion.catalogo
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from constantes import GEOLOCALIZACION_CACHE_DIR, LOCALIDADES_LA_PLATA_PATH, LOCALIDADES_MINISTERIO_PATH
from geolocalizacion.georef_client import GeorefClient

MUNICIPIO_ID = "060441"

_ALIAS_MINISTERIO_A_GEOREF = {
    "ISLA MARTIN GARCIA": "MARTIN GARCIA",
    "BARRIO RUTA SOL": "RUTA SOL",
}

_RADIO_TIERRA_M = 6_371_000


@dataclass(frozen=True)
class LocalidadMinisterio:
    nombre: str
    uta_2020: str
    uta_2010: str
    lat: float
    lon: float


@dataclass(frozen=True)
class LocalidadValidada:
    nombre: str
    georef_id: str
    lat: float
    lon: float
    uta_2020: str | None
    uta_2010: str | None
    lat_ministerio: float | None
    lon_ministerio: float | None
    delta_metros: float | None
    fuentes: str  # "georef+ministerio" | "solo_georef"
    nota: str = ""


@dataclass(frozen=True)
class ReporteValidacion:
    total: int
    confirmadas_por_ambas_fuentes: int
    solo_georef: tuple[str, ...]
    delta_mediana_m: float
    delta_maximo_m: float
    delta_maximo_nombre: str


def _normalizar(nombre: str) -> str:
    sin_acentos = "".join(c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn")
    sin_puntuacion = re.sub(r"[().]", " ", sin_acentos.upper())
    return re.sub(r"\s+", " ", sin_puntuacion).strip()


def _haversine_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * _RADIO_TIERRA_M * math.asin(math.sqrt(a))


def cargar_ministerio(path: Path | str) -> list[LocalidadMinisterio]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return [
            LocalidadMinisterio(
                nombre=fila["Nombre"].strip(),
                uta_2020=fila["Código UTA 2020"].strip(),
                uta_2010=fila["Código UTA 2010"].strip(),
                lat=float(fila["Latitud"].replace(",", ".")),
                lon=float(fila["Longitud"].replace(",", ".")),
            )
            for fila in csv.DictReader(f, delimiter=";")
            if fila.get("Nombre")
        ]


def _deduplicar_asentamientos(asentamientos: list[dict]) -> list[dict]:
    """Georef duplica localidad censal + asentamiento homónimo (mismo
    nombre); nos quedamos con el id más largo, más específico."""
    por_nombre: dict[str, dict] = {}
    for a in asentamientos:
        clave = _normalizar(a["nombre"])
        actual = por_nombre.get(clave)
        if actual is None or len(a["id"]) > len(actual["id"]):
            por_nombre[clave] = a
    return list(por_nombre.values())


def construir_catalogo(
    asentamientos: list[dict], ministerio: list[LocalidadMinisterio]
) -> list[LocalidadValidada]:
    ministerio_por_nombre_georef = {}
    for m in ministerio:
        clave = _normalizar(m.nombre)
        clave = _ALIAS_MINISTERIO_A_GEOREF.get(clave, clave)
        ministerio_por_nombre_georef[clave] = m

    catalogo = []
    for a in _deduplicar_asentamientos(asentamientos):
        clave = _normalizar(a["nombre"])
        m = ministerio_por_nombre_georef.get(clave)
        if m is not None:
            delta = round(_haversine_metros(a["lat"], a["lon"], m.lat, m.lon), 1)
            catalogo.append(
                LocalidadValidada(
                    nombre=a["nombre"],
                    georef_id=a["id"],
                    lat=a["lat"],
                    lon=a["lon"],
                    uta_2020=m.uta_2020,
                    uta_2010=m.uta_2010,
                    lat_ministerio=m.lat,
                    lon_ministerio=m.lon,
                    delta_metros=delta,
                    fuentes="georef+ministerio",
                )
            )
        else:
            catalogo.append(
                LocalidadValidada(
                    nombre=a["nombre"],
                    georef_id=a["id"],
                    lat=a["lat"],
                    lon=a["lon"],
                    uta_2020=None,
                    uta_2010=None,
                    lat_ministerio=None,
                    lon_ministerio=None,
                    delta_metros=None,
                    fuentes="solo_georef",
                    nota=(
                        "Sin contraparte en el listado del Ministerio de Obras Públicas; "
                        "localidad real confirmada manualmente por el equipo del proyecto "
                        "(no es un error de Georef)."
                    ),
                )
            )

    return sorted(catalogo, key=lambda loc: loc.nombre)


def generar_reporte(catalogo: list[LocalidadValidada]) -> ReporteValidacion:
    confirmadas = [loc for loc in catalogo if loc.fuentes == "georef+ministerio"]
    solo_georef = tuple(loc.nombre for loc in catalogo if loc.fuentes == "solo_georef")
    deltas = sorted(loc.delta_metros for loc in confirmadas)
    peor = max(confirmadas, key=lambda loc: loc.delta_metros) if confirmadas else None
    return ReporteValidacion(
        total=len(catalogo),
        confirmadas_por_ambas_fuentes=len(confirmadas),
        solo_georef=solo_georef,
        delta_mediana_m=deltas[len(deltas) // 2] if deltas else 0.0,
        delta_maximo_m=peor.delta_metros if peor else 0.0,
        delta_maximo_nombre=peor.nombre if peor else "",
    )


def generar_csv(
    ministerio_path: Path | str = LOCALIDADES_MINISTERIO_PATH,
    destino: Path | str = LOCALIDADES_LA_PLATA_PATH,
    cache_dir: Path | str = GEOLOCALIZACION_CACHE_DIR,
    municipio_id: str = MUNICIPIO_ID,
    force_refresh: bool = False,
) -> tuple[Path, ReporteValidacion]:
    client = GeorefClient(cache_dir=cache_dir)
    asentamientos = client.get_asentamientos(municipio_id, force_refresh=force_refresh)
    ministerio = cargar_ministerio(ministerio_path)

    catalogo = construir_catalogo(asentamientos, ministerio)
    reporte = generar_reporte(catalogo)

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    columnas = [
        "nombre", "georef_id", "lat", "lon", "uta_2020", "uta_2010",
        "lat_ministerio", "lon_ministerio", "delta_metros", "fuentes", "nota",
    ]
    with destino_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for loc in catalogo:
            writer.writerow(
                {
                    "nombre": loc.nombre,
                    "georef_id": loc.georef_id,
                    "lat": loc.lat,
                    "lon": loc.lon,
                    "uta_2020": loc.uta_2020 or "",
                    "uta_2010": loc.uta_2010 or "",
                    "lat_ministerio": loc.lat_ministerio if loc.lat_ministerio is not None else "",
                    "lon_ministerio": loc.lon_ministerio if loc.lon_ministerio is not None else "",
                    "delta_metros": loc.delta_metros if loc.delta_metros is not None else "",
                    "fuentes": loc.fuentes,
                    "nota": loc.nota,
                }
            )

    return destino_path, reporte


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ministerio", default=LOCALIDADES_MINISTERIO_PATH)
    parser.add_argument("--destino", default=LOCALIDADES_LA_PLATA_PATH)
    parser.add_argument("--cache-dir", default=GEOLOCALIZACION_CACHE_DIR)
    parser.add_argument("--municipio-id", default=MUNICIPIO_ID)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    destino, reporte = generar_csv(
        ministerio_path=args.ministerio,
        destino=args.destino,
        cache_dir=args.cache_dir,
        municipio_id=args.municipio_id,
        force_refresh=args.force_refresh,
    )

    print(
        f"{destino} -- {reporte.total} localidades, "
        f"{reporte.confirmadas_por_ambas_fuentes} confirmadas por georef+ministerio "
        f"(Δ mediana {reporte.delta_mediana_m:.0f} m, máx {reporte.delta_maximo_m:.0f} m en {reporte.delta_maximo_nombre!r})"
    )
    if reporte.solo_georef:
        print(f"solo georef (sin contraparte en el Ministerio): {', '.join(reporte.solo_georef)}")


if __name__ == "__main__":
    main()
