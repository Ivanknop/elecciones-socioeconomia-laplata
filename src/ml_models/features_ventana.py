"""Features intra e interventana -- Fase 4 del panel temporal de ventanas
electorales (ver `docs/especificacion_panel_temporal.md` §5). Itera
genéricamente sobre `registro_variables.csv`: agregar una variable nueva
(fila en el registro + columna en `series_economicas_mensuales.csv`) hace
que sus features aparezcan solas, sin tocar este archivo -- no hay ningún
`if id_variable == ...` acá (D9).

Ventana corta (`_vc`): [fecha_inicio_vc, fecha_fin_vc], ambos extremos
incluidos (interpretación literal de la especificación §3.4). Bloque largo
(`_vl`): [fecha_inicio_vl, fecha_fin_vc] -- solo si `fecha_inicio_vl` existe
(la primera transición de cada nivel no tiene bloque largo, D3).
"""
from __future__ import annotations

from datetime import date

from ml_models.cargar_series_economicas import FilaRegistroVariable

_POLARIDADES_VALIDAS = {"positiva", "negativa", "ambigua"}


def _parsear_fecha(fecha_iso: str) -> date:
    return date.fromisoformat(fecha_iso[:10])


def _meses_en_ventana(fecha_inicio_iso: str, fecha_fin_iso: str) -> list[date]:
    """Todos los primeros-de-mes entre las dos fechas, ambos extremos
    incluidos."""
    inicio, fin = _parsear_fecha(fecha_inicio_iso), _parsear_fecha(fecha_fin_iso)
    mes_inicio = date(inicio.year, inicio.month, 1)
    mes_fin = date(fin.year, fin.month, 1)
    meses = []
    cursor = mes_inicio
    while cursor <= mes_fin:
        meses.append(cursor)
        cursor = date(cursor.year + 1, 1, 1) if cursor.month == 12 else date(cursor.year, cursor.month + 1, 1)
    return meses


def _valores_disponibles(serie: dict[date, float | None], meses: list[date]) -> list[float]:
    return [serie[m] for m in meses if serie.get(m) is not None]


def _nivel(valores: list[float]) -> float | None:
    return sum(valores) / len(valores) if valores else None


def _pendiente(valores: list[float]) -> float | None:
    """Coeficiente de una regresión lineal simple sobre el índice temporal
    0..n-1 (OLS, sin dependencias extra); None con <2 puntos."""
    n = len(valores)
    if n < 2:
        return None
    media_x = (n - 1) / 2
    media_y = sum(valores) / n
    numerador = sum((i - media_x) * (v - media_y) for i, v in enumerate(valores))
    denominador = sum((i - media_x) ** 2 for i in range(n))
    return numerador / denominador if denominador else None


def _volatilidad(valores: list[float]) -> float | None:
    n = len(valores)
    if n < 2:
        return None
    media = sum(valores) / n
    return (sum((v - media) ** 2 for v in valores) / (n - 1)) ** 0.5


def _final(serie: dict[date, float | None], meses_ventana: list[date]) -> float | None:
    """Media de los últimos 6 meses de la ventana (los últimos 6 antes de
    la elección t, recortados a lo que efectivamente cubre esta ventana)."""
    ultimos_6 = meses_ventana[-6:]
    return _nivel(_valores_disponibles(serie, ultimos_6))


def _acum(serie: dict[date, float | None], meses_ventana: list[date]) -> float | None:
    """Variación % entre el primer y el último valor real disponible en la
    ventana -- pensado para índices tipo IPC (inflación acumulada), no para
    flujos con signo (ver nota de `resultado_fiscal` en registro_variables.csv)."""
    con_fecha = [(m, serie[m]) for m in meses_ventana if serie.get(m) is not None]
    if len(con_fecha) < 2:
        return None
    primero, ultimo = con_fecha[0][1], con_fecha[-1][1]
    if primero == 0:
        return None
    return (ultimo / primero - 1) * 100


def calcular_features_ventana_variable(
    var: FilaRegistroVariable,
    serie: dict[date, float | None],
    fecha_inicio_vc: str,
    fecha_fin_vc: str,
    fecha_inicio_vl: str | None,
) -> dict[str, float | bool | None]:
    """Features intraventana (`_nivel`/`_pendiente`/`_volatilidad`/`_final`/
    `_acum`) de una variable, para `_vc` y (si existe) `_vl`. Reglas de
    aplicabilidad del §5.4.1: `periodicidad_nativa=anual` -> solo `_nivel`;
    `es_flujo=false` -> sin `_acum`. Cobertura parcial en cualquiera de las
    dos ventanas -> `<id_variable>_cobertura_parcial=True`."""
    if var.polaridad not in _POLARIDADES_VALIDAS:
        raise ValueError(
            f"{var.id_variable!r}: polaridad {var.polaridad!r} inválida -- debe ser "
            f"'positiva'/'negativa'/'ambigua', nunca vacía (registro_variables.csv)."
        )

    resultado: dict[str, float | bool | None] = {}
    cobertura_parcial = False

    ventanas = [("vc", fecha_inicio_vc, fecha_fin_vc)]
    if fecha_inicio_vl is not None:
        ventanas.append(("vl", fecha_inicio_vl, fecha_fin_vc))

    for sufijo, inicio, fin in ventanas:
        meses = _meses_en_ventana(inicio, fin)
        valores = _valores_disponibles(serie, meses)
        if valores and len(valores) < len(meses):
            cobertura_parcial = True
        elif not valores:
            cobertura_parcial = True

        resultado[f"{var.id_variable}_nivel_{sufijo}"] = _nivel(valores)
        if var.periodicidad_nativa != "anual":
            resultado[f"{var.id_variable}_pendiente_{sufijo}"] = _pendiente(valores)
            resultado[f"{var.id_variable}_volatilidad_{sufijo}"] = _volatilidad(valores)
            resultado[f"{var.id_variable}_final_{sufijo}"] = _final(serie, meses)
            if var.es_flujo:
                resultado[f"{var.id_variable}_acum_{sufijo}"] = _acum(serie, meses)

    resultado[f"{var.id_variable}_cobertura_parcial"] = cobertura_parcial
    return resultado


def calcular_features_interventana_variable(
    var: FilaRegistroVariable,
    features_vc_actual: dict[str, float | bool | None],
    features_vc_anterior: dict[str, float | bool | None] | None,
) -> dict[str, float | bool | None]:
    """`_delta_nivel`/`_delta_pendiente`/`_mejoro` (§5.3), comparando la
    ventana corta actual contra la ventana corta de la transición anterior
    del mismo nivel. `_mejoro` se omite si `polaridad=ambigua` (§5.4).
    `None`/vacío si no hay transición anterior (primera ventana del nivel)."""
    if var.polaridad not in _POLARIDADES_VALIDAS:
        raise ValueError(f"{var.id_variable!r}: polaridad {var.polaridad!r} inválida.")

    nivel_actual = features_vc_actual.get(f"{var.id_variable}_nivel_vc")
    pendiente_actual = features_vc_actual.get(f"{var.id_variable}_pendiente_vc")

    if features_vc_anterior is None:
        nivel_anterior = pendiente_anterior = None
    else:
        nivel_anterior = features_vc_anterior.get(f"{var.id_variable}_nivel_vc")
        pendiente_anterior = features_vc_anterior.get(f"{var.id_variable}_pendiente_vc")

    resultado: dict[str, float | bool | None] = {}

    delta_nivel = (
        nivel_actual - nivel_anterior if nivel_actual is not None and nivel_anterior is not None else None
    )
    resultado[f"{var.id_variable}_delta_nivel"] = delta_nivel
    resultado[f"{var.id_variable}_delta_pendiente"] = (
        pendiente_actual - pendiente_anterior
        if pendiente_actual is not None and pendiente_anterior is not None
        else None
    )

    if var.polaridad != "ambigua":
        if delta_nivel is None:
            mejoro = None
        elif var.polaridad == "positiva":
            mejoro = delta_nivel > 0
        else:  # negativa
            mejoro = delta_nivel < 0
        resultado[f"{var.id_variable}_mejoro"] = mejoro

    return resultado
