"""Un gráfico por año con el total (todos los circuitos) de cada cargo/nivel
disputado ese año, por campo ideológico. No suma los cargos entre sí.

Uso:
    python -m analisis.cuadros_anualizados --anio 2023
    python -m analisis.cuadros_anualizados               # todos los años disponibles
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from analisis.graficos import (
    CATEGORIAS_NO_IDEOLOGICAS,
    IDEOLOGIAS,
    _cargar_circuito,
    _votos_no_ideologicos,
    _votos_por_ideologia,
    color_categoria,
    etiqueta_categoria,
)
from constantes import CARGO_LABEL, DATA_DISTRITO_DIR

NIVELES_POR_ANIO = {
    2001: ["nacional", "provincial", "municipal"],
    2003: ["presidente", "gobernador", "intendente"],
    2005: ["nacional", "provincial", "municipal"],
    2007: ["presidente", "gobernador", "intendente"],
    2009: ["nacional", "provincial", "municipal"],
    2011: ["presidente", "gobernador", "intendente"],
    2013: ["nacional", "provincial", "municipal"],
    2015: ["presidente", "gobernador", "intendente"],
    2017: ["nacional", "provincial", "municipal"],
    2019: ["presidente", "gobernador", "intendente"],
    2021: ["nacional", "provincial", "municipal"],
    2023: ["presidente", "gobernador", "intendente"],
    2025: ["nacional"],
}

def _niveles_disponibles(data_dir: Path | str, anio: int) -> list[str]:
    data_dir = Path(data_dir)
    return [
        nivel
        for nivel in NIVELES_POR_ANIO.get(anio, [])
        if (data_dir / str(anio) / nivel / "generales" / f"circuito_{nivel}.json").exists()
    ]


def graficar_cuadro_anual(data_dir: Path | str, anio: int, en_porcentaje: bool = False, ax=None):
    """Barras agrupadas: un grupo por campo ideológico, una barra por cargo
    dentro de cada grupo.
    """
    niveles = _niveles_disponibles(data_dir, anio)
    if not niveles:
        raise FileNotFoundError(f"no hay datos de {anio} en {data_dir!r}")

    categorias = list(IDEOLOGIAS.values()) + CATEGORIAS_NO_IDEOLOGICAS
    totales_por_nivel = {}
    for nivel in niveles:
        contenido = _cargar_circuito(data_dir, anio, nivel)
        totales = _votos_por_ideologia(contenido, circuito_id=None)
        totales.update(_votos_no_ideologicos(contenido, circuito_id=None))
        totales_por_nivel[nivel] = totales

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 5))

    n_niveles = len(niveles)
    ancho = 0.8 / n_niveles
    x = np.arange(len(categorias))
    alphas = np.linspace(0.5, 1.0, n_niveles)

    for i, nivel in enumerate(niveles):
        totales = totales_por_nivel[nivel]
        total_nivel = sum(totales.values())
        valores = [totales.get(categoria, 0) for categoria in categorias]
        if en_porcentaje:
            valores = [v / total_nivel * 100 if total_nivel else 0 for v in valores]
        colores = [color_categoria(categoria) for categoria in categorias]
        ax.bar(
            x + i * ancho, valores, width=ancho * 0.92, label=CARGO_LABEL[nivel],
            color=colores, edgecolor="white", linewidth=0.5, alpha=alphas[i],
        )

    ax.set_xticks(x + ancho * (n_niveles - 1) / 2)
    ax.set_xticklabels([etiqueta_categoria(categoria) for categoria in categorias], rotation=20, ha="right")
    ax.set_ylabel("% del padrón" if en_porcentaje else "votos / personas")
    metrica = "% del padrón" if en_porcentaje else "votos y ausentismo"
    ax.set_title(f"La Plata {anio} — {metrica}, por campo ideológico + blanco/nulo + ausentismo, por cargo")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def generar_cuadro_anual(data_dir: Path | str, graficos_dir: Path | str, anio: int) -> Path:
    salida = Path(graficos_dir) / str(anio)
    salida.mkdir(parents=True, exist_ok=True)

    fig = graficar_cuadro_anual(data_dir, anio, en_porcentaje=False)
    fig.savefig(salida / f"{anio}_votos.png", dpi=100)
    plt.close(fig)

    fig = graficar_cuadro_anual(data_dir, anio, en_porcentaje=True)
    fig.savefig(salida / f"{anio}_porcentaje.png", dpi=100)
    plt.close(fig)

    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, help="si se omite, corre todos los años disponibles")
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    parser.add_argument("--graficos-dir", default="graficos/distrito")
    args = parser.parse_args()

    anios = [args.anio] if args.anio else sorted(NIVELES_POR_ANIO)
    for anio in anios:
        niveles = _niveles_disponibles(args.data_dir, anio)
        if not niveles:
            print(f"{anio}: sin datos, se omite")
            continue
        salida = generar_cuadro_anual(args.data_dir, args.graficos_dir, anio)
        print(f"{anio}: {niveles} -> {salida}/{anio}_{{votos,porcentaje}}.png")


if __name__ == "__main__":
    main()
