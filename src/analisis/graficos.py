"""Gráficos de barras y torta por campo ideológico, a partir de los JSON de
totales por circuito (`data/<anio>/<nivel>/generales/circuito_<nivel>.json`,
ver `notebooks/04_totales_por_circuito.ipynb`). Siempre incluyen, además de
las categorías ideológicas, `blanco_nulo` y `ausentismo`
(`CATEGORIAS_NO_IDEOLOGICAS`, `_votos_no_ideologicos`).

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

# Dos muestras que no son posición ideológica pero tienen que aparecer siempre
# junto al desglose por campo_ideologico/filiacion_politica -- ver
# `_votos_no_ideologicos`. Colores neutros (gris), para no competir con la
# paleta divergente azul-rojo de la ideología.
CATEGORIAS_NO_IDEOLOGICAS = ["blanco_nulo", "ausentismo"]

_ETIQUETA_NO_IDEOLOGICA = {
    "blanco_nulo": "blanco + nulo",
    "ausentismo": "ausentismo",
}

_COLOR_NO_IDEOLOGICA = {
    "blanco_nulo": "#c9c9c9",
    "ausentismo": "#4d4d4d",
}

_CLAVES_BLANCO_NULO = {"EN BLANCO", "BLANCOS", "NULO", "NULOS"}


def etiqueta_categoria(categoria: str) -> str:
    """Texto para eje/leyenda."""
    return _ETIQUETA_NO_IDEOLOGICA.get(categoria, categoria)


def color_categoria(categoria: str) -> str:
    return _COLOR_IDEOLOGIA.get(categoria) or _COLOR_NO_IDEOLOGICA[categoria]


def _cargar_circuito(data_dir: Path | str, anio: int, nivel: str) -> dict:
    path = Path(data_dir) / str(anio) / nivel / "generales" / f"circuito_{nivel}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _circuitos_seleccionados(contenido: dict, circuito_id: str | None) -> list[dict]:
    if circuito_id is None:
        return list(contenido["circuitos"].values())
    if circuito_id not in contenido["circuitos"]:
        raise KeyError(f"circuito_id {circuito_id!r} no existe en este archivo")
    return [contenido["circuitos"][circuito_id]]


def _votos_por_ideologia(contenido: dict, circuito_id: str | None) -> dict[str, int]:
    votos: dict[str, int] = {}
    for c in _circuitos_seleccionados(contenido, circuito_id):
        for info in c["positivos"].values():
            clave = IDEOLOGIAS[info["campo_ideologico"]]
            votos[clave] = votos.get(clave, 0) + info["votos"]
    return votos


def _votos_no_ideologicos(contenido: dict, circuito_id: str | None) -> dict[str, int]:
    """`blanco_nulo` (fue a votar, no eligió agrupación) y `ausentismo`
    (padrón - votos válidos).

    Votos válidos = positivos + todo `otros` (blanco, nulo, recurridos,
    impugnados/comando -- lo que exista ese año). Los procedimentales
    (recurridos/impugnados/comando) entran en la resta de `ausentismo` pero,
    a diferencia de `blanco_nulo`, no se muestran como categoría propia.
    """
    electores = positivos = otros_total = blanco_nulo = 0
    for c in _circuitos_seleccionados(contenido, circuito_id):
        electores += c["electores"]
        positivos += sum(info["votos"] for info in c["positivos"].values())
        for categoria, votos in c["otros"].items():
            otros_total += votos
            if categoria.upper() in _CLAVES_BLANCO_NULO:
                blanco_nulo += votos
    return {"blanco_nulo": blanco_nulo, "ausentismo": electores - positivos - otros_total}


def _preparar(data_dir, anio, nivel, circuito_id) -> tuple[list[str], list[int], list[str]]:
    contenido = _cargar_circuito(data_dir, anio, nivel)
    votos = _votos_por_ideologia(contenido, circuito_id)
    extra = _votos_no_ideologicos(contenido, circuito_id)
    ideologias = [c for c in IDEOLOGIAS.values() if c in votos]  # conserva izquierda -> derecha radical
    claves = ideologias + CATEGORIAS_NO_IDEOLOGICAS
    valores = [votos[c] for c in ideologias] + [extra[c] for c in CATEGORIAS_NO_IDEOLOGICAS]
    etiquetas = [etiqueta_categoria(c) for c in claves]
    return etiquetas, valores, [color_categoria(c) for c in claves]


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
    ax.set_ylabel("votos / personas")
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
    elif any(v < 0 for v in valores):
        # Circuitos chicos subdivididos (ej. familia 504/505/508/509, sin
        # resolución equivalente a la 1990/2007 -- ver skill laplata-electoral)
        # pueden traer más votos que `electores` para ese circuito puntual,
        # lo que da `ausentismo` negativo. Una torta no puede representar un
        # gajo negativo -- se documenta la anomalía en vez de recortar el
        # valor a cero, que ocultaría el problema de padrón subyacente.
        ax.text(
            0.5, 0.5,
            "no se puede graficar: ausentismo negativo en este circuito\n(posible anomalía de padrón, ver skill laplata-electoral)",
            ha="center", va="center", wrap=True, transform=ax.transAxes,
        )
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
