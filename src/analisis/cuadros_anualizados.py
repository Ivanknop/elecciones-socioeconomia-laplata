"""Un gráfico por año que reúne, uno al lado del otro, el total (todos los
circuitos) de cada cargo/nivel disputado ese año, por campo ideológico.

**No suma los cargos entre sí**: cada uno se dibuja como su propia serie de
barras. Sumar Presidente + Gobernador + Intendente en un solo número
sugeriría más comparabilidad de la que realmente hay entre cargos distintos
(el mismo problema que señala §2.4 del plan de correcciones para
`serie_temporal.py`) — acá se evita desde el diseño en vez de repetirlo.

Uso:
    python -m analisis.cuadros_anualizados --anio 2023
    python -m analisis.cuadros_anualizados               # todos los años disponibles
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from analisis.graficos import IDEOLOGIAS, _COLOR_IDEOLOGIA, _cargar_circuito, _votos_por_ideologia

# Cargos que compitieron cada año en La Plata (ver README). No todos los años
# tienen los tres niveles: 2025 legislativo solo trajo Diputados Nacionales
# para este distrito (hallazgo #12 del README).
NIVELES_POR_ANIO = {
    2011: ["presidente", "gobernador", "intendente"],
    2013: ["nacional", "provincial", "municipal"],
    2015: ["presidente", "gobernador", "intendente"],
    2017: ["nacional", "provincial", "municipal"],
    2019: ["presidente", "gobernador", "intendente"],
    2021: ["nacional", "provincial", "municipal"],
    2023: ["presidente", "gobernador", "intendente"],
    2025: ["nacional"],
}

CARGO_LABEL = {
    "presidente": "Presidente",
    "gobernador": "Gobernador",
    "intendente": "Intendente",
    "nacional": "Diputados Nac.",
    "provincial": "Diputados Prov.",
    "municipal": "Concejales",
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
    dentro de cada grupo — todos los cargos de `anio` en el mismo gráfico,
    sin sumarlos entre sí.
    """
    niveles = _niveles_disponibles(data_dir, anio)
    if not niveles:
        raise FileNotFoundError(f"no hay datos de {anio} en {data_dir!r}")

    ideologias = list(IDEOLOGIAS.values())
    totales_por_nivel = {}
    for nivel in niveles:
        contenido = _cargar_circuito(data_dir, anio, nivel)
        totales_por_nivel[nivel] = _votos_por_ideologia(contenido, circuito_id=None)

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 5))

    n_niveles = len(niveles)
    ancho = 0.8 / n_niveles
    x = np.arange(len(ideologias))
    alphas = np.linspace(0.5, 1.0, n_niveles)

    for i, nivel in enumerate(niveles):
        totales = totales_por_nivel[nivel]
        total_nivel = sum(totales.values())
        valores = [totales.get(ideologia, 0) for ideologia in ideologias]
        if en_porcentaje:
            valores = [v / total_nivel * 100 if total_nivel else 0 for v in valores]
        colores = [_COLOR_IDEOLOGIA[ideologia] for ideologia in ideologias]
        ax.bar(
            x + i * ancho, valores, width=ancho * 0.92, label=CARGO_LABEL[nivel],
            color=colores, edgecolor="white", linewidth=0.5, alpha=alphas[i],
        )

    ax.set_xticks(x + ancho * (n_niveles - 1) / 2)
    ax.set_xticklabels(ideologias, rotation=20, ha="right")
    ax.set_ylabel("% de los positivos" if en_porcentaje else "votos")
    metrica = "% por campo ideológico" if en_porcentaje else "votos por campo ideológico"
    ax.set_title(f"La Plata {anio} — {metrica}, por cargo (no sumado entre cargos)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def generar_cuadro_anual(data_dir: Path | str, graficos_dir: Path | str, anio: int) -> Path:
    salida = Path(graficos_dir) / "cuadros_anualizados"
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
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--graficos-dir", default="graficos")
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
