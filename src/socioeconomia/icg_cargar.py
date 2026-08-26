"""Carga del microdato ICG (Índice de Confianza en el Gobierno, UTDT) --
`data/socioeconomia/icg/Base_histórica_2001-presente-ICG.dta`, insumo
externo no regenerable colocado manualmente por quien corre el pipeline
(ver `data/socioeconomia/icg/README.md`).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from constantes import ICG_RAW_PATH

# Ciudad==7 es La Plata (ver Codebook_ICG.pdf, tabla "Ciudad").
CIUDAD_LA_PLATA = 7

COL_PESO = "ponderacion_UTDT"
COL_ICG = "ICG"


def cargar_microdatos(path: Path | str = ICG_RAW_PATH) -> pd.DataFrame:
    """Lee el `.dta` crudo, normaliza `año`/`mes` a `int` y valida
    ICG/ponderación -- falla ruidosamente si no se cumple."""
    df = pd.read_stata(path, convert_categoricals=False)

    # 17 de 314.817 filas (~0,005%) no tienen año/mes -- sin identificador
    # temporal no hay bucket (año, mes) al que asignarlas, se excluyen acá
    # (no en construir_serie_headline/construir_series_demograficas) para
    # que ambas trabajen siempre sobre año/mes ya enteros, sin nulos.
    df = df.dropna(subset=["año", "mes"])
    df["año"] = df["año"].astype(int)
    df["mes"] = df["mes"].astype(int)

    if df[COL_ICG].isna().any():
        raise ValueError(f"'{COL_ICG}' tiene valores nulos -- se esperaba sin nulos")
    if not df[COL_ICG].between(0, 5).all():
        raise ValueError(f"'{COL_ICG}' tiene valores fuera de [0, 5]")
    if df[COL_PESO].isna().any():
        raise ValueError(f"'{COL_PESO}' tiene valores nulos -- se esperaba sin nulos")

    return df
