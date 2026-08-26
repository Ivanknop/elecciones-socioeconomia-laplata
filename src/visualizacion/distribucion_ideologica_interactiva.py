"""Pestaña interactiva "Distribución ideológica (V-Party)", mismo patrón
que `mapa_interactivo.py` (selector Nivel + Año, autoplay). Detalle en
skill `laplata-visualizacion`.

Uso:
    PYTHONPATH=src python -m visualizacion.distribucion_ideologica_interactiva
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from analisis.graficos import _COLOR_FILIACION
from analisis.serie_temporal import NIVELES, _puntos_del_nivel
from analisis.totales_por_lista import NIVEL_A_NIVEL_CSV, _COLOR_SIN_CLASIFICAR
from analisis.vparty_cuadrantes_local import (
    _color_por_partido,
    _limites_globales,
    cargar_filiaciones,
    cargar_posiciones_propias,
    tabla_distrito,
    tabla_localidades,
)
from constantes import (
    CARGO_LABEL,
    CIRCUITOS_GEOJSON_PATH,
    CIRCUITOS_POR_LOCALIDAD_PATH,
    CLASIFICACION_IDEOLOGICA_PATH,
    DATA_DISTRITO_DIR,
    LOCALIDADES_LA_PLATA_PATH,
)
from electoral.localidades import cargar_circuito_localidad_geo
from visualizacion.mapa_interactivo import _cargar_geojson_circuitos, _cargar_localidades


def _serializar_puntos(
    df_slice, filiacion_de: dict[str, str], colores: dict[str, str],
) -> list[dict]:
    """Una fila de `df_slice` -> un punto serializable para el payload;
    `filiacion_de`/`colores` ya resueltos por quien llama."""
    puntos = []
    for _, fila in df_slice.iterrows():
        agrupacion = fila["agrupacion"]
        puntos.append({
            "agrupacion": agrupacion,
            "votos": int(fila["votos"]),
            "votos_pct": round(float(fila["votos_porcentaje"]), 2),
            "economico": round(float(fila["economico"]), 3),
            "progresismo": round(float(fila["progresismo"]), 3),
            "populismo": round(float(fila["populismo"]), 3),
            "filiacion": filiacion_de.get(agrupacion),
            "color": colores.get(agrupacion, _COLOR_SIN_CLASIFICAR),
        })
    return puntos


def _tabla_distrito_por_nivel(
    data_dir: Path | str,
    posiciones: dict[tuple[str, str, str], tuple[float, float, float]],
    filiaciones: dict[tuple[str, str, str], str],
) -> dict:
    """{"<año>_<nivel>": {...}}, mismos puntos que `generar_distrito`, acá
    como dict serializable en vez de un PNG."""
    distrito = {}
    for nivel in NIVELES:
        df_todo = tabla_distrito(nivel, posiciones, data_dir)
        if df_todo.empty:
            continue
        cargo_por_anio = dict(_puntos_del_nivel(data_dir, nivel))

        for anio in sorted(df_todo["year"].unique()):
            df_anio = df_todo[df_todo["year"] == anio]
            cargo = cargo_por_anio[anio]
            nivel_csv = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
            filiacion_de = {
                agrupacion: filiaciones.get((str(anio), nivel_csv, agrupacion))
                for agrupacion in df_anio["agrupacion"]
            }
            colores = _color_por_partido(list(df_anio["agrupacion"]), filiacion_de)
            puntos = _serializar_puntos(df_anio, filiacion_de, colores)

            distrito[f"{int(anio)}_{nivel}"] = {
                "anio": int(anio), "nivel": nivel, "cargo": cargo, "cargo_label": CARGO_LABEL[cargo],
                "puntos": puntos,
            }

    return distrito


def _localidad_puntos_por_nivel(
    data_dir: Path | str,
    crosswalk_path: Path | str,
    posiciones: dict[tuple[str, str, str], tuple[float, float, float]],
    filiaciones: dict[tuple[str, str, str], str],
) -> dict:
    """{"<localidad>": {"<año>_<nivel>": {...}}}, mismos puntos que
    `generar_localidad_por_anio`; color sobre universo distrital, igual en
    cualquier localidad."""
    localidad_puntos: dict[str, dict] = {}
    for nivel in NIVELES:
        df_todo = tabla_distrito(nivel, posiciones, data_dir)
        df_loc = tabla_localidades(nivel, posiciones, data_dir, crosswalk_path)
        if df_todo.empty or df_loc.empty:
            continue
        cargo_por_anio = dict(_puntos_del_nivel(data_dir, nivel))

        for anio in sorted(df_todo["year"].unique()):
            cargo = cargo_por_anio[anio]
            nivel_csv = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
            agrupaciones_distrito = list(df_todo.loc[df_todo["year"] == anio, "agrupacion"])
            filiacion_de = {
                agrupacion: filiaciones.get((str(anio), nivel_csv, agrupacion))
                for agrupacion in agrupaciones_distrito
            }
            colores = _color_por_partido(agrupaciones_distrito, filiacion_de)

            df_anio_loc = df_loc[df_loc["year"] == anio]
            for localidad, grupo in df_anio_loc.groupby("localidad"):
                puntos = _serializar_puntos(grupo, filiacion_de, colores)
                localidad_puntos.setdefault(localidad, {})[f"{int(anio)}_{nivel}"] = {
                    "anio": int(anio), "nivel": nivel, "cargo": cargo, "cargo_label": CARGO_LABEL[cargo],
                    "puntos": puntos,
                }

    return localidad_puntos


def construir_payload(
    data_dir: Path | str = DATA_DISTRITO_DIR,
    geojson_path: Path | str = CIRCUITOS_GEOJSON_PATH,
    localidades_path: Path | str = LOCALIDADES_LA_PLATA_PATH,
    crosswalk_path: Path | str = CIRCUITOS_POR_LOCALIDAD_PATH,
    clasificacion_path: Path | str = CLASIFICACION_IDEOLOGICA_PATH,
) -> dict:
    posiciones = cargar_posiciones_propias(clasificacion_path)
    filiaciones = cargar_filiaciones(clasificacion_path)

    distrito = _tabla_distrito_por_nivel(data_dir, posiciones, filiaciones)
    localidad_puntos = _localidad_puntos_por_nivel(data_dir, crosswalk_path, posiciones, filiaciones)
    xlim, ylim = _limites_globales(posiciones)

    geojson = _cargar_geojson_circuitos(geojson_path)
    circuito_localidad = cargar_circuito_localidad_geo(crosswalk_path)
    for feature in geojson["features"]:
        circuito_localidad.setdefault(feature["properties"]["circuito_id"], None)

    fam_names = sorted({f for f in filiaciones.values()})

    nivel_labels = {
        nivel: f"{nivel.capitalize()} ({CARGO_LABEL[ejecutivo]} / {CARGO_LABEL[legislativo]})"
        for nivel, (ejecutivo, legislativo) in NIVELES.items()
    }

    return {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "geojson": geojson,
        "circuito_localidad": circuito_localidad,
        "localidades": _cargar_localidades(localidades_path),
        "fam_colors": {k: v for k, v in _COLOR_FILIACION.items() if k in fam_names},
        "nivel_labels": nivel_labels,
        "distrito": distrito,
        "localidad_puntos": localidad_puntos,
        "eje_limites": {"x": round(xlim[1], 3), "y": round(ylim[1], 3)},
    }


def generar_distribucion_interactiva(
    destino: Path | str = "docs/distribucion_ideologica_la_plata.html",
    data_dir: Path | str = DATA_DISTRITO_DIR,
) -> Path:
    payload = construir_payload(data_dir=data_dir)

    plantilla_path = Path(__file__).parent / "distribucion_ideologica_template.html"
    plantilla = plantilla_path.read_text(encoding="utf-8")
    html = plantilla.replace(
        "/*__RAW_DATA__*/",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    destino_path.write_text(html, encoding="utf-8")
    return destino_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--destino", default="docs/distribucion_ideologica_la_plata.html")
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    args = parser.parse_args()

    destino = generar_distribucion_interactiva(destino=args.destino, data_dir=args.data_dir)
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
