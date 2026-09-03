"""Panel trimestral en formato largo 

Uso:
    PYTHONPATH=src python -m ml_models.construir_panel_trimestral
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from constantes import (
    OFICIALISMO_POR_NIVEL_PATH,
    PANEL_TRIMESTRAL_DIR,
    REGISTRO_VARIABLES_PATH,
    RESULTADO_DISTRITO_PATH,
    SERIES_ECONOMICAS_MENSUALES_PATH,
    VENTANAS_PATH,
)
from ml_models.cargar_series_economicas import FilaRegistroVariable, cargar_registro
from ml_models.construir_calendario import NIVELES
from ml_models.construir_panel_ventanas import (
    _cargar_oficialismo_por_nivel,
    _cargar_resultado_distrito,
    _cargar_series_mensuales,
    _cargar_ventanas,
    _leer_dicts,
)
from ml_models.construir_resultado_distrito import FilaResultadoDistrito
from ml_models.features_ventana import _meses_en_ventana


def calcular_n_trimestres(fecha_inicio_vc: str, fecha_fin_vc: str) -> int:
    """`round(meses_entre_elecciones / 3)` -- variable por ventana real (6
    a 10 en el calendario 2001-2025), nunca fijo en 8 (corrige el supuesto
    de D4, ver D13 en `docs/decisiones_metodologicas.md`)."""
    inicio = date.fromisoformat(fecha_inicio_vc[:10])
    fin = date.fromisoformat(fecha_fin_vc[:10])
    meses = (fin.year - inicio.year) * 12 + (fin.month - inicio.month)
    return round(meses / 3)


def _particionar_meses(meses: list[date], n: int) -> list[list[date]]:
    """Reparte `meses` en `n` grupos contiguos lo más parejos posible
    (equivalente a `numpy.array_split`)."""
    largo, resto = divmod(len(meses), n)
    grupos = []
    cursor = 0
    for i in range(n):
        tamano = largo + (1 if i < resto else 0)
        grupos.append(meses[cursor : cursor + tamano])
        cursor += tamano
    return grupos


def _promedio_trimestre(serie: dict[date, float | None], meses: list[date]) -> float | None:
    """Promedio simple de los meses con dato real de `meses`; `None` si
    ninguno lo tiene (nunca se imputa)."""
    valores = [serie[m] for m in meses if serie.get(m) is not None]
    return sum(valores) / len(valores) if valores else None


def _ancla_inicial(serie: dict[date, float | None], mes_eleccion_t_menos_1: date) -> float | None:
    """Último valor real de `serie` en o antes de `mes_eleccion_t_menos_1`
    -- ancla de arranque de `_variacion_flujo_trimestre` para el primer
    trimestre de cada ventana."""
    candidatos = sorted((m, v) for m, v in serie.items() if m <= mes_eleccion_t_menos_1 and v is not None)
    return candidatos[-1][1] if candidatos else None


def _variacion_flujo_trimestre(
    serie: dict[date, float | None], meses: list[date], ancla: float | None
) -> tuple[float | None, float | None]:
    """Variación % del índice de nivel entre `ancla` (último valor
    conocido antes de este trimestre) y el último valor real dentro de
    `meses`; devuelve también el ancla actualizada para el próximo
    trimestre (se mantiene si este trimestre no tuvo dato real -- nunca se
    interpola ni se compone contra un valor bruto). `None` si falta ancla
    o no hay dato real en el trimestre."""
    con_dato = [(m, serie[m]) for m in meses if serie.get(m) is not None]
    if not con_dato:
        return None, ancla
    ultimo = con_dato[-1][1]
    valor = (ultimo / ancla - 1) * 100 if ancla not in (None, 0) else None
    return valor, ultimo


def _variables_con_datos(
    registro: list[FilaRegistroVariable], series_mensuales: dict[str, dict[date, float | None]]
) -> list[FilaRegistroVariable]:
    """Filtra a variables con al menos un valor real (D9): agregar una
    variable nueva no requiere tocar este script."""
    return [
        var for var in registro if any(v is not None for v in series_mensuales.get(var.id_variable, {}).values())
    ]


def _parsear_bool_csv(valor: str) -> bool | None:
    """Mismo formato que `_escribir_csv` escribe para columnas booleanas
    -- parser único, no reimplementar en otro módulo."""
    if not valor:
        return None
    return valor.strip().lower() == "true"


def _cargar_periodo_intervenido(path: Path | str) -> dict[date, bool]:
    """Columna `periodo_intervenido` de `series_economicas_mensuales.csv`
    por mes -- `_cargar_series_mensuales` (Fase 4) no la trae, solo las
    columnas del registro."""
    return {date.fromisoformat(r["fecha"]): _parsear_bool_csv(r["periodo_intervenido"]) or False for r in _leer_dicts(path)}


def _fila_frontera(
    v: dict,
    tipo_fila: str,
    orden: int,
    anio: int,
    nivel: str,
    fecha: str,
    resultado_por_anio_nivel: dict[tuple[int, str], FilaResultadoDistrito],
    oficialismo_por_nivel: dict[tuple[int, str], dict],
    variables: list[FilaRegistroVariable],
) -> dict:
    """`gana_oficialismo`/`share_oficialismo`/`agrupacion_oficialismo`
    cruzados por (año, nivel); columnas económicas en `None` -- la
    elección es un evento, no un promedio."""
    resultado = resultado_por_anio_nivel.get((anio, nivel))
    of = oficialismo_por_nivel.get((anio, nivel))
    fila = {
        "id_transicion": v["id_transicion"],
        "nivel": nivel,
        "anio_t": v["anio_t"],
        "anio_t_menos_1": v["anio_t_menos_1"],
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


def construir_panel_trimestral(
    ventanas: list[dict],
    registro: list[FilaRegistroVariable],
    series_mensuales: dict[str, dict[date, float | None]],
    periodo_intervenido_por_mes: dict[date, bool],
    resultado_por_anio_nivel: dict[tuple[int, str], FilaResultadoDistrito],
    oficialismo_por_nivel: dict[tuple[int, str], dict],
    nivel: str,
) -> list[dict]:
    """Pura -- todo cargado en memoria. Duplicación intencional entre
    ventanas adyacentes (la elección t de una es la t-1 de la siguiente):
    cada `id_transicion` es autocontenida, mismo principio que
    `panel_ventanas.csv`."""
    variables = _variables_con_datos(registro, series_mensuales)

    filas: list[dict] = []
    for v in sorted((v for v in ventanas if v["nivel"] == nivel), key=lambda v: v["anio_t"]):
        n = calcular_n_trimestres(v["fecha_inicio_vc"], v["fecha_fin_vc"])
        meses = _meses_en_ventana(v["fecha_inicio_vc"], v["fecha_fin_vc"])[1:]
        grupos = _particionar_meses(meses, n)

        filas.append(
            _fila_frontera(
                v,
                "eleccion_t_menos_1",
                0,
                v["anio_t_menos_1"],
                nivel,
                v["fecha_inicio_vc"],
                resultado_por_anio_nivel,
                oficialismo_por_nivel,
                variables,
            )
        )

        mes_eleccion_t_menos_1 = date.fromisoformat(v["fecha_inicio_vc"][:10])
        anclas = {
            var.id_variable: _ancla_inicial(series_mensuales[var.id_variable], mes_eleccion_t_menos_1)
            for var in variables
            if var.es_flujo
        }

        for i, grupo in enumerate(grupos, start=1):
            fila = {
                "id_transicion": v["id_transicion"],
                "nivel": nivel,
                "anio_t": v["anio_t"],
                "anio_t_menos_1": v["anio_t_menos_1"],
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
                v,
                "eleccion_t",
                n + 1,
                v["anio_t"],
                nivel,
                v["fecha_fin_vc"],
                resultado_por_anio_nivel,
                oficialismo_por_nivel,
                variables,
            )
        )
    return filas


def _escribir_csv(path: Path | str, filas: list[dict], columnas: list[str]) -> Path:
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for fila in filas:
            writer.writerow({col: (fila.get(col) if fila.get(col) is not None else "") for col in columnas})
    return destino


def generar_csvs(
    ventanas_path: Path | str = VENTANAS_PATH,
    registro_path: Path | str = REGISTRO_VARIABLES_PATH,
    series_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
    resultado_path: Path | str = RESULTADO_DISTRITO_PATH,
    oficialismo_path: Path | str = OFICIALISMO_POR_NIVEL_PATH,
    destino_dir: Path | str = PANEL_TRIMESTRAL_DIR,
) -> list[Path]:
    """Un CSV por nivel (mismo código, parametrizado), nunca un cuarto
    archivo apilado (D7/D10)."""
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
        "anio_t_menos_1",
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
        filas = construir_panel_trimestral(
            ventanas, registro, series_mensuales, periodo_intervenido_por_mes, resultado_por_anio_nivel, oficialismo_por_nivel, nivel
        )
        destinos.append(_escribir_csv(Path(destino_dir) / f"panel_trimestral_{nivel}.csv", filas, columnas))
    return destinos


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    for destino in generar_csvs():
        print(destino)


if __name__ == "__main__":
    main()
