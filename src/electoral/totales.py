"""Resultado total por agrupación política, un CSV por (año, nivel, etapa), a
partir de `data/distrito/<año>/<nivel>/<etapa>/circuito_<nivel>.json` (no de
la API ni del JSON agregado crudo -- ver docs/FUNCIONALIDADES.md, "Anomalía
conocida: JSON agregado de Presidente 2019": ese agregado subestima Presidente
2019, `circuito_<nivel>.json` ya está corregido porque sale del CSV oficial).
`etapa` es `generales`, `paso`, o `balotaje` -- estas dos últimas solo existen
para los (año, nivel) donde efectivamente hubo esa instancia (ver
docs/FUNCIONALIDADES.md, "PASO y balotaje").

Suma los `positivos` de todos los circuitos de ese (año, nivel, etapa) con
`totalizar_agrupaciones` (`electoral.models`), la misma función que combinaría
resultados parciales por mesa si hiciera falta ese nivel de detalle.

Salida: `generales` mantiene la ruta histórica
`data/totales/<nivel>/<año>/resultado_total.csv` (compatibilidad hacia atrás);
`paso`/`balotaje` van a `data/totales/<nivel>/<año>/<etapa>/resultado_total.csv`,
hermana de esa ruta.

Uso:
    PYTHONPATH=src python -m electoral.totales --anio 2023 --nivel intendente
    PYTHONPATH=src python -m electoral.totales --anio 2023 --nivel intendente --etapa paso
    PYTHONPATH=src python -m electoral.totales                    # todo lo disponible
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from electoral.models import ValorAgrupacion, totalizar_agrupaciones


def _combos_disponibles(data_dir: Path | str) -> list[tuple[int, str, str]]:
    """(año, nivel, etapa) para los que ya existe `circuito_<nivel>.json`."""
    combos = []
    for path in Path(data_dir).glob("*/*/*/circuito_*.json"):
        etapa = path.parents[0].name
        nivel = path.parents[1].name
        anio = int(path.parents[2].name)
        combos.append((anio, nivel, etapa))
    return sorted(combos)


def resultado_total_por_agrupacion(
    data_dir: Path | str, anio: int, nivel: str, etapa: str = "generales"
) -> list[ValorAgrupacion]:
    circuito_json = Path(data_dir) / str(anio) / nivel / etapa / f"circuito_{nivel}.json"
    contenido = json.loads(circuito_json.read_text(encoding="utf-8"))

    valores = [
        ValorAgrupacion(id_agrupacion=id_agrupacion, nombre_agrupacion=info["nombre"], votos=info["votos"], votos_porcentaje=0.0)
        for circuito in contenido["circuitos"].values()
        for id_agrupacion, info in circuito["positivos"].items()
    ]
    return totalizar_agrupaciones(valores)


def generar_csv_totales(
    data_dir: Path | str, salida_dir: Path | str, anio: int, nivel: str, etapa: str = "generales"
) -> Path:
    totales = resultado_total_por_agrupacion(data_dir, anio, nivel, etapa)

    circuito_json = Path(data_dir) / str(anio) / nivel / etapa / f"circuito_{nivel}.json"
    salida = Path(salida_dir) / nivel / str(anio)
    if etapa != "generales":
        salida = salida / etapa
    salida.mkdir(parents=True, exist_ok=True)
    destino = salida / "resultado_total.csv"

    with destino.open("w", encoding="utf-8", newline="") as f:
        f.write(f"# Resultado total por agrupación -- La Plata, {nivel} {etapa} {anio}\n")
        f.write(f"# Fuente: suma de los circuitos de {circuito_json.as_posix()}\n")
        writer = csv.writer(f)
        writer.writerow(["id_agrupacion", "agrupacion", "votos", "votos_porcentaje"])
        for v in totales:
            writer.writerow([v.id_agrupacion, v.nombre_agrupacion, v.votos, f"{v.votos_porcentaje:.2f}"])

    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, help="si se omite, corre todos los años disponibles")
    parser.add_argument("--nivel", help="si se omite, corre todos los niveles disponibles para ese año")
    parser.add_argument("--etapa", help="generales/paso/balotaje -- si se omite, corre todas las etapas disponibles")
    parser.add_argument("--data-dir", default="data/distrito")
    parser.add_argument("--salida-dir", default="data/totales")
    args = parser.parse_args()

    combos = _combos_disponibles(args.data_dir)
    if args.anio:
        combos = [(anio, nivel, etapa) for anio, nivel, etapa in combos if anio == args.anio]
    if args.nivel:
        combos = [(anio, nivel, etapa) for anio, nivel, etapa in combos if nivel == args.nivel]
    if args.etapa:
        combos = [(anio, nivel, etapa) for anio, nivel, etapa in combos if etapa == args.etapa]

    if not combos:
        print("sin datos para los filtros pedidos")
        return

    for anio, nivel, etapa in combos:
        destino = generar_csv_totales(args.data_dir, args.salida_dir, anio, nivel, etapa)
        print(f"{anio} {nivel} {etapa} -> {destino}")


if __name__ == "__main__":
    main()
