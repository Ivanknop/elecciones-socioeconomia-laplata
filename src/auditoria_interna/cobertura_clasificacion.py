"""Auditoría de cobertura de `clasificacion_ideologica_agrupaciones.csv`:
total de votos sin `campo_ideologico`/`filiacion_politica`/V-Party por
(año, nivel), y qué agrupaciones conviene clasificar primero (las que
más votos desbloquean). Cruza los votos reales de
`data/tfi_data/elecciones/<año>_<nivel>.csv` (2001-2025) contra el CSV
de clasificación vigente -- no usa la clasificación embebida en esos
mismos CSV de elecciones porque puede haber quedado desactualizada
respecto del CSV maestro (`clasificacion_ideologica_agrupaciones.csv` se
edita a mano y no siempre se propaga de vuelta a `elecciones/`).

A demanda, no forma parte de ningún pipeline. Cada corrida además agrega
una línea a `cobertura_clasificacion_log.csv` (timestamp + totales
globales + variación contra la corrida anterior, sin desglose por año/
nivel/agrupación) -- ese log sí se acumula, a diferencia del reporte
Markdown que se sobreescribe.

Uso:
    PYTHONPATH=src python -m auditoria_interna.cobertura_clasificacion
    PYTHONPATH=src python -m auditoria_interna.cobertura_clasificacion --top-n 10
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from analisis.completar_clasificacion_historica import _cargo_de_archivo
from analisis.totales_por_lista import NIVEL_A_NIVEL_CSV
from constantes import (
    CLASIFICACION_IDEOLOGICA_PATH,
    COBERTURA_CLASIFICACION_LOG_PATH,
    COBERTURA_CLASIFICACION_PATH,
    ELECCIONES_DIR,
)

_NO_AGRUPACIONES = {"BLANCO", "NULO", "VOTANTES_HABILITADOS"}
_DIMENSIONES = ("campo_ideologico", "filiacion_politica", "vparty_economico")
_ETIQUETA_DIMENSION = {
    "campo_ideologico": "campo ideológico",
    "filiacion_politica": "filiación política",
    "vparty_economico": "V-Party",
}
_COLUMNAS_LOG = (
    "timestamp", "total_votos",
    "sin_campo_ideologico", "sin_filiacion_politica", "sin_vparty_economico",
    "delta_total_votos",
    "delta_sin_campo_ideologico", "delta_sin_filiacion_politica", "delta_sin_vparty_economico",
)


def leer_votos_reales(elecciones_dir: Path | str) -> list[dict]:
    """(anio, nivel, agrupacion, votos) por cada agrupación real de cada
    `<año>_<nivel>.csv` -- `nivel` normalizado igual que en
    `clasificacion_ideologica_agrupaciones.csv` (`NIVEL_A_NIVEL_CSV`,
    gobernador->gobernacion)."""
    elecciones_dir = Path(elecciones_dir)
    filas: list[dict] = []
    for path in sorted(elecciones_dir.glob("*.csv")):
        anio = int(path.stem.split("_")[0])
        cargo = _cargo_de_archivo(path)
        nivel = NIVEL_A_NIVEL_CSV.get(cargo, cargo)
        with path.open(encoding="utf-8", newline="") as f:
            f.readline()  # '# Total de votos, elección general -- ...'
            for fila in csv.DictReader(f):
                if fila["agrupacion"] in _NO_AGRUPACIONES:
                    continue
                filas.append({
                    "anio": anio,
                    "nivel": nivel,
                    "agrupacion": fila["agrupacion"],
                    "votos": int(fila["votos"]),
                })
    return filas


def leer_clasificacion(path: Path | str) -> dict[tuple[str, str, str], dict]:
    """{(anio, nivel, agrupacion): fila} desde
    `clasificacion_ideologica_agrupaciones.csv`, clave en los mismos tipos
    que produce `csv.DictReader` (todo string) para calzar directo con
    los valores crudos del CSV -- la comparación de tipos la hace
    `calcular_cobertura`."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {(f["anio"], f["nivel"], f["agrupacion"]): f for f in csv.DictReader(f)}


def calcular_cobertura(votos: list[dict], clasificacion: dict[tuple[str, str, str], dict]) -> list[dict]:
    """Una fila por (año, nivel, agrupación) con sus votos y qué
    dimensión de clasificación falta (`campo_ideologico`,
    `filiacion_politica`, `vparty_economico` como representante de las
    tres columnas V-Party)."""
    filas = []
    for v in votos:
        clave = (str(v["anio"]), v["nivel"], v["agrupacion"])
        fila_clasif = clasificacion.get(clave, {})
        faltantes = [d for d in _DIMENSIONES if not fila_clasif.get(d)]
        filas.append({**v, "faltantes": faltantes})
    return filas


def resumen_por_anio_nivel(filas: list[dict]) -> list[dict]:
    """Una fila por (año, nivel): votos totales + votos sin cada una de
    las tres dimensiones + el mismo valor como % del total de ese (año,
    nivel) -- para poder evaluar de un vistazo si un hueco es relevante
    (mismo votos absolutos pesan distinto en una elección chica que en
    una grande). Ordenado (año, nivel)."""
    agregados: dict[tuple[int, str], dict] = defaultdict(
        lambda: {"total_votos": 0, **{d: 0 for d in _DIMENSIONES}}
    )
    for f in filas:
        clave = (f["anio"], f["nivel"])
        agregados[clave]["total_votos"] += f["votos"]
        for d in f["faltantes"]:
            agregados[clave][d] += f["votos"]

    resultado = []
    for (anio, nivel), valores in agregados.items():
        total = valores["total_votos"]
        fila = {"anio": anio, "nivel": nivel, **valores}
        for d in _DIMENSIONES:
            fila[f"{d}_pct"] = (valores[d] / total * 100) if total else 0.0
        resultado.append(fila)
    resultado.sort(key=lambda r: (r["anio"], r["nivel"]))
    return resultado


def calcular_totales_globales(resumen: list[dict]) -> dict:
    """Suma `resumen_por_anio_nivel` a un único totalizador (votos
    totales + sin cada dimensión) para el log -- sin desglose por año/
    nivel, a propósito (ver docstring del módulo)."""
    totales = {"total_votos": 0, **{d: 0 for d in _DIMENSIONES}}
    for r in resumen:
        totales["total_votos"] += r["total_votos"]
        for d in _DIMENSIONES:
            totales[d] += r[d]
    return totales


def leer_ultima_entrada_log(path: Path | str) -> dict | None:
    """Última fila de `cobertura_clasificacion_log.csv`, o `None` si el
    log todavía no existe o está vacío (primera corrida)."""
    path = Path(path)
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    return filas[-1] if filas else None


def calcular_delta(actual: dict, anterior: dict | None) -> dict:
    """Variación de cada totalizador contra la corrida anterior -- 0 si
    no hay corrida anterior (primera vez que se corre el script)."""
    if anterior is None:
        return {"total_votos": 0, **{d: 0 for d in _DIMENSIONES}}
    return {
        "total_votos": actual["total_votos"] - int(anterior["total_votos"]),
        **{d: actual[d] - int(anterior[f"sin_{d}"]) for d in _DIMENSIONES},
    }


def registrar_corrida(path: Path | str, timestamp: str, totales: dict, delta: dict) -> None:
    """Agrega una línea a `cobertura_clasificacion_log.csv` -- append-only,
    crea el archivo con encabezado si es la primera corrida."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fila = {
        "timestamp": timestamp,
        "total_votos": totales["total_votos"],
        **{f"sin_{d}": totales[d] for d in _DIMENSIONES},
        "delta_total_votos": delta["total_votos"],
        **{f"delta_sin_{d}": delta[d] for d in _DIMENSIONES},
    }
    escribir_encabezado = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_COLUMNAS_LOG)
        if escribir_encabezado:
            writer.writeheader()
        writer.writerow(fila)


def top_n_partidos_a_clasificar(filas: list[dict], n: int = 5) -> list[dict]:
    """Agrupaciones ordenadas por votos totales afectados por al menos
    una dimensión de clasificación faltante (suma sobre todas sus
    apariciones año/nivel) -- las que más votos desbloquearían si se
    clasificaran. `anios` trae los años (ordenados, sin repetir) en los
    que esa agrupación aparece con algo faltante, para saber en qué fila
    de `clasificacion_ideologica_agrupaciones.csv` completar."""
    agregados: dict[str, dict] = defaultdict(
        lambda: {"votos_sin_clasificar": 0, "apariciones_sin_clasificar": 0, "faltantes": set(), "anios": set()}
    )
    for f in filas:
        if not f["faltantes"]:
            continue
        acc = agregados[f["agrupacion"]]
        acc["votos_sin_clasificar"] += f["votos"]
        acc["apariciones_sin_clasificar"] += 1
        acc["faltantes"].update(f["faltantes"])
        acc["anios"].add(f["anio"])

    resultado = [
        {"agrupacion": agrupacion, **valores, "anios": sorted(valores["anios"])}
        for agrupacion, valores in agregados.items()
    ]
    resultado.sort(key=lambda r: r["votos_sin_clasificar"], reverse=True)
    return resultado[:n]


def _fmt_miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _fmt_pct(v: float) -> str:
    return f"{v:.1f}%"


def _fmt_delta(n: int) -> str:
    return f"{n:+,}".replace(",", ".")


def generar_reporte_markdown(
    resumen: list[dict], top: list[dict], anio_min: int, anio_max: int,
    timestamp: str, totales: dict, delta: dict,
) -> str:
    lineas = [
        "# Cobertura de clasificación de agrupaciones",
        "",
        f"Votos reales de `data/tfi_data/elecciones/` ({anio_min}-{anio_max}) cruzados "
        "contra `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`. "
        "Generado por `PYTHONPATH=src python -m auditoria_interna.cobertura_clasificacion` -- "
        "este reporte no versiona historial, se sobreescribe en cada corrida; el historial "
        "de corridas (totales + variación, sin desglose) vive en "
        "`cobertura_clasificacion_log.csv`, que sí se acumula.",
        "",
        f"**Última corrida**: {timestamp} -- "
        f"{_fmt_miles(totales['total_votos'])} votos totales ({_fmt_delta(delta['total_votos'])} vs. corrida anterior), "
        f"{_fmt_miles(totales['campo_ideologico'])} sin campo ideológico ({_fmt_delta(delta['campo_ideologico'])}), "
        f"{_fmt_miles(totales['filiacion_politica'])} sin filiación política ({_fmt_delta(delta['filiacion_politica'])}), "
        f"{_fmt_miles(totales['vparty_economico'])} sin V-Party ({_fmt_delta(delta['vparty_economico'])}).",
        "",
        "## Votos sin clasificar por año y nivel",
        "",
        "| Año | Nivel | Votos totales | Sin campo ideológico | % | Sin filiación política | % | Sin V-Party | % |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in resumen:
        lineas.append(
            f"| {r['anio']} | {r['nivel']} | {_fmt_miles(r['total_votos'])} | "
            f"{_fmt_miles(r['campo_ideologico'])} | {_fmt_pct(r['campo_ideologico_pct'])} | "
            f"{_fmt_miles(r['filiacion_politica'])} | {_fmt_pct(r['filiacion_politica_pct'])} | "
            f"{_fmt_miles(r['vparty_economico'])} | {_fmt_pct(r['vparty_economico_pct'])} |"
        )

    lineas += [
        "",
        f"## Top {len(top)} agrupaciones a clasificar",
        "",
        "Ordenadas por votos totales afectados por al menos una clasificación "
        "faltante, sumando todas sus apariciones (año, nivel).",
        "",
        "| # | Agrupación | Votos sin clasificar | Apariciones sin clasificar | Año(s) | Falta |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(top, start=1):
        falta = ", ".join(_ETIQUETA_DIMENSION[d] for d in _DIMENSIONES if d in r["faltantes"])
        anios = ", ".join(str(a) for a in r["anios"])
        lineas.append(
            f"| {i} | {r['agrupacion']} | {_fmt_miles(r['votos_sin_clasificar'])} | "
            f"{r['apariciones_sin_clasificar']} | {anios} | {falta} |"
        )
    lineas.append("")
    return "\n".join(lineas)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--elecciones-dir", default=ELECCIONES_DIR)
    ap.add_argument("--clasificacion-path", default=CLASIFICACION_IDEOLOGICA_PATH)
    ap.add_argument("--salida", default=COBERTURA_CLASIFICACION_PATH)
    ap.add_argument("--log-path", default=COBERTURA_CLASIFICACION_LOG_PATH)
    ap.add_argument("--top-n", type=int, default=5)
    args = ap.parse_args()

    votos = leer_votos_reales(args.elecciones_dir)
    clasificacion = leer_clasificacion(args.clasificacion_path)
    filas = calcular_cobertura(votos, clasificacion)
    resumen = resumen_por_anio_nivel(filas)
    top = top_n_partidos_a_clasificar(filas, args.top_n)

    totales = calcular_totales_globales(resumen)
    anterior = leer_ultima_entrada_log(args.log_path)
    delta = calcular_delta(totales, anterior)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    registrar_corrida(args.log_path, timestamp, totales, delta)

    anios = [f["anio"] for f in filas]
    reporte = generar_reporte_markdown(resumen, top, min(anios), max(anios), timestamp, totales, delta)

    destino = Path(args.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(reporte, encoding="utf-8")
    print(f"OK: {destino} (log: {args.log_path})")


if __name__ == "__main__":
    main()
