"""Correspondencia espacial entre circuitos electorales y radios censales,
vía join espacial ponderado por área (`geopandas`). Detalle en
`docs/FUNCIONALIDADES.md`."""
from __future__ import annotations

import re

import geopandas as gpd
import pandas as pd

_CIRCUITO_RE = re.compile(r"^0*(\d+)([A-Za-z]*)$")


def canonicalizar_circuito_id(raw: str) -> str:
    """Misma normalización que notebook 04: sin ceros a la izquierda,
    sufijo de letra en mayúsculas (ej. "0496F" -> "496F")."""
    m = _CIRCUITO_RE.match(raw.strip())
    if not m:
        return raw.strip()
    numero, letra = m.groups()
    return numero + letra.upper()


def cargar_circuitos_electorales(path: str, departamento: str | None = None) -> gpd.GeoDataFrame:
    """Carga circuitos electorales (formato CNE/PBA) y agrega `circuito_id`
    canónico; `departamento` filtra por nombre exacto."""
    gdf = gpd.read_file(path)
    if departamento is not None:
        gdf = gdf[gdf["departamen"].str.strip() == departamento].copy()
    gdf["circuito_id"] = gdf["circuito"].map(canonicalizar_circuito_id)
    return gdf[["circuito_id", "geometry"]].reset_index(drop=True)


def cargar_radios_censales(path: str, censo_anio: int) -> gpd.GeoDataFrame:
    """Carga radios censales (formato CONICET) para un censo puntual; id
    de radio = columna `COD_<censo_anio>`."""
    gdf = gpd.read_file(path)
    columna_id = f"COD_{censo_anio}"
    gdf = gdf.rename(columns={columna_id: "radio_censal_id"})
    gdf["censo_anio"] = censo_anio
    return gdf[["radio_censal_id", "censo_anio", "geometry"]].reset_index(drop=True)


def calcular_correspondencia(
    circuitos: gpd.GeoDataFrame, radios: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Reparte cada radio censal entre los circuitos que intersecta,
    ponderado por área; `match_limpio=True` si cayó en uno solo."""
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
