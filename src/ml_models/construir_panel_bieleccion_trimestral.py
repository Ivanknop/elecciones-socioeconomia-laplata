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
    OFICIALISMO_POR_NIVEL_PATH,
    PANEL_BIELECCION_TRIMESTRAL_DIR,
    REGISTRO_VARIABLES_PATH,
    RESULTADO_DISTRITO_PATH,
    SERIES_ECONOMICAS_MENSUALES_PATH,
    VENTANAS_PATH,
)
from ml_models.cargar_series_economicas import FilaRegistroVariable, cargar_registro
from ml_models.construir_calendario import NIVELES
from ml_models.construir_panel_trimestral import (
    _ancla_inicial,
    _cargar_periodo_intervenido,
    _escribir_csv,
    _particionar_meses,
    _promedio_trimestre,
    _variables_con_datos,
    _variacion_flujo_trimestre,
    calcular_n_trimestres,
)
from ml_models.construir_panel_ventanas import (
    _cargar_oficialismo_por_nivel,
    _cargar_resultado_distrito,
    _cargar_series_mensuales,
    _cargar_ventanas,
)
from ml_models.construir_resultado_distrito import FilaResultadoDistrito
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
    resultado_por_anio_nivel: dict[tuple[int, str], FilaResultadoDistrito],
    oficialismo_por_nivel: dict[tuple[int, str], dict],
    variables: list[FilaRegistroVariable],
) -> dict:
    """Análoga a `construir_panel_trimestral._fila_frontera`, con
    `anio_t_menos_2` en vez de `anio_t_menos_1`."""
    resultado = resultado_por_anio_nivel.get((anio, nivel))
    of = oficialismo_por_nivel.get((anio, nivel))
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
        "periodo_intervenido": None,
        "gana_oficialismo": resultado.gana_oficialismo if resultado else None,
        "share_oficialismo": resultado.share_oficialismo if resultado else None,
        "agrupacion_oficialismo": of["agrupacion_oficialismo"] if of else None,
    }
    for var in variables:
        fila[var.id_variable] = None
    return fila


def construir_panel_bieleccion_trimestral(
    ventanas: list[dict],
    registro: list[FilaRegistroVariable],
    series_mensuales: dict[str, dict[date, float | None]],
    periodo_intervenido_por_mes: dict[date, bool],
    resultado_por_anio_nivel: dict[tuple[int, str], FilaResultadoDistrito],
    oficialismo_por_nivel: dict[tuple[int, str], dict],
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
                resultado_por_anio_nivel,
                oficialismo_por_nivel,
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
                "periodo_intervenido": any(periodo_intervenido_por_mes.get(m, False) for m in grupo),
                "gana_oficialismo": None,
                "share_oficialismo": None,
                "agrupacion_oficialismo": None,
            }
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
                resultado_por_anio_nivel,
                oficialismo_por_nivel,
                variables,
            )
        )
    return filas


def generar_csvs(
    ventanas_path: Path | str = VENTANAS_PATH,
    registro_path: Path | str = REGISTRO_VARIABLES_PATH,
    series_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
    resultado_path: Path | str = RESULTADO_DISTRITO_PATH,
    oficialismo_path: Path | str = OFICIALISMO_POR_NIVEL_PATH,
    destino_dir: Path | str = PANEL_BIELECCION_TRIMESTRAL_DIR,
) -> list[Path]:
    ventanas = _cargar_ventanas(ventanas_path)
    registro = cargar_registro(registro_path)
    series_mensuales = _cargar_series_mensuales(series_path, registro)
    periodo_intervenido_por_mes = _cargar_periodo_intervenido(series_path)
    resultado_por_anio_nivel = _cargar_resultado_distrito(resultado_path)
    oficialismo_por_nivel = _cargar_oficialismo_por_nivel(oficialismo_path)

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
        "periodo_intervenido",
        "gana_oficialismo",
        "share_oficialismo",
        "agrupacion_oficialismo",
    ] + sorted(var.id_variable for var in variables)

    destinos = []
    for nivel in NIVELES:
        filas = construir_panel_bieleccion_trimestral(
            ventanas, registro, series_mensuales, periodo_intervenido_por_mes, resultado_por_anio_nivel, oficialismo_por_nivel, nivel
        )
        destinos.append(_escribir_csv(Path(destino_dir) / f"panel_bieleccion_trimestral_{nivel}.csv", filas, columnas))
    return destinos


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    for destino in generar_csvs():
        print(destino)


if __name__ == "__main__":
    main()
