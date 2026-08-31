"""Cuadrantes ideológicos V-Party (económico × progresismo, tamaño = % de
votos) por (año, nivel), leídos directo de `data/tfi_data/elecciones/`. Un
PNG por combinación en `graficos/tfi/v-party/`. No usa `vparty_cuadrantes_local`
(deprecado) salvo sus helpers de color, aún activos.

Uso:
    PYTHONPATH=src python -m analisis.vparty_distribucion_tfi
    PYTHONPATH=src python -m analisis.vparty_distribucion_tfi --anio 2023 --nivel municipal
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analisis.vparty_cuadrantes import EJE_X, EJE_Y, _asignar_offsets, _radio_por_populismo
from analisis.vparty_cuadrantes_local import _color_por_partido
from constantes import ELECCIONES_DIR

RUTA_SALIDA_DIR = Path("graficos/tfi/v-party")

_PATRON_ARCHIVO = re.compile(r"^(\d{4})_(\w+)\.csv$")


def cargar_eleccion(path: Path | str) -> pd.DataFrame:
    """Filas de un `<año>_<nivel>.csv` con cobertura V-Party, sin BLANCO/NULO."""
    df = pd.read_csv(path, skiprows=1)  # primera línea es un comentario, no el header
    df = df[~df["agrupacion"].isin(("BLANCO", "NULO"))]
    df = df.dropna(subset=["vparty_economico", "vparty_progresismo", "vparty_populismo"])
    return df.rename(columns={
        "vparty_economico": EJE_X, "vparty_progresismo": EJE_Y, "vparty_populismo": "populismo",
    }).reset_index(drop=True)


def combos_disponibles(elecciones_dir: Path | str = ELECCIONES_DIR) -> list[tuple[int, str, Path]]:
    """(año, nivel, path) por cada `<año>_<nivel>.csv` encontrado."""
    combos = []
    for path in sorted(Path(elecciones_dir).glob("*.csv")):
        m = _PATRON_ARCHIVO.match(path.name)
        if m:
            combos.append((int(m.group(1)), m.group(2), path))
    return combos


def limites_globales(dfs: list[pd.DataFrame]) -> tuple[tuple[float, float], tuple[float, float]]:
    """Límites de eje fijos y simétricos respecto de 0 sobre toda la
    cobertura cargada, para que los PNG sean comparables entre años."""
    dfs_no_vacios = [df for df in dfs if not df.empty]
    if not dfs_no_vacios:
        return (-1.0, 1.0), (-1.0, 1.0)
    todo = pd.concat(dfs_no_vacios, ignore_index=True)
    return (
        (-(todo[EJE_X].abs().max() + 0.6), todo[EJE_X].abs().max() + 0.6),
        (-(todo[EJE_Y].abs().max() + 0.4), todo[EJE_Y].abs().max() + 0.4),
    )


def graficar_cuadrantes_eleccion(
    df: pd.DataFrame,
    ruta_salida: Path,
    colores: dict[str, str],
    titulo: str,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    xlabel: str = "Izquierda / Estatismo ← posición económica → Derecha / Mercado",
    ylabel: str = "Conservador ← progresismo social → Progresista",
) -> Path:
    """Scatter económico × progresismo de una elección: color = familia
    política, tamaño = % de votos. `xlim`/`ylim` fijos, ver `limites_globales`."""
    df = df.reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(13, 10))

    df["radio"] = _radio_por_populismo(df["votos_porcentaje"])
    offsets_por_fila = dict(zip(df.index, _asignar_offsets(df)))

    for _, fila in df.iterrows():
        ax.scatter(
            fila[EJE_X], fila[EJE_Y], s=fila["radio"],
            color=colores.get(fila["agrupacion"], "#999999"),
            edgecolor="white", linewidth=0.8, alpha=0.9, zorder=3,
        )
    for idx, fila in df.iterrows():
        dx, dy, ha = offsets_por_fila[idx]
        ax.annotate(
            fila["agrupacion"], (fila[EJE_X], fila[EJE_Y]),
            xytext=(dx, dy), textcoords="offset points", ha=ha,
            fontsize=8, color="#333333",
        )

    ax.axvline(0, color="#999999", linewidth=1, linestyle="--", zorder=1)
    ax.axhline(0, color="#999999", linewidth=1, linestyle="--", zorder=1)

    x_min, x_max = xlim
    y_min, y_max = ylim
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    estilo_cuadrante = dict(fontsize=9, color="#666666", style="italic")
    ax.text(x_min + 0.1, y_max - 0.03 * (y_max - y_min), "Izquierda · Progresista", ha="left", va="top", **estilo_cuadrante)
    ax.text(x_max - 0.1, y_max - 0.03 * (y_max - y_min), "Derecha · Progresista", ha="right", va="top", **estilo_cuadrante)
    ax.text(x_min + 0.1, y_min + 0.03 * (y_max - y_min), "Izquierda · Conservador", ha="left", va="bottom", **estilo_cuadrante)
    ax.text(x_max - 0.1, y_min + 0.03 * (y_max - y_min), "Derecha · Conservador", ha="right", va="bottom", **estilo_cuadrante)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(titulo, fontsize=12)

    v_min, v_max = df["votos_porcentaje"].min(), df["votos_porcentaje"].max()
    valores_ref = sorted({v_min, (v_min + v_max) / 2, v_max})
    radios_ref = _radio_por_populismo(pd.Series(valores_ref), v_min, v_max)
    puntos_ref = [
        plt.scatter([], [], s=r, color="#888888", alpha=0.85, edgecolor="white", linewidth=0.8)
        for r in radios_ref
    ]
    ax.legend(
        puntos_ref, [f"{v:.1f}%" for v in valores_ref],
        title="% de votos", loc="center left", bbox_to_anchor=(1.01, 0.5),
        frameon=False, labelspacing=1.5,
    )

    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5, zorder=0)
    fig.tight_layout()
    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def generar_todos(
    elecciones_dir: Path | str = ELECCIONES_DIR,
    salida_dir: Path | str = RUTA_SALIDA_DIR,
    anio: int | None = None,
    nivel: str | None = None,
) -> list[Path]:
    """Un PNG por (año, nivel) disponible, filtrable por `anio`/`nivel`."""
    combos = combos_disponibles(elecciones_dir)
    if anio:
        combos = [c for c in combos if c[0] == anio]
    if nivel:
        combos = [c for c in combos if c[1] == nivel]

    dfs = {(a, n): cargar_eleccion(p) for a, n, p in combos}
    xlim, ylim = limites_globales(list(dfs.values()))

    salida_dir = Path(salida_dir)
    destinos = []
    for (a, n), df in sorted(dfs.items()):
        if df.empty:
            continue
        colores = _color_por_partido(list(df["agrupacion"]), dict(zip(df["agrupacion"], df["filiacion_politica"])))
        destino = salida_dir / f"{a}_{n}.png"
        graficar_cuadrantes_eleccion(
            df, destino, colores, xlim=xlim, ylim=ylim,
            titulo=(
                f"La Plata — {n} {a}: económico × progresismo social (tamaño = % de votos)\n"
                "color por familia política (clasificación propia calibrada contra V-Party)"
            ),
        )
        destinos.append(destino)
    return destinos


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, help="si se omite, corre todos los años disponibles")
    parser.add_argument("--nivel", help="municipal/provincial/nacional -- si se omite, corre los tres")
    parser.add_argument("--elecciones-dir", default=ELECCIONES_DIR)
    parser.add_argument("--salida-dir", default=RUTA_SALIDA_DIR)
    args = parser.parse_args()

    destinos = generar_todos(args.elecciones_dir, args.salida_dir, args.anio, args.nivel)
    if not destinos:
        print("sin datos para los filtros pedidos")
        return
    for destino in destinos:
        print(f"-> {destino}")


if __name__ == "__main__":
    main()
