"""Pestaña interactiva "Distancia ideológica por fuerza": para cada nivel,
un scatter de burbujas año × distancia al oficialismo con signo (D18,
`data/tfi_data/distancias_ideologicas.csv`).

Uso:
    PYTHONPATH=src python -m visualizacion.distancia_por_fuerza
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from constantes import DISTANCIAS_IDEOLOGICAS_PATH

_COLOR_DERECHA = "#2966a3"
_COLOR_IZQUIERDA = "#c0392b"
_COLOR_NEUTRO = "#9e9e9e"


def _lado_y_color(distancia_economico: float) -> tuple[str, str]:
    if distancia_economico == 0:
        return "oficialismo_o_empate", _COLOR_NEUTRO
    if distancia_economico > 0:
        return "derecha", _COLOR_DERECHA
    return "izquierda", _COLOR_IZQUIERDA


def _serializar_puntos(df: pd.DataFrame) -> list[dict]:
    puntos = []
    for _, fila in df.iterrows():
        lado, color = _lado_y_color(fila["distancia_economico_al_oficialismo"])
        signo = {"derecha": 1.0, "izquierda": -1.0, "oficialismo_o_empate": 0.0}[lado]
        puntos.append({
            "anio": int(fila["anio"]),
            "agrupacion": fila["agrupacion"],
            "share": round(float(fila["share"]), 2),
            "es_oficialismo": bool(fila["es_oficialismo"]),
            "distancia_economico": round(float(fila["distancia_economico_al_oficialismo"]), 3),
            "distancia_progresismo": round(float(fila["distancia_progresismo_al_oficialismo"]), 3),
            "distancia_euclidea": round(float(fila["distancia_euclidea_al_oficialismo"]), 3),
            "distancia_firmada": round(signo * float(fila["distancia_euclidea_al_oficialismo"]), 3),
            "lado": lado,
            "color": color,
        })
    return puntos


def construir_payload(path: Path | str = DISTANCIAS_IDEOLOGICAS_PATH) -> dict:
    """Solo fuerzas viables con V-Party cargado (`distancia_euclidea_al_oficialismo`
    no vacío) -- lo que no tiene score no entra al gráfico, no se imputa."""
    df = pd.read_csv(path)
    df = df.dropna(subset=["distancia_euclidea_al_oficialismo"])

    puntos_por_nivel = {nivel: _serializar_puntos(grupo) for nivel, grupo in df.groupby("nivel")}

    return {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "niveles": sorted(puntos_por_nivel.keys()),
        "puntos": puntos_por_nivel,
        "anio_min": int(df["anio"].min()),
        "anio_max": int(df["anio"].max()),
        "distancia_max": round(float(df["distancia_euclidea_al_oficialismo"].max()), 3),
    }


def generar_distancia_por_fuerza(
    destino: Path | str = "docs/distancia_por_fuerza_la_plata.html",
    path: Path | str = DISTANCIAS_IDEOLOGICAS_PATH,
) -> Path:
    payload = construir_payload(path=path)

    plantilla_path = Path(__file__).parent / "distancia_por_fuerza_template.html"
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
    parser.add_argument("--destino", default="docs/distancia_por_fuerza_la_plata.html")
    parser.add_argument("--path", default=DISTANCIAS_IDEOLOGICAS_PATH)
    args = parser.parse_args()

    destino = generar_distancia_por_fuerza(destino=args.destino, path=args.path)
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
