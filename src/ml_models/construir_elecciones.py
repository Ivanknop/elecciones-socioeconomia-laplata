"""Total de votos de la elección general de cada (año, nivel): agrupaciones
(con `campo_ideologico`/`filiacion_politica`/V-Party) + BLANCO/NULO +
VOTANTES_HABILITADOS (padrón, ver `_electores`), un CSV por combinación en
`data/tfi_data/elecciones/`.

**VOTANTES_HABILITADOS no es una agrupación**: `votos_porcentaje` siempre
100, no entra en el `total` que reparte el resto de los porcentajes --
cualquier consumidor de estos CSV que no la filtre explícitamente
contaría el padrón como si fuera un partido más.

Es la fuente de referencia para resultado+clasificación por (año,nivel) --
`graficos/agrupaciones/<año>/<nivel>/*.json` (generado por el ahora
deprecado `analisis.vparty_cuadrantes_local.generar_distrito`) es un
subconjunto de esto, no al revés (ver CLAUDE.md).

**Falta 2001-2009**: sin `circuito_<cargo>.json` para esos años,
`_combos_disponibles` no los ofrece -- se intentó conseguir ese detalle
sin éxito, ver `docs/adquisicion_datos_especializacion.md` §1.a. Si
aparece, alcanza con volcarlo a
`data/distrito/<año>/<cargo>/generales/circuito_<cargo>.json` y correr
este script de nuevo.

Uso:
    PYTHONPATH=src python -m ml_models.construir_elecciones
    PYTHONPATH=src python -m ml_models.construir_elecciones --anio 2023 --nivel municipal
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

from analisis.totales_por_lista import NIVEL_A_NIVEL_CSV
from constantes import CALENDARIO_ELECTORAL_PATH, CLASIFICACION_IDEOLOGICA_PATH, DATA_DISTRITO_DIR, ELECCIONES_DIR
from electoral.totales import resultado_total_por_agrupacion
from ml_models.construir_calendario import FilaCalendario, _cargar_clasificacion
from ml_models.construir_resultado_distrito import _cargo_de_eleccion, _circuito_disponible

_CLAVES_BLANCO = {"EN BLANCO", "BLANCOS"}
_CLAVES_NULO = {"NULO", "NULOS"}

_COLUMNAS_CLASIFICACION = ("campo_ideologico", "filiacion_politica", "vparty_economico", "vparty_progresismo", "vparty_populismo")


@dataclass(frozen=True)
class FilaEleccion:
    id_agrupacion: str
    agrupacion: str
    votos: int
    votos_porcentaje: float
    campo_ideologico: str
    filiacion_politica: str
    vparty_economico: str
    vparty_progresismo: str
    vparty_populismo: str


def _blanco_nulo(data_dir: Path | str, anio: int, cargo: str) -> tuple[int, int]:
    """Suma BLANCO/NULO de todos los circuitos de `circuito_<cargo>.json`
    (generales) -- mismas claves que `analisis.graficos._CLAVES_BLANCO_NULO`,
    separadas en vez de fusionadas."""
    path = Path(data_dir) / str(anio) / cargo / "generales" / f"circuito_{cargo}.json"
    contenido = json.loads(path.read_text(encoding="utf-8"))
    blanco = nulo = 0
    for circuito in contenido["circuitos"].values():
        for categoria, votos in circuito["otros"].items():
            categoria = categoria.upper()
            if categoria in _CLAVES_BLANCO:
                blanco += votos
            elif categoria in _CLAVES_NULO:
                nulo += votos
    return blanco, nulo


def _electores(data_dir: Path | str, anio: int, cargo: str) -> int:
    """Suma `electores` (padrón) de todos los circuitos de
    `circuito_<cargo>.json` -- para la fila VOTANTES_HABILITADOS, que
    `ml_models.construir_resultado_distrito` usa para `participacion` en
    vez de repetir esta suma; ningún otro script debe tratarla como una
    agrupación (sin clasificación/V-Party, `votos_porcentaje` fijo en 100)."""
    path = Path(data_dir) / str(anio) / cargo / "generales" / f"circuito_{cargo}.json"
    contenido = json.loads(path.read_text(encoding="utf-8"))
    return sum(c["electores"] for c in contenido["circuitos"].values())


def _clasificacion_de_agrupacion(
    clasificacion: dict[tuple[str, str, str], dict], anio: int, agrupacion: str, cargo: str
) -> tuple[str, str, str, str, str]:
    """(campo_ideologico, filiacion_politica, vparty_*) de `agrupacion` en
    `anio`/`cargo`; vacíos si no hay fila, join estricto. `cargo`->`nivel`
    vía `NIVEL_A_NIVEL_CSV` (gobernador->gobernacion)."""
    nivel_csv = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
    fila = clasificacion.get((str(anio), agrupacion.strip().upper(), nivel_csv))
    if fila is None:
        return ("", "", "", "", "")
    return tuple(fila.get(col, "") for col in _COLUMNAS_CLASIFICACION)


def construir_eleccion(
    data_dir: Path | str, anio: int, cargo: str, clasificacion: dict[tuple[str, str, str], dict] | None = None
) -> list[FilaEleccion]:
    """Agrupaciones + BLANCO + NULO de `cargo` en `anio`, `votos_porcentaje`
    recalculado sobre las tres. `clasificacion` completa ideología/V-Party
    por agrupación (BLANCO/NULO quedan vacíos)."""
    clasificacion = clasificacion or {}
    agrupaciones = resultado_total_por_agrupacion(data_dir, anio, cargo, etapa="generales")
    blanco, nulo = _blanco_nulo(data_dir, anio, cargo)
    total = sum(v.votos for v in agrupaciones) + blanco + nulo

    def _pct(votos: int) -> float:
        return (votos / total * 100) if total else 0.0

    filas = [
        FilaEleccion(
            v.id_agrupacion, v.nombre_agrupacion, v.votos, _pct(v.votos),
            *_clasificacion_de_agrupacion(clasificacion, anio, v.nombre_agrupacion, cargo),
        )
        for v in agrupaciones
    ]
    filas.append(FilaEleccion("BLANCO", "BLANCO", blanco, _pct(blanco), "", "", "", "", ""))
    filas.append(FilaEleccion("NULO", "NULO", nulo, _pct(nulo), "", "", "", "", ""))
    electores = _electores(data_dir, anio, cargo)
    filas.append(FilaEleccion("VOTANTES_HABILITADOS", "VOTANTES_HABILITADOS", electores, 100.0, "", "", "", "", ""))
    return filas


def _cargar_calendario(path: Path | str) -> list[FilaCalendario]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return [
            FilaCalendario(
                anio=int(r["anio"]),
                nivel=r["nivel"],
                fecha_eleccion=r["fecha_eleccion"],
                tipo_eleccion=r["tipo_eleccion"],
                desdoblada=r["desdoblada"].strip().lower() == "true",
                cargos_en_juego=r["cargos_en_juego"],
            )
            for r in csv.DictReader(f)
        ]


def _combos_disponibles(calendario: list[FilaCalendario], data_dir: Path | str) -> list[tuple[int, str, str]]:
    """(año, nivel, cargo) para los que hay `circuito_<cargo>.json`
    cacheado -- mismo filtro que `construir_voto_partido_distrito`."""
    combos = []
    for fc in calendario:
        cargo = _cargo_de_eleccion(fc.nivel, fc.tipo_eleccion)
        if _circuito_disponible(data_dir, fc.anio, cargo):
            combos.append((fc.anio, fc.nivel, cargo))
    return sorted(combos)


def generar_csv_eleccion(
    data_dir: Path | str,
    salida_dir: Path | str,
    anio: int,
    nivel: str,
    cargo: str,
    clasificacion: dict[tuple[str, str, str], dict] | None = None,
) -> Path:
    """Escribe `<salida_dir>/<anio>_<nivel>.csv` con las columnas de `FilaEleccion`."""
    filas = construir_eleccion(data_dir, anio, cargo, clasificacion)
    destino = Path(salida_dir) / f"{anio}_{nivel}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        f.write(f"# Total de votos, elección general -- La Plata, {nivel} {anio} (cargo: {cargo})\n")
        writer = csv.writer(f)
        writer.writerow([
            "id_agrupacion", "agrupacion", "votos", "votos_porcentaje",
            "campo_ideologico", "filiacion_politica", "vparty_economico", "vparty_progresismo", "vparty_populismo",
        ])
        for fila in filas:
            writer.writerow([
                fila.id_agrupacion, fila.agrupacion, fila.votos, f"{fila.votos_porcentaje:.4f}",
                fila.campo_ideologico, fila.filiacion_politica,
                fila.vparty_economico, fila.vparty_progresismo, fila.vparty_populismo,
            ])
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, help="si se omite, corre todos los años disponibles")
    parser.add_argument("--nivel", help="nacional/provincial/municipal -- si se omite, corre los tres")
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    parser.add_argument("--calendario-path", default=CALENDARIO_ELECTORAL_PATH)
    parser.add_argument("--clasificacion-path", default=CLASIFICACION_IDEOLOGICA_PATH)
    parser.add_argument("--salida-dir", default=ELECCIONES_DIR)
    args = parser.parse_args()

    calendario = _cargar_calendario(args.calendario_path)
    clasificacion = _cargar_clasificacion(args.clasificacion_path)
    combos = _combos_disponibles(calendario, args.data_dir)
    if args.anio:
        combos = [c for c in combos if c[0] == args.anio]
    if args.nivel:
        combos = [c for c in combos if c[1] == args.nivel]

    if not combos:
        print("sin datos para los filtros pedidos")
        return

    for anio, nivel, cargo in combos:
        destino = generar_csv_eleccion(args.data_dir, args.salida_dir, anio, nivel, cargo, clasificacion)
        print(f"{anio} {nivel} -> {destino}")


if __name__ == "__main__":
    main()
