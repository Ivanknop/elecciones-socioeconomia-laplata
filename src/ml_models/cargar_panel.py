"""Interfaz de carga de `panel_ventanas.csv` para modelado -- D7/D10 (ver
`docs/decisiones_metodologicas.md`). Los tres niveles comparten regresores
económicos idénticos dentro de una misma ventana (la economía es una sola);
lo único que varía entre series es la variable dependiente, porque varía
quién es el oficialismo. Apilarlos sin una decisión explícita trataría
~13 shocks económicos distintos como 31 observaciones independientes,
inflando artificialmente la precisión de cualquier estimación -- por eso
`cargar_panel` exige `nivel` (sin default) y el apilado vive en una función
aparte que exige justificación.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from constantes import PANEL_VENTANAS_PATH

NIVELES_VALIDOS = ("municipal", "provincial", "nacional")


def cargar_panel(nivel: str, panel_path: Path | str = PANEL_VENTANAS_PATH) -> pd.DataFrame:
    """Carga el panel de ventanas para UN nivel de gobierno. `nivel` es
    obligatorio por diseño metodológico (D7/D10): los tres niveles
    constituyen series paralelas que no deben apilarse sin una decisión
    explícita. Ver `docs/especificacion_panel_temporal.md` §7."""
    if nivel not in NIVELES_VALIDOS:
        raise ValueError(f"nivel debe ser uno de {NIVELES_VALIDOS}, no {nivel!r}")
    df = pd.read_csv(panel_path)
    return df[df["nivel"] == nivel].reset_index(drop=True)


def cargar_panel_apilado(justificacion: str, panel_path: Path | str = PANEL_VENTANAS_PATH) -> pd.DataFrame:
    """Carga las tres series apiladas en un único panel. Requiere una
    `justificacion` explícita y no vacía (se registra en log) -- solo para
    comparar especificaciones de pooling (D7), nunca la vía por defecto
    para modelar."""
    if not justificacion or not justificacion.strip():
        raise ValueError(
            "cargar_panel_apilado requiere una justificación explícita y no vacía -- "
            "el apilado de los tres niveles no es la vía por defecto (D7/D10)."
        )
    print(f"[cargar_panel_apilado] apilando los 3 niveles -- justificación: {justificacion}")
    return pd.read_csv(panel_path)
