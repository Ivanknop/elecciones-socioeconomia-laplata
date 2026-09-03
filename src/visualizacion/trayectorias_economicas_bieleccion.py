"""Pestaña interactiva "Trayectorias económicas bielección": igual que
`trayectorias_economicas.py` pero sobre `panel_bieleccion_trimestral_
<nivel>.csv` (bloque largo `_vl`: elección t-2 a t, salta la t-1
intermedia). Mismo esquema de payload que el módulo base
(`anio_inicio_ventana`/`agrupacion_inicio` genéricos) para reusar el
template sin cambios -- acá `anio_inicio_ventana` es la elección t-2, no t-1.

Uso:
    PYTHONPATH=src python -m visualizacion.trayectorias_economicas_bieleccion
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from constantes import PANEL_BIELECCION_TRIMESTRAL_DIR, SERIES_ECONOMICAS_MENSUALES_PATH
from ml_models.construir_calendario import NIVELES
from ml_models.construir_panel_trimestral import _promedio_trimestre
from ml_models.construir_panel_ventanas import _leer_dicts
from ml_models.features_ventana import _meses_en_ventana
from visualizacion.trayectorias_economicas import (
    _cargar_series_mensuales_crudas,
    _label_ventana,
    _salario_real_usd_mensual,
    _serie_variable,
    _UNIDADES,
    _variables_de,
)

_COLUMNAS_FIJAS = {
    "id_transicion",
    "nivel",
    "anio_t",
    "anio_t_menos_2",
    "orden",
    "tipo_fila",
    "fecha_inicio",
    "fecha_fin",
    "n_meses",
    "periodo_intervenido",
    "gana_oficialismo",
    "share_oficialismo",
    "agrupacion_oficialismo",
}


def construir_payload(
    panel_dir: Path | str = PANEL_BIELECCION_TRIMESTRAL_DIR,
    series_mensuales_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
) -> dict:
    """Pura -- toma directorios/rutas, no hace red."""
    salario_usd_mensual = _salario_real_usd_mensual(_cargar_series_mensuales_crudas(series_mensuales_path))

    trayectorias: dict[str, dict] = {}
    variables: set[str] = set()

    for nivel in NIVELES:
        filas = _leer_dicts(Path(panel_dir) / f"panel_bieleccion_trimestral_{nivel}.csv")
        variables_del_nivel = [v if v != "salario_real" else "salario_real_usd" for v in _variables_de(filas, _COLUMNAS_FIJAS)]
        variables.update(variables_del_nivel)

        por_transicion: dict[str, list[dict]] = {}
        for f in filas:
            por_transicion.setdefault(f["id_transicion"], []).append(f)

        nivel_dict = {}
        for id_transicion, filas_v in por_transicion.items():
            filas_v.sort(key=lambda f: int(f["orden"]))
            frontera_t_menos_2 = next(f for f in filas_v if f["tipo_fila"] == "eleccion_t_menos_2")
            frontera_t = next(f for f in filas_v if f["tipo_fila"] == "eleccion_t")
            filas_trimestre = [f for f in filas_v if f["tipo_fila"] == "trimestre"]

            series = {}
            for var in _variables_de(filas, _COLUMNAS_FIJAS):
                if var == "salario_real":
                    series["salario_real_usd"] = [
                        _promedio_trimestre(salario_usd_mensual, _meses_en_ventana(f["fecha_inicio"], f["fecha_fin"]))
                        for f in filas_trimestre
                    ]
                else:
                    series[var] = _serie_variable(filas_trimestre, var)

            nivel_dict[id_transicion] = {
                "anio_t": int(frontera_t["anio_t"]),
                "anio_inicio_ventana": int(frontera_t_menos_2["anio_t_menos_2"]),
                "label": _label_ventana(frontera_t_menos_2["anio_t_menos_2"], frontera_t["anio_t"]),
                "agrupacion_inicio": frontera_t_menos_2["agrupacion_oficialismo"],
                "agrupacion_t": frontera_t["agrupacion_oficialismo"],
                "series": series,
            }
        trayectorias[nivel] = nivel_dict

    variables_final = sorted(variables)
    return {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "niveles": list(NIVELES),
        "variables": variables_final,
        "unidades": {var: _UNIDADES.get(var, "") for var in variables_final},
        "trayectorias": trayectorias,
    }


def generar_trayectorias_economicas_bieleccion(
    destino: Path | str = "docs/trayectorias_economicas_bieleccion_la_plata.html",
    panel_dir: Path | str = PANEL_BIELECCION_TRIMESTRAL_DIR,
    series_mensuales_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
) -> Path:
    payload = construir_payload(panel_dir=panel_dir, series_mensuales_path=series_mensuales_path)

    plantilla_path = Path(__file__).parent / "trayectorias_economicas_template.html"
    plantilla = plantilla_path.read_text(encoding="utf-8")
    html = plantilla.replace(
        "/*__RAW_DATA__*/",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    html = html.replace("__TITULO__", "Trayectorias económicas bielección — Partido de La Plata")
    html = html.replace(
        "__META__",
        "movimiento trimestral de una ventana de 4 años (dos elecciones, t-2 a t) por vez · 2001-2025<br>"
        "fuente: panel_bieleccion_trimestral_&lt;nivel&gt;.csv (series económicas nacionales)",
    )

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    destino_path.write_text(html, encoding="utf-8")
    return destino_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--destino", default="docs/trayectorias_economicas_bieleccion_la_plata.html")
    parser.add_argument("--panel-dir", default=PANEL_BIELECCION_TRIMESTRAL_DIR)
    parser.add_argument("--series-mensuales", default=SERIES_ECONOMICAS_MENSUALES_PATH)
    args = parser.parse_args()

    destino = generar_trayectorias_economicas_bieleccion(
        destino=args.destino, panel_dir=args.panel_dir, series_mensuales_path=args.series_mensuales
    )
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
