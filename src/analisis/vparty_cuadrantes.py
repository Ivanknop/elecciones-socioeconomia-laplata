"""Cuadrantes ideológicos nacionales V-Party (económico × progresismo,
tamaño = populismo), Diputados 2001-2019. Fórmulas y fuente detalladas en
`docs/vparty_cuadrantes.md`."""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from constantes import VPARTY_PATH

RUTA_DATOS = Path(VPARTY_PATH)
# El JSON (`obtener_tuplas`) es el artefacto versionado -- contrato de datos
# para reconstruir la visualización más adelante. El PNG es conveniencia
# local, no se trackea (ver .gitignore).
RUTA_SALIDA_JSON = Path("graficos/agrupaciones/vparty_cuadrantes_economico_progresismo_populismo.json")
RUTA_SALIDA = Path("graficos/agrupaciones/vparty_cuadrantes_economico_progresismo_populismo.png")

COL_ECONOMICO = "v2pariglef"
COL_POPULISMO = "v2xpa_popul"
COLS_PROGRESISMO = ["v2pawomlab", "v2palgbt", "v2paimmig", "v2parelig"]

EJE_X = "economico"
EJE_Y = "progresismo"
TAMANO = "populismo"

# Radio del punto (en puntos^2 de área, para scatter) según populismo.
RADIO_MIN, RADIO_MAX = 60, 500

# Orden fijo, una entrada por elección presente en el dataset (2001-2019),
# paleta "deep" de seaborn (10 colores).
COLOR_POR_ANIO = {
    2001: "#937860",
    2003: "#DA8BC3",
    2005: "#8C8C8C",
    2007: "#CCB974",
    2009: "#64B5CD",
    2011: "#4C72B0",
    2013: "#DD8452",
    2015: "#55A868",
    2017: "#C44E52",
    2019: "#8172B2",
}

_OFFSETS_CANDIDATOS = [
    (8, 6, "left"),
    (-8, 6, "right"),
    (8, -16, "left"),
    (-8, -16, "right"),
    (8, 22, "left"),
    (-8, -24, "right"),
]

UMBRAL_FUSION = 0.05

COLOR_FUSIONADO = "#4d4d4d"


def _fusionar_por_cercania(
    df: pd.DataFrame, umbral: float = UMBRAL_FUSION, col_etiqueta: str = "v2pashname", col_anio: str = "year",
) -> pd.DataFrame:
    """Fusiona en un punto las elecciones cercanas de un mismo partido
    (unión transitiva); promedia posición y populismo."""
    x_rango = df[EJE_X].max() - df[EJE_X].min() or 1
    y_rango = df[EJE_Y].max() - df[EJE_Y].min() or 1

    filas = []
    for etiqueta, grupo in df.groupby(col_etiqueta, sort=False):
        grupo = grupo.reset_index(drop=True)
        n = len(grupo)
        padre = list(range(n))

        def encontrar(i: int) -> int:
            while padre[i] != i:
                padre[i] = padre[padre[i]]
                i = padre[i]
            return i

        def unir(i: int, j: int) -> None:
            ri, rj = encontrar(i), encontrar(j)
            if ri != rj:
                padre[rj] = ri

        for i in range(n):
            for j in range(i + 1, n):
                dx = abs(float(grupo.loc[i, EJE_X]) - float(grupo.loc[j, EJE_X])) / x_rango
                dy = abs(float(grupo.loc[i, EJE_Y]) - float(grupo.loc[j, EJE_Y])) / y_rango
                if dx < umbral and dy < umbral:
                    unir(i, j)

        grupo["_raiz"] = [encontrar(i) for i in range(n)]
        for _, sub in grupo.groupby("_raiz"):
            anios = sorted(int(a) for a in sub[col_anio].unique())
            filas.append({
                "etiqueta_base": etiqueta,
                "anios": anios,
                "n_fusionadas": len(sub),
                EJE_X: sub[EJE_X].mean(),
                EJE_Y: sub[EJE_Y].mean(),
                TAMANO: sub[TAMANO].mean(),
            })

    return pd.DataFrame(filas)


def _etiqueta_punto(fila: pd.Series) -> str:
    if fila["n_fusionadas"] == 1:
        return f"{fila['etiqueta_base']} '{str(fila['anios'][0])[-2:]}"
    return f"{fila['etiqueta_base']} {'-'.join(str(a) for a in fila['anios'])}"


def _asignar_offsets(df: pd.DataFrame, umbral: float = 0.05) -> list[tuple[int, int, str]]:
    """Reparte offsets de etiqueta entre puntos cercanos, para evitar solapado."""
    x_rango = df[EJE_X].max() - df[EJE_X].min() or 1
    y_rango = df[EJE_Y].max() - df[EJE_Y].min() or 1
    grupos: list[list[float]] = []  # [x_norm, y_norm, cantidad_asignada]
    offsets = []
    for _, fila in df.iterrows():
        xn, yn = fila[EJE_X] / x_rango, fila[EJE_Y] / y_rango
        grupo = next(
            (g for g in grupos if abs(g[0] - xn) < umbral and abs(g[1] - yn) < umbral),
            None,
        )
        if grupo is None:
            grupo = [xn, yn, 0]
            grupos.append(grupo)
        offsets.append(_OFFSETS_CANDIDATOS[int(grupo[2]) % len(_OFFSETS_CANDIDATOS)])
        grupo[2] += 1
    return offsets


def cargar_posiciones(ruta: Path = RUTA_DATOS) -> pd.DataFrame:
    """Carga el CSV y calcula (económico, progresismo, populismo) por
    partido-elección, descartando filas sin cobertura de expertos."""
    df = pd.read_csv(ruta)
    df["year"] = df["year"].astype(int)
    df = df.dropna(subset=[COL_ECONOMICO, COL_POPULISMO] + COLS_PROGRESISMO).reset_index(drop=True)

    df[EJE_X] = df[COL_ECONOMICO]
    df[EJE_Y] = df[COLS_PROGRESISMO].mean(axis=1)
    df[TAMANO] = df[COL_POPULISMO]

    return df


def obtener_tuplas(df: pd.DataFrame) -> dict[tuple[str, int], tuple[float, float, float]]:
    """{(sigla, año): (económico, progresismo, populismo)}, para graficar
    cualquier par de ejes sin recalcular."""
    return {
        (fila["v2pashname"], int(fila["year"])): (
            round(fila[EJE_X], 3),
            round(fila[EJE_Y], 3),
            round(fila[TAMANO], 3),
        )
        for _, fila in df.iterrows()
    }


def _radio_por_populismo(
    valores: pd.Series, v_min: float | None = None, v_max: float | None = None,
) -> pd.Series:
    """Escala populismo (0-1) a un radio de punto; `v_min`/`v_max`
    opcionales para escalar puntos ya fusionados."""
    if v_min is None:
        v_min = valores.min()
    if v_max is None:
        v_max = valores.max()
    if v_max == v_min:
        return pd.Series(RADIO_MIN, index=valores.index)
    return RADIO_MIN + (valores - v_min) / (v_max - v_min) * (RADIO_MAX - RADIO_MIN)


def graficar_cuadrantes(
    df: pd.DataFrame,
    ruta_salida: Path = RUTA_SALIDA,
    col_etiqueta: str = "v2pashname",
    col_anio: str = "year",
    color_por_anio: dict[int, str] | None = None,
    titulo: str = (
        "Fuerzas políticas argentinas: económico × progresismo social (tamaño = populismo)\n"
        "Elecciones a Diputados 2001-2019 (V-Party, V-Dem Institute)"
    ),
    xlabel: str = "Izquierda / Estatismo ← Regulación económica (v2pariglef) → Derecha / Mercado",
    ylabel: str = "Conservador ← Índice de progresismo social → Progresista",
) -> Path:
    color_por_anio = color_por_anio or COLOR_POR_ANIO
    fig, ax = plt.subplots(figsize=(13, 10))

    combinado = _fusionar_por_cercania(df, col_etiqueta=col_etiqueta, col_anio=col_anio)
    combinado["etiqueta"] = combinado.apply(_etiqueta_punto, axis=1)

    v_min, v_max = df[TAMANO].min(), df[TAMANO].max()
    combinado["radio"] = _radio_por_populismo(combinado[TAMANO], v_min, v_max)

    offsets_por_fila = dict(zip(combinado.index, _asignar_offsets(combinado)))

    singulares = combinado[combinado["n_fusionadas"] == 1]
    fusionadas = combinado[combinado["n_fusionadas"] > 1]

    for anio, grupo in singulares.groupby(singulares["anios"].map(lambda a: a[0])):
        color = color_por_anio.get(int(anio), "#888888")
        ax.scatter(
            grupo[EJE_X], grupo[EJE_Y],
            s=grupo["radio"], color=color, edgecolor="white", linewidth=0.8,
            alpha=0.85, zorder=3, label=str(int(anio)),
        )

    if not fusionadas.empty:
        ax.scatter(
            fusionadas[EJE_X], fusionadas[EJE_Y],
            s=fusionadas["radio"], color=COLOR_FUSIONADO, edgecolor="white",
            linewidth=1.2, alpha=0.9, zorder=4, label="2+ elecciones\n(posición promedio)",
        )

    for idx, fila in combinado.iterrows():
        dx, dy, ha = offsets_por_fila[idx]
        ax.annotate(
            fila["etiqueta"],
            (fila[EJE_X], fila[EJE_Y]),
            xytext=(dx, dy), textcoords="offset points", ha=ha,
            fontsize=8, color="#333333",
        )

    # x=0: centro por construcción de v2pariglef (escala continua centrada
    # en 0; negativo=izquierda/estatismo, positivo=derecha/mercado).
    # y=0: centro por construcción del promedio de las 4 variables sociales
    # (cada una es una escala continua centrada en 0).
    ax.axvline(0, color="#999999", linewidth=1, linestyle="--", zorder=1)
    ax.axhline(0, color="#999999", linewidth=1, linestyle="--", zorder=1)

    x_min, x_max = df[EJE_X].min() - 0.6, df[EJE_X].max() + 0.6
    y_min, y_max = df[EJE_Y].min() - 0.4, df[EJE_Y].max() + 0.4
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

    leyenda_anios = ax.legend(
        title="Elección\n(color)", loc="center left", bbox_to_anchor=(1.01, 0.68), frameon=False,
    )
    ax.add_artist(leyenda_anios)

    v_min, v_max = df[TAMANO].min(), df[TAMANO].max()
    valores_ref = [v_min, (v_min + v_max) / 2, v_max]
    radios_ref = _radio_por_populismo(pd.Series(valores_ref))
    puntos_ref = [
        plt.scatter([], [], s=r, color="#888888", alpha=0.85, edgecolor="white", linewidth=0.8)
        for r in radios_ref
    ]
    ax.legend(
        puntos_ref, [f"{v:.2f}" for v in valores_ref],
        title="Populismo\n(v2xpa_popul)", loc="center left", bbox_to_anchor=(1.01, 0.25),
        frameon=False, labelspacing=1.5,
    )

    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5, zorder=0)

    fig.tight_layout()
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def _tuplas_a_registros(tuplas: dict[tuple[str, int], tuple[float, float, float]]) -> list[dict]:
    """`obtener_tuplas()` a lista de registros serializable en JSON (las
    claves tupla (sigla, año) no son válidas como clave JSON)."""
    return [
        {"sigla": sigla, "anio": anio, EJE_X: econ, EJE_Y: prog, TAMANO: pop}
        for (sigla, anio), (econ, prog, pop) in tuplas.items()
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    total = len(pd.read_csv(RUTA_DATOS))
    df = cargar_posiciones()

    RUTA_SALIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    RUTA_SALIDA_JSON.write_text(
        json.dumps(_tuplas_a_registros(obtener_tuplas(df)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    ruta = graficar_cuadrantes(df)
    print(f"Gráfico guardado en {ruta} ({len(df)} de {total} fuerzas graficadas)")
    print(f"JSON guardado en {RUTA_SALIDA_JSON}")


if __name__ == "__main__":
    main()