"""Targets electorales (D18/D19) calculados directo sobre un par de filas
frontera (`tipo_fila` `"eleccion_t"`/`"eleccion_t_menos_1"` o
`"eleccion_t_menos_2"`) de un panel trimestral (`panel_trimestral_<nivel>.csv`,
`panel_bieleccion_trimestral_<nivel>.csv`, o el `panel_k` de horizonte
configurable) -- genérico respecto de qué extremo es "anterior" (t-1 o
t-2), solo depende de que ambas filas traigan las columnas de
`COLUMNAS_ELECCION_PANEL` (`construir_elecciones_resumen.py`). Extraído de
`construir_panel_lasso_bieleccion.py` para no duplicar estas fórmulas en
cada panel nuevo que reconstruya targets desde sus propias filas frontera."""
from __future__ import annotations

import pandas as pd

from ml_models.construir_panel_ventanas import clasificar_cuadrante_desplazamiento


def voto_exit(frontera: pd.Series) -> dict[str, float | None]:
    """Mismas fórmulas que `construir_elecciones_resumen.calcular_participacion_voto_exit`
    (D19), aplicadas directo sobre una fila frontera -- ya trae
    `participacion_pct`/`ausentismo`/`votos_blancos_y_nulos`/
    `votantes_habilitados`, sin necesidad de releer `elecciones.csv`."""
    habilitados = frontera["votantes_habilitados"]
    if pd.isna(habilitados):
        return {"participacion_pct": None, "voto_exit_ausentismo_pct": None, "voto_exit_blanco_nulo_pct": None}
    ausentismo, blanco_nulo = frontera["ausentismo"], frontera["votos_blancos_y_nulos"]
    return {
        "participacion_pct": frontera["participacion_pct"] if pd.notna(frontera["participacion_pct"]) else None,
        "voto_exit_ausentismo_pct": ausentismo / habilitados * 100 if pd.notna(ausentismo) else None,
        "voto_exit_blanco_nulo_pct": blanco_nulo / habilitados * 100 if pd.notna(blanco_nulo) else None,
    }


def delta(actual: float | None, anterior: float | None) -> float | None:
    return actual - anterior if actual is not None and anterior is not None else None


def delta_min(actual: float, anterior: float) -> float | None:
    """Mínimo de `dispersion_cobertura_share` entre las dos puntas de la
    transición (D18) -- ambas siempre presentes (0.0, nunca NaN, D17)."""
    return min(actual, anterior) if pd.notna(actual) and pd.notna(anterior) else None


def calcular_targets(frontera_t: pd.Series, frontera_anterior: pd.Series) -> dict:
    """`delta_v`, participación/voto-exit (D19), desplazamiento ideológico
    (D18) -- `frontera_anterior` es la fila `eleccion_t_menos_1` o
    `eleccion_t_menos_2` según el panel que llame a esta función, la
    fórmula no distingue cuál."""
    share_t = frontera_t["share_oficialismo"]
    share_anterior = frontera_anterior["share_oficialismo"]
    delta_v = share_t - share_anterior if pd.notna(share_t) and pd.notna(share_anterior) else None

    exit_t, exit_anterior = voto_exit(frontera_t), voto_exit(frontera_anterior)
    delta_dispersion_economico_mu = delta(
        frontera_t["dispersion_economico_mu"] if pd.notna(frontera_t["dispersion_economico_mu"]) else None,
        frontera_anterior["dispersion_economico_mu"] if pd.notna(frontera_anterior["dispersion_economico_mu"]) else None,
    )
    delta_dispersion_progresismo_mu = delta(
        frontera_t["dispersion_progresismo_mu"] if pd.notna(frontera_t["dispersion_progresismo_mu"]) else None,
        frontera_anterior["dispersion_progresismo_mu"] if pd.notna(frontera_anterior["dispersion_progresismo_mu"]) else None,
    )
    magnitud_desplazamiento_ideologico = (
        (delta_dispersion_economico_mu ** 2 + delta_dispersion_progresismo_mu ** 2) ** 0.5
        if delta_dispersion_economico_mu is not None and delta_dispersion_progresismo_mu is not None
        else None
    )

    return {
        "delta_v": delta_v,
        "delta_participacion_pct": delta(exit_t["participacion_pct"], exit_anterior["participacion_pct"]),
        "delta_voto_exit_ausentismo_pct": delta(exit_t["voto_exit_ausentismo_pct"], exit_anterior["voto_exit_ausentismo_pct"]),
        "delta_voto_exit_blanco_nulo_pct": delta(exit_t["voto_exit_blanco_nulo_pct"], exit_anterior["voto_exit_blanco_nulo_pct"]),
        "delta_dispersion_economico_mu": delta_dispersion_economico_mu,
        "delta_dispersion_progresismo_mu": delta_dispersion_progresismo_mu,
        "magnitud_desplazamiento_ideologico": magnitud_desplazamiento_ideologico,
        "cuadrante_desplazamiento": clasificar_cuadrante_desplazamiento(delta_dispersion_economico_mu, delta_dispersion_progresismo_mu),
        "dispersion_cobertura_share_min": delta_min(
            frontera_t["dispersion_cobertura_share"], frontera_anterior["dispersion_cobertura_share"]
        ),
    }
