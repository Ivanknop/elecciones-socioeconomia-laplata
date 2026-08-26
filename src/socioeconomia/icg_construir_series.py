"""Construcción de series ICG ponderadas (`ponderacion_UTDT`) desde
`icg_cargar.cargar_microdatos`: `construir_serie_headline` (La Plata vs.
país, mensual) y `construir_series_demograficas` (por sexo/edad/edu).
Criterios y resolución en `data/socioeconomia/ICG.md`."""
from __future__ import annotations

from typing import Literal

import pandas as pd

from socioeconomia.icg_cargar import CIUDAD_LA_PLATA, COL_ICG, COL_PESO


def _agregar_ponderado(d: pd.DataFrame, cols_grupo: list[str]) -> pd.DataFrame:
    """Promedio de ICG ponderado por `ponderacion_UTDT`, agrupado por
    `cols_grupo`. Devuelve columnas `cols_grupo + ["icg", "n"]`."""
    numerador = d[COL_ICG] * d[COL_PESO]
    agg = d.assign(_numerador=numerador).groupby(cols_grupo, as_index=False).agg(
        _numerador_sum=("_numerador", "sum"),
        _peso_sum=(COL_PESO, "sum"),
        n=(COL_ICG, "size"),
    )
    agg["icg"] = agg["_numerador_sum"] / agg["_peso_sum"]
    return agg.drop(columns=["_numerador_sum", "_peso_sum"])


def construir_serie_headline(
    df: pd.DataFrame, anio_desde: int = 2011, anio_hasta: int | None = None,
) -> pd.DataFrame:
    """Una fila por (año, mes); `anio_hasta=None` resuelve al año máximo
    presente en `df`, sin capar a un valor hardcodeado."""
    if anio_hasta is None:
        anio_hasta = int(df["año"].max())
    recorte = df[(df["año"] >= anio_desde) & (df["año"] <= anio_hasta)]

    lp = _agregar_ponderado(recorte[recorte["Ciudad"] == CIUDAD_LA_PLATA], ["año", "mes"])
    pais = _agregar_ponderado(recorte, ["año", "mes"])  # incluye La Plata

    salida = lp.merge(pais, on=["año", "mes"], how="outer", suffixes=("_la_plata", "_pais"))
    salida["brecha"] = salida["icg_la_plata"] - salida["icg_pais"]
    salida = salida.sort_values(["año", "mes"]).reset_index(drop=True)
    return salida[["año", "mes", "icg_la_plata", "icg_pais", "brecha", "n_la_plata", "n_pais"]]


def construir_series_demograficas(
    df: pd.DataFrame,
    corte: Literal["sexo", "edad", "edu"],
    resolucion: Literal["mensual", "anual"],
    anio_desde: int = 2011,
    anio_hasta: int | None = None,
) -> pd.DataFrame:
    """Una fila por (tiempo, categoría de `corte`), con `n` incluido;
    `df` ya viene filtrado al grano geográfico."""
    if anio_hasta is None:
        anio_hasta = int(df["año"].max())
    recorte = df[(df["año"] >= anio_desde) & (df["año"] <= anio_hasta)].dropna(subset=[corte])

    cols_tiempo = ["año"] if resolucion == "anual" else ["año", "mes"]
    agg = _agregar_ponderado(recorte, cols_tiempo + [corte])
    return agg.sort_values(cols_tiempo + [corte]).reset_index(drop=True)
