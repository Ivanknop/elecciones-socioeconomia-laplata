"""Pestaña interactiva "Distribución ideológica (V-Party)": cuadrantes
económico × progresismo por (nivel, año), desde `data/tfi_data/elecciones/`
(cobertura 2001-2025, sin desglose por localidad -- ver skill
`laplata-visualizacion`).

Uso:
    PYTHONPATH=src python -m visualizacion.distribucion_ideologica_interactiva
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from analisis.graficos import _COLOR_FILIACION
from analisis.vparty_cuadrantes_local import _color_por_partido
from analisis.vparty_distribucion_tfi import cargar_eleccion, combos_disponibles, limites_globales
from constantes import CARGO_LABEL, ELECCIONES_DIR

_PATRON_CARGO = re.compile(r"\(cargo: (\w+)\)")


def _cargo_de_archivo(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        m = _PATRON_CARGO.search(f.readline())
    return m.group(1) if m else ""


def _serializar_puntos(df: pd.DataFrame) -> list[dict]:
    filiacion_de = {
        fila["agrupacion"]: fila["filiacion_politica"] if pd.notna(fila["filiacion_politica"]) else None
        for _, fila in df.iterrows()
    }
    colores = _color_por_partido(list(df["agrupacion"]), filiacion_de)
    return [
        {
            "agrupacion": fila["agrupacion"],
            "votos": int(fila["votos"]),
            "votos_pct": round(float(fila["votos_porcentaje"]), 2),
            "economico": round(float(fila["economico"]), 3),
            "progresismo": round(float(fila["progresismo"]), 3),
            "populismo": round(float(fila["populismo"]), 3),
            "filiacion": filiacion_de.get(fila["agrupacion"]),
            "color": colores.get(fila["agrupacion"], "#9e9e9e"),
        }
        for _, fila in df.iterrows()
    ]


def construir_payload(elecciones_dir: Path | str = ELECCIONES_DIR) -> dict:
    combos = combos_disponibles(elecciones_dir)
    cargados = [(anio, nivel, path, cargar_eleccion(path)) for anio, nivel, path in combos]
    xlim, ylim = limites_globales([df for _, _, _, df in cargados])

    distrito = {}
    fam_names: set[str] = set()
    for anio, nivel, path, df in cargados:
        if df.empty:
            continue
        cargo = _cargo_de_archivo(path)
        fam_names.update(f for f in df["filiacion_politica"] if pd.notna(f))
        distrito[f"{anio}_{nivel}"] = {
            "anio": anio, "nivel": nivel, "cargo": cargo,
            "cargo_label": CARGO_LABEL.get(cargo, cargo),
            "puntos": _serializar_puntos(df),
        }

    nivel_labels = {nivel: nivel.capitalize() for _, nivel, _, _ in cargados}

    return {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fam_colors": {k: v for k, v in _COLOR_FILIACION.items() if k in fam_names},
        "nivel_labels": nivel_labels,
        "distrito": distrito,
        "eje_limites": {"x": round(xlim[1], 3), "y": round(ylim[1], 3)},
    }


def generar_distribucion_interactiva(
    destino: Path | str = "docs/distribucion_ideologica_la_plata.html",
    elecciones_dir: Path | str = ELECCIONES_DIR,
) -> Path:
    payload = construir_payload(elecciones_dir=elecciones_dir)

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
    parser.add_argument("--elecciones-dir", default=ELECCIONES_DIR)
    args = parser.parse_args()

    destino = generar_distribucion_interactiva(destino=args.destino, elecciones_dir=args.elecciones_dir)
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
