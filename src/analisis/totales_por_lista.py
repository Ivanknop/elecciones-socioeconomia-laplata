"""Gráfico de barras horizontales con el resultado total por agrupación
(lista), un gráfico por (año, nivel), a partir de
`electoral.totales.resultado_total_por_agrupacion` -- no relee `data/totales/`
(ese CSV es agnóstico de la clasificación ideológica a propósito, ver
`electoral/totales.py`); acá se colorea por `campo_ideologico`, joineado en
vivo contra `clasificacion_ideologica_agrupaciones.csv` igual que
`serie_temporal_filiacion.py` hace con `filiacion_politica`.

Uso:
    PYTHONPATH=src python -m analisis.totales_por_lista --anio 2023 --nivel intendente
    PYTHONPATH=src python -m analisis.totales_por_lista                    # todo lo disponible
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

from analisis.graficos import IDEOLOGIAS, _COLOR_IDEOLOGIA
from electoral.totales import _combos_disponibles, resultado_total_por_agrupacion

# Mismo mapeo que notebooks/04_totales_por_circuito.ipynb: la clasificación
# usa "gobernacion", el resto de los scripts usa "gobernador".
NIVEL_A_NIVEL_CSV = {"gobernador": "gobernacion"}

_COLOR_SIN_CLASIFICAR = "#9e9e9e"  # no debería usarse nunca: circuito_<nivel>.json exige clasificación (join estricto en notebook 04)


def _cargar_campo_ideologico(agrupaciones_dir: Path | str) -> dict[tuple[str, str, str], str]:
    archivo = Path(agrupaciones_dir) / "clasificacion_ideologica_agrupaciones.csv"
    with open(archivo, encoding="utf-8") as f:
        return {(r["anio"], r["nivel"], r["agrupacion"]): r["campo_ideologico"] for r in csv.DictReader(f)}


def graficar_totales_por_lista(
    data_dir: Path | str, agrupaciones_dir: Path | str, anio: int, nivel: str, ax=None,
):
    totales = resultado_total_por_agrupacion(data_dir, anio, nivel)
    clasificacion = _cargar_campo_ideologico(agrupaciones_dir)
    nivel_csv = NIVEL_A_NIVEL_CSV.get(nivel, nivel)

    colores = []
    for v in totales:
        campo = clasificacion.get((str(anio), nivel_csv, v.nombre_agrupacion))
        colores.append(_COLOR_IDEOLOGIA[IDEOLOGIAS[campo]] if campo else _COLOR_SIN_CLASIFICAR)

    if ax is None:
        _, ax = plt.subplots(figsize=(9, max(3, 0.45 * len(totales))))

    etiquetas = [v.nombre_agrupacion for v in totales]
    valores = [v.votos for v in totales]
    y = range(len(totales))
    barras = ax.barh(y, valores, color=colores)
    ax.set_yticks(list(y), labels=etiquetas, fontsize="small")
    ax.invert_yaxis()  # el más votado arriba
    ax.set_xlabel("votos")
    ax.set_title(f"La Plata — {nivel} {anio} — resultado total por agrupación")
    ax.spines[["top", "right"]].set_visible(False)
    etiquetas_barra = [f"{v.votos:,} ({v.votos_porcentaje:.1f}%)" for v in totales]
    ax.bar_label(barras, labels=etiquetas_barra, padding=3, fontsize="small")
    if valores:
        ax.set_xlim(0, max(valores) * 1.3)  # deja lugar a la derecha de la barra más larga para su etiqueta
    ax.figure.tight_layout()
    return ax.figure


def generar_totales_por_lista(
    data_dir: Path | str, agrupaciones_dir: Path | str, graficos_dir: Path | str, anio: int, nivel: str,
) -> Path:
    salida = Path(graficos_dir)
    salida.mkdir(parents=True, exist_ok=True)

    fig = graficar_totales_por_lista(data_dir, agrupaciones_dir, anio, nivel)
    destino = salida / f"{anio}_{nivel}_barras.png"
    fig.savefig(destino, dpi=100)
    plt.close(fig)

    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, help="si se omite, corre todos los años disponibles")
    parser.add_argument("--nivel", help="si se omite, corre todos los niveles disponibles para ese año")
    parser.add_argument("--data-dir", default="data/distrito")
    parser.add_argument("--agrupaciones-dir", default="data/agrupaciones")
    parser.add_argument("--graficos-dir", default="graficos/distrito/totales_por_lista")
    args = parser.parse_args()

    combos = _combos_disponibles(args.data_dir)
    if args.anio:
        combos = [(anio, nivel) for anio, nivel in combos if anio == args.anio]
    if args.nivel:
        combos = [(anio, nivel) for anio, nivel in combos if nivel == args.nivel]

    if not combos:
        print("sin datos para los filtros pedidos")
        return

    for anio, nivel in combos:
        destino = generar_totales_por_lista(args.data_dir, args.agrupaciones_dir, args.graficos_dir, anio, nivel)
        print(f"{anio} {nivel} -> {destino}")


if __name__ == "__main__":
    main()
