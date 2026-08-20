"""Serie temporal por campo ideológico, un gráfico por localidad y nivel de
gobierno (2011-2025), a partir de los cuadros ya agregados en
`data/por_localidad/*.csv`.

Cada localidad incluye siempre `SIN_DETERMINAR` como una serie más -- son
votos reales de circuitos sin localidad asignada ese año, nunca se ocultan
(ver `data/geolocalizacion/fuentes_extra/CIRCUITOS_LOCALIDADES.md`). La confiabilidad de la
clasificación de cada localidad está en
`data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`.

Uso:
    python -m analisis.serie_temporal_por_localidad                          # todas las localidades, los 3 niveles
    python -m analisis.serie_temporal_por_localidad --nivel municipal
    python -m analisis.serie_temporal_por_localidad --localidad VILLA_ELVIRA
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analisis.graficos import CATEGORIAS_NO_IDEOLOGICAS, IDEOLOGIAS, color_categoria, etiqueta_categoria
from analisis.serie_temporal import CARGO_LABEL, NIVELES, _puntos_del_nivel
from constantes import DATA_DISTRITO_DIR, DATA_POR_LOCALIDAD_DIR

CATEGORIAS = list(IDEOLOGIAS.values()) + CATEGORIAS_NO_IDEOLOGICAS


def _ruta_cuadro(cuadros_dir: Path | str, anio: int, cargo: str) -> Path:
    return Path(cuadros_dir) / f"{anio}_{cargo}_generales_localidad.csv"


def _cargar_cuadro(cuadros_dir: Path | str, anio: int, cargo: str) -> pd.DataFrame:
    return pd.read_csv(_ruta_cuadro(cuadros_dir, anio, cargo), comment="#")


def _puntos_con_cuadro(data_dir: Path | str, cuadros_dir: Path | str, nivel: str) -> list[tuple[int, str]]:
    """Igual que `_puntos_del_nivel`, pero solo los (año, cargo) para los que
    ya existe el cuadro por localidad."""
    return [
        (anio, cargo)
        for anio, cargo in _puntos_del_nivel(data_dir, nivel)
        if _ruta_cuadro(cuadros_dir, anio, cargo).exists()
    ]


def _localidades_en_puntos(cuadros_dir: Path | str, puntos: list[tuple[int, str]]) -> list[str]:
    localidades: set[str] = set()
    for anio, cargo in puntos:
        localidades.update(_cargar_cuadro(cuadros_dir, anio, cargo)["localidad"])
    return sorted(localidades)


def _serie_localidad(cuadros_dir: Path | str, puntos: list[tuple[int, str]], localidad: str):
    """Devuelve ({categoria: [votos por punto]}, [total por punto]), con
    `categoria` recorriendo `CATEGORIAS` (ideologías + blanco_nulo +
    ausentismo). Cuadros viejos sin las columnas nuevas cuentan como 0 en
    vez de fallar."""
    serie = {categoria: [] for categoria in CATEGORIAS}
    totales = []
    for anio, cargo in puntos:
        df = _cargar_cuadro(cuadros_dir, anio, cargo)
        fila = df[df["localidad"] == localidad]
        valores = {
            categoria: (fila[categoria].iloc[0] if not fila.empty and categoria in df.columns else 0)
            for categoria in CATEGORIAS
        }
        totales.append(sum(valores.values()))
        for categoria in CATEGORIAS:
            serie[categoria].append(valores[categoria])
    return serie, totales


def graficar_serie_localidad(
    data_dir: Path | str, cuadros_dir: Path | str, nivel: str, localidad: str,
    en_porcentaje: bool = False, ax=None,
):
    puntos = _puntos_con_cuadro(data_dir, cuadros_dir, nivel)
    if not puntos:
        raise FileNotFoundError(f"no hay cuadros por localidad generados para el nivel {nivel!r}")

    serie, totales = _serie_localidad(cuadros_dir, puntos, localidad)
    anios = [a for a, _ in puntos]
    etiquetas_x = [f"{a}\n{CARGO_LABEL[cargo]}" for a, cargo in puntos]

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))

    for categoria in CATEGORIAS:
        valores = serie[categoria]
        if en_porcentaje:
            valores = [v / t * 100 if t else 0 for v, t in zip(valores, totales)]
        ax.plot(anios, valores, marker="o", label=etiqueta_categoria(categoria), color=color_categoria(categoria))

    ax.set_xticks(anios, labels=etiquetas_x, fontsize="small")
    ax.set_ylabel("% del padrón" if en_porcentaje else "votos / personas")
    metrica = "% del padrón" if en_porcentaje else "votos y ausentismo"
    ax.set_title(f"La Plata — {localidad} — {nivel} — {metrica}, por campo ideológico + blanco/nulo + ausentismo, {anios[0]}-{anios[-1]}")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize="small", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def generar_serie_localidad(
    data_dir: Path | str, cuadros_dir: Path | str, graficos_dir: Path | str, nivel: str, localidad: str,
) -> Path:
    salida = Path(graficos_dir)
    salida.mkdir(parents=True, exist_ok=True)

    fig = graficar_serie_localidad(data_dir, cuadros_dir, nivel, localidad, en_porcentaje=False)
    fig.savefig(salida / f"{localidad}_{nivel}_votos.png", dpi=100)
    plt.close(fig)

    fig = graficar_serie_localidad(data_dir, cuadros_dir, nivel, localidad, en_porcentaje=True)
    fig.savefig(salida / f"{localidad}_{nivel}_porcentaje.png", dpi=100)
    plt.close(fig)

    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nivel", choices=list(NIVELES), help="si se omite, corre los 3 niveles")
    parser.add_argument("--localidad", help="si se omite, corre todas las localidades disponibles para ese nivel")
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    parser.add_argument("--cuadros-dir", default=DATA_POR_LOCALIDAD_DIR)
    parser.add_argument("--graficos-dir", default="graficos/por_localidad")
    args = parser.parse_args()

    niveles = [args.nivel] if args.nivel else list(NIVELES)
    total_imagenes = 0
    for nivel in niveles:
        puntos = _puntos_con_cuadro(args.data_dir, args.cuadros_dir, nivel)
        if not puntos:
            print(f"{nivel}: sin cuadros por localidad generados, se omite (correr antes analisis.cuadros_por_localidad)")
            continue

        localidades = [args.localidad] if args.localidad else _localidades_en_puntos(args.cuadros_dir, puntos)
        for localidad in localidades:
            salida = generar_serie_localidad(args.data_dir, args.cuadros_dir, args.graficos_dir, nivel, localidad)
            total_imagenes += 2

        anios = [a for a, _ in puntos]
        print(f"{nivel}: {len(localidades)} localidades, {anios[0]}-{anios[-1]} -> {salida}")

    print(f"{total_imagenes} imágenes generadas")


if __name__ == "__main__":
    main()
