"""Genera, para un (año, nivel), los gráficos de barras y torta por campo
ideológico: uno por cada circuito, más uno acumulado con el total del
(año, nivel).

Uso:
    python -m analisis.generar_graficos --anio 2011 --nivel intendente
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

from analisis.graficos import graficar_barras, graficar_torta
from constantes import DATA_DISTRITO_DIR


def generar_graficos(data_dir: Path | str, graficos_dir: Path | str, anio: int, nivel: str) -> Path:
    data_dir = Path(data_dir)
    circuito_json = data_dir / str(anio) / nivel / "generales" / f"circuito_{nivel}.json"
    contenido = json.loads(circuito_json.read_text(encoding="utf-8"))
    circuito_ids = sorted(contenido["circuitos"])

    salida = Path(graficos_dir) / str(anio) / nivel
    salida.mkdir(parents=True, exist_ok=True)

    for circuito_id in [*circuito_ids, None]:  # None = acumulado, se hace al final
        nombre = circuito_id if circuito_id is not None else "total"

        fig = graficar_barras(data_dir, anio, nivel, circuito_id)
        fig.savefig(salida / f"{nombre}_barras.png", dpi=100)
        plt.close(fig)

        fig = graficar_torta(data_dir, anio, nivel, circuito_id)
        fig.savefig(salida / f"{nombre}_torta.png", dpi=100)
        plt.close(fig)

    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, required=True)
    parser.add_argument("--nivel", required=True, help="presidente | gobernador | intendente | nacional | provincial | municipal")
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    parser.add_argument("--graficos-dir", default="graficos/distrito")
    args = parser.parse_args()

    salida = generar_graficos(args.data_dir, args.graficos_dir, args.anio, args.nivel)
    circuito_json = Path(args.data_dir) / str(args.anio) / args.nivel / "generales" / f"circuito_{args.nivel}.json"
    n_circuitos = len(json.loads(circuito_json.read_text(encoding="utf-8"))["circuitos"])
    print(f"{n_circuitos} circuitos + 1 acumulado -> {salida} ({(n_circuitos + 1) * 2} imágenes)")


if __name__ == "__main__":
    main()
