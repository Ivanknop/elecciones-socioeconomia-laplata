"""Construye la tabla anual de series macroeconómicas nacionales de
frecuencia anual (2011-2025), a partir del catálogo
`data/macroeconomia/catalogo_series_anuales.csv` y de datos.gob.ar
(`macroeconomia.datos_gob_client`).

Separado de `macroeconomia.series` (grano mensual) a propósito: forzar una
serie anual dentro de una tabla fila-por-mes deja esa columna con ~93%
de celdas vacías (solo 1 de cada 12 filas puede tener dato real, y sin
forward-fill -- ver `macroeconomia.series` -- ninguna de las otras 11 lo
tiene nunca). Separar el grano evita ese ruido: acá cada fila es un año, y
una serie anual con cobertura completa llena el 100% de sus celdas en vez
de ~7%.

## Reglas de normalización

Mismo criterio que `macroeconomia.series`, adaptado a grano anual: una
celda solo tiene valor si la fuente publicó exactamente para ese año; si
no, queda vacía (`""`) y `observaciones` lo declara. Nunca se rellena ni
se repite un valor de un año anterior.

Uso:
    PYTHONPATH=src python -m macroeconomia.series_anuales
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from macroeconomia.datos_gob_client import DatosGobClient
from macroeconomia.series import ConceptoCatalogo, _parsear_puntos, cargar_catalogo


def _valor_exacto_para_anio(puntos: list[tuple[date, float]], anio: int) -> float | None:
    """Valor de la fuente con fecha de origen en el año `anio` -- las series
    anuales de datos.gob.ar fechan cada punto al 1° de enero del año que
    publican, así que comparar por año equivale a comparar la fecha exacta."""
    for fecha, valor in puntos:
        if fecha.year == anio:
            return valor
        if fecha.year > anio:
            break
    return None


@dataclass(frozen=True)
class ReporteCoberturaAnual:
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


def construir_tabla_anual(
    catalogo: list[ConceptoCatalogo],
    puntos_por_concepto: dict[str, list[tuple[date, float]]],
    anio_inicio: int = 2011,
    anio_fin: int = 2025,
) -> tuple[list[dict], ReporteCoberturaAnual]:
    """Pura -- no hace red. `puntos_por_concepto` ya viene parseado
    (concepto -> lista de `(fecha, valor)` ascendente, ver
    `macroeconomia.series._parsear_puntos`)."""
    anios = list(range(anio_inicio, anio_fin + 1))
    conceptos_sin_dato = tuple(c.concepto for c in catalogo if not puntos_por_concepto.get(c.concepto))

    filas = []
    celdas_reales = celdas_vacias = 0

    for anio in anios:
        fila = {"anio": anio}
        observaciones = []
        for concepto in catalogo:
            puntos = puntos_por_concepto.get(concepto.concepto, [])
            valor = _valor_exacto_para_anio(puntos, anio)

            if valor is None:
                fila[concepto.concepto] = ""
                celdas_vacias += 1
                observaciones.append(f"{concepto.concepto}: sin dato (la fuente no publicó para este año)")
                continue

            fila[concepto.concepto] = valor
            celdas_reales += 1

        fila["observaciones"] = "; ".join(observaciones)
        filas.append(fila)

    reporte = ReporteCoberturaAnual(
        conceptos_totales=len(catalogo),
        conceptos_sin_ningun_dato=conceptos_sin_dato,
        celdas_totales=len(anios) * len(catalogo),
        celdas_con_dato_real=celdas_reales,
        celdas_vacias=celdas_vacias,
    )
    return filas, reporte


def generar_csv(
    catalogo_path: Path | str = "data/macroeconomia/catalogo_series_anuales.csv",
    destino: Path | str = "data/macroeconomia/series_macro_anuales_2011_2025.csv",
    cache_dir: Path | str = "data/macroeconomia/_cache/datos_gob",
    anio_inicio: int = 2011,
    anio_fin: int = 2025,
    force_refresh: bool = False,
) -> tuple[Path, ReporteCoberturaAnual]:
    catalogo = cargar_catalogo(catalogo_path)
    client = DatosGobClient(cache_dir=cache_dir)

    puntos_por_concepto = {}
    for concepto in catalogo:
        crudo = client.get_serie(concepto.id_datos_gob, force_refresh=force_refresh)
        puntos_por_concepto[concepto.concepto] = _parsear_puntos(crudo["data"])

    filas, reporte = construir_tabla_anual(catalogo, puntos_por_concepto, anio_inicio, anio_fin)

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    columnas = ["anio"] + [c.concepto for c in catalogo] + ["observaciones"]
    with destino_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)

    return destino_path, reporte


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalogo", default="data/macroeconomia/catalogo_series_anuales.csv")
    parser.add_argument("--destino", default="data/macroeconomia/series_macro_anuales_2011_2025.csv")
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
