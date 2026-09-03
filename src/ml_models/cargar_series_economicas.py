"""Panel mensual de series económicas 2001-2025.

Uso:
    PYTHONPATH=src python -m ml_models.cargar_series_economicas
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from constantes import (
    ICG_RAW_PATH,
    MACRO_CACHE_DATOS_GOB_DIR,
    REGISTRO_VARIABLES_PATH,
    SERIES_ECONOMICAS_MENSUALES_PATH,
)
from macroeconomia.datos_gob_client import DatosGobClient
from macroeconomia.series import _parsear_puntos
from socioeconomia.icg_cargar import cargar_microdatos
from socioeconomia.icg_construir_series import construir_serie_headline

ANIO_INICIO = 2001
ANIO_FIN = 2025

_PERIODO_INTERVENIDO_DESDE = date(2007, 1, 1)
_PERIODO_INTERVENIDO_HASTA = date(2015, 12, 1)

_LOOKBACK_MESES = {"trimestral": 3, "semestral": 6, "anual": 12}

_DATOS_GOB_IDS: dict[str, list[str]] = {
    "desocupacion": ["42.3_EPH_PUNTUATAL_0_M_30"],
    "salario_real": ["158.1_REPTE_0_0_5"],  # RIPTE nominal; se deflacta genéricamente más abajo
    "tc_oficial": ["175.1_DR_ESTANSE_0_0_20"],
    "reservas": ["92.1_RID_0_0_32"],
    "ipc": ["178.1_NL_GENERAL_0_0_13", "97.2_ING_2008_M_17", "148.3_INIVELNAL_DICI_M_26"],
    "icc": ["380.3_ICC_NACIONNAL_0_T_12"],
    "resultado_fiscal": ["379.4_RESULTADO_006__36_27", "379.5_RESULTADO_014__36_68", "379.9_RESULTADO_017__31_73"],
    "emae": ["143.3_NO_PR_2004_A_21"],
}


@dataclass(frozen=True)
class FilaRegistroVariable:
    id_variable: str
    descripcion: str
    fuente: str
    url_fuente: str
    periodicidad_nativa: str
    cobertura_desde: str
    cobertura_hasta: str
    nivel_geografico: str
    polaridad: str
    es_flujo: bool
    nominal: bool
    bloque_tematico: str
    estado: str
    nota_metodologica: str


def cargar_registro(path: Path | str = REGISTRO_VARIABLES_PATH) -> list[FilaRegistroVariable]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return [
            FilaRegistroVariable(
                id_variable=r["id_variable"],
                descripcion=r["descripcion"],
                fuente=r["fuente"],
                url_fuente=r["url_fuente"],
                periodicidad_nativa=r["periodicidad_nativa"],
                cobertura_desde=r["cobertura_desde"],
                cobertura_hasta=r["cobertura_hasta"],
                nivel_geografico=r["nivel_geografico"],
                polaridad=r["polaridad"],
                es_flujo=r["es_flujo"].strip().lower() == "true",
                nominal=r["nominal"].strip().lower() == "true",
                bloque_tematico=r["bloque_tematico"],
                estado=r["estado"],
                nota_metodologica=r["nota_metodologica"],
            )
            for r in csv.DictReader(f)
        ]


def _cargar_icg(anio_desde: int = 2001) -> list[tuple[date, float]]:
    """`icg_pais` -- serie nacional, no La Plata (reusa el microdato ya
    cargado en el repo, ver `socioeconomia.icg_construir_series`)."""
    df = cargar_microdatos(ICG_RAW_PATH)
    serie = construir_serie_headline(df, anio_desde=anio_desde)
    return sorted((date(int(r["año"]), int(r["mes"]), 1), float(r["icg_pais"])) for _, r in serie.iterrows())


def _cargar_datos_gob(ids: list[str], client: DatosGobClient, start_date: str = "2000-01-01") -> list[tuple[date, float]]:
    """Encadena una o más series de datos.gob.ar; si se solapan en una
    fecha, la última de la lista pisa a las anteriores (vintage más nuevo
    tiene prioridad). `force_refresh=True`: varias de estas series ya
    estaban cacheadas por `macroeconomia.series` con su propio default de
    `start_date="2010-01-01"`"""
    por_fecha: dict[date, float] = {}
    for serie_id in ids:
        crudo = client.get_serie(serie_id, start_date=start_date, force_refresh=True)
        for fecha, valor in _parsear_puntos(crudo["data"]):
            por_fecha[fecha] = valor
    return sorted(por_fecha.items())


_LOADERS = {"icg": lambda client: _cargar_icg(ANIO_INICIO)}


def _cargar_puntos_de_variable(id_variable: str, client: DatosGobClient) -> list[tuple[date, float]]:
    if id_variable in _LOADERS:
        return _LOADERS[id_variable](client)
    if id_variable in _DATOS_GOB_IDS:
        return _cargar_datos_gob(_DATOS_GOB_IDS[id_variable], client, start_date=f"{ANIO_INICIO}-01-01")
    return []


def _meses_en_rango(anio_inicio: int, anio_fin: int) -> list[date]:
    return [date(anio, mes, 1) for anio in range(anio_inicio, anio_fin + 1) for mes in range(1, 13)]


def _homogeneizar_mensual(
    puntos: list[tuple[date, float]], periodicidad_nativa: str, meses: list[date]
) -> dict[date, float | None]:
    """`diaria` no repite un valor hacia otro mes; `trimestral`/`semestral`/
    `anual` usa el punto más reciente pero nunca más viejo que su propio
    período (`_LOOKBACK_MESES`), no "lo último disponible sin límite"."""
    resultado: dict[date, float | None] = {}
    if periodicidad_nativa == "diaria":
        por_mes: dict[tuple[int, int], list[tuple[date, float]]] = {}
        for fecha, valor in puntos:
            por_mes.setdefault((fecha.year, fecha.month), []).append((fecha, valor))
        for mes in meses:
            del_mes = por_mes.get((mes.year, mes.month))
            resultado[mes] = max(del_mes, key=lambda p: p[0])[1] if del_mes else None
        return resultado

    lookback = _LOOKBACK_MESES.get(periodicidad_nativa)
    for mes in meses:
        candidatos = [(fecha, valor) for fecha, valor in puntos if fecha <= mes]
        if not candidatos:
            resultado[mes] = None
            continue
        fecha_mas_reciente, valor_mas_reciente = max(candidatos, key=lambda p: p[0])
        if lookback is None:  # mensual: solo exacto
            resultado[mes] = valor_mas_reciente if fecha_mas_reciente == mes else None
        else:
            meses_de_atraso = (mes.year - fecha_mas_reciente.year) * 12 + (mes.month - fecha_mas_reciente.month)
            resultado[mes] = valor_mas_reciente if meses_de_atraso < lookback else None
    return resultado


def _deflactar(serie_nominal: dict[date, float | None], ipc: dict[date, float | None]) -> dict[date, float | None]:
    """`serie / ipc * 100` mes a mes; vacía si falta cualquiera de los dos
    -- nunca inventa un IPC para deflactar (hereda el hueco de `ipc`)."""
    return {
        mes: (serie_nominal[mes] / ipc[mes] * 100) if (serie_nominal.get(mes) is not None and ipc.get(mes) is not None) else None
        for mes in serie_nominal
    }


def construir_tabla_mensual(
    registro: list[FilaRegistroVariable],
    puntos_por_variable: dict[str, list[tuple[date, float]]],
    anio_inicio: int = ANIO_INICIO,
    anio_fin: int = ANIO_FIN,
) -> list[dict]:
    """Pura -- no hace red. `puntos_por_variable` ya viene parseado (misma
    idea que `macroeconomia.series.construir_tabla_mensual`)."""
    meses = _meses_en_rango(anio_inicio, anio_fin)

    series_mensuales: dict[str, dict[date, float | None]] = {}
    ipc_mensual: dict[date, float | None] | None = None
    for var in registro:
        puntos = puntos_por_variable.get(var.id_variable, [])
        if not puntos:
            series_mensuales[var.id_variable] = {mes: None for mes in meses}
            continue
        serie = _homogeneizar_mensual(puntos, var.periodicidad_nativa, meses)
        series_mensuales[var.id_variable] = serie
        if var.id_variable == "ipc":
            ipc_mensual = serie

    for var in registro:
        if var.nominal and var.id_variable != "ipc":
            if ipc_mensual is None:
                series_mensuales[var.id_variable] = {mes: None for mes in meses}
            else:
                series_mensuales[var.id_variable] = _deflactar(series_mensuales[var.id_variable], ipc_mensual)

    filas = []
    for mes in meses:
        fila = {"fecha": mes.isoformat()}
        fila["periodo_intervenido"] = _PERIODO_INTERVENIDO_DESDE <= mes <= _PERIODO_INTERVENIDO_HASTA
        for var in registro:
            valor = series_mensuales.get(var.id_variable, {}).get(mes)
            fila[var.id_variable] = valor if valor is not None else ""
        filas.append(fila)
    return filas


def generar_csv(
    registro_path: Path | str = REGISTRO_VARIABLES_PATH,
    destino: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
    cache_dir: Path | str = MACRO_CACHE_DATOS_GOB_DIR,
    anio_inicio: int = ANIO_INICIO,
    anio_fin: int = ANIO_FIN,
) -> Path:
    registro = cargar_registro(registro_path)
    client = DatosGobClient(cache_dir=cache_dir)

    puntos_por_variable = {var.id_variable: _cargar_puntos_de_variable(var.id_variable, client) for var in registro}
    filas = construir_tabla_mensual(registro, puntos_por_variable, anio_inicio, anio_fin)

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    columnas = ["fecha", "periodo_intervenido"] + [var.id_variable for var in registro]
    with destino_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)
    return destino_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--registro", default=REGISTRO_VARIABLES_PATH)
    parser.add_argument("--destino", default=SERIES_ECONOMICAS_MENSUALES_PATH)
    args = parser.parse_args()
    destino = generar_csv(registro_path=args.registro, destino=args.destino)
    print(f"{destino}")


if __name__ == "__main__":
    main()
