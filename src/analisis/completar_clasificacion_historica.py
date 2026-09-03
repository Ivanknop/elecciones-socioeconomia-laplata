"""Extiende `clasificacion_ideologica_agrupaciones.csv` (poblada por los
notebooks 02/03 vía `circuito_<cargo>.json`, por eso limitada a 2011-2025)
con las agrupaciones 2001-2009, cuya clasificación vive únicamente en
`data/tfi_data/elecciones/<año>_<nivel>.csv` -- ese rango nunca pasó por
los notebooks porque no tiene `circuito_<cargo>.json`
(`ml_models.construir_elecciones` documenta el mismo hueco en su propio
docstring), así que su `campo_ideologico`/`filiacion_politica`/`vparty_*`
se completó a mano directamente en esos CSV durante la sesión "Agrega
elecciones 2001-2009..." (ver `docs/adquisicion_datos_especializacion.md`
§1.a) en vez de vía el CSV maestro.

Append-only, mismo invariante que las notebooks 02/03 (ver CLAUDE.md):
nunca sobreescribe una fila (año, nivel, agrupación) ya presente en el CSV
destino -- correrlo de nuevo después de que 2001-2009 ya esté incorporado
no duplica ni pisa nada.

Uso:
  PYTHONPATH=src python -m analisis.completar_clasificacion_historica
  PYTHONPATH=src python -m analisis.completar_clasificacion_historica --anio-max 2009
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from analisis.totales_por_lista import NIVEL_A_NIVEL_CSV
from constantes import CLASIFICACION_IDEOLOGICA_PATH, ELECCIONES_DIR

_COLUMNAS = (
    "anio", "agrupacion", "nivel", "campo_ideologico", "filiacion_politica",
    "vparty_economico", "vparty_progresismo", "vparty_populismo",
)
_NO_AGRUPACIONES = {"BLANCO", "NULO", "VOTANTES_HABILITADOS"}
_RE_CARGO = re.compile(r"\(cargo: (\w+)\)")


def _cargo_de_archivo(path: Path) -> str:
    with path.open(encoding="utf-8") as f:
        primera_linea = f.readline()
    m = _RE_CARGO.search(primera_linea)
    if not m:
        raise ValueError(f"{path}: no se pudo extraer el cargo de la primera línea: {primera_linea!r}")
    return m.group(1)


def leer_clasificacion_de_eleccion(path: Path | str) -> list[dict]:
    """Una fila por agrupación de `<año>_<nivel>.csv` (excluye
    BLANCO/NULO/VOTANTES_HABILITADOS, que no son agrupaciones), con
    `nivel` normalizado al mismo valor que usa
    `clasificacion_ideologica_agrupaciones.csv` (`NIVEL_A_NIVEL_CSV`,
    gobernador->gobernacion; el resto de los cargos ya coincide)."""
    path = Path(path)
    anio = int(path.stem.split("_")[0])
    cargo = _cargo_de_archivo(path)
    nivel = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
    with path.open(encoding="utf-8", newline="") as f:
        f.readline()  # '# Total de votos, elección general -- ...'
        filas_crudas = list(csv.DictReader(f))
    return [
        {
            "anio": str(anio),
            "agrupacion": fila["agrupacion"],
            "nivel": nivel,
            "campo_ideologico": fila["campo_ideologico"],
            "filiacion_politica": fila["filiacion_politica"],
            "vparty_economico": fila["vparty_economico"],
            "vparty_progresismo": fila["vparty_progresismo"],
            "vparty_populismo": fila["vparty_populismo"],
        }
        for fila in filas_crudas
        if fila["agrupacion"] not in _NO_AGRUPACIONES
    ]


def extraer_clasificacion_historica(elecciones_dir: Path | str, anio_max: int = 2009) -> list[dict]:
    """Todas las filas-agrupación de `<año>_<nivel>.csv` con año <=
    `anio_max` -- por diseño 2001-2009, el único rango cuya clasificación
    no vive en el CSV maestro (ver docstring del módulo)."""
    elecciones_dir = Path(elecciones_dir)
    filas: list[dict] = []
    for path in sorted(elecciones_dir.glob("*.csv")):
        anio = int(path.stem.split("_")[0])
        if anio > anio_max:
            continue
        filas.extend(leer_clasificacion_de_eleccion(path))
    return filas


def fusionar_clasificacion(existentes: list[dict], nuevas: list[dict]) -> list[dict]:
    """Append-only: agrega de `nuevas` solo las filas cuya clave (año,
    nivel, agrupación) no está ya en `existentes` -- nunca sobreescribe,
    mismo invariante que los notebooks 02/03 (ver CLAUDE.md, sección
    `data/agrupaciones/`). Resultado ordenado (año, nivel, agrupación),
    mismo criterio que ya usa el CSV existente."""
    claves = {(f["anio"], f["nivel"], f["agrupacion"]) for f in existentes}
    agregadas = [f for f in nuevas if (f["anio"], f["nivel"], f["agrupacion"]) not in claves]
    combinado = existentes + agregadas
    combinado.sort(key=lambda f: (int(f["anio"]), f["nivel"], f["agrupacion"]))
    return combinado


def leer_clasificacion_existente(path: Path | str) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escribir_clasificacion(filas: list[dict], path: Path | str) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_COLUMNAS)
        writer.writeheader()
        writer.writerows(filas)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--elecciones-dir", default=ELECCIONES_DIR)
    ap.add_argument("--clasificacion-path", default=CLASIFICACION_IDEOLOGICA_PATH)
    ap.add_argument("--anio-max", type=int, default=2009, help="último año a incorporar (inclusive)")
    args = ap.parse_args()

    existentes = leer_clasificacion_existente(args.clasificacion_path)
    nuevas = extraer_clasificacion_historica(args.elecciones_dir, args.anio_max)
    combinado = fusionar_clasificacion(existentes, nuevas)
    agregadas = len(combinado) - len(existentes)
    escribir_clasificacion(combinado, args.clasificacion_path)
    print(
        f"OK: {agregadas} filas nuevas (año <= {args.anio_max}) agregadas a "
        f"{args.clasificacion_path} -- total {len(combinado)}"
    )


if __name__ == "__main__":
    main()
