"""`panel_k` (D32): ventana de K trimestres antes de una elección E, sobre
`panel_trimestral_<nivel>.csv` (D13) -- una sola pieza atómica en dos modos.
"nivel": una sola ventana `W_t` (K trimestres antes de E), sin necesitar la
elección anterior -- encuadre de voto retrospectivo de "memoria corta".
"delta": `W_t` y `W_{t-1}` (K trimestres antes de la elección anterior),
restadas -- el panel_k originalmente especificado en D32, retrospectivo
sobre cambio económico interelectoral. Ambos modos comparten el mismo
motor de agregación por ventana (`_ventana_k`); no depende de
`panel_ventanas.csv` en absoluto, así que resuelve de raíz el descarte de
filas completas por un solo `NaN` interventana que sufre `cargar_panel`
(ver `docs/especificaciones/especificacion_empalme_ipc.md` §5 para el
contexto de origen).

Exploratorio (etapa de barrido de K, `notebooks/ml/exploratorio_panel_k/`)
-- este módulo en sí vive en la ubicación normal de código porque no
ensucia nada: no lo importa ningún notebook ya promovido.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from constantes import PANEL_TRIMESTRAL_DIR, REGISTRO_VARIABLES_PATH
from ml_models.cargar_panel import COLUMNAS_OUTCOME_ELECTORAL
from ml_models.cargar_series_economicas import FilaRegistroVariable, cargar_registro
from ml_models.features_ventana import _nivel, _pendiente, _volatilidad
from ml_models.targets_frontera import calcular_targets

NIVELES_VALIDOS = ("municipal", "provincial", "nacional")
MODOS_VALIDOS = ("nivel", "delta")
POLITICAS_TRUNCADO = ("truncar", "descartar")
UNIVERSOS_VALIDOS = ("completo", "sin_eph")

# Mismos 6 prefijos que `PREFIJOS_EPH` en `04_lasso_eph_local.ipynb` -- precedente
# directo para excluir el universo EPH por prefijo en vez de por columna exacta
# (cubre automáticamente cualquier sufijo `_kt`/`_kt1`/`_kd`/`_final_kt`/etc. de
# cada una de las 6 variables, sin listarlos uno por uno).
PREFIJOS_EPH = (
    "tasa_informalidad", "pct_sin_cobertura_salud", "hacinamiento_medio",
    "pct_hogares_ayuda_social_gobierno", "pct_hogares_prestamo_bancario",
    "pct_hogares_vendio_pertenencias",
)

# Metadata propia de panel_k -- deliberadamente NO se extiende
# cargar_panel.COLUMNAS_METADATA_PANEL: esa constante está atada al esquema
# de panel_ventanas.csv (fecha_inicio_vc, anio_t_menos_2, etc.), ninguna de
# las cuales existe acá. COLUMNAS_OUTCOME_ELECTORAL sí se reutiliza tal cual
# (mismos nombres de target, vía targets_frontera).
COLUMNAS_METADATA_PANEL_K = (
    "id_transicion", "nivel", "anio_t", "anio_t_menos_1", "k", "modo", "politica_truncado",
    "k_efectivo_t", "meses_efectivos_t", "ventana_truncada_t",
    "k_efectivo_t_menos_1", "meses_efectivos_t_menos_1", "ventana_truncada_t_menos_1",
    "ventana_truncada",
)


def _acum_compuesto(valores: list[float]) -> float | None:
    """Composición multiplicativa de tasas % trimestrales ya encadenadas
    (`_variacion_flujo_trimestre`, D13) -- no es `features_ventana._acum`
    (esa opera sobre niveles mensuales crudos, no sobre tasas ya
    diferenciadas). `None` si `valores` está vacío."""
    if not valores:
        return None
    producto = 1.0
    for v in valores:
        producto *= 1 + v / 100
    return (producto - 1) * 100


def _ventana_k(
    quarters: list[tuple[float | None, int]],
    k: int,
    es_flujo: bool,
    reducido: bool,
    n_final: int = 2,
) -> dict[str, float | int | bool | None]:
    """Agrega los últimos `k` trimestres (`quarters[-k:]`, o menos si la
    transición no tiene tantos) de UNA variable en UNA ventana. `quarters`
    ya viene recortado a las filas `tipo_fila=='trimestre'` de una
    transición, como `(valor, n_meses)`, ordenadas por `orden` ascendente.
    Reutiliza `_nivel`/`_pendiente`/`_volatilidad` de `features_ventana.py`
    -- mismo patrón que `_agregar_variable` en
    `construir_panel_lasso_bieleccion.py`, extendido con `acum` (solo
    `es_flujo`), `cobertura_parcial` y metadata de la ventana.
    `reducido=True` (D26, `paquete_atributos`) -> únicamente `nivel` en el
    resultado, igual que `calcular_features_ventana_variable` con `_vc`.
    `final` se omite (`None`) si `k_efectivo<=2` (D25: sería idéntico a
    `nivel`)."""
    ultimos = quarters[-k:] if k > 0 else []
    valores = [v for v, _ in ultimos if v is not None]
    k_efectivo = len(ultimos)

    resultado: dict[str, float | int | bool | None] = {
        "nivel": _nivel(valores),
        "k_efectivo": k_efectivo,
        "meses_efectivos": sum(n for _, n in ultimos),
        "ventana_truncada": k_efectivo < k,
        "cobertura_parcial": (not valores) or (len(valores) < len(ultimos)),
    }
    if reducido:
        return resultado

    resultado["pendiente"] = _pendiente(valores)
    resultado["volatilidad"] = _volatilidad(valores)
    resultado["final"] = _nivel(valores[-n_final:]) if k_efectivo > n_final else None
    if es_flujo:
        resultado["acum"] = _acum_compuesto(valores)
    return resultado


def _quarters_de_variable(trimestres: pd.DataFrame, variable: str) -> list[tuple[float | None, int]]:
    """`(valor, n_meses)` de cada fila de `trimestres` (ya filtrada a
    `tipo_fila=='trimestre'` y ordenada por `orden`) para una variable."""
    return [
        (v if pd.notna(v) else None, int(n))
        for v, n in zip(trimestres[variable], trimestres["n_meses"])
    ]


def _ventanas_por_variable(
    trimestres: pd.DataFrame, k: int, registro: list[FilaRegistroVariable]
) -> dict[str, dict[str, float | int | bool | None]]:
    return {
        var.id_variable: _ventana_k(
            _quarters_de_variable(trimestres, var.id_variable), k, var.es_flujo,
            var.paquete_atributos == "reducido",
        )
        for var in registro
        if var.id_variable in trimestres.columns
    }


def _transiciones_ordenadas_y_anterior(panel: pd.DataFrame) -> tuple[list[str], dict[str, str | None]]:
    """A partir de `panel_trimestral_<nivel>.csv` (ya de UN nivel): lista de
    `id_transicion` ordenada por `anio_t`, y diccionario id_transicion ->
    id_transicion previo del mismo nivel (`None` para la primera).
    Adyacencia (`anio_t_menos_1` de una transición == `anio_t` de la
    anterior en esta lista) verificada con datos reales en los 3 niveles,
    sin excepciones -- ni siquiera la de `(2003, nacional)` (D31) la
    rompe."""
    orden = (
        panel[panel["tipo_fila"] == "eleccion_t"][["id_transicion", "anio_t"]]
        .drop_duplicates()
        .sort_values("anio_t")["id_transicion"]
        .tolist()
    )
    anterior: dict[str, str | None] = {orden[0]: None} if orden else {}
    for id_previo, id_actual in zip(orden, orden[1:]):
        anterior[id_actual] = id_previo
    return orden, anterior


def construir_fila_k(
    id_transicion: str,
    modo: str,
    k: int,
    politica_truncado: str,
    trimestres_por_transicion: dict[str, pd.DataFrame],
    fronteras_por_transicion: dict[str, tuple[pd.Series, pd.Series]],
    transicion_anterior: dict[str, str | None],
    registro: list[FilaRegistroVariable],
) -> dict | None:
    """Una fila de panel_k para UNA transición (t-1->t) de un nivel.
    Targets (`delta_v`, participación/voto-exit, desplazamiento
    ideológico) vía `targets_frontera.calcular_targets` sobre las dos
    filas frontera de ESTA transición -- igual en los dos modos, nunca
    requiere la transición anterior. Modo "nivel": solo agrega `W_t`. Modo
    "delta": además busca `W_{t-1}` en la transición anterior -- si no
    existe (primera transición del nivel, análogo a D3 para el bloque
    largo `vl`), la fila no se puede construir, devuelve `None`.
    `politica_truncado=='descartar'` -> `None` si alguna ventana usada
    (`kt`, o `kt`+`kt1` en modo delta) resultó truncada. Cada lado (`kt`,
    `kt1`) se resuelve con su propia cobertura de forma independiente: si
    `kt1` cae en un período sin dato de una variable, esa columna puntual
    queda `None`, pero el resto de la fila (otras variables, `kt`,
    targets) no se pierde."""
    if modo not in MODOS_VALIDOS:
        raise ValueError(f"modo debe ser uno de {MODOS_VALIDOS}, no {modo!r}")
    if politica_truncado not in POLITICAS_TRUNCADO:
        raise ValueError(f"politica_truncado debe ser uno de {POLITICAS_TRUNCADO}, no {politica_truncado!r}")

    frontera_t_menos_1, frontera_t = fronteras_por_transicion[id_transicion]
    targets = calcular_targets(frontera_t, frontera_t_menos_1)

    trimestres_t = trimestres_por_transicion[id_transicion]
    ventanas_t = _ventanas_por_variable(trimestres_t, k, registro)

    ventanas_t_menos_1: dict[str, dict] | None = None
    if modo == "delta":
        id_anterior = transicion_anterior.get(id_transicion)
        if id_anterior is None:
            return None
        ventanas_t_menos_1 = _ventanas_por_variable(trimestres_por_transicion[id_anterior], k, registro)

    ventana_truncada = any(v["ventana_truncada"] for v in ventanas_t.values())
    if ventanas_t_menos_1 is not None:
        ventana_truncada = ventana_truncada or any(v["ventana_truncada"] for v in ventanas_t_menos_1.values())
    if politica_truncado == "descartar" and ventana_truncada:
        return None

    fila: dict[str, float | int | bool | str | None] = {
        "id_transicion": id_transicion,
        "nivel": frontera_t["nivel"],
        "anio_t": frontera_t["anio_t"],
        "anio_t_menos_1": frontera_t["anio_t_menos_1"],
        "k": k,
        "modo": modo,
        "politica_truncado": politica_truncado,
        "delta_v": targets["delta_v"],
        "gana_oficialismo": frontera_t["gana_oficialismo"],
        "share_oficialismo": frontera_t["share_oficialismo"],
        "delta_participacion_pct": targets["delta_participacion_pct"],
        "delta_voto_exit_ausentismo_pct": targets["delta_voto_exit_ausentismo_pct"],
        "delta_voto_exit_blanco_nulo_pct": targets["delta_voto_exit_blanco_nulo_pct"],
        "delta_dispersion_economico_mu": targets["delta_dispersion_economico_mu"],
        "delta_dispersion_progresismo_mu": targets["delta_dispersion_progresismo_mu"],
        "magnitud_desplazamiento_ideologico": targets["magnitud_desplazamiento_ideologico"],
        "cuadrante_desplazamiento": targets["cuadrante_desplazamiento"],
        "dispersion_cobertura_share_min": targets["dispersion_cobertura_share_min"],
    }

    primera_ventana_t = next(iter(ventanas_t.values()), None)
    if primera_ventana_t is not None:
        fila["k_efectivo_t"] = primera_ventana_t["k_efectivo"]
        fila["meses_efectivos_t"] = primera_ventana_t["meses_efectivos"]
        fila["ventana_truncada_t"] = primera_ventana_t["ventana_truncada"]
    if ventanas_t_menos_1 is not None:
        primera_ventana_t_menos_1 = next(iter(ventanas_t_menos_1.values()), None)
        if primera_ventana_t_menos_1 is not None:
            fila["k_efectivo_t_menos_1"] = primera_ventana_t_menos_1["k_efectivo"]
            fila["meses_efectivos_t_menos_1"] = primera_ventana_t_menos_1["meses_efectivos"]
            fila["ventana_truncada_t_menos_1"] = primera_ventana_t_menos_1["ventana_truncada"]
        fila["ventana_truncada"] = ventana_truncada

    for var in registro:
        prefijo = var.id_variable
        vt = ventanas_t.get(prefijo)
        if vt is None:
            continue

        fila[f"{prefijo}_nivel_kt"] = vt["nivel"]
        if "pendiente" in vt:
            fila[f"{prefijo}_pendiente_kt"] = vt["pendiente"]
            fila[f"{prefijo}_volatilidad_kt"] = vt["volatilidad"]
            fila[f"{prefijo}_final_kt"] = vt["final"]
        if "acum" in vt:
            fila[f"{prefijo}_acum_kt"] = vt["acum"]
        cobertura = vt["cobertura_parcial"]

        if ventanas_t_menos_1 is not None:
            vt1 = ventanas_t_menos_1.get(prefijo)
            if vt1 is not None:
                fila[f"{prefijo}_nivel_kt1"] = vt1["nivel"]
                if "pendiente" in vt1:
                    fila[f"{prefijo}_pendiente_kt1"] = vt1["pendiente"]
                    fila[f"{prefijo}_volatilidad_kt1"] = vt1["volatilidad"]
                    fila[f"{prefijo}_final_kt1"] = vt1["final"]
                if "acum" in vt1:
                    fila[f"{prefijo}_acum_kt1"] = vt1["acum"]
                cobertura = cobertura or vt1["cobertura_parcial"]
                nivel_kt, nivel_kt1 = vt["nivel"], vt1["nivel"]
                fila[f"{prefijo}_nivel_kd"] = (
                    nivel_kt - nivel_kt1 if nivel_kt is not None and nivel_kt1 is not None else None
                )
            else:
                fila[f"{prefijo}_nivel_kt1"] = None
                fila[f"{prefijo}_nivel_kd"] = None

        fila[f"{prefijo}_cobertura_parcial"] = cobertura

    return fila


def construir_panel_k(
    nivel: str,
    k: int,
    modo: str,
    politica_truncado: str = "truncar",
    panel_dir: Path | str = PANEL_TRIMESTRAL_DIR,
    registro_path: Path | str = REGISTRO_VARIABLES_PATH,
) -> pd.DataFrame:
    """Arma el panel_k completo de UN nivel -- carga
    `panel_trimestral_<nivel>.csv`, arma la trayectoria trimestral y las
    filas frontera por transición, y llama `construir_fila_k` por
    transición (saltea las que devuelven `None`: primera transición del
    nivel en modo delta, o filas truncadas con `politica_truncado=='descartar'`)."""
    if nivel not in NIVELES_VALIDOS:
        raise ValueError(f"nivel debe ser uno de {NIVELES_VALIDOS}, no {nivel!r}")
    if modo not in MODOS_VALIDOS:
        raise ValueError(f"modo debe ser uno de {MODOS_VALIDOS}, no {modo!r}")
    if politica_truncado not in POLITICAS_TRUNCADO:
        raise ValueError(f"politica_truncado debe ser uno de {POLITICAS_TRUNCADO}, no {politica_truncado!r}")

    panel = pd.read_csv(Path(panel_dir) / f"panel_trimestral_{nivel}.csv")
    registro = cargar_registro(registro_path)

    trimestres_por_transicion = {
        id_transicion: grupo[grupo["tipo_fila"] == "trimestre"].sort_values("orden").reset_index(drop=True)
        for id_transicion, grupo in panel.groupby("id_transicion", sort=False)
    }
    fronteras_por_transicion = {
        id_transicion: (
            grupo[grupo["tipo_fila"] == "eleccion_t_menos_1"].iloc[0],
            grupo[grupo["tipo_fila"] == "eleccion_t"].iloc[0],
        )
        for id_transicion, grupo in panel.groupby("id_transicion", sort=False)
    }
    orden, transicion_anterior = _transiciones_ordenadas_y_anterior(panel)

    filas = []
    for id_transicion in orden:
        fila = construir_fila_k(
            id_transicion, modo, k, politica_truncado,
            trimestres_por_transicion, fronteras_por_transicion, transicion_anterior, registro,
        )
        if fila is not None:
            filas.append(fila)
    return pd.DataFrame(filas)


def columnas_candidatas_k(
    df: pd.DataFrame, universo: str = "completo", excluir_adicional: tuple[str, ...] = ()
) -> list[str]:
    """Análoga a `cargar_panel.columnas_candidatas`, contra
    `COLUMNAS_METADATA_PANEL_K` (propia de este módulo) en vez de
    `cargar_panel.COLUMNAS_METADATA_PANEL` -- reutiliza
    `cargar_panel.COLUMNAS_OUTCOME_ELECTORAL` tal cual (mismos targets).
    `universo="completo"` (default) es el comportamiento de siempre, sin
    cambios. `universo="sin_eph"` excluye además cualquier columna que
    empiece con uno de los 6 prefijos de `PREFIJOS_EPH` -- exclusión
    estática por universo, no la exclusión dinámica por cluster de
    colinealidad que se había propuesto antes y no se implementó."""
    if universo not in UNIVERSOS_VALIDOS:
        raise ValueError(f"universo debe ser uno de {UNIVERSOS_VALIDOS}, no {universo!r}")
    excluir = set(COLUMNAS_METADATA_PANEL_K) | set(COLUMNAS_OUTCOME_ELECTORAL) | set(excluir_adicional)
    columnas = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in excluir]
    if universo == "sin_eph":
        columnas = [c for c in columnas if not any(c.startswith(p) for p in PREFIJOS_EPH)]
    return columnas
