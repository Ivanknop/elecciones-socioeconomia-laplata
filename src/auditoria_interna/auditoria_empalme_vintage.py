"""Auditoría programática de huecos internos en variables derivadas de un
índice encadenado (`ipc`, `salario_real`, `resultado_fiscal`) -- D33
(`docs/especificaciones/especificacion_empalme_ipc.md`), punto 1 del
alcance de §6: por ventana × variable, marcar si la ventana tiene dato
real de ambos lados de un hueco interno (candidato a corte de vintage sin
rebasar), en vez de asumir a mano cuáles transiciones lo tienen.

No reemplaza el hallazgo ya documentado en D33 (que fue manual, sobre
`ipc`) -- lo generaliza a las 3 variables. Cubre `panel_ventanas.csv`
(ventanas `vc`/`vl`, reconstruidas desde `ventanas.csv` +
`series_economicas_mensuales.csv`, que no guarda los valores mensuales
crudos) y los dos paneles trimestrales (`panel_trimestral_<nivel>.csv`,
`panel_bieleccion_trimestral_<nivel>.csv`) -- no audita
`panel_ventanas_bieleccion.csv` por separado: es una agregación derivada
de `panel_bieleccion_trimestral_<nivel>.csv` sin ninguna ventana propia
adicional, auditar la fuente ya lo cubre. Sirve de "antes" para comparar
contra el "después" una vez reemplazada la serie de `ipc` por FACPCE.

A demanda, no forma parte de ningún pipeline.

Uso:
    PYTHONPATH=src python -m auditoria_interna.auditoria_empalme_vintage
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from constantes import (
    AUDITORIA_EMPALME_VINTAGE_PATH,
    PANEL_BIELECCION_TRIMESTRAL_DIR,
    PANEL_TRIMESTRAL_DIR,
    REGISTRO_VARIABLES_PATH,
    SERIES_ECONOMICAS_MENSUALES_PATH,
    VENTANAS_PATH,
)
from ml_models.cargar_series_economicas import cargar_registro
from ml_models.construir_calendario import NIVELES
from ml_models.construir_panel_ventanas import _cargar_series_mensuales, _cargar_ventanas
from ml_models.features_ventana import _meses_en_ventana

VARIABLES_A_AUDITAR = ("ipc", "salario_real", "resultado_fiscal")


def huecos_internos(valores_ordenados: list[tuple[date, float | None]]) -> list[tuple[date, date, int]]:
    """Tramos de fechas consecutivas sin dato real que tienen dato real
    inmediatamente antes Y después dentro de la lista -- ignora huecos en
    los bordes (antes del primer dato real o después del último, que no
    son "cruces de corte" sino simple falta de cobertura). Devuelve
    `(inicio_hueco, fin_hueco, n_periodos)` por cada tramo encontrado,
    ordenados por fecha; lista vacía si no hay ninguno."""
    con_dato = [i for i, (_, v) in enumerate(valores_ordenados) if pd.notna(v)]
    if len(con_dato) < 2:
        return []
    huecos = []
    for a, b in zip(con_dato, con_dato[1:]):
        if b - a > 1:
            huecos.append((valores_ordenados[a + 1][0], valores_ordenados[b - 1][0], b - a - 1))
    return huecos


def saltos_de_nivel(
    df: pd.DataFrame,
    variables: tuple[str, ...] = VARIABLES_A_AUDITAR,
    sufijo: str = "_nivel_vc",
    umbral_alto: float = 2.0,
    umbral_bajo: float = 0.5,
) -> pd.DataFrame:
    """D33 §6 punto 2: por nivel, ordena transiciones por `anio_t` y calcula
    `razon_abs = |valor(t)| / |valor(t-1)|` entre transiciones consecutivas
    de `{variable}{sufijo}` (`_nivel_vc` por defecto -- media de toda la
    ventana corta, la misma columna donde se encontró a mano el salto x4 de
    `salario_real_nivel_vc`, D33 §3.1). Marca una fila si `razon_abs` excede
    `umbral_alto`/cae debajo de `umbral_bajo`, o si el signo cambia entre
    transiciones consecutivas (`resultado_fiscal` puede ser superávit o
    déficit -- un cociente crudo con signos opuestos no es interpretable
    como "razón de escala", así que se marca aparte, nunca se calcula
    `razon_abs` sobre un cambio de signo). Ninguna razón económica se asume
    de antemano -- valores que excedan el umbral necesitan lectura manual
    para decidir si son un salto de vintage o una variación real."""
    filas = []
    for nivel, grupo in df.sort_values("anio_t").groupby("nivel", sort=False):
        grupo = grupo.reset_index(drop=True)
        for variable in variables:
            col = f"{variable}{sufijo}"
            if col not in grupo.columns:
                continue
            for i in range(1, len(grupo)):
                anterior, actual = grupo[col].iloc[i - 1], grupo[col].iloc[i]
                if pd.isna(anterior) or pd.isna(actual):
                    continue
                cambia_signo = (actual > 0) != (anterior > 0) and actual != 0 and anterior != 0
                razon_abs = None if anterior == 0 else abs(actual) / abs(anterior)
                marca = cambia_signo or (razon_abs is not None and (razon_abs > umbral_alto or razon_abs < umbral_bajo))
                if marca:
                    filas.append({
                        "nivel": nivel, "variable": variable, "columna": col,
                        "id_transicion_anterior": grupo["id_transicion"].iloc[i - 1],
                        "id_transicion_actual": grupo["id_transicion"].iloc[i],
                        "valor_anterior": anterior, "valor_actual": actual,
                        "razon_abs": razon_abs, "cambia_signo": cambia_signo,
                    })
    columnas = ["nivel", "variable", "columna", "id_transicion_anterior", "id_transicion_actual",
                "valor_anterior", "valor_actual", "razon_abs", "cambia_signo"]
    return pd.DataFrame(filas, columns=columnas)


def auditar_ventanas_mensuales(
    ventanas: list[dict], series: dict[str, dict[date, float | None]], variables: tuple[str, ...] = VARIABLES_A_AUDITAR
) -> pd.DataFrame:
    """Por transición x variable x ventana (`vc`, y `vl` si la transición
    tiene bloque largo): hueco(s) interno(s) real(es) dentro de esa
    ventana -- fuente: `series_economicas_mensuales.csv` recortada al
    rango de fechas de la ventana (`panel_ventanas.csv` no guarda los
    valores mensuales crudos, solo los agregados)."""
    filas = []
    for v in ventanas:
        rangos = [("vc", v["fecha_inicio_vc"], v["fecha_fin_vc"])]
        if v["fecha_inicio_vl"]:
            rangos.append(("vl", v["fecha_inicio_vl"], v["fecha_fin_vc"]))
        for sufijo, inicio, fin in rangos:
            meses = _meses_en_ventana(inicio, fin)
            for variable in variables:
                serie = series.get(variable, {})
                ordenados = [(m, serie.get(m)) for m in meses]
                for inicio_hueco, fin_hueco, n in huecos_internos(ordenados):
                    filas.append({
                        "id_transicion": v["id_transicion"], "nivel": v["nivel"], "variable": variable,
                        "ventana": sufijo, "inicio_hueco": inicio_hueco.isoformat(),
                        "fin_hueco": fin_hueco.isoformat(), "n_meses_hueco": n,
                    })
    return pd.DataFrame(filas, columns=["id_transicion", "nivel", "variable", "ventana", "inicio_hueco", "fin_hueco", "n_meses_hueco"])


def auditar_panel_trimestral(panel: pd.DataFrame, variables: tuple[str, ...] = VARIABLES_A_AUDITAR) -> pd.DataFrame:
    """Mismo criterio que `auditar_ventanas_mensuales`, sobre un panel ya
    trimestralizado (`panel_trimestral_<nivel>.csv` o
    `panel_bieleccion_trimestral_<nivel>.csv`) -- una sola "ventana" por
    transición (toda la extensión de sus filas `tipo_fila=='trimestre'`,
    ya autocontenida, no hay distinción vc/vl acá)."""
    filas = []
    for id_transicion, grupo in panel.groupby("id_transicion", sort=False):
        trimestres = grupo[grupo["tipo_fila"] == "trimestre"].sort_values("orden")
        nivel = grupo["nivel"].iloc[0]
        for variable in variables:
            if variable not in trimestres.columns:
                continue
            ordenados = list(zip(trimestres["orden"], trimestres[variable]))
            for inicio_hueco, fin_hueco, n in huecos_internos(ordenados):
                filas.append({
                    "id_transicion": id_transicion, "nivel": nivel, "variable": variable,
                    "orden_inicio_hueco": inicio_hueco, "orden_fin_hueco": fin_hueco, "n_trimestres_hueco": n,
                })
    return pd.DataFrame(filas, columns=["id_transicion", "nivel", "variable", "orden_inicio_hueco", "orden_fin_hueco", "n_trimestres_hueco"])


def _generar_reporte_markdown(resultados: dict[str, pd.DataFrame]) -> str:
    lineas = [
        "# Auditoría programática de huecos internos (D33, §6 punto 1)",
        "",
        "Generado por `auditoria_interna.auditoria_empalme_vintage` -- reporte, no se acumula "
        "(se sobreescribe en cada corrida, mismo criterio que `cobertura_clasificacion.md`).",
        "",
    ]
    for archivo, df in resultados.items():
        lineas.append(f"## `{archivo}`")
        lineas.append("")
        if df.empty:
            lineas.append("Sin huecos internos detectados.")
        else:
            lineas.append(_tabla_markdown(df))
        lineas.append("")
    return "\n".join(lineas)


def _tabla_markdown(df: pd.DataFrame) -> str:
    """Tabla Markdown a mano -- `DataFrame.to_markdown()` requiere
    `tabulate`, que no está en `requirements.txt` (no se agrega una
    dependencia solo para formatear un reporte)."""
    encabezado = "| " + " | ".join(df.columns) + " |"
    separador = "|" + "|".join("---" for _ in df.columns) + "|"
    filas = ["| " + " | ".join(str(v) for v in fila) + " |" for fila in df.itertuples(index=False)]
    return "\n".join([encabezado, separador, *filas])


def generar_reporte(
    ventanas_path: Path | str = VENTANAS_PATH,
    registro_path: Path | str = REGISTRO_VARIABLES_PATH,
    series_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
    panel_trimestral_dir: Path | str = PANEL_TRIMESTRAL_DIR,
    panel_bieleccion_trimestral_dir: Path | str = PANEL_BIELECCION_TRIMESTRAL_DIR,
    destino: Path | str = AUDITORIA_EMPALME_VINTAGE_PATH,
) -> Path:
    ventanas = _cargar_ventanas(ventanas_path)
    registro = cargar_registro(registro_path)
    series = _cargar_series_mensuales(series_path, registro)

    resultados = {
        "panel_ventanas.csv": auditar_ventanas_mensuales(ventanas, series),
    }
    for nombre, directorio, prefijo in [
        ("panel_trimestral_<nivel>.csv", panel_trimestral_dir, "panel_trimestral"),
        ("panel_bieleccion_trimestral_<nivel>.csv", panel_bieleccion_trimestral_dir, "panel_bieleccion_trimestral"),
    ]:
        partes = []
        for nivel in NIVELES:
            path = Path(directorio) / f"{prefijo}_{nivel}.csv"
            if path.exists():
                partes.append(auditar_panel_trimestral(pd.read_csv(path)))
        resultados[nombre] = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(_generar_reporte_markdown(resultados), encoding="utf-8")
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    print(generar_reporte())


if __name__ == "__main__":
    main()
