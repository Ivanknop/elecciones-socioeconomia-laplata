"""Resultado total por agrupación (lista) más blanco+nulo, a partir de
`electoral.totales.resultado_total_por_agrupacion`. Ya no genera gráficos
propios (el bar chart por (año, nivel) se retiró de `graficos/` por no
aportar al nuevo enfoque temporal, ver CLAUDE.md); este módulo sobrevive
como capa de datos compartida por `vparty_cuadrantes_local.py`,
`comparativo_nivel.py`, `distribucion_ideologica_interactiva.py` y
`ml_models/construir_calendario.py`/`construir_elecciones.py`."""
from __future__ import annotations

from analisis.graficos import _cargar_circuito, _votos_no_ideologicos
from electoral.models import ValorAgrupacion, totalizar_agrupaciones
from electoral.totales import resultado_total_por_agrupacion

NIVEL_A_NIVEL_CSV = {"gobernador": "gobernacion"}

_COLOR_SIN_CLASIFICAR = "#9e9e9e"

_ID_BLANCO_NULO = "BLANCO_NULO"
_NOMBRE_BLANCO_NULO = "BLANCO + NULO"


def resultado_total_con_blanco_nulo(data_dir, anio: int, nivel: str) -> list[ValorAgrupacion]:
    """`resultado_total_por_agrupacion` más una entrada `BLANCO + NULO`,
    todo reordenado y con `votos_porcentaje` recalculado sobre el nuevo
    total."""
    agrupaciones = resultado_total_por_agrupacion(data_dir, anio, nivel)
    contenido = _cargar_circuito(data_dir, anio, nivel)
    blanco_nulo = _votos_no_ideologicos(contenido, circuito_id=None)["blanco_nulo"]

    entradas = [*agrupaciones, ValorAgrupacion(_ID_BLANCO_NULO, _NOMBRE_BLANCO_NULO, blanco_nulo, 0.0)]
    return totalizar_agrupaciones(entradas)
