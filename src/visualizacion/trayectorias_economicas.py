"""Pestaña interactiva "Trayectorias económicas trimestrales": elegida una
ventana electoral (nivel + año) de `data/tfi_data/panel/panel_trimestral_
<nivel>.csv` (Fase 5), muestra el movimiento trimestral de una variable
económica dentro de esa ventana -- un gráfico por ventana, no las 31
superpuestas -- por posición relativa (orden 1..N, no fecha calendario)
(ver skill `laplata-visualizacion`).

Uso:
    PYTHONPATH=src python -m visualizacion.trayectorias_economicas
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from constantes import PANEL_TRIMESTRAL_DIR, SERIES_ECONOMICAS_MENSUALES_PATH
from ml_models.construir_calendario import NIVELES
from ml_models.construir_panel_trimestral import _promedio_trimestre
from ml_models.construir_panel_ventanas import _leer_dicts
from ml_models.features_ventana import _meses_en_ventana

_COLUMNAS_FIJAS = {
    "id_transicion",
    "nivel",
    "anio_t",
    "anio_t_menos_1",
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

# Etiquetas para el template, no una fuente nueva del dato -- resumen de
# lo que registro_variables.csv ya documenta (nota_metodologica). `ipc` es
# flujo trimestral (es_flujo=true, ver
# construir_panel_trimestral._variacion_flujo_trimestre), no nivel de índice.
_UNIDADES = {
    "desocupacion": "%",
    "emae": "índice (2004=100)",
    "icc": "índice (puntos)",
    "icg": "índice (puntos)",
    "ipc": "variación % acumulada del trimestre",
    "reservas": "millones de USD",
    "resultado_fiscal": "millones de $ corrientes",
    "salario_real_usd": "RIPTE nominal / tipo de cambio oficial (USD)",
    "tc_oficial": "$ (pesos) por USD",
}


def _variables_de(filas: list[dict], columnas_fijas: set[str] = _COLUMNAS_FIJAS) -> list[str]:
    """Columnas económicas reales presentes en `filas` (D9 -- nunca una
    lista hardcodeada). `columnas_fijas` es parametrizable: la reusa
    `trayectorias_economicas_bieleccion` con su propio esquema fijo."""
    if not filas:
        return []
    return sorted(set(filas[0].keys()) - columnas_fijas)


_ESCALA_PORCENTAJE = {"desocupacion"}


def _serie_variable(filas_trimestre: list[dict], id_variable: str) -> list[float | None]:
    """`None` donde el CSV trae vacío, nunca interpolado. `desocupacion`
    se multiplica por 100: el CSV de origen la trae en fracción 0-1."""
    escala = 100 if id_variable in _ESCALA_PORCENTAJE else 1
    return [float(f[id_variable]) * escala if f[id_variable] != "" else None for f in filas_trimestre]


def _label_ventana(anio_t_menos_1: str, anio_t: str) -> str:
    return f"{anio_t_menos_1}→{anio_t}"


def _cargar_series_mensuales_crudas(path: Path | str) -> dict[str, dict[date, float | None]]:
    """`ipc` acá es el índice crudo, no la variación % que Fase 5 aplica en
    el panel trimestral -- necesario para reconstruir el salario nominal
    (ver `_salario_real_usd_mensual`)."""
    columnas = ("ipc", "tc_oficial", "salario_real")
    series: dict[str, dict[date, float | None]] = {c: {} for c in columnas}
    for r in _leer_dicts(path):
        mes = date.fromisoformat(r["fecha"])
        for c in columnas:
            crudo = r.get(c, "")
            series[c][mes] = float(crudo) if crudo != "" else None
    return series


def _salario_real_usd_mensual(series_mensuales_crudas: dict[str, dict[date, float | None]]) -> dict[date, float | None]:
    """RIPTE en dólar oficial. `salario_real` viene deflactado por `ipc`
    (índice, no pesos) -- se revierte (`nominal = salario_real * ipc / 100`)
    antes de dividir por `tc_oficial`; dividir directo da un orden de
    magnitud equivocado (probado empíricamente: ~15-20 en vez de
    ~1000-1500 USD/mes)."""
    salario_real, ipc, tc = series_mensuales_crudas["salario_real"], series_mensuales_crudas["ipc"], series_mensuales_crudas["tc_oficial"]
    resultado: dict[date, float | None] = {}
    for mes, sr in salario_real.items():
        ipc_v, tc_v = ipc.get(mes), tc.get(mes)
        if sr is None or ipc_v is None or not tc_v:
            resultado[mes] = None
        else:
            resultado[mes] = (sr * ipc_v / 100) / tc_v
    return resultado


def construir_payload(
    panel_dir: Path | str = PANEL_TRIMESTRAL_DIR,
    series_mensuales_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
) -> dict:
    """Pura -- toma directorios/rutas, no hace red."""
    salario_usd_mensual = _salario_real_usd_mensual(_cargar_series_mensuales_crudas(series_mensuales_path))

    trayectorias: dict[str, dict] = {}
    variables: set[str] = set()

    for nivel in NIVELES:
        filas = _leer_dicts(Path(panel_dir) / f"panel_trimestral_{nivel}.csv")
        variables_del_nivel = [v if v != "salario_real" else "salario_real_usd" for v in _variables_de(filas)]
        variables.update(variables_del_nivel)

        por_transicion: dict[str, list[dict]] = {}
        for f in filas:
            por_transicion.setdefault(f["id_transicion"], []).append(f)

        nivel_dict = {}
        for id_transicion, filas_v in por_transicion.items():
            filas_v.sort(key=lambda f: int(f["orden"]))
            frontera_t_menos_1 = next(f for f in filas_v if f["tipo_fila"] == "eleccion_t_menos_1")
            frontera_t = next(f for f in filas_v if f["tipo_fila"] == "eleccion_t")
            filas_trimestre = [f for f in filas_v if f["tipo_fila"] == "trimestre"]

            series = {}
            for var in _variables_de(filas):
                if var == "salario_real":
                    series["salario_real_usd"] = [
                        _promedio_trimestre(salario_usd_mensual, _meses_en_ventana(f["fecha_inicio"], f["fecha_fin"]))
                        for f in filas_trimestre
                    ]
                else:
                    series[var] = _serie_variable(filas_trimestre, var)

            nivel_dict[id_transicion] = {
                "anio_t": int(frontera_t["anio_t"]),
                "anio_inicio_ventana": int(frontera_t_menos_1["anio_t_menos_1"]),
                "label": _label_ventana(frontera_t_menos_1["anio_t_menos_1"], frontera_t["anio_t"]),
                "agrupacion_inicio": frontera_t_menos_1["agrupacion_oficialismo"],
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


def generar_trayectorias_economicas(
    destino: Path | str = "docs/trayectorias_economicas_la_plata.html",
    panel_dir: Path | str = PANEL_TRIMESTRAL_DIR,
    series_mensuales_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
) -> Path:
    payload = construir_payload(panel_dir=panel_dir, series_mensuales_path=series_mensuales_path)

    plantilla_path = Path(__file__).parent / "trayectorias_economicas_template.html"
    plantilla = plantilla_path.read_text(encoding="utf-8")
    html = plantilla.replace(
        "/*__RAW_DATA__*/",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    html = html.replace("__TITULO__", "Trayectorias económicas trimestrales — Partido de La Plata")
    html = html.replace(
        "__META__",
        "movimiento trimestral de una ventana electoral por vez · 2001-2025<br>"
        "fuente: panel_trimestral_&lt;nivel&gt;.csv (series económicas nacionales)",
    )

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    destino_path.write_text(html, encoding="utf-8")
    return destino_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--destino", default="docs/trayectorias_economicas_la_plata.html")
    parser.add_argument("--panel-dir", default=PANEL_TRIMESTRAL_DIR)
    parser.add_argument("--series-mensuales", default=SERIES_ECONOMICAS_MENSUALES_PATH)
    args = parser.parse_args()

    destino = generar_trayectorias_economicas(
        destino=args.destino, panel_dir=args.panel_dir, series_mensuales_path=args.series_mensuales
    )
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
