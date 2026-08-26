"""Gráfico de la serie ICG headline (La Plata vs. país, mensual), un
panel dos líneas, desde el CSV de `icg_exportar_csv.py`.

Uso:
    PYTHONPATH=src python -m socioeconomia.icg_graficos
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from constantes import ICG_HEADLINE_PATH

_AZUL = "#2a78d6"
_NARANJA = "#eb6834"

RUTA_SALIDA = Path("graficos/socioeconomia/icg/serie_icg_la_plata_pais_2011_presente.png")


def _leer_csv(path: Path | str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _quitar_spines(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)


def graficar_serie_headline(filas: list[dict], ax=None):
    """Serie mensual La Plata vs. país, ICG ponderado (0-5); huecos quedan
    visibles, nunca interpolados."""
    fechas = [date(int(f["año"]), int(f["mes"]), 1) for f in filas]
    la_plata = [float(f["icg_la_plata"]) if f["icg_la_plata"] else None for f in filas]
    pais = [float(f["icg_pais"]) if f["icg_pais"] else None for f in filas]

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 4.5))

    ax.plot(fechas, la_plata, color=_AZUL, linewidth=1.6, label="La Plata")
    ax.plot(fechas, pais, color=_NARANJA, linewidth=1.6, label="País (pooled, incluye La Plata)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylim(0, 5)
    ax.set_ylabel("ICG (0-5)")
    ax.set_title(
        f"Índice de Confianza en el Gobierno — La Plata vs. país, {fechas[0].year}-{fechas[-1].year}\n"
        "Promedio ponderado (ponderacion_UTDT) — fuente: UTDT, Escuela de Gobierno"
    )
    _quitar_spines(ax)
    ax.legend(frameon=False)
    ax.figure.tight_layout()
    return ax.figure


def generar_grafico(
    headline_path: Path | str = ICG_HEADLINE_PATH, destino: Path | str = RUTA_SALIDA,
) -> Path:
    filas = _leer_csv(headline_path)
    fig = graficar_serie_headline(filas)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=100)
    plt.close(fig)
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--headline-path", default=ICG_HEADLINE_PATH)
    parser.add_argument("--destino", default=str(RUTA_SALIDA))
    args = parser.parse_args()

    destino = generar_grafico(args.headline_path, args.destino)
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
