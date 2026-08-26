"""Un PNG por concepto del catálogo macroeconómico, mensual + anual. No
rellena huecos -- corte visible, mismo criterio que `macroeconomia.series`.

Uso:
    PYTHONPATH=src python -m macroeconomia.graficos                        # los 22 conceptos
    PYTHONPATH=src python -m macroeconomia.graficos --concepto ipc_nacional  # uno puntual
"""
from __future__ import annotations

import argparse
import csv
import re
import textwrap
from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from constantes import (
    MACRO_CACHE_DATOS_GOB_DIR,
    MACRO_CATALOGO_SERIES_ANUALES_PATH,
    MACRO_CATALOGO_SERIES_PATH,
    MACRO_SERIES_ANUAL_PATH,
    MACRO_SERIES_MENSUAL_PATH,
)
from macroeconomia.datos_gob_client import DatosGobClient
from macroeconomia.series import ConceptoCatalogo, cargar_catalogo

COLOR = "#256abf"

# La fuente (datos.gob.ar) describe estas tres como "Porcentaje" pero el
# dato ya llega -- y se guarda en el CSV -- sin multiplicar por 100
# (0.074 = 7,4%): ver la nota de `tasa_desocupacion` en catalogo_series.csv.
# Mostrar "Porcentaje" en el eje sería engañoso con esos valores, así que
# se pisa la unidad de la fuente por la que realmente tienen los datos.
_UNIDAD_OVERRIDE = {
    "tasa_desocupacion": "fracción (0 a 1), no porcentaje -- ver nota",
    "tasa_empleo": "fracción (0 a 1), no porcentaje -- ver nota",
    "tasa_actividad": "fracción (0 a 1), no porcentaje -- ver nota",
}


def _leer_filas(path: Path | str) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _valor(fila: dict, concepto: str) -> float | None:
    crudo = fila.get(concepto, "")
    return float(crudo) if crudo not in ("", None) else None


def unidad_de(client: DatosGobClient, concepto: ConceptoCatalogo) -> str:
    """Unidad real del dato desde la metadata cacheada; si falta, degrada
    a una etiqueta explícita en vez de fallar."""
    override = _UNIDAD_OVERRIDE.get(concepto.concepto)
    if override:
        return override

    try:
        crudo = client.get_serie(concepto.id_datos_gob)
    except Exception:
        return "unidad no disponible (sin caché ni red)"

    meta = crudo.get("meta") or []
    if len(meta) < 2:
        return "unidad no informada por la fuente"

    field = meta[1].get("field", {})
    dataset = meta[1].get("dataset", {})
    unidad = field.get("units") or "unidad no informada por la fuente"
    if unidad.strip().lower() == "índice":
        base = re.search(r"[Bb]ase [^.]+", dataset.get("title", "") or "")
        if base:
            unidad = f"Índice, {base.group(0)}"
    return unidad


def _anotar_notas(ax, notas: str) -> None:
    if not notas:
        return
    ax.text(
        0.0, -0.16, textwrap.fill(notas, 100),
        transform=ax.transAxes, fontsize=7, color="#666666", va="top",
    )


def graficar_concepto_mensual(filas: list[dict], concepto: ConceptoCatalogo, unidad: str, ax=None):
    fechas = [date.fromisoformat(f["fecha"]) for f in filas]
    valores = [_valor(f, concepto.concepto) for f in filas]

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))

    ax.plot(fechas, valores, color=COLOR, linewidth=1.5, marker="o", markersize=2.5)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylabel(unidad)
    titulo = concepto.concepto.replace("_", " ")
    ax.set_title(f"{titulo} — serie mensual, {fechas[0].year}-{fechas[-1].year}\nUnidad: {unidad}", fontsize=11)
    _anotar_notas(ax, concepto.notas)
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def graficar_concepto_anual(filas: list[dict], concepto: ConceptoCatalogo, unidad: str, ax=None):
    anios = [int(f["anio"]) for f in filas]
    valores = [_valor(f, concepto.concepto) for f in filas]

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))

    ax.plot(anios, valores, marker="o", color=COLOR, linewidth=1.5)
    ax.set_xticks(anios, labels=[str(a) for a in anios], fontsize="small")
    ax.set_ylabel(unidad)
    titulo = concepto.concepto.replace("_", " ")
    ax.set_title(f"{titulo} — serie anual, {anios[0]}-{anios[-1]}\nUnidad: {unidad}", fontsize=11)
    _anotar_notas(ax, concepto.notas)
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def generar_graficos(
    graficos_dir: Path | str = "graficos/macroeconomia",
    catalogo_path: Path | str = MACRO_CATALOGO_SERIES_PATH,
    series_path: Path | str = MACRO_SERIES_MENSUAL_PATH,
    catalogo_anual_path: Path | str = MACRO_CATALOGO_SERIES_ANUALES_PATH,
    series_anual_path: Path | str = MACRO_SERIES_ANUAL_PATH,
    cache_dir: Path | str = MACRO_CACHE_DATOS_GOB_DIR,
    concepto_filtro: str | None = None,
) -> list[Path]:
    for p in (series_path, series_anual_path):
        if not Path(p).exists():
            raise FileNotFoundError(
                f"{p} no existe -- correr antes `python -m macroeconomia.series` "
                "y `python -m macroeconomia.series_anuales`"
            )

    salida = Path(graficos_dir)
    salida.mkdir(parents=True, exist_ok=True)
    generados = []
    client = DatosGobClient(cache_dir=cache_dir)

    catalogo = cargar_catalogo(catalogo_path)
    if concepto_filtro:
        catalogo = [c for c in catalogo if c.concepto == concepto_filtro]
    if catalogo:
        filas = _leer_filas(series_path)
        for concepto in catalogo:
            unidad = unidad_de(client, concepto)
            fig = graficar_concepto_mensual(filas, concepto, unidad)
            destino = salida / f"{concepto.concepto}.png"
            fig.savefig(destino, dpi=100)
            plt.close(fig)
            generados.append(destino)

    catalogo_anual = cargar_catalogo(catalogo_anual_path)
    if concepto_filtro:
        catalogo_anual = [c for c in catalogo_anual if c.concepto == concepto_filtro]
    if catalogo_anual:
        filas_anual = _leer_filas(series_anual_path)
        for concepto in catalogo_anual:
            unidad = unidad_de(client, concepto)
            fig = graficar_concepto_anual(filas_anual, concepto, unidad)
            destino = salida / f"{concepto.concepto}.png"
            fig.savefig(destino, dpi=100)
            plt.close(fig)
            generados.append(destino)

    return generados


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--concepto", help="si se omite, genera los 22 conceptos (mensuales + anuales)")
    parser.add_argument("--catalogo", default=MACRO_CATALOGO_SERIES_PATH)
    parser.add_argument("--series", default=MACRO_SERIES_MENSUAL_PATH)
    parser.add_argument("--catalogo-anual", default=MACRO_CATALOGO_SERIES_ANUALES_PATH)
    parser.add_argument("--series-anual", default=MACRO_SERIES_ANUAL_PATH)
    parser.add_argument("--graficos-dir", default="graficos/macroeconomia")
    parser.add_argument("--cache-dir", default=MACRO_CACHE_DATOS_GOB_DIR)
    args = parser.parse_args()

    generados = generar_graficos(
        graficos_dir=args.graficos_dir,
        catalogo_path=args.catalogo,
        series_path=args.series,
        catalogo_anual_path=args.catalogo_anual,
        series_anual_path=args.series_anual,
        cache_dir=args.cache_dir,
        concepto_filtro=args.concepto,
    )

    if not generados:
        print(f"sin resultados -- ¿--concepto {args.concepto!r} no existe en ningún catálogo?")
        return

    print(f"{len(generados)} gráficos en {args.graficos_dir}/:")
    for p in generados:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
