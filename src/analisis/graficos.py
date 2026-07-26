"""Gráficos de barras y torta por campo ideológico, a partir de los JSON de
totales por circuito (`data/<anio>/<nivel>/circuito_<nivel>.json`, ver
`notebooks/04_totales_por_circuito.ipynb`).

Funciones reutilizables: se llaman con el (año, nivel, circuito) que haga
falta y devuelven la figura. `circuito_id=None` agrega todos los circuitos
de ese (año, nivel) — el acumulado de La Plata. Para generar los gráficos de
todos los circuitos de un (año, nivel) de una sola vez, ver
`generar_graficos.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

IDEOLOGIAS = {
    "1": "izquierda",
    "2": "centro izquierda",
    "3": "centro",
    "4": "centro derecha",
    "5": "derecha",
    "6": "derecha radical",
}

_COLOR_IDEOLOGIA = {
    "izquierda": "#0d366b",
    "centro izquierda": "#256abf",
    "centro": "#86b6ef",
    "centro derecha": "#f4a889",
    "derecha": "#d9573f",
    "derecha radical": "#8f1d0f",
}


def _cargar_circuito(data_dir: Path | str, anio: int, nivel: str) -> dict:
    path = Path(data_dir) / str(anio) / nivel / f"circuito_{nivel}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _votos_por_ideologia(contenido: dict, circuito_id: str | None) -> dict[str, int]:
    if circuito_id is None:
        circuitos = contenido["circuitos"].values()
    elif circuito_id not in contenido["circuitos"]:
        raise KeyError(f"circuito_id {circuito_id!r} no existe en este archivo")
    else:
        circuitos = [contenido["circuitos"][circuito_id]]

    votos: dict[str, int] = {}
    for c in circuitos:
        for info in c["positivos"].values():
            clave = IDEOLOGIAS[info["campo_ideologico"]]
            votos[clave] = votos.get(clave, 0) + info["votos"]
    return votos


def _preparar(data_dir, anio, nivel, circuito_id) -> tuple[list[str], list[int], list[str]]:
    contenido = _cargar_circuito(data_dir, anio, nivel)
    votos = _votos_por_ideologia(contenido, circuito_id)
    claves = [c for c in IDEOLOGIAS.values() if c in votos]  # conserva izquierda -> derecha radical
    return claves, [votos[c] for c in claves], [_COLOR_IDEOLOGIA[c] for c in claves]


def _titulo(anio: int, nivel: str, circuito_id: str | None) -> str:
    alcance = f"circuito {circuito_id}" if circuito_id else "acumulado, todos los circuitos"
    return f"La Plata — {nivel} {anio} — {alcance}"


def graficar_barras(data_dir: Path | str, anio: int, nivel: str, circuito_id: str | None = None, ax=None):
    """Gráfico de barras de votos por campo ideológico, para un circuito puntual
    o para el acumulado de todo el (año, nivel) si `circuito_id` es `None`.
    """
    claves, valores, colores = _preparar(data_dir, anio, nivel, circuito_id)
    total = sum(valores)

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4))
    barras = ax.bar(claves, valores, color=colores)
    ax.set_ylabel("votos")
    ax.set_title(_titulo(anio, nivel, circuito_id))
    ax.tick_params(axis="x", rotation=30)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(y=0.15)  # deja lugar arriba de las barras para las etiquetas
    if total == 0:
        etiquetas = [f"{v:,}" for v in valores]
    else:
        etiquetas = [f"{v:,}\n({v / total:.1%})" for v in valores]
    ax.bar_label(barras, labels=etiquetas, padding=3, fontsize="small")
    ax.figure.tight_layout()
    return ax.figure


def graficar_torta(data_dir: Path | str, anio: int, nivel: str, circuito_id: str | None = None, ax=None):
    """Gráfico de torta (share de votos) por campo ideológico, para un circuito
    puntual o para el acumulado de todo el (año, nivel) si `circuito_id` es `None`.
    """
    claves, valores, colores = _preparar(data_dir, anio, nivel, circuito_id)
    total = sum(valores)

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))

    if total == 0:
        ax.text(0.5, 0.5, "sin votos positivos", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
    else:
        def autopct(pct):
            votos = round(pct / 100 * total)
            return f"{votos:,}\n{pct:.1f}%"

        _, _, autotexts = ax.pie(valores, colors=colores, autopct=autopct, pctdistance=0.75)
        for text in autotexts:
            text.set_color("white")
            text.set_fontsize("small")
        ax.legend(claves, loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize="small", frameon=False)

    ax.set_title(_titulo(anio, nivel, circuito_id))
    ax.figure.tight_layout()
    return ax.figure
