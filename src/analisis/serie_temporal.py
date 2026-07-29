"""Serie temporal por campo ideológico (2011-2025), un gráfico por nivel de
gobierno.

Uso:
    python -m analisis.serie_temporal                     # los 3 niveles
    python -m analisis.serie_temporal --nivel provincial  # uno puntual
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from analisis.graficos import IDEOLOGIAS, _COLOR_IDEOLOGIA, _cargar_circuito, _votos_por_ideologia

NIVELES = {
    "nacional": ("presidente", "nacional"),
    "provincial": ("gobernador", "provincial"),
    "municipal": ("intendente", "municipal"),
}

CARGO_LABEL = {
    "presidente": "Presidente",
    "nacional": "Diputados Nac.",
    "gobernador": "Gobernador",
    "provincial": "Diputados Prov.",
    "intendente": "Intendente",
    "municipal": "Concejales",
}


def _anios_disponibles(data_dir: Path | str, nivel_especifico: str) -> list[int]:
    return sorted(
        int(p.parents[2].name)
        for p in Path(data_dir).glob(f"*/{nivel_especifico}/generales/circuito_{nivel_especifico}.json")
    )


def _puntos_del_nivel(data_dir: Path | str, nivel: str) -> list[tuple[int, str]]:
    """(año, cargo_especifico) ordenados por año, para los dos cargos que arman `nivel`."""
    ejecutivo, legislativo = NIVELES[nivel]
    puntos = [(a, ejecutivo) for a in _anios_disponibles(data_dir, ejecutivo)]
    puntos += [(a, legislativo) for a in _anios_disponibles(data_dir, legislativo)]
    puntos.sort()

    anios = [a for a, _ in puntos]
    if len(anios) != len(set(anios)):
        raise ValueError(f"año duplicado entre {ejecutivo!r} y {legislativo!r} para {nivel!r}: {puntos}")
    return puntos


def _serie_por_anio(data_dir: Path | str, nivel: str):
    """Devuelve (puntos, {ideologia: [votos por punto]}, [total por punto])
    con `puntos` = [(año, cargo_especifico), ...] ordenado."""
    puntos = _puntos_del_nivel(data_dir, nivel)
    if not puntos:
        raise FileNotFoundError(f"no hay datos para el nivel {nivel!r} en {data_dir!r}")

    serie = {ideologia: [] for ideologia in IDEOLOGIAS.values()}
    totales = []
    for anio, cargo in puntos:
        contenido = _cargar_circuito(data_dir, anio, cargo)
        votos = _votos_por_ideologia(contenido, circuito_id=None)
        totales.append(sum(votos.values()))
        for ideologia in IDEOLOGIAS.values():
            serie[ideologia].append(votos.get(ideologia, 0))
    return puntos, serie, totales


def graficar_serie_temporal(data_dir: Path | str, nivel: str, en_porcentaje: bool = False, ax=None):
    puntos, serie, totales = _serie_por_anio(data_dir, nivel)
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
    ax.set_title(f"La Plata — {nivel} — {metrica}, {anios[0]}-{anios[-1]}")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize="small", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def generar_serie_temporal(data_dir: Path | str, graficos_dir: Path | str, nivel: str) -> Path:
    salida = Path(graficos_dir) / "serie_temporal"
    salida.mkdir(parents=True, exist_ok=True)

    fig = graficar_serie_temporal(data_dir, nivel, en_porcentaje=False)
    fig.savefig(salida / f"{nivel}_votos.png", dpi=100)
    plt.close(fig)

    fig = graficar_serie_temporal(data_dir, nivel, en_porcentaje=True)
    fig.savefig(salida / f"{nivel}_porcentaje.png", dpi=100)
    plt.close(fig)

    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nivel", choices=list(NIVELES), help="si se omite, corre los 3 niveles")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--graficos-dir", default="graficos")
    args = parser.parse_args()

    niveles = [args.nivel] if args.nivel else list(NIVELES)
    for nivel in niveles:
        try:
            puntos = _puntos_del_nivel(args.data_dir, nivel)
        except Exception:
            puntos = []
        if not puntos:
            print(f"{nivel}: sin datos, se omite")
            continue
        salida = generar_serie_temporal(args.data_dir, args.graficos_dir, nivel)
        anios = [a for a, _ in puntos]
        print(f"{nivel}: {anios[0]}-{anios[-1]} ({len(puntos)} puntos: {puntos}) -> {salida}/{nivel}_{{votos,porcentaje}}.png")


if __name__ == "__main__":
    main()
