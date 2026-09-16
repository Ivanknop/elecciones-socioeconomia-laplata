"""Interfaz de carga de `panel_ventanas.csv` para modelado
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from constantes import PANEL_VENTANAS_PATH

NIVELES_VALIDOS = ("municipal", "provincial", "nacional")

# Metadata de trazabilidad de la ventana (identifican qué período temporal
# produjo el resto de las columnas), no variables explicativas -- año/fecha
# cruda actuaría como proxy de tendencia temporal con N=7-12 por nivel si
# entrara como regresor (D23). Nunca se sacan de panel_ventanas.csv (siguen
# siendo necesarias para trazabilidad/auditoría de cada ventana), solo se
# excluyen acá, en el paso de armado de la matriz de features.
COLUMNAS_METADATA_PANEL = (
    "id_transicion", "fecha_inicio_vc", "fecha_fin_vc", "fecha_inicio_vl",
    "anio_t", "anio_t_menos_1", "anio_t_menos_2",
)


def columnas_candidatas(df: pd.DataFrame, sufijo: str = "_vc") -> list[str]:
    """Columnas numéricas con `sufijo`, excluyendo siempre
    `COLUMNAS_METADATA_PANEL` -- reemplaza el filtro ad hoc que se repetía
    en cada notebook (`fecha_inicio_vc`/`fecha_fin_vc` terminan en `_vc`
    igual que las variables económicas; antes de esto solo quedaban afuera
    porque `pd.read_csv` las tipa como string, no por una exclusión
    explícita)."""
    return [
        c for c in df.columns
        if c.endswith(sufijo) and pd.api.types.is_numeric_dtype(df[c]) and c not in COLUMNAS_METADATA_PANEL
    ]


def sin_metadata(columnas: list[str]) -> list[str]:
    """Filtra cualquier lista de columnas candidatas armada por otro
    mecanismo (`.select_dtypes`, lista a mano, etc.) contra
    `COLUMNAS_METADATA_PANEL`."""
    return [c for c in columnas if c not in COLUMNAS_METADATA_PANEL]


def cargar_panel(nivel: str, panel_path: Path | str = PANEL_VENTANAS_PATH) -> pd.DataFrame:
    """Carga el panel de ventanas para UN nivel de gobierno. `nivel` es
    obligatorio por diseño metodológico: los tres niveles
    constituyen series paralelas que no deben apilarse sin una decisión
    explícita."""
    if nivel not in NIVELES_VALIDOS:
        raise ValueError(f"nivel debe ser uno de {NIVELES_VALIDOS}, no {nivel!r}")
    df = pd.read_csv(panel_path)
    return df[df["nivel"] == nivel].reset_index(drop=True)


def cargar_panel_apilado(justificacion: str, panel_path: Path | str = PANEL_VENTANAS_PATH) -> pd.DataFrame:
    """Carga las tres series apiladas en un único panel. Requiere una
    `justificacion` explícita y no vacía (se registra en log)"""
    if not justificacion or not justificacion.strip():
        raise ValueError(
            "cargar_panel_apilado requiere una justificación explícita y no vacía -- "
            "el apilado de los tres niveles no es la vía por defecto."
        )
    print(f"[cargar_panel_apilado] apilando los 3 niveles -- justificación: {justificacion}")
    return pd.read_csv(panel_path)
