"""Posición V-Party propia (real o estimada) de cada agrupación en las
elecciones de La Plata, agregada a grano distrito (`tabla_distrito`) y a
grano localidad (`tabla_localidades`, análisis secundario del enfoque
espacial anterior al pivot del panel temporal -- D8, ver
docs/decisiones_metodologicas.md). `_color_por_partido`/`_sombras` (color
por familia política, con variantes de luminosidad para partidos de una
misma familia) las reutilizan `analisis/vparty_distribucion_tfi.py` y
`visualizacion/distribucion_ideologica_interactiva.py`.
"""
from __future__ import annotations

import colorsys
import csv
import json
from pathlib import Path

import pandas as pd

from analisis.graficos import _COLOR_FILIACION
from analisis.serie_temporal import _puntos_del_nivel
from analisis.totales_por_lista import NIVEL_A_NIVEL_CSV, _COLOR_SIN_CLASIFICAR
from constantes import (
    CIRCUITOS_POR_LOCALIDAD_PATH,
    CLASIFICACION_IDEOLOGICA_PATH,
    DATA_DISTRITO_DIR,
)
from electoral.localidades import agrupar_resultados_por_localidad, cargar_circuito_localidad_geo
from electoral.totales import resultado_total_por_agrupacion

_LUMINOSIDAD_MIN, _LUMINOSIDAD_MAX = 0.25, 0.78


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
