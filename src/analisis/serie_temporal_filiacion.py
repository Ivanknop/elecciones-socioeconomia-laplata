"""Serie temporal por filiación política (2011-2025), un gráfico por nivel de
gobierno -- complementa `serie_temporal.py` (que grafica por `campo_ideologico`,
posición ideológico-programática por elección) con la dimensión de familia/identidad
partidaria (`data/agrupaciones/tabla_referencia_filiacion_politica.csv`), que no
varía por año/nivel -- ver docs/nota_metodologica.md §5.2 y docs/AUDITORIA_ESTADO.md.

No genera el gráfico "_votos" (solo "_filiacion_porcentaje.png") ni toca
`circuito_<nivel>.json`/notebook 04 -- lee `filiacion_politica` en el momento de
graficar, uniendo por `nombre`/`agrupacion` contra
`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`.

Uso:
    python -m analisis.serie_temporal_filiacion                     # los 3 niveles
    python -m analisis.serie_temporal_filiacion --nivel provincial  # uno puntual
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

from analisis.graficos import (
    CATEGORIAS_NO_IDEOLOGICAS,
    _COLOR_FILIACION,
    _cargar_circuito,
    _votos_no_ideologicos,
    color_categoria,
    etiqueta_categoria,
    etiquetar_puntos,
)
from analisis.serie_temporal import CARGO_LABEL, NIVELES, _puntos_del_nivel
from constantes import AGRUPACIONES_DIR, DATA_DISTRITO_DIR

# `_COLOR_FILIACION` (import de arriba) es la única fuente de estos colores
# -- viene de `data/agrupaciones/colorimetria_familia_politica.csv` vía
# `graficos.py`, no se hardcodea acá. El orden de sus filas es el que fija
# el orden de graficado/leyenda (no se cicla ni se reordena por año/nivel).


def _cargar_filiaciones(agrupaciones_dir: Path | str) -> dict[str, str]:
    """`{agrupacion: filiacion_politica}` desde
    `clasificacion_ideologica_agrupaciones.csv` -- no varía por año/nivel, así
    que alcanza con deduplicar por `agrupacion` (verificado 1:1 al fusionar
    `tabla_referencia_filiacion_politica.csv`)."""
    archivo = Path(agrupaciones_dir) / "clasificacion_ideologica_agrupaciones.csv"
    with open(archivo, encoding="utf-8") as f:
        filas = csv.DictReader(f)
        return {r["agrupacion"]: r["filiacion_politica"] for r in filas}


def _votos_por_filiacion(contenido: dict, filiaciones: dict[str, str], circuito_id: str | None) -> dict[str, int]:
    if circuito_id is None:
        circuitos = contenido["circuitos"].values()
    elif circuito_id not in contenido["circuitos"]:
        raise KeyError(f"circuito_id {circuito_id!r} no existe en este archivo")
    else:
        circuitos = [contenido["circuitos"][circuito_id]]

    votos: dict[str, int] = {}
    for c in circuitos:
        for info in c["positivos"].values():
            # KeyError si `nombre` no está en la clasificación -- nunca se
            # enmascara en silencio una agrupación sin filiación asignada,
            # mismo criterio que ya aplica `campo_ideologico` en graficos.py.
            clave = filiaciones[info["nombre"]]
            votos[clave] = votos.get(clave, 0) + info["votos"]
    return votos


def _serie_por_anio_filiacion(data_dir: Path | str, agrupaciones_dir: Path | str, nivel: str):
    """Devuelve (puntos, {filiacion|categoria: [votos por punto]}, [total por
    punto]) con `puntos` = [(año, cargo_especifico), ...] ordenado. Además de
    las filiaciones, la serie siempre trae `blanco_nulo` y `ausentismo`
    (`CATEGORIAS_NO_IDEOLOGICAS`)."""
    puntos = _puntos_del_nivel(data_dir, nivel)
    if not puntos:
        raise FileNotFoundError(f"no hay datos para el nivel {nivel!r} en {data_dir!r}")

    filiaciones = _cargar_filiaciones(agrupaciones_dir)
    categorias = list(_COLOR_FILIACION) + CATEGORIAS_NO_IDEOLOGICAS
    serie = {c: [] for c in categorias}
    totales = []
    for anio, cargo in puntos:
        contenido = _cargar_circuito(data_dir, anio, cargo)
        votos = _votos_por_filiacion(contenido, filiaciones, circuito_id=None)
        votos.update(_votos_no_ideologicos(contenido, circuito_id=None))
        totales.append(sum(votos.values()))
        for c in categorias:
            serie[c].append(votos.get(c, 0))
    return puntos, serie, totales


def graficar_serie_temporal_filiacion(data_dir: Path | str, agrupaciones_dir: Path | str, nivel: str, ax=None):
    """% del padrón por filiación política + blanco/nulo + ausentismo."""
    puntos, serie, totales = _serie_por_anio_filiacion(data_dir, agrupaciones_dir, nivel)
    anios = [a for a, _ in puntos]
    etiquetas_x = [f"{a}\n{CARGO_LABEL[cargo]}" for a, cargo in puntos]

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))

    i = 0
    for filiacion, color in _COLOR_FILIACION.items():
        valores = serie[filiacion]
        if not any(valores):
            continue  # esta filiación no tuvo votos en ningún punto de este nivel -- no ensucia la leyenda
        porcentajes = [v / t * 100 if t else 0 for v, t in zip(valores, totales)]
        ax.plot(anios, porcentajes, marker="o", label=filiacion, color=color)
        etiquetar_puntos(ax, anios, porcentajes, color, arriba=(i % 2 == 0))
        i += 1

    for categoria in CATEGORIAS_NO_IDEOLOGICAS:
        valores = serie[categoria]
        porcentajes = [v / t * 100 if t else 0 for v, t in zip(valores, totales)]
        color = color_categoria(categoria)
        ax.plot(anios, porcentajes, marker="o", label=etiqueta_categoria(categoria), color=color)
        etiquetar_puntos(ax, anios, porcentajes, color, arriba=(i % 2 == 0))
        i += 1

    ax.set_xticks(anios, labels=etiquetas_x, fontsize="small")
    ax.set_ylabel("% del padrón")
    ax.set_title(f"La Plata — {nivel} — % por filiación política + blanco/nulo + ausentismo, {anios[0]}-{anios[-1]}")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize="small", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def generar_serie_temporal_filiacion(
    data_dir: Path | str, agrupaciones_dir: Path | str, graficos_dir: Path | str, nivel: str
) -> Path:
    salida = Path(graficos_dir) / "serie_temporal"
    salida.mkdir(parents=True, exist_ok=True)

    fig = graficar_serie_temporal_filiacion(data_dir, agrupaciones_dir, nivel)
    destino = salida / f"{nivel}_filiacion_porcentaje.png"
    fig.savefig(destino, dpi=100)
    plt.close(fig)

    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nivel", choices=list(NIVELES), help="si se omite, corre los 3 niveles")
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    parser.add_argument("--agrupaciones-dir", default=AGRUPACIONES_DIR)
    parser.add_argument("--graficos-dir", default="graficos/distrito")
    args = parser.parse_args()

    niveles = [args.nivel] if args.nivel else list(NIVELES)
    for nivel in niveles:
        try:
            puntos = _puntos_del_nivel(args.data_dir, nivel)
        except Exception:
            puntos = []
        if not puntos:
            print(f"{nivel}: sin datos, se omite")
            continue
        destino = generar_serie_temporal_filiacion(args.data_dir, args.agrupaciones_dir, args.graficos_dir, nivel)
        anios = [a for a, _ in puntos]
        print(f"{nivel}: {anios[0]}-{anios[-1]} ({len(puntos)} puntos) -> {destino}")


if __name__ == "__main__":
    main()
