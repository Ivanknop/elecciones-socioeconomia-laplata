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

# Resultado electoral o derivado de resultado electoral (D27) -- describen
# QUÉ PASÓ en la elección t (quién ganó, cuánto sacó, cuánto cambió la
# ideología del electorado, cuánta gente votó/se ausentó/votó en blanco),
# nunca una variable económica independiente. Ninguna termina en "_vc": el
# viejo filtro por sufijo las excluía sin que nadie lo haya diseñado así.
# Cubre simétricamente la familia propia de cada uno de los dos objetivos
# de modelado que conviven en panel_ventanas.csv (delta_v en 01.1_lasso_*.ipynb;
# magnitud_desplazamiento_ideologico en 03_desplazamiento_ideologico.ipynb)
# para que el target de uno no se cuele como feature del otro.
COLUMNAS_OUTCOME_ELECTORAL = (
    "delta_v", "gana_oficialismo", "share_oficialismo", "agrupacion_oficialismo",
    "continuidad_oficialismo", "delta_posicion_ideologica", "distancia_oficialismo_alternativa",
    "delta_dispersion_economico_mu", "delta_dispersion_progresismo_mu",
    "delta_sigma2_economico", "delta_sigma2_progresismo",
    "magnitud_desplazamiento_ideologico", "cuadrante_desplazamiento",
    "dispersion_cobertura_share_min",
    "participacion_pct_t", "participacion_pct_t_menos_1", "participacion_relevante_t",
    "voto_exit_ausentismo_pct_t", "voto_exit_ausentismo_pct_t_menos_1",
    "voto_exit_blanco_nulo_pct_t", "voto_exit_blanco_nulo_pct_t_menos_1",
    "delta_participacion_pct", "delta_voto_exit_ausentismo_pct", "delta_voto_exit_blanco_nulo_pct",
)


def columnas_candidatas(df: pd.DataFrame, excluir_adicional: tuple[str, ...] = ()) -> list[str]:
    """Todas las columnas numéricas del panel, excluyendo metadata
    (`COLUMNAS_METADATA_PANEL`), resultado electoral o derivado de
    resultado (`COLUMNAS_OUTCOME_ELECTORAL`, D27) y lo que se pase en
    `excluir_adicional` -- el/los target(s) propios del notebook que
    llama, incluido un target construido en el notebook que no es columna
    real del panel (ver `01.3_lasso_voto_exit.ipynb`)."""
    excluir = set(COLUMNAS_METADATA_PANEL) | set(COLUMNAS_OUTCOME_ELECTORAL) | set(excluir_adicional)
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in excluir]


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
