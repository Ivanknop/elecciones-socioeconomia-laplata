"""Gráfico de cuadrantes ideológicos usando V-Party (V-Dem Institute).

Ubica cada fuerza política (partido-elección, Diputados 2011-2019) en un
plano de dos ejes -- estatismo (eje X) y progresismo social (eje Y) -- con
el índice de populismo representado como tamaño del punto. Fuente:
``data/agrupaciones/v-party/v_party_argentina_2011_2019_espaniol.csv``
(sólo se usa ``v2pashname`` para las etiquetas, no la columna en español;
se lee este archivo y no ``v_party_argentina_2011_2019.csv`` porque este
último no está versionado -- ver el README de esa carpeta).

Para cada partido-elección se calcula la tupla ``(economico, progresismo,
populismo)``:

- ``economico``: ``v2pariglef`` tal cual la publica V-Party -- negativo
  indica izquierda/estatismo económico y positivo derecha/mercado.
- ``progresismo``: promedio de ``v2pawomlab``, ``v2palgbt``, ``v2paimmig``
  y ``v2parelig`` -- no es una columna nativa de V-Party, es una
  construcción propia para este proyecto. Positivo = progresista,
  negativo = conservador.
- ``populismo``: ``v2xpa_popul`` tal cual, ya acotado 0-1 por construcción,
  usado acá para el tamaño del punto en vez de un eje propio.

"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from constantes import VPARTY_PATH

RUTA_DATOS = Path(VPARTY_PATH)
RUTA_SALIDA = Path("graficos/agrupaciones/vparty_cuadrantes_economico_progresismo_populismo.png")

# Columnas fuente de V-Party usadas para construir la tupla.
COL_ECONOMICO = "v2pariglef"
COL_POPULISMO = "v2xpa_popul"
COLS_PROGRESISMO = ["v2pawomlab", "v2palgbt", "v2paimmig", "v2parelig"]

# Nombres de la tupla (economico, progresismo, populismo) ya calculada.
EJE_X = "economico"
EJE_Y = "progresismo"
TAMANO = "populismo"

# Radio del punto (en puntos^2 de área, para scatter) según populismo.
RADIO_MIN, RADIO_MAX = 60, 500

# Orden fijo, una entrada por elección presente en el dataset (2011-2019).
COLOR_POR_ANIO = {
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
    """Fusiona en un solo punto las elecciones de un mismo partido que
    estén cerca entre sí en el plano (economico, progresismo).

    Agrupa por ``col_etiqueta`` y arma componentes conexas dentro de cada
    partido: dos filas quedan en el mismo grupo si su distancia normalizada
    es menor a ``umbral`` en ambos ejes, con unión transitiva (si A está
    cerca de B y B cerca de C, las tres quedan juntas aunque A y C no lo
    estén directamente) — así una fuerza que se mueve gradualmente de
    elección en elección no queda partida en dos por un corte arbitrario.
    Cada grupo resultante promedia posición y populismo, y junta los años
    fusionados (p. ej. "FPV-PJ" 2011+2013+2015 → un punto con etiqueta
    "FPV-PJ 2011-2013-2015"). ``col_etiqueta``/``col_anio`` parametrizan el
    nombre de columna de partido/año en ``df`` -- por defecto los de V-Party
    nacional (``v2pashname``/``year``), para poder reusar esta función con
    otras fuentes (ver ``analisis.vparty_cuadrantes_local``); la salida
    siempre usa la clave fija ``etiqueta_base``, sin importar ``col_etiqueta``.
    """
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
    """Reparte offsets de etiqueta entre puntos cercanos para evitar solapado.

    Agrupa puntos a distancia menor a ``umbral`` (fracción del rango de cada
    eje) y les va asignando offsets distintos de ``_OFFSETS_CANDIDATOS`` en
    orden, en vez de repetir siempre el mismo desplazamiento fijo.
    """
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
    """Carga el CSV, calcula la tupla (estatismo, progresismo, populismo)
    por partido-elección y descarta filas sin cobertura de expertos.

    De las 35 filas partido-elección del dataset, 9 no tienen ninguna
    variable de posicionamiento (ver README de ``data/agrupaciones/v-party/``:
    umbral de cobertura de expertos no alcanzado, o alianza sin codificación
    propia) y quedan afuera del cálculo y del gráfico.
    """
    df = pd.read_csv(ruta)
    df["year"] = df["year"].astype(int)
    df = df.dropna(subset=[COL_ECONOMICO, COL_POPULISMO] + COLS_PROGRESISMO).reset_index(drop=True)

    df[EJE_X] = df[COL_ECONOMICO]
    df[EJE_Y] = df[COLS_PROGRESISMO].mean(axis=1)
    df[TAMANO] = df[COL_POPULISMO]

    return df


def obtener_tuplas(df: pd.DataFrame) -> dict[tuple[str, int], tuple[float, float, float]]:
    """Devuelve {(sigla, año): (economico, progresismo, populismo)} para
    graficar libremente cualquier par de ejes, o los tres, sin recalcular.
    """
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
    """Escala el índice de populismo (0-1) a un radio de punto entre
    RADIO_MIN y RADIO_MAX. ``v_min``/``v_max`` son opcionales para poder
    escalar puntos fusionados (que promedian populismo) contra el rango
    real de los 26 datos crudos en vez del rango, más angosto, de los
    promedios ya fusionados.
    """
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
        "Elecciones a Diputados 2011-2019 (V-Party, V-Dem Institute)"
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    df = cargar_posiciones()
    ruta = graficar_cuadrantes(df)
    print(f"Gráfico guardado en {ruta} ({len(df)} de 35 fuerzas graficadas)")


if __name__ == "__main__":
    main()