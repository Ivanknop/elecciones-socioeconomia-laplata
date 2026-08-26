"""Gráficos de barras/torta por campo ideológico desde `circuito_<nivel>.json`.
Incluye siempre `blanco_nulo`/`ausentismo`. Única fuente de colores por
campo ideológico/filiación del repo -- ver CLAUDE.md, "Colores de cada
espacio político"."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

from constantes import (
    CAMPO_IDEOLOGICO_PATH,
    COLORIMETRIA_CAMPO_IDEOLOGICO_PATH,
    COLORIMETRIA_FAMILIA_POLITICA_PATH,
    REPO_ROOT,
)

# Antes hardcodeada acá mismo (duplicando `data/agrupaciones/campo_ideologico.csv`,
# que no tenía ningún lector en todo el repo) -- ahora ese CSV es la única
# fuente de la escala, resuelto por ruta absoluta a partir de la raíz del
# repo (`constantes.REPO_ROOT`) para no depender del cwd desde el que se
# importe el módulo.
_CAMPO_IDEOLOGICO_CSV = REPO_ROOT / CAMPO_IDEOLOGICO_PATH
_COLORIMETRIA_CAMPO_CSV = REPO_ROOT / COLORIMETRIA_CAMPO_IDEOLOGICO_PATH
_COLORIMETRIA_FAMILIA_CSV = REPO_ROOT / COLORIMETRIA_FAMILIA_POLITICA_PATH


def _cargar_escala_ideologica(path: Path | str = _CAMPO_IDEOLOGICO_CSV) -> dict[str, str]:
    """{valor: ideología}, mismo orden (izquierda→derecha radical) del CSV;
    valores 1-6 ordinales, no cardinales."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {fila["valor"]: fila["ideologia"] for fila in csv.DictReader(f)}


def _cargar_colorimetria(path: Path | str, columna_clave: str) -> dict[str, str]:
    """{valor: color_hex} desde un CSV de colorimetría de dos columnas
    (`<columna_clave>,color`)."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {fila[columna_clave].strip(): fila["color"].strip() for fila in csv.DictReader(f)}


IDEOLOGIAS = _cargar_escala_ideologica()
_COLOR_IDEOLOGIA = _cargar_colorimetria(_COLORIMETRIA_CAMPO_CSV, "campo_ideologico")
_COLOR_FILIACION = _cargar_colorimetria(_COLORIMETRIA_FAMILIA_CSV, "familia_politica")

# Dos muestras que no son posición ideológica pero tienen que aparecer siempre
# junto al desglose por campo_ideologico/filiacion_politica -- ver
# `_votos_no_ideologicos`. Colores neutros (gris), para no competir con la
# paleta de la colorimetría de ideología/filiación.
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


def etiquetar_puntos(ax, x, y, color: str, arriba: bool = True) -> None:
    """Escribe el valor (`{:.1f}%`) sobre cada punto, mismo color que la
    serie; `arriba` alterna la posición de la etiqueta."""
    offset = (0, 6) if arriba else (0, -10)
    va = "bottom" if arriba else "top"
    for xi, yi in zip(x, y):
        ax.annotate(
            f"{yi:.1f}%", (xi, yi), textcoords="offset points", xytext=offset,
            ha="center", va=va, fontsize="x-small", color=color,
        )


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
    """`blanco_nulo` y `ausentismo` (padrón - votos válidos); procedimentales
    entran en `ausentismo` pero no como categoría propia."""
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
    """Barras de votos por campo ideológico: un circuito, o el acumulado
    del (año, nivel) si `circuito_id` es `None`."""
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
    """Torta (share de votos) por campo ideológico: un circuito, o el
    acumulado del (año, nivel) si `circuito_id` es `None`."""
    claves, valores, colores = _preparar(data_dir, anio, nivel, circuito_id)
    total = sum(valores)

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))

    if total == 0:
        ax.text(0.5, 0.5, "sin votos positivos", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
    elif any(v < 0 for v in valores):
        # Circuitos chicos subdivididos (ej. familia 504/505/508/509, sin
        # resolución equivalente a la 1990/2007 -- ver skill laplata-elecciones)
        # pueden traer más votos que `electores` para ese circuito puntual,
        # lo que da `ausentismo` negativo. Una torta no puede representar un
        # gajo negativo -- se documenta la anomalía en vez de recortar el
        # valor a cero, que ocultaría el problema de padrón subyacente.
        ax.text(
            0.5, 0.5,
            "no se puede graficar: ausentismo negativo en este circuito\n(posible anomalía de padrón, ver skill laplata-elecciones)",
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
