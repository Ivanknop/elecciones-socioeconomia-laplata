"""Construye la tabla mensual unificada de series macroeconómicas nacionales
(2011-2025) a partir del catálogo `data/macroeconomia/catalogo_series.csv` y
de datos.gob.ar (`macroeconomia.datos_gob_client`). Ver
`docs/plan_macroeconomia.md` para el detalle de cada variable y las
decisiones metodológicas.

## Reglas de normalización

- Salida: una fila por mes, ordenada por fecha, una columna por concepto del
  catálogo (en el mismo orden en que aparecen sus filas), más `observaciones`.
- **Nunca se rellena ni se repite un valor.** Una celda solo tiene dato si la
  fuente publicó exactamente para ese mes (o, en series diarias, para algún
  día hábil de ese mes); si no, queda vacía (`""`) y `observaciones` lo
  declara. Es una decisión de diseño, no un hueco a "arreglar": un
  forward-fill automático le da apariencia de dato mensual real a una serie
  trimestral o anual, y quien consuma el CSV puede terminar promediando o
  graficando un valor repetido sin darse cuenta de que no es un dato nuevo
  de ese mes. Si alguien quiere repetir/interpolar sobre las celdas vacías,
  lo decide explícitamente él mismo -- este script no lo hace por
  adelantado.
- Series con frecuencia menor a mensual (trimestral, anual): solo el mes de
  origen del dato queda con valor (ej. enero/abril/julio/octubre para una
  serie trimestral) -- los demás meses del período quedan vacíos.
- Series diarias: se agregan a mensual tomando el último valor hábil
  (lunes a viernes) del mes -- es agregación de un dato real, no relleno.
  Si ese día hábil no tiene dato publicado (feriado no bursátil), se usa el
  hábil anterior más cercano dentro del mismo mes y se deja constancia en
  `observaciones`. Si ningún día hábil del mes tiene dato, la celda queda
  vacía -- no cae al valor de un mes anterior.
- Meses anteriores al primer dato publicado de una serie quedan vacíos por
  la misma regla general (no hay dato exacto para ese mes) -- nunca se
  inventa un valor.

Uso:
    PYTHONPATH=src python -m macroeconomia.series
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from macroeconomia.datos_gob_client import DatosGobClient


@dataclass(frozen=True)
class ConceptoCatalogo:
    concepto: str
    id_datos_gob: str
    periodicidad_fuente: str
    dimension: str
    notas: str = ""


def cargar_catalogo(path: Path | str) -> list[ConceptoCatalogo]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return [
            ConceptoCatalogo(
                concepto=fila["concepto"],
                id_datos_gob=fila["id_datos_gob"],
                periodicidad_fuente=fila["periodicidad_fuente"],
                dimension=fila["dimension"],
                notas=fila.get("notas", ""),
            )
            for fila in csv.DictReader(f)
        ]


def _parsear_puntos(data_cruda: list) -> list[tuple[date, float]]:
    """`[[fecha_str, valor|None], ...]` (como llega de la API) -> lista de
    `(date, float)` ascendente, descartando los `null`."""
    puntos = [
        (date.fromisoformat(str(fecha_str)[:10]), valor)
        for fecha_str, valor in data_cruda
        if valor is not None
    ]
    return sorted(puntos)


def _ultimo_dia_del_mes(mes: date) -> date:
    if mes.month == 12:
        return mes.replace(day=31)
    return mes.replace(month=mes.month + 1, day=1) - timedelta(days=1)


def _meses_en_rango(anio_inicio: int, anio_fin: int) -> list[date]:
    return [date(anio, mes, 1) for anio in range(anio_inicio, anio_fin + 1) for mes in range(1, 13)]


def _valor_exacto_para_mes(puntos: list[tuple[date, float]], mes: date) -> float | None:
    """Valor de la fuente con fecha de origen exactamente `mes`. Sirve para
    series mensuales, trimestrales y anuales por igual: la fecha de origen es
    siempre el primer día del período que publica la fuente, así que solo el
    mes de origen real de un dato trimestral/anual queda con valor -- no se
    repite hacia los meses siguientes del mismo período."""
    for fecha, valor in puntos:
        if fecha == mes:
            return valor
        if fecha > mes:
            break
    return None


def _valor_para_mes_diario(puntos_por_fecha: dict[date, float], mes: date) -> tuple[float | None, date | None, bool]:
    """Último valor hábil (lunes a viernes) del mes. Devuelve
    `(valor, fecha_usada, fue_ajustado)` -- `fue_ajustado` es True si el
    día hábil de cierre del mes no tenía dato y se usó uno anterior dentro
    del mismo mes."""
    fin_de_mes = _ultimo_dia_del_mes(mes)
    cursor = fin_de_mes
    ultimo_habil_del_mes = None
    while cursor >= mes:
        if cursor.weekday() < 5:  # lunes=0 ... viernes=4
            if ultimo_habil_del_mes is None:
                ultimo_habil_del_mes = cursor
            if cursor in puntos_por_fecha:
                return puntos_por_fecha[cursor], cursor, cursor != ultimo_habil_del_mes
        cursor -= timedelta(days=1)
    return None, None, False


def _resolver_celda(
    concepto: ConceptoCatalogo,
    puntos: list[tuple[date, float]],
    puntos_diarios: dict[date, float],
    mes: date,
) -> tuple[float | None, str | None]:
    """`(valor, nota_extra)` para un concepto en un mes dado. `None` en
    `valor` significa celda vacía -- nunca se repite un valor anterior."""
    if concepto.periodicidad_fuente == "diaria":
        valor, fecha_usada, fue_ajustado = _valor_para_mes_diario(puntos_diarios, mes)
        if valor is None:
            return None, None  # ningún día hábil del mes tuvo dato -> vacía
        nota = (
            f"último hábil con dato {fecha_usada.isoformat()}, no el cierre exacto del mes"
            if fue_ajustado
            else None
        )
        return valor, nota

    valor = _valor_exacto_para_mes(puntos, mes)
    return valor, None


@dataclass(frozen=True)
class ReporteCobertura:
    conceptos_totales: int
    conceptos_sin_ningun_dato: tuple[str, ...]
    celdas_totales: int
    celdas_con_dato_real: int
    celdas_vacias: int

    @property
    def porcentaje_dato_real(self) -> float:
        return self.celdas_con_dato_real / self.celdas_totales * 100 if self.celdas_totales else 0.0

    @property
    def porcentaje_vacio(self) -> float:
        return self.celdas_vacias / self.celdas_totales * 100 if self.celdas_totales else 0.0


def construir_tabla_mensual(
    catalogo: list[ConceptoCatalogo],
    puntos_por_concepto: dict[str, list[tuple[date, float]]],
    anio_inicio: int = 2011,
    anio_fin: int = 2025,
) -> tuple[list[dict], ReporteCobertura]:
    """Pura -- no hace red. `puntos_por_concepto` ya viene parseado
    (concepto -> lista de `(fecha, valor)` ascendente, ver `_parsear_puntos`)."""
    meses = _meses_en_rango(anio_inicio, anio_fin)
    puntos_diarios_por_concepto = {
        c.concepto: dict(puntos_por_concepto.get(c.concepto, []))
        for c in catalogo
        if c.periodicidad_fuente == "diaria"
    }
    conceptos_sin_dato = tuple(c.concepto for c in catalogo if not puntos_por_concepto.get(c.concepto))

    filas = []
    celdas_reales = celdas_vacias = 0

    for mes in meses:
        fila = {"fecha": mes.isoformat()}
        observaciones = []
        for concepto in catalogo:
            puntos = puntos_por_concepto.get(concepto.concepto, [])
            puntos_diarios = puntos_diarios_por_concepto.get(concepto.concepto, {})
            valor, nota_extra = _resolver_celda(concepto, puntos, puntos_diarios, mes)

            if valor is None:
                fila[concepto.concepto] = ""
                celdas_vacias += 1
                observaciones.append(f"{concepto.concepto}: sin dato (la fuente no publicó para este mes)")
                continue

            fila[concepto.concepto] = valor
            celdas_reales += 1
            if nota_extra:
                observaciones.append(f"{concepto.concepto}: {nota_extra}")

        fila["observaciones"] = "; ".join(observaciones)
        filas.append(fila)

    reporte = ReporteCobertura(
        conceptos_totales=len(catalogo),
        conceptos_sin_ningun_dato=conceptos_sin_dato,
        celdas_totales=len(meses) * len(catalogo),
        celdas_con_dato_real=celdas_reales,
        celdas_vacias=celdas_vacias,
    )
    return filas, reporte


def generar_csv(
    catalogo_path: Path | str = "data/macroeconomia/catalogo_series.csv",
    destino: Path | str = "data/macroeconomia/series_macro_2011_2025.csv",
    cache_dir: Path | str = "data/macroeconomia/_cache/datos_gob",
    anio_inicio: int = 2011,
    anio_fin: int = 2025,
    force_refresh: bool = False,
) -> tuple[Path, ReporteCobertura]:
    catalogo = cargar_catalogo(catalogo_path)
    client = DatosGobClient(cache_dir=cache_dir)

    puntos_por_concepto = {}
    for concepto in catalogo:
        crudo = client.get_serie(concepto.id_datos_gob, force_refresh=force_refresh)
        puntos_por_concepto[concepto.concepto] = _parsear_puntos(crudo["data"])

    filas, reporte = construir_tabla_mensual(catalogo, puntos_por_concepto, anio_inicio, anio_fin)

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    columnas = ["fecha"] + [c.concepto for c in catalogo] + ["observaciones"]
    with destino_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)

    return destino_path, reporte


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalogo", default="data/macroeconomia/catalogo_series.csv")
    parser.add_argument("--destino", default="data/macroeconomia/series_macro_2011_2025.csv")
    parser.add_argument("--cache-dir", default="data/macroeconomia/_cache/datos_gob")
    parser.add_argument("--anio-inicio", type=int, default=2011)
    parser.add_argument("--anio-fin", type=int, default=2025)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    destino, reporte = generar_csv(
        catalogo_path=args.catalogo,
        destino=args.destino,
        cache_dir=args.cache_dir,
        anio_inicio=args.anio_inicio,
        anio_fin=args.anio_fin,
        force_refresh=args.force_refresh,
    )
    print(
        f"{destino} -- {reporte.celdas_con_dato_real}/{reporte.celdas_totales} celdas con dato real "
        f"({reporte.porcentaje_dato_real:.1f}%), {reporte.celdas_vacias} vacías ({reporte.porcentaje_vacio:.1f}%)"
    )
    if reporte.conceptos_sin_ningun_dato:
        print(f"conceptos sin ningún dato: {', '.join(reporte.conceptos_sin_ningun_dato)}")


if __name__ == "__main__":
    main()
