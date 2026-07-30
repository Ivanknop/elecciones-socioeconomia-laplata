"""Correspondencia espacial entre circuitos electorales y radios censales.

Circuitos electorales (Cámara Nacional Electoral) y radios censales (INDEC)
son geografías de instituciones distintas, sin identificador compartido: no
hay forma de unirlos por id, como sí se puede con `circuito_id` entre años
electorales (ver `notebooks/04_totales_por_circuito.ipynb`). Este módulo
resuelve esa correspondencia con un join espacial (`geopandas`): cada radio
censal se reparte entre los circuitos que intersecta, ponderado por área.

Los radios que caen enteros dentro de un solo circuito quedan con
`peso_area=1.0` y `match_limpio=True`. Los radios que cruzan un límite de
circuito quedan repartidos en varias filas cuyos pesos suman 1.0 para ese
radio, con `match_limpio=False` — cualquier cifra socioeconómica por
circuito construida a partir de esas filas es una estimación por área, no
un conteo censal, y debe tratarse como tal (ver README, sección de la capa
socioeconómica).
"""
from __future__ import annotations

import re

import geopandas as gpd
import pandas as pd

_CIRCUITO_RE = re.compile(r"^0*(\d+)([A-Za-z]*)$")


def canonicalizar_circuito_id(raw: str) -> str:
    """Misma regla de normalización que `notebooks/04_totales_por_circuito.ipynb`:
    sin ceros a la izquierda, con cualquier sufijo de letra en mayúsculas
    (ej. "0496F" -> "496F").
    """
    m = _CIRCUITO_RE.match(raw.strip())
    if not m:
        return raw.strip()
    numero, letra = m.groups()
    return numero + letra.upper()


def cargar_circuitos_electorales(path: str, departamento: str | None = None) -> gpd.GeoDataFrame:
    """Carga la capa de circuitos electorales (formato CNE/PBA, ver README) y
    agrega `circuito_id` canónico. `departamento` filtra por el nombre exacto
    de la columna `departamen` si se pasa (ej. "La Plata").
    """
    gdf = gpd.read_file(path)
    if departamento is not None:
        gdf = gdf[gdf["departamen"].str.strip() == departamento].copy()
    gdf["circuito_id"] = gdf["circuito"].map(canonicalizar_circuito_id)
    return gdf[["circuito_id", "geometry"]].reset_index(drop=True)


def cargar_radios_censales(path: str, censo_anio: int) -> gpd.GeoDataFrame:
    """Carga una capa de radios censales (formato armonizado CONICET
    1991/2001/2010/2022, ver README) para un censo puntual. El id de radio es
    la columna `COD_<censo_anio>` de esa capa (código compuesto
    provincia+departamento+fracción+radio).
    """
    gdf = gpd.read_file(path)
    columna_id = f"COD_{censo_anio}"
    gdf = gdf.rename(columns={columna_id: "radio_censal_id"})
    gdf["censo_anio"] = censo_anio
    return gdf[["radio_censal_id", "censo_anio", "geometry"]].reset_index(drop=True)


def calcular_correspondencia(
    circuitos: gpd.GeoDataFrame, radios: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Reparte cada radio censal entre los circuitos electorales que
    intersecta, ponderado por área. Devuelve una fila por (radio, circuito)
    con `peso_area` (los pesos de un mismo radio suman 1.0) y `match_limpio`
    (True si el radio cayó entero dentro de un único circuito).

    Ambas capas se reproyectan a un CRS UTM estimado a partir de los
    circuitos, para que el área se calcule en metros y no en grados.
    """
    crs_metrico = circuitos.estimate_utm_crs()
    circuitos_m = circuitos.to_crs(crs_metrico)
    radios_m = radios.to_crs(crs_metrico)

    area_radio = radios_m.set_index("radio_censal_id").geometry.area

    interseccion = gpd.overlay(radios_m, circuitos_m, how="intersection")
    interseccion["area_interseccion"] = interseccion.geometry.area

    filas = (
        interseccion.groupby(["radio_censal_id", "censo_anio", "circuito_id"])[
            "area_interseccion"
        ]
        .sum()
        .reset_index()
    )
    filas["peso_area"] = filas.apply(
        lambda fila: fila["area_interseccion"] / area_radio[fila["radio_censal_id"]],
        axis=1,
    )
    conteo_circuitos = filas.groupby("radio_censal_id")["circuito_id"].transform("count")
    filas["match_limpio"] = conteo_circuitos == 1

    return filas[
        ["circuito_id", "radio_censal_id", "censo_anio", "peso_area", "match_limpio"]
    ].sort_values(["circuito_id", "radio_censal_id"]).reset_index(drop=True)
