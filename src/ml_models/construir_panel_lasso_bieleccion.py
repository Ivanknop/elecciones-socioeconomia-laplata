"""Panel ancho, una fila por transición bielección (t-2 -> t), para
modelado LASSO/Bayes -- misma forma que `panel_ventanas.csv` pero
construido a partir de `data/tfi_data/panel/t-2/panel_bieleccion_trimestral_<nivel>.csv`
(D14) en vez de `series_economicas_mensuales.csv`. Variable a predecir:
`delta_v` sobre el bloque largo (`share_oficialismo` de la fila
`eleccion_t` menos la de `eleccion_t_menos_2`). Variables explicativas:
trayectoria trimestral (`_nivel_trim`/`_pendiente_trim`/`_volatilidad_trim`/
`_final_trim`) de cada variable de `registro_variables.csv` sobre las
filas `tipo_fila == "trimestre"` de la transición.

Uso:
    PYTHONPATH=src python -m ml_models.construir_panel_lasso_bieleccion
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from constantes import PANEL_BIELECCION_TRIMESTRAL_DIR, PANEL_VENTANAS_BIELECCION_PATH
from ml_models.construir_calendario import NIVELES
from ml_models.features_ventana import _nivel, _pendiente, _volatilidad
from ml_models.targets_frontera import calcular_targets


def _agregar_variable(valores: list[float], n_final: int = 2) -> dict[str, float | None]:
    """`_nivel`/`_pendiente`/`_volatilidad` (mismas fórmulas que
    `features_ventana.py`, sobre la serie ya trimestralizada en vez de
    mensual) más `_final` (media de los últimos `n_final` trimestres --
    2 trimestres ~ 6 meses, mismo horizonte que `_final` mensual)."""
    return {
        "nivel": _nivel(valores),
        "pendiente": _pendiente(valores),
        "volatilidad": _volatilidad(valores),
        "final": _nivel(valores[-n_final:]) if valores else None,
    }


def construir_fila_transicion(filas_transicion: pd.DataFrame, variables: list[str]) -> dict:
    """Una fila de `filas_transicion` por `tipo_fila` (`eleccion_t_menos_2`,
    `trimestre`×N, `eleccion_t`), todas del mismo `id_transicion`."""
    frontera_t = filas_transicion[filas_transicion["tipo_fila"] == "eleccion_t"].iloc[0]
    frontera_t_menos_2 = filas_transicion[filas_transicion["tipo_fila"] == "eleccion_t_menos_2"].iloc[0]
    trimestres = filas_transicion[filas_transicion["tipo_fila"] == "trimestre"]

    targets = calcular_targets(frontera_t, frontera_t_menos_2)
    fila = {
        "id_transicion": filas_transicion["id_transicion"].iloc[0],
        "nivel": filas_transicion["nivel"].iloc[0],
        "anio_t": frontera_t["anio_t"],
        "anio_t_menos_2": frontera_t["anio_t_menos_2"],
        "delta_v": targets["delta_v"],
        "gana_oficialismo": frontera_t["gana_oficialismo"],
        "share_oficialismo": frontera_t["share_oficialismo"],
        "delta_participacion_pct": targets["delta_participacion_pct"],
        "delta_voto_exit_ausentismo_pct": targets["delta_voto_exit_ausentismo_pct"],
        "delta_voto_exit_blanco_nulo_pct": targets["delta_voto_exit_blanco_nulo_pct"],
        "delta_dispersion_economico_mu": targets["delta_dispersion_economico_mu"],
        "delta_dispersion_progresismo_mu": targets["delta_dispersion_progresismo_mu"],
        "magnitud_desplazamiento_ideologico": targets["magnitud_desplazamiento_ideologico"],
        "cuadrante_desplazamiento": targets["cuadrante_desplazamiento"],
        "dispersion_cobertura_share_min": targets["dispersion_cobertura_share_min"],
    }
    for variable in variables:
        valores_completos = trimestres[variable]
        valores = valores_completos.dropna().tolist()
        fila[f"{variable}_cobertura_parcial"] = bool(valores) and len(valores) < len(valores_completos)
        for sufijo, valor in _agregar_variable(valores).items():
            fila[f"{variable}_{sufijo}_trim"] = valor
    return fila


def construir_panel(niveles: tuple[str, ...] = NIVELES, panel_dir: Path | str = PANEL_BIELECCION_TRIMESTRAL_DIR) -> pd.DataFrame:
    filas = []
    for nivel in niveles:
        df_nivel = pd.read_csv(Path(panel_dir) / f"panel_bieleccion_trimestral_{nivel}.csv")
        variables = [
            c for c in df_nivel.columns
            if c not in (
                "id_transicion", "nivel", "anio_t", "anio_t_menos_2", "orden", "tipo_fila",
                "fecha_inicio", "fecha_fin", "n_meses", "votantes_habilitados", "votos_positivos",
                "votos_blancos", "votos_nulos", "ausentismo", "votos_blancos_y_nulos",
                "participacion_pct", "gana_oficialismo", "share_oficialismo", "agrupacion_oficialismo",
                "n_fuerzas_viables", "share_marginal_acumulado", "share_oposicion_principal",
                "share_otras_fuerzas_viables", "dispersion_economico_mu", "dispersion_economico_sigma2",
                "dispersion_progresismo_mu", "dispersion_progresismo_sigma2", "dispersion_cobertura_share",
                "resultado_disponible",
            )
        ]
        for id_transicion, filas_transicion in df_nivel.groupby("id_transicion", sort=False):
            filas.append(construir_fila_transicion(filas_transicion, variables))
    return pd.DataFrame(filas)


def generar_csv(destino: Path | str = PANEL_VENTANAS_BIELECCION_PATH, panel_dir: Path | str = PANEL_BIELECCION_TRIMESTRAL_DIR) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    construir_panel(panel_dir=panel_dir).to_csv(destino, index=False)
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    print(generar_csv())


if __name__ == "__main__":
    main()
