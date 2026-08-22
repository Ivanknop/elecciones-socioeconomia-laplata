"""Pestaña interactiva "Distribución ideológica (V-Party)" -- mismo patrón de
interacción temporal que `mapa_interactivo.py` (selector Nivel + Año,
autoplay)

Solo Nivel + Año (nacional/provincial/municipal, sin el toggle Cargo/Nivel
del mapa electoral) -- los cuadros V-Party de este repo solo existen por
nivel unificado (`analisis.serie_temporal.NIVELES`), nunca por cargo suelto.


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
from analisis.vparty_cuadrantes_local import _color_por_partido, cargar_filiaciones, cargar_posiciones_propias, tabla_distrito
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


def _tabla_distrito_por_nivel(data_dir: Path | str, clasificacion_path: Path | str) -> dict:
    """`{"<año>_<nivel>": {...}}`, una entrada por (año, nivel unificado) con
    cobertura V-Party -- mismos puntos que produciría
    `vparty_cuadrantes_local.generar_distrito` para ese (año, nivel), acá
    como dict serializable en vez de un PNG."""
    posiciones = cargar_posiciones_propias(clasificacion_path)
    filiaciones = cargar_filiaciones(clasificacion_path)

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

            puntos = []
            for _, fila in df_anio.iterrows():
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

            distrito[f"{int(anio)}_{nivel}"] = {
                "anio": int(anio), "nivel": nivel, "cargo": cargo, "cargo_label": CARGO_LABEL[cargo],
                "puntos": puntos,
            }

    return distrito


def construir_payload(
    data_dir: Path | str = DATA_DISTRITO_DIR,
    geojson_path: Path | str = CIRCUITOS_GEOJSON_PATH,
    localidades_path: Path | str = LOCALIDADES_LA_PLATA_PATH,
    crosswalk_path: Path | str = CIRCUITOS_POR_LOCALIDAD_PATH,
    clasificacion_path: Path | str = CLASIFICACION_IDEOLOGICA_PATH,
) -> dict:
    distrito = _tabla_distrito_por_nivel(data_dir, clasificacion_path)

    geojson = _cargar_geojson_circuitos(geojson_path)
    circuito_localidad = cargar_circuito_localidad_geo(crosswalk_path)
    for feature in geojson["features"]:
        circuito_localidad.setdefault(feature["properties"]["circuito_id"], None)

    filiaciones = cargar_filiaciones(clasificacion_path)
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
