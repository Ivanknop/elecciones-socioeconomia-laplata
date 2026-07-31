"""Serie temporal por campo ideológico, un gráfico por localidad y nivel de
gobierno (2011-2025), a partir de los cuadros ya agregados en
`graficos/cuadros_por_localidad/*.csv` (ver `analisis.cuadros_por_localidad`
-- este script no vuelve a leer `circuito_<nivel>.json` ni el crosswalk
directamente, así que hay que correr `cuadros_por_localidad` primero).

Reusa la fusión ejecutivo+legislativo de `analisis.serie_temporal.NIVELES`
(nacional=presidente+diputados nac., provincial=gobernador+diputados prov.,
municipal=intendente+concejales) para que los puntos de cada serie sean
comparables a los de `graficos/serie_temporal/`.

Cada localidad incluye siempre `SIN_DETERMINAR` como una serie más -- son
votos reales de circuitos sin localidad asignada ese año, nunca se ocultan
(ver `data/fuentes_extras/LOCALIDADES_README.md`). La confiabilidad de la
clasificación de cada localidad está en
`data/fuentes_extras/AUDITORIA_DISCREPANCIAS.md`.

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

from analisis.graficos import IDEOLOGIAS, _COLOR_IDEOLOGIA
from analisis.serie_temporal import CARGO_LABEL, NIVELES, _puntos_del_nivel

CUADROS_DIR = "cuadros_por_localidad"


def _ruta_cuadro(graficos_dir: Path | str, anio: int, cargo: str) -> Path:
    return Path(graficos_dir) / CUADROS_DIR / f"{anio}_{cargo}_generales_localidad.csv"


def _cargar_cuadro(graficos_dir: Path | str, anio: int, cargo: str) -> pd.DataFrame:
    return pd.read_csv(_ruta_cuadro(graficos_dir, anio, cargo), comment="#")


def _puntos_con_cuadro(data_dir: Path | str, graficos_dir: Path | str, nivel: str) -> list[tuple[int, str]]:
    """Igual que `_puntos_del_nivel`, pero solo los (año, cargo) para los que
    ya existe el cuadro por localidad (no todo lo que tiene `circuito_<nivel>.json`
    tiene necesariamente su cuadro generado)."""
    return [
        (anio, cargo)
        for anio, cargo in _puntos_del_nivel(data_dir, nivel)
        if _ruta_cuadro(graficos_dir, anio, cargo).exists()
    ]


def _localidades_en_puntos(graficos_dir: Path | str, puntos: list[tuple[int, str]]) -> list[str]:
    localidades: set[str] = set()
    for anio, cargo in puntos:
        localidades.update(_cargar_cuadro(graficos_dir, anio, cargo)["localidad"])
    return sorted(localidades)


def _serie_localidad(graficos_dir: Path | str, puntos: list[tuple[int, str]], localidad: str):
    """Devuelve ({ideologia: [votos por punto]}, [total_positivos por punto])."""
    serie = {ideologia: [] for ideologia in IDEOLOGIAS.values()}
    totales = []
    for anio, cargo in puntos:
        df = _cargar_cuadro(graficos_dir, anio, cargo)
        fila = df[df["localidad"] == localidad]
        valores = {
            ideologia: (fila[ideologia].iloc[0] if not fila.empty else 0)
            for ideologia in IDEOLOGIAS.values()
        }
        totales.append(sum(valores.values()))
        for ideologia in IDEOLOGIAS.values():
            serie[ideologia].append(valores[ideologia])
    return serie, totales


def graficar_serie_localidad(
    data_dir: Path | str, graficos_dir: Path | str, nivel: str, localidad: str,
    en_porcentaje: bool = False, ax=None,
):
    puntos = _puntos_con_cuadro(data_dir, graficos_dir, nivel)
    if not puntos:
        raise FileNotFoundError(f"no hay cuadros por localidad generados para el nivel {nivel!r}")

    serie, totales = _serie_localidad(graficos_dir, puntos, localidad)
    anios = [a for a, _ in puntos]
    etiquetas_x = [f"{a}\n{CARGO_LABEL[cargo]}" for a, cargo in puntos]

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))

    for ideologia in IDEOLOGIAS.values():
        valores = serie[ideologia]
        if en_porcentaje:
            valores = [v / t * 100 if t else 0 for v, t in zip(valores, totales)]
        ax.plot(anios, valores, marker="o", label=ideologia, color=_COLOR_IDEOLOGIA[ideologia])

    ax.set_xticks(anios, labels=etiquetas_x, fontsize="small")
    ax.set_ylabel("% de los positivos" if en_porcentaje else "votos")
    metrica = "% por campo ideológico" if en_porcentaje else "votos por campo ideológico"
    ax.set_title(f"La Plata — {localidad} — {nivel} — {metrica}, {anios[0]}-{anios[-1]}")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize="small", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def generar_serie_localidad(data_dir: Path | str, graficos_dir: Path | str, nivel: str, localidad: str) -> Path:
    salida = Path(graficos_dir) / CUADROS_DIR / "imagenes"
    salida.mkdir(parents=True, exist_ok=True)

    fig = graficar_serie_localidad(data_dir, graficos_dir, nivel, localidad, en_porcentaje=False)
    fig.savefig(salida / f"{localidad}_{nivel}_votos.png", dpi=100)
    plt.close(fig)

    fig = graficar_serie_localidad(data_dir, graficos_dir, nivel, localidad, en_porcentaje=True)
    fig.savefig(salida / f"{localidad}_{nivel}_porcentaje.png", dpi=100)
    plt.close(fig)

    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nivel", choices=list(NIVELES), help="si se omite, corre los 3 niveles")
    parser.add_argument("--localidad", help="si se omite, corre todas las localidades disponibles para ese nivel")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--graficos-dir", default="graficos")
    args = parser.parse_args()

    niveles = [args.nivel] if args.nivel else list(NIVELES)
    total_imagenes = 0
    for nivel in niveles:
        puntos = _puntos_con_cuadro(args.data_dir, args.graficos_dir, nivel)
        if not puntos:
            print(f"{nivel}: sin cuadros por localidad generados, se omite (correr antes analisis.cuadros_por_localidad)")
            continue

        localidades = [args.localidad] if args.localidad else _localidades_en_puntos(args.graficos_dir, puntos)
        for localidad in localidades:
            salida = generar_serie_localidad(args.data_dir, args.graficos_dir, nivel, localidad)
            total_imagenes += 2

        anios = [a for a, _ in puntos]
        print(f"{nivel}: {len(localidades)} localidades, {anios[0]}-{anios[-1]} -> {salida}")

    print(f"{total_imagenes} imágenes generadas")


if __name__ == "__main__":
    main()
