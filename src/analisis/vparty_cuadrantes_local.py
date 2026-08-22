"""Gráfico de cuadrantes ideológicos (económico × progresismo) con votos
reales de La Plata, análogo a `vparty_cuadrantes.py` pero construido con
los datos locales en vez del dataset nacional de V-Party -- el encoding de
color/tamaño difiere por grano, ver más abajo.

Fuente de posición: las columnas `vparty_economico`/`vparty_progresismo`/
`vparty_populismo` ya cargadas en `clasificacion_ideologica_agrupaciones.csv`
(fuente real V-Party + estimación propia por encuesta de expertos, ver
`docs/vparty_cuadrantes.md`) -- **no** se recalcula ni se aproxima nada acá,
solo se filtran las agrupaciones que ya tienen esas tres columnas pobladas
para cada (año, cargo); el resto queda fuera del gráfico, mismo criterio
que `vparty_cuadrantes.cargar_posiciones`.

Cada punto es una agrupación en una elección "generales" (PASO/balotaje no
se grafican, mismo alcance que `totales_por_lista.py`).

**Encoding visual distinto por grano** -- son dos preguntas distintas, no
una elección de estilo:

- **distrito** (una elección a la vez, ver más abajo): color = familia
  política (`filiacion_politica`, sombreada por partido dentro de la
  familia -- ver `_color_por_partido`, misma colorimetría que
  `colorimetria_familia_politica.csv`, la única fuente de esos colores en
  el repo, ver CLAUDE.md "Colores de cada espacio político"), tamaño = %
  de votos de ese partido en esa elección puntual. Populismo queda **fuera
  del gráfico** por ahora (no ocupa ni color ni tamaño), aunque la columna
  sigue disponible en `tabla_distrito` para quien la quiera agregar
  después.
- **localidad** (todas las elecciones juntas en un solo PNG, ver más
  abajo): sigue el esquema original de `vparty_cuadrantes.graficar_cuadrantes`
  -- color = año (para poder seguir a una misma fuerza de elección en
  elección), tamaño = populismo, con fusión de puntos cercanos entre años
  vía `vparty_cuadrantes._fusionar_por_cercania`. No se tocó todavía --
  mismo encoding que antes de este cambio.

**Nivel unificado, no por cargo**: `presidente`/`nacional`,
`gobernador`/`provincial` e `intendente`/`municipal` son el mismo nivel de
gobierno visto en años ejecutivos vs. legislativos -- graficarlos por
separado los deja con la mitad de las elecciones cada uno (ejecutivo:
2011/2015/2019/2023; legislativo: 2013/2017/2021/2025), cuando lo que
importa acá es la serie completa 2011-2025 de ese nivel. Por eso este
módulo reusa `NIVELES`/`_puntos_del_nivel` de `analisis.serie_temporal`
(mismo mapeo que ya combina ambos cargos ahí) en vez de tratar los 6
nombres de directorio de `data/distrito/` como niveles independientes --
un año nunca tiene los dos cargos de un mismo nivel a la vez, así que no
hay ambigüedad al fusionarlos en una sola serie por año.

Dos grillas de agregación (fuente de votos, no de encoding visual -- eso ya
está arriba):

- **distrito**: sumando votos de toda La Plata -- a partir de
  `electoral.totales.resultado_total_por_agrupacion`. Va a
  `graficos/agrupaciones/<año>/v_party_<nivel>.png` (git-tracked, mismo
  criterio que los PNG nacionales que ya viven en `graficos/agrupaciones/`).
- **localidad**: sumando votos solo de los circuitos de esa localidad --
  mismo crosswalk geolocalizado que usa `analisis.cuadros_por_localidad`
  por defecto (`data/geolocalizacion/circuitos_por_localidad.csv`, vía
  `electoral.localidades.agrupar_resultados_por_localidad`, agnóstica de
  que acá se agrupa por agrupación en vez de por campo_ideologico). Va a
  `graficos/por_localidad/vparty/` (no versionado, mismo criterio que el
  resto de `graficos/por_localidad/`: se regenera en un par de minutos).

El join año/cargo/agrupación usa `NIVEL_A_NIVEL_CSV` de
`analisis.totales_por_lista` (mismo `"gobernador"` -> `"gobernacion"` que
resuelve ese script) -- `clasificacion_ideologica_agrupaciones.csv` nombra
ese cargo distinto al resto del pipeline, ver `docs/FUNCIONALIDADES.md`.

Uso:
    PYTHONPATH=src python -m analisis.vparty_cuadrantes_local --grano distrito
    PYTHONPATH=src python -m analisis.vparty_cuadrantes_local --grano localidad --nivel municipal
    PYTHONPATH=src python -m analisis.vparty_cuadrantes_local              # todo lo disponible
"""
from __future__ import annotations

import argparse
import colorsys
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analisis.graficos import _COLOR_FILIACION
from analisis.serie_temporal import NIVELES, _puntos_del_nivel
from analisis.totales_por_lista import NIVEL_A_NIVEL_CSV, _COLOR_SIN_CLASIFICAR
from analisis.vparty_cuadrantes import EJE_X, EJE_Y, _asignar_offsets, _radio_por_populismo, graficar_cuadrantes
from constantes import (
    CARGO_LABEL,
    CIRCUITOS_POR_LOCALIDAD_PATH,
    CLASIFICACION_IDEOLOGICA_PATH,
    DATA_DISTRITO_DIR,
)
from electoral.localidades import agrupar_resultados_por_localidad, cargar_circuito_localidad_geo
from electoral.totales import resultado_total_por_agrupacion

RUTA_DISTRITO_DIR = Path("graficos/agrupaciones")
RUTA_LOCALIDAD_DIR = Path("graficos/por_localidad/vparty")

_CMAP_ANIOS = plt.get_cmap("tab10")

# Rango de luminosidad (HLS) dentro del cual se generan las sombras por
# partido de un mismo color de familia -- ni tan claro que se pierda contra
# el fondo blanco, ni tan oscuro que se acerque al negro.
_LUMINOSIDAD_MIN, _LUMINOSIDAD_MAX = 0.25, 0.78


# ---------------------------------------------------------------------------
# 1. Posiciones V-Party propias (real + estimación) por (año, nivel_csv, agrupación)
# ---------------------------------------------------------------------------

def cargar_posiciones_propias(
    path: Path | str = CLASIFICACION_IDEOLOGICA_PATH,
) -> dict[tuple[str, str, str], tuple[float, float, float]]:
    """(anio, nivel_csv, agrupacion) -> (economico, progresismo, populismo)
    para las filas de `clasificacion_ideologica_agrupaciones.csv` con
    cobertura V-Party -- las demás quedan afuera de este gráfico.
    """
    posiciones = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["vparty_economico"]:
                continue
            clave = (r["anio"], r["nivel"], r["agrupacion"])
            posiciones[clave] = (
                float(r["vparty_economico"]),
                float(r["vparty_progresismo"]),
                float(r["vparty_populismo"]),
            )
    return posiciones


def cargar_filiaciones(
    path: Path | str = CLASIFICACION_IDEOLOGICA_PATH,
) -> dict[tuple[str, str, str], str]:
    """(anio, nivel_csv, agrupacion) -> filiacion_politica, para colorear
    cada partido en base al color de su familia política ya definido en
    `colorimetria_familia_politica.csv` (ver `_color_por_partido`) en vez
    de inventar una paleta nueva. Independiente del filtro de cobertura
    V-Party de `cargar_posiciones_propias` -- una agrupación puede tener
    `filiacion_politica` sin tener aún posición V-Party."""
    filiaciones = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["filiacion_politica"]:
                continue
            filiaciones[(r["anio"], r["nivel"], r["agrupacion"])] = r["filiacion_politica"]
    return filiaciones


# ---------------------------------------------------------------------------
# 2. Grano distrito (toda La Plata, un total por año)
# ---------------------------------------------------------------------------

def tabla_distrito(
    nivel: str,
    posiciones: dict[tuple[str, str, str], tuple[float, float, float]],
    data_dir: Path | str = DATA_DISTRITO_DIR,
) -> pd.DataFrame:
    """Una fila por (agrupación, año) con cobertura V-Party, sumando votos
    de todos los circuitos de La Plata para cada año "generales" disponible
    del `nivel` unificado (combina el cargo ejecutivo y el legislativo de
    ese nivel, ver `analisis.serie_temporal.NIVELES`)."""
    filas = []
    for anio, cargo in _puntos_del_nivel(data_dir, nivel):
        nivel_csv = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
        for v in resultado_total_por_agrupacion(data_dir, anio, cargo):
            clave = (str(anio), nivel_csv, v.nombre_agrupacion)
            if clave not in posiciones:
                continue
            econ, prog, pop = posiciones[clave]
            filas.append({
                "agrupacion": v.nombre_agrupacion, "year": anio,
                "economico": econ, "progresismo": prog, "populismo": pop,
                "votos": v.votos, "votos_porcentaje": v.votos_porcentaje,
            })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 3. Grano localidad (votos por agrupación agregados por circuito->localidad)
# ---------------------------------------------------------------------------

def _votos_por_circuito_agrupacion(contenido: dict) -> dict[str, dict[str, float]]:
    """circuito_id -> {agrupacion: votos}, análogo a
    `cuadros_por_localidad._votos_por_circuito` pero sin bucketizar por
    campo_ideologico -- acá se necesita el detalle por agrupación para
    poder unir contra las posiciones V-Party propias."""
    resultados: dict[str, dict[str, float]] = {}
    for circuito_id, circuito in contenido["circuitos"].items():
        fila: dict[str, float] = {}
        for info in circuito["positivos"].values():
            fila[info["nombre"]] = fila.get(info["nombre"], 0) + info["votos"]
        resultados[circuito_id] = fila
    return resultados


def tabla_localidades(
    nivel: str,
    posiciones: dict[tuple[str, str, str], tuple[float, float, float]],
    data_dir: Path | str = DATA_DISTRITO_DIR,
    crosswalk_path: Path | str = CIRCUITOS_POR_LOCALIDAD_PATH,
) -> pd.DataFrame:
    """Una fila por (localidad, agrupación, año) con cobertura V-Party, para
    las localidades de una vez -- evita recalcular el groupby por circuito
    una vez por localidad. `nivel` es el nivel unificado (ver
    `tabla_distrito`), no un nombre de directorio de `data/distrito/`."""
    mapa = cargar_circuito_localidad_geo(crosswalk_path)

    filas = []
    for anio, cargo in _puntos_del_nivel(data_dir, nivel):
        nivel_csv = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
        circuito_json = Path(data_dir) / str(anio) / cargo / "generales" / f"circuito_{cargo}.json"
        contenido = json.loads(circuito_json.read_text(encoding="utf-8"))
        resultados = _votos_por_circuito_agrupacion(contenido)
        agrupado, _reporte = agrupar_resultados_por_localidad(resultados, mapa, fuente=str(crosswalk_path))

        columnas_agrupacion = [c for c in agrupado.columns if c not in ("localidad", "circuitos")]
        for _, fila_loc in agrupado.iterrows():
            localidad = fila_loc["localidad"]
            for nombre_agrup in columnas_agrupacion:
                votos = fila_loc[nombre_agrup]
                if not votos:
                    continue
                clave = (str(anio), nivel_csv, nombre_agrup)
                if clave not in posiciones:
                    continue
                econ, prog, pop = posiciones[clave]
                filas.append({
                    "localidad": localidad, "agrupacion": nombre_agrup, "year": anio,
                    "economico": econ, "progresismo": prog, "populismo": pop,
                    "votos": votos,
                })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 4. Graficado
# ---------------------------------------------------------------------------

def _color_por_anio(anios: list[int]) -> dict[int, str]:
    return {anio: _CMAP_ANIOS(i % 10) for i, anio in enumerate(sorted(set(anios)))}


def _sombras(color_hex: str, n: int) -> list[str]:
    """`n` variaciones de luminosidad de `color_hex` (mismo matiz/saturación,
    luminosidad repartida en `[_LUMINOSIDAD_MIN, _LUMINOSIDAD_MAX]`), para
    distinguir partidos dentro de una misma familia política sin abandonar
    el color de esa familia."""
    color_hex = color_hex.lstrip("#")
    r, g, b = (int(color_hex[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    if n == 1:
        luminosidades = [l]
    else:
        lo = max(_LUMINOSIDAD_MIN, l - 0.28)
        hi = min(_LUMINOSIDAD_MAX, l + 0.28)
        luminosidades = [lo + (hi - lo) * i / (n - 1) for i in range(n)]

    colores = []
    for l_i in luminosidades:
        r_i, g_i, b_i = colorsys.hls_to_rgb(h, l_i, s)
        colores.append("#{:02x}{:02x}{:02x}".format(round(r_i * 255), round(g_i * 255), round(b_i * 255)))
    return colores


def _color_por_partido(agrupaciones: list[str], filiacion_de: dict[str, str]) -> dict[str, str]:
    """agrupación -> color: sombras de `_COLOR_FILIACION[filiacion_politica]`
    (ver `docs/vparty_cuadrantes.md`/CLAUDE.md, "Colores de cada espacio
    político") agrupadas por familia -- todos los partidos de una misma
    familia comparten matiz, cada uno con una luminosidad distinta dentro
    de esa familia (orden alfabético, para que sea determinístico entre
    corridas). Partidos sin `filiacion_politica` conocida, o con una que no
    está en la colorimetría, van en el gris neutro que ya usa
    `totales_por_lista._COLOR_SIN_CLASIFICAR` para el mismo caso."""
    agrupaciones_por_familia: dict[str | None, list[str]] = {}
    for agrupacion in agrupaciones:
        familia = filiacion_de.get(agrupacion)
        agrupaciones_por_familia.setdefault(familia, []).append(agrupacion)

    colores: dict[str, str] = {}
    for familia, agrupaciones_familia in agrupaciones_por_familia.items():
        base = _COLOR_FILIACION.get(familia) if familia else None
        agrupaciones_ordenadas = sorted(agrupaciones_familia)
        if base is None:
            for agrupacion in agrupaciones_ordenadas:
                colores[agrupacion] = _COLOR_SIN_CLASIFICAR
            continue
        for agrupacion, color in zip(agrupaciones_ordenadas, _sombras(base, len(agrupaciones_ordenadas))):
            colores[agrupacion] = color
    return colores


def graficar_cuadrantes_partido(
    df: pd.DataFrame,
    ruta_salida: Path,
    colores: dict[str, str],
    titulo: str,
    xlabel: str = "Izquierda / Estatismo ← posición económica → Derecha / Mercado",
    ylabel: str = "Conservador ← progresismo social → Progresista",
) -> Path:
    """Scatter económico × progresismo, un punto por partido: color = familia
    política (sombreada por partido, ver `_color_por_partido`), tamaño = %
    de votos de ese partido en la elección. A diferencia de
    `vparty_cuadrantes.graficar_cuadrantes` (color = año, tamaño =
    populismo, pensado para comparar la misma fuerza a través de varias
    elecciones) acá cada PNG es una sola elección -- no hay fusión de
    puntos entre años, ni populismo en el gráfico (queda afuera del
    encoding por ahora, sigue disponible como columna en `df`)."""
    df = df.reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(13, 10))

    df["radio"] = _radio_por_populismo(df["votos_porcentaje"])
    offsets_por_fila = dict(zip(df.index, _asignar_offsets(df)))

    for _, fila in df.iterrows():
        ax.scatter(
            fila[EJE_X], fila[EJE_Y], s=fila["radio"],
            color=colores.get(fila["agrupacion"], _COLOR_SIN_CLASIFICAR),
            edgecolor="white", linewidth=0.8, alpha=0.9, zorder=3,
        )

    for idx, fila in df.iterrows():
        dx, dy, ha = offsets_por_fila[idx]
        ax.annotate(
            fila["agrupacion"], (fila[EJE_X], fila[EJE_Y]),
            xytext=(dx, dy), textcoords="offset points", ha=ha,
            fontsize=8, color="#333333",
        )

    ax.axvline(0, color="#999999", linewidth=1, linestyle="--", zorder=1)
    ax.axhline(0, color="#999999", linewidth=1, linestyle="--", zorder=1)

    x_min, x_max = df[EJE_X].min() - 0.6, df[EJE_X].max() + 0.6
    y_min, y_max = df[EJE_Y].min() - 0.4, df[EJE_Y].max() + 0.4
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    estilo_cuadrante = dict(fontsize=9, color="#666666", style="italic")
    ax.text(x_min + 0.1, y_max - 0.03 * (y_max - y_min), "Izquierda · Progresista", ha="left", va="top", **estilo_cuadrante)
    ax.text(x_max - 0.1, y_max - 0.03 * (y_max - y_min), "Derecha · Progresista", ha="right", va="top", **estilo_cuadrante)
    ax.text(x_min + 0.1, y_min + 0.03 * (y_max - y_min), "Izquierda · Conservador", ha="left", va="bottom", **estilo_cuadrante)
    ax.text(x_max - 0.1, y_min + 0.03 * (y_max - y_min), "Derecha · Conservador", ha="right", va="bottom", **estilo_cuadrante)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(titulo, fontsize=12)

    v_min, v_max = df["votos_porcentaje"].min(), df["votos_porcentaje"].max()
    valores_ref = sorted({v_min, (v_min + v_max) / 2, v_max})
    radios_ref = _radio_por_populismo(pd.Series(valores_ref), v_min, v_max)
    puntos_ref = [
        plt.scatter([], [], s=r, color="#888888", alpha=0.85, edgecolor="white", linewidth=0.8)
        for r in radios_ref
    ]
    ax.legend(
        puntos_ref, [f"{v:.1f}%" for v in valores_ref],
        title="% de votos", loc="center left", bbox_to_anchor=(1.01, 0.5),
        frameon=False, labelspacing=1.5,
    )

    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5, zorder=0)
    fig.tight_layout()
    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def generar_distrito(
    nivel: str,
    posiciones: dict[tuple[str, str, str], tuple[float, float, float]],
    filiaciones: dict[tuple[str, str, str], str],
    data_dir: Path | str = DATA_DISTRITO_DIR,
    salida_dir: Path | str = RUTA_DISTRITO_DIR,
) -> list[Path]:
    """Un PNG por (año, nivel unificado) -- `<salida_dir>/<año>/v_party_<nivel>.png`,
    una elección a la vez en vez de todas juntas en un solo scatter con
    color por año (eso sigue disponible armando el df vos mismo con
    `tabla_distrito` + `graficar_cuadrantes`)."""
    df_todo = tabla_distrito(nivel, posiciones, data_dir)
    if df_todo.empty:
        return []

    cargo_por_anio = dict(_puntos_del_nivel(data_dir, nivel))
    salida_dir = Path(salida_dir)
    destinos = []
    for anio in sorted(df_todo["year"].unique()):
        df_anio = df_todo[df_todo["year"] == anio]
        cargo = cargo_por_anio[anio]
        nivel_csv = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
        filiacion_de = {
            agrupacion: filiaciones.get((str(anio), nivel_csv, agrupacion))
            for agrupacion in df_anio["agrupacion"]
        }
        colores = _color_por_partido(list(df_anio["agrupacion"]), filiacion_de)

        salida_anio_dir = salida_dir / str(anio)
        salida_anio_dir.mkdir(parents=True, exist_ok=True)
        destino = salida_anio_dir / f"v_party_{nivel}.png"
        graficar_cuadrantes_partido(
            df_anio, destino, colores,
            titulo=(
                f"La Plata — {nivel} {anio} ({CARGO_LABEL[cargo]}): "
                "económico × progresismo social (tamaño = % de votos)\n"
                "color por familia política (clasificación propia calibrada contra V-Party)"
            ),
        )
        destinos.append(destino)
    return destinos


def generar_localidad(
    nivel: str,
    localidad: str,
    tabla_larga: pd.DataFrame,
    salida_dir: Path | str = RUTA_LOCALIDAD_DIR,
) -> Path | None:
    df = tabla_larga.loc[tabla_larga["localidad"] == localidad].drop(columns="localidad")
    if df.empty:
        return None

    anios = sorted(df["year"].unique())
    salida_dir = Path(salida_dir)
    salida_dir.mkdir(parents=True, exist_ok=True)
    destino = salida_dir / f"{nivel}_{localidad}.png"
    graficar_cuadrantes(
        df, ruta_salida=destino, col_etiqueta="agrupacion", col_anio="year",
        color_por_anio=_color_por_anio(anios),
        titulo=(
            f"{localidad} — {nivel}: económico × progresismo social (tamaño = populismo)\n"
            f"Elecciones generales {anios[0]}-{anios[-1]}, ejecutivo + legislativo combinados "
            "(clasificación propia calibrada contra V-Party)"
        ),
        xlabel="Izquierda / Estatismo ← posición económica → Derecha / Mercado",
        ylabel="Conservador ← progresismo social → Progresista",
    )
    return destino


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--grano", choices=["distrito", "localidad", "todos"], default="todos")
    parser.add_argument("--nivel", choices=list(NIVELES), help="si se omite, corre los 3 niveles")
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    parser.add_argument("--referencia", default=CLASIFICACION_IDEOLOGICA_PATH)
    parser.add_argument("--crosswalk", default=CIRCUITOS_POR_LOCALIDAD_PATH)
    args = parser.parse_args()

    posiciones = cargar_posiciones_propias(args.referencia)
    filiaciones = cargar_filiaciones(args.referencia)
    niveles = [args.nivel] if args.nivel else list(NIVELES)

    if args.grano in ("distrito", "todos"):
        for nivel in niveles:
            destinos = generar_distrito(nivel, posiciones, filiaciones, args.data_dir)
            if destinos:
                for destino in destinos:
                    print(f"distrito {nivel} -> {destino}")
            else:
                print(f"distrito {nivel}: sin agrupaciones con cobertura V-Party")

    if args.grano in ("localidad", "todos"):
        for nivel in niveles:
            tabla_larga = tabla_localidades(nivel, posiciones, args.data_dir, args.crosswalk)
            if tabla_larga.empty:
                print(f"localidad {nivel}: sin agrupaciones con cobertura V-Party")
                continue
            for localidad in sorted(tabla_larga["localidad"].unique()):
                destino = generar_localidad(nivel, localidad, tabla_larga)
                if destino:
                    print(f"localidad {nivel} {localidad} -> {destino}")


if __name__ == "__main__":
    main()
