"""Construcción de series ICG (promedio ponderado por `ponderacion_UTDT`) a
partir del microdato ya cargado por `icg_cargar.cargar_microdatos`.

Dos formas de agregación:

- `construir_serie_headline`: una fila por (año, mes), La Plata vs. país --
  el entregable inmediato (serie temporal, un gráfico).
- `construir_series_demograficas`: una fila por (tiempo, categoría del
  corte), reusable para sexo/edad/edu -- CSV de datos, sin gráfico
  todavía. Quien llama decide el grano geográfico filtrando `df` antes de
  pasarlo (todo el país, o solo `Ciudad == CIUDAD_LA_PLATA`) y la
  resolución (`"mensual"` para país, `"anual"` para La Plata -- ver
  `data/socioeconomia/ICG.md`, el N mensual de La Plata es demasiado
  chico para sostener un corte demográfico mes a mes).

`icg_pais` (headline) incluye a La Plata en el promedio pooleado -- mismo
criterio que la propia fuente, `ponderacion_UTDT` existe justamente para
ponderar cada ciudad dentro de un agregado nacional único. La brecha se
autocontiene (La Plata es parte de su propio término de referencia), a
propósito.
"""
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
    """Una fila por (año, mes). `anio_hasta=None` (default) resuelve al año
    máximo realmente presente en `df` -- la serie sale completa hasta el
    último dato real del `.dta` cargado, sin capar a un año hardcodeado.

    """
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
    """Una fila por (tiempo, categoría de `corte`), con `n` de muestra
    siempre incluido para que quien consuma el CSV juzgue la
    confiabilidad de cada punto. `df` ya viene filtrado por quien llama
    al grano geográfico deseado (país entero, o solo La Plata) -- esta
    función no decide eso, solo agrupa por tiempo (`resolucion`) y por
    `corte`. Filas con `corte` nulo se excluyen (`dropna`) -- solo
    relevante para `edu` (~0,04% de nulos en 2011 en adelante), `sexo`/
    `edad` no tienen nulos.
    """
    if anio_hasta is None:
        anio_hasta = int(df["año"].max())
    recorte = df[(df["año"] >= anio_desde) & (df["año"] <= anio_hasta)].dropna(subset=[corte])

    cols_tiempo = ["año"] if resolucion == "anual" else ["año", "mes"]
    agg = _agregar_ponderado(recorte, cols_tiempo + [corte])
    return agg.sort_values(cols_tiempo + [corte]).reset_index(drop=True)
