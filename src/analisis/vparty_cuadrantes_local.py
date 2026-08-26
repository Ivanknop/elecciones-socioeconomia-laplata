"""Cuadrantes ideológicos V-Party (económico × progresismo) con votos
reales de La Plata, análogo a `vparty_cuadrantes.py` pero a partir de
datos locales. Encoding de color/tamaño y agregación difieren por grano
(distrito/localidad) -- detalle en `docs/vparty_cuadrantes.md` y CLAUDE.md.

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
RUTA_LOCALIDAD_POR_ANIO_DIR = Path("graficos/agrupaciones/por_localidad")

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
    """(año, nivel, agrupación) → posición V-Party (real o estimada) desde
    `clasificacion_ideologica_agrupaciones.csv`, solo filas con cobertura."""
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
    """(año, nivel, agrupación) → filiación política, para colorear por
    partido vía `_color_por_partido` -- independiente de la cobertura V-Party."""
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
    """Votos por (agrupación, año), sumados en toda La Plata, para
    agrupaciones con cobertura V-Party -- `nivel` combina ejecutivo/legislativo."""
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
    """circuito_id → {agrupación: votos}, sin agrupar por campo_ideologico."""
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
    """Votos por (localidad, agrupación, año) con cobertura V-Party;
    `votos_porcentaje` sobre el total de esa localidad, comparable con `tabla_distrito`."""
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
            total_localidad = sum(fila_loc[c] for c in columnas_agrupacion)
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
                    "votos_porcentaje": (votos / total_localidad * 100) if total_localidad else 0.0,
                })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 4. Graficado
# ---------------------------------------------------------------------------

def _color_por_anio(anios: list[int]) -> dict[int, str]:
    return {anio: _CMAP_ANIOS(i % 10) for i, anio in enumerate(sorted(set(anios)))}


def _sombras(color_hex: str, n: int) -> list[str]:
    """`n` variaciones de luminosidad de `color_hex`, para distinguir
    partidos dentro de una misma familia política."""
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
    """agrupación → color: sombras del color de su familia política (CLAUDE.md);
    gris si no clasificada."""
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


def _limites_globales(
    posiciones: dict[tuple[str, str, str], tuple[float, float, float]],
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Límites de eje fijos y simétricos respecto de 0, sobre toda la
    cobertura V-Party, para que los PNG sean comparables."""
    if not posiciones:
        return (-1.0, 1.0), (-1.0, 1.0)
    x_max = max(abs(econ) for econ, _, _ in posiciones.values()) + 0.6
    y_max = max(abs(prog) for _, prog, _ in posiciones.values()) + 0.4
    return (-x_max, x_max), (-y_max, y_max)


def graficar_cuadrantes_partido(
    df: pd.DataFrame,
    ruta_salida: Path,
    colores: dict[str, str],
    titulo: str,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    xlabel: str = "Izquierda / Estatismo ← posición económica → Derecha / Mercado",
    ylabel: str = "Conservador ← progresismo social → Progresista",
) -> Path:
    """Scatter económico × progresismo por partido: color = familia
    política, tamaño = % de votos. `xlim`/`ylim` fijos, ver `_limites_globales`."""
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

    x_min, x_max = xlim
    y_min, y_max = ylim
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
    """Un PNG por (año, nivel), distrito completo --
    `<salida_dir>/<año>/v_party_<nivel>.png`."""
    df_todo = tabla_distrito(nivel, posiciones, data_dir)
    if df_todo.empty:
        return []

    xlim, ylim = _limites_globales(posiciones)
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
            df_anio, destino, colores, xlim=xlim, ylim=ylim,
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


def generar_localidad_por_anio(
    nivel: str,
    posiciones: dict[tuple[str, str, str], tuple[float, float, float]],
    filiaciones: dict[tuple[str, str, str], str],
    data_dir: Path | str = DATA_DISTRITO_DIR,
    crosswalk_path: Path | str = CIRCUITOS_POR_LOCALIDAD_PATH,
    salida_dir: Path | str = RUTA_LOCALIDAD_POR_ANIO_DIR,
    tabla_larga: pd.DataFrame | None = None,
) -> list[Path]:
    """Un PNG por (localidad, año, nivel), mismo encoding y límites de eje
    que `generar_distrito` -- va a `graficos/agrupaciones/por_localidad/` (no versionado)."""
    if tabla_larga is None:
        tabla_larga = tabla_localidades(nivel, posiciones, data_dir, crosswalk_path)
    if tabla_larga.empty:
        return []

    xlim, ylim = _limites_globales(posiciones)
    cargo_por_anio = dict(_puntos_del_nivel(data_dir, nivel))
    salida_dir = Path(salida_dir)
    destinos = []
    for (localidad, anio), grupo in tabla_larga.groupby(["localidad", "year"]):
        cargo = cargo_por_anio[anio]
        nivel_csv = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
        filiacion_de = {
            agrupacion: filiaciones.get((str(anio), nivel_csv, agrupacion))
            for agrupacion in grupo["agrupacion"]
        }
        colores = _color_por_partido(list(grupo["agrupacion"]), filiacion_de)

        salida_anio_dir = salida_dir / str(anio)
        salida_anio_dir.mkdir(parents=True, exist_ok=True)
        destino = salida_anio_dir / f"v_party_{nivel}_{localidad}.png"
        graficar_cuadrantes_partido(
            grupo, destino, colores, xlim=xlim, ylim=ylim,
            titulo=(
                f"{localidad} — {nivel} {anio} ({CARGO_LABEL[cargo]}): "
                "económico × progresismo social (tamaño = % de votos)\n"
                "color por familia política (clasificación propia calibrada contra V-Party)"
            ),
        )
        destinos.append(destino)
    return destinos


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

            destinos_por_anio = generar_localidad_por_anio(
                nivel, posiciones, filiaciones, args.data_dir, args.crosswalk,
                tabla_larga=tabla_larga,
            )
            for destino in destinos_por_anio:
                print(f"localidad por año {nivel} -> {destino}")


if __name__ == "__main__":
    main()
