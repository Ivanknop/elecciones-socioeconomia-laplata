"""Panel trimestral "bielección" -- variante de `construir_panel_trimestral.py`
que cubre el bloque largo (ventana `_vl` de `features_ventana.py`: elección
t-2 a elección t, 4 años/dos elecciones) en vez de la ventana corta (`_vc`,
t-1 a t). 

Uso:
    PYTHONPATH=src python -m ml_models.construir_panel_bieleccion_trimestral
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from constantes import (
    ELECCIONES_RESUMEN_PATH,
    PANEL_BIELECCION_TRIMESTRAL_DIR,
    REGISTRO_VARIABLES_PATH,
    SERIES_ECONOMICAS_MENSUALES_PATH,
    VENTANAS_PATH,
)
from ml_models.cargar_series_economicas import FilaRegistroVariable, cargar_registro
from ml_models.construir_calendario import NIVELES
from ml_models.construir_elecciones_resumen import COLUMNAS_ELECCION_PANEL, FilaEleccion, cargar_elecciones
from ml_models.construir_panel_trimestral import (
    _ancla_inicial,
    _escribir_csv,
    _particionar_meses,
    _promedio_trimestre,
    _variables_con_datos,
    _variacion_flujo_trimestre,
    calcular_n_trimestres,
)
from ml_models.construir_panel_ventanas import _cargar_series_mensuales, _cargar_ventanas
from ml_models.features_ventana import _meses_en_ventana


def _fila_frontera(
    tipo_fila: str,
    orden: int,
    id_transicion: str,
    nivel: str,
    anio_t: int,
    anio_t_menos_2: int,
    anio: int,
    fecha: str,
    elecciones_por_anio_nivel: dict[tuple[int, str], FilaEleccion],
    variables: list[FilaRegistroVariable],
) -> dict:
    """Análoga a `construir_panel_trimestral._fila_frontera`, con
    `anio_t_menos_2` en vez de `anio_t_menos_1`."""
    eleccion = elecciones_por_anio_nivel.get((anio, nivel))
    fila = {
        "id_transicion": id_transicion,
        "nivel": nivel,
        "anio_t": anio_t,
        "anio_t_menos_2": anio_t_menos_2,
        "orden": orden,
        "tipo_fila": tipo_fila,
        "fecha_inicio": fecha,
        "fecha_fin": fecha,
        "n_meses": None,
    }
    for col in COLUMNAS_ELECCION_PANEL:
        fila[col] = getattr(eleccion, col) if eleccion is not None else None
    for var in variables:
        fila[var.id_variable] = None
    return fila


def construir_panel_bieleccion_trimestral(
    ventanas: list[dict],
    registro: list[FilaRegistroVariable],
    series_mensuales: dict[str, dict[date, float | None]],
    elecciones_por_anio_nivel: dict[tuple[int, str], FilaEleccion],
    nivel: str,
) -> list[dict]:
    """Pura -- mismas fuentes que `construir_panel_trimestral`, ventana
    [fecha_inicio_vl, fecha_fin_vc] en vez de [fecha_inicio_vc, fecha_fin_vc]."""
    variables = _variables_con_datos(registro, series_mensuales)

    filas: list[dict] = []
    for v in sorted((v for v in ventanas if v["nivel"] == nivel), key=lambda v: v["anio_t"]):
        if v["fecha_inicio_vl"] is None:
            continue
        anio_t, anio_t_menos_2 = v["anio_t"], v["anio_t_menos_2"]
        fecha_inicio_vl, fecha_fin_vc = v["fecha_inicio_vl"], v["fecha_fin_vc"]
        id_transicion = f"{nivel}_{anio_t_menos_2}_{anio_t}"

        n = calcular_n_trimestres(fecha_inicio_vl, fecha_fin_vc)
        meses = _meses_en_ventana(fecha_inicio_vl, fecha_fin_vc)[1:]
        grupos = _particionar_meses(meses, n)

        filas.append(
            _fila_frontera(
                "eleccion_t_menos_2",
                0,
                id_transicion,
                nivel,
                anio_t,
                anio_t_menos_2,
                anio_t_menos_2,
                fecha_inicio_vl,
                elecciones_por_anio_nivel,
                variables,
            )
        )

        mes_eleccion_t_menos_2 = date.fromisoformat(fecha_inicio_vl[:10])
        anclas = {
            var.id_variable: _ancla_inicial(series_mensuales[var.id_variable], mes_eleccion_t_menos_2)
            for var in variables
            if var.es_flujo
        }

        for i, grupo in enumerate(grupos, start=1):
            fila = {
                "id_transicion": id_transicion,
                "nivel": nivel,
                "anio_t": anio_t,
                "anio_t_menos_2": anio_t_menos_2,
                "orden": i,
                "tipo_fila": "trimestre",
                "fecha_inicio": grupo[0].isoformat(),
                "fecha_fin": grupo[-1].isoformat(),
                "n_meses": len(grupo),
            }
            for col in COLUMNAS_ELECCION_PANEL:
                fila[col] = None
            for var in variables:
                serie = series_mensuales[var.id_variable]
                if var.es_flujo:
                    valor, anclas[var.id_variable] = _variacion_flujo_trimestre(serie, grupo, anclas[var.id_variable])
                else:
                    valor = _promedio_trimestre(serie, grupo)
                fila[var.id_variable] = valor
            filas.append(fila)

        filas.append(
            _fila_frontera(
                "eleccion_t",
                n + 1,
                id_transicion,
                nivel,
                anio_t,
                anio_t_menos_2,
                anio_t,
                fecha_fin_vc,
                elecciones_por_anio_nivel,
                variables,
            )
        )
    return filas


def generar_csvs(
    ventanas_path: Path | str = VENTANAS_PATH,
    registro_path: Path | str = REGISTRO_VARIABLES_PATH,
    series_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
    elecciones_path: Path | str = ELECCIONES_RESUMEN_PATH,
    destino_dir: Path | str = PANEL_BIELECCION_TRIMESTRAL_DIR,
) -> list[Path]:
    ventanas = _cargar_ventanas(ventanas_path)
    registro = cargar_registro(registro_path)
    series_mensuales = _cargar_series_mensuales(series_path, registro)
    elecciones_por_anio_nivel = cargar_elecciones(elecciones_path)

    variables = _variables_con_datos(registro, series_mensuales)
    columnas = [
        "id_transicion",
        "nivel",
        "anio_t",
        "anio_t_menos_2",
        "orden",
        "tipo_fila",
        "fecha_inicio",
        "fecha_fin",
        "n_meses",
    ] + COLUMNAS_ELECCION_PANEL + sorted(var.id_variable for var in variables)

    destinos = []
    for nivel in NIVELES:
        filas = construir_panel_bieleccion_trimestral(ventanas, registro, series_mensuales, elecciones_por_anio_nivel, nivel)
        destinos.append(_escribir_csv(Path(destino_dir) / f"panel_bieleccion_trimestral_{nivel}.csv", filas, columnas))
    return destinos


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    for destino in generar_csvs():
        print(destino)


if __name__ == "__main__":
    main()
