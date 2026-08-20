"""Agrupa resultados electorales por circuito en localidades de La Plata.
`agrupar_resultados_por_localidad` es agnóstica de la fuente: recibe un
`circuito_id -> localidad` ya resuelto y suma. Dos formas de construir ese
mapa, según la fuente:

- `cargar_circuito_localidad_geo` + `data/geolocalizacion/circuitos_por_localidad.csv`
  -- **la fuente por defecto** desde la reconstrucción del flujo por
  localidad (ver skill `laplata-geolocalizacion`,
  `data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md`): crosswalk derivado por
  nearest-neighbor contra el catálogo geolocalizado del Ministerio de Obras
  Públicas + Georef-AR (36 localidades), sin niveles de cobertura -- cubre
  los 68 circuitos de `circuitos_electorales_la_plata.geojson` con una fila
  cada uno. Cualquier `circuito_id` de un año electoral que no esté en esos
  68 (ej. `504C`, visto en legislativas 2017/2021 pero fuera del recorte
  geojson vigente) cae en `SIN_DETERMINAR`, igual que con el crosswalk
  anterior.
- `cargar_crosswalk` + `mapa_localidad_por_circuito` + `data/geolocalizacion/fuentes_extra/circuito_localidad.csv`
  -- el crosswalk histórico por nombre de barrio (Resolución 1990/2007 +
  relevamiento periodístico, diseño y estado en
  `data/geolocalizacion/fuentes_extra/CIRCUITOS_LOCALIDADES.md`; auditoría de confiabilidad
  en `data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`), con tres niveles de
  cobertura que nunca se mezclan sin pedirlo explícitamente vía
  `niveles_cobertura`:

  - `NIVEL_OFICIAL` ("oficial_confirmada"): Resolución 1990/2007. La
    mayoría de estos circuitos tiene una única localidad dominante, pero no
    es requisito -- alcanza con que la localidad figure textualmente en la
    tabla oficial del circuito (ver decisión de interpretación #4 en
    `AUDITORIA_DISCREPANCIAS.md`, sobre 503 y 503A -> MELCHOR_ROMERO).
  - `NIVEL_REVISION_WEB` ("revision_web"): relevamiento de El Día revisado
    contra fuentes adicionales en la web, más confiable que el periodístico
    crudo pero sin el respaldo administrativo de la Resolución 1990/2007.
  - `NIVEL_PERIODISTICO` ("periodistico_no_oficial"): relevamiento de El
    Día sin esa revisión adicional, no administrativo.

  Cuando se piden varios, la precedencia es siempre
  `NIVEL_OFICIAL` > `NIVEL_REVISION_WEB` > `NIVEL_PERIODISTICO`, se pidan
  los tres o solo algunos, para cualquier circuito que tenga fila en más de
  uno. Un cuarto nivel, `NIVEL_NO_AGRUPABLE` ("oficial_no_agrupable"), saca
  al circuito del mapa aunque tenga fila periodística.

  Este crosswalk sigue siendo la fuente para análisis que específicamente
  quieran nombre de barrio en vez de localidad oficial del Ministerio, o
  para reproducir resultados previos a la reconstrucción -- no se borró ni
  se dejó de mantener, solo dejó de ser el default de
  `analisis.cuadros_por_localidad`.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

NIVEL_OFICIAL = "oficial_confirmada"
NIVEL_REVISION_WEB = "revision_web"
NIVEL_PERIODISTICO = "periodistico_no_oficial"
NIVEL_NO_AGRUPABLE = "oficial_no_agrupable"

SIN_DETERMINAR = "SIN_DETERMINAR"


@dataclass(frozen=True)
class FilaCrosswalk:
    circuito_id: str
    localidad: str
    fuente: str
    cobertura: str


def cargar_crosswalk(path: Path | str) -> list[FilaCrosswalk]:
    with Path(path).open(encoding="utf-8") as f:
        return [
            FilaCrosswalk(
                circuito_id=raw["circuito_id"],
                localidad=raw["localidad"],
                fuente=raw["fuente"],
                cobertura=raw["cobertura"],
            )
            for raw in csv.DictReader(f)
        ]


def cargar_circuito_localidad_geo(path: Path | str) -> dict[str, str]:
    """`circuito_id -> localidad` desde el crosswalk geolocalizado
    (`data/geolocalizacion/circuitos_por_localidad.csv`, columnas
    `circuito;localidad;distancia_metros`, separador `;`). A diferencia de
    `cargar_crosswalk` + `mapa_localidad_por_circuito`, no hay niveles de
    cobertura que resolver: cada circuito tiene una sola fila."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {fila["circuito"]: fila["localidad"] for fila in csv.DictReader(f, delimiter=";")}


def mapa_localidad_por_circuito(
    crosswalk: list[FilaCrosswalk],
    niveles_cobertura: tuple[str, ...] = (NIVEL_OFICIAL, NIVEL_REVISION_WEB),
) -> dict[str, str]:
    """circuito_id -> localidad, aplicando la precedencia oficial > revisión web
    > periodístico y excluyendo siempre los circuitos marcados `oficial_no_agrupable`.
    """
    mapa: dict[str, str] = {}
    for nivel in (NIVEL_PERIODISTICO, NIVEL_REVISION_WEB, NIVEL_OFICIAL):  # cada uno pisa al anterior
        if nivel not in niveles_cobertura:
            continue
        for fila in crosswalk:
            if fila.cobertura == nivel:
                mapa[fila.circuito_id] = fila.localidad

    for fila in crosswalk:
        if fila.cobertura == NIVEL_NO_AGRUPABLE:
            mapa.pop(fila.circuito_id, None)

    return mapa


def circuitos_con_discrepancia(crosswalk: list[FilaCrosswalk]) -> list[dict[str, str]]:
    """Circuitos donde `oficial_confirmada` y `periodistico_no_oficial` traen
    una etiqueta de localidad distinta (comparación literal de etiquetas, no
    contra los códigos de localidad internos de cada circuito -- para eso ver
    `data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`).
    """
    por_circuito: dict[str, dict[str, str]] = {}
    for fila in crosswalk:
        por_circuito.setdefault(fila.circuito_id, {})[fila.cobertura] = fila.localidad

    discrepancias = [
        {"circuito_id": circuito_id, NIVEL_OFICIAL: niveles[NIVEL_OFICIAL], NIVEL_PERIODISTICO: niveles[NIVEL_PERIODISTICO]}
        for circuito_id, niveles in por_circuito.items()
        if NIVEL_OFICIAL in niveles and NIVEL_PERIODISTICO in niveles and niveles[NIVEL_OFICIAL] != niveles[NIVEL_PERIODISTICO]
    ]
    return sorted(discrepancias, key=lambda d: d["circuito_id"])


@dataclass(frozen=True)
class ReporteCobertura:
    circuitos_totales: int
    circuitos_agrupados: int
    circuitos_sin_determinar: tuple[str, ...]
    votos_totales: float
    votos_agrupados: float
    fuente: str

    @property
    def porcentaje_circuitos(self) -> float:
        return self.circuitos_agrupados / self.circuitos_totales * 100 if self.circuitos_totales else 0.0

    @property
    def porcentaje_votos(self) -> float:
        return self.votos_agrupados / self.votos_totales * 100 if self.votos_totales else 0.0

    def __str__(self) -> str:
        sin_determinar = ", ".join(self.circuitos_sin_determinar) or "(ninguno)"
        return (
            f"cobertura: {self.circuitos_agrupados}/{self.circuitos_totales} circuitos "
            f"({self.porcentaje_circuitos:.1f}%), {self.votos_agrupados:,.0f}/{self.votos_totales:,.0f} votos "
            f"({self.porcentaje_votos:.1f}%) -- fuente: {self.fuente}. "
            f"Sin determinar: {sin_determinar}"
        )


def agrupar_resultados_por_localidad(
    resultados_por_circuito: Mapping[str, Mapping[str, float] | float],
    mapa_circuito_localidad: Mapping[str, str],
    columna_total: str = "votos",
    fuente: str = "",
) -> tuple[pd.DataFrame, ReporteCobertura]:
    """Agrupa `resultados_por_circuito` (circuito_id -> valor, o circuito_id ->
    {columna: valor}) por localidad usando el mapa `circuito_id -> localidad`
    ya resuelto -- agnóstica de dónde salió ese mapa (`cargar_circuito_localidad_geo`
    o `mapa_localidad_por_circuito`). Nunca descarta un circuito: el que no
    tiene localidad asignada cae en la fila `SIN_DETERMINAR`. `fuente` es una
    etiqueta libre para `ReporteCobertura` (ej. la ruta del crosswalk usado),
    no afecta la agrupación.
    """
    filas = []
    sin_determinar = []
    votos_totales = 0.0
    votos_agrupados = 0.0

    for circuito_id, valores in resultados_por_circuito.items():
        if not isinstance(valores, Mapping):
            valores = {columna_total: valores}
        localidad = mapa_circuito_localidad.get(circuito_id, SIN_DETERMINAR)
        if localidad == SIN_DETERMINAR:
            sin_determinar.append(circuito_id)

        total_circuito = valores.get(columna_total, 0)
        votos_totales += total_circuito
        if localidad != SIN_DETERMINAR:
            votos_agrupados += total_circuito

        filas.append({"localidad": localidad, "circuito_id": circuito_id, **valores})

    df = pd.DataFrame(filas)
    columnas_valor = [c for c in df.columns if c not in ("localidad", "circuito_id")]

    agrupado = df.groupby("localidad", as_index=False)[columnas_valor].sum()
    agrupado["circuitos"] = agrupado["localidad"].map(df.groupby("localidad")["circuito_id"].count())

    if SIN_DETERMINAR not in agrupado["localidad"].values:
        fila_vacia = {"localidad": SIN_DETERMINAR, "circuitos": 0, **{c: 0 for c in columnas_valor}}
        agrupado = pd.concat([agrupado, pd.DataFrame([fila_vacia])], ignore_index=True)

    agrupado = agrupado.sort_values("localidad").reset_index(drop=True)

    reporte = ReporteCobertura(
        circuitos_totales=len(resultados_por_circuito),
        circuitos_agrupados=len(resultados_por_circuito) - len(sin_determinar),
        circuitos_sin_determinar=tuple(sorted(sin_determinar)),
        votos_totales=votos_totales,
        votos_agrupados=votos_agrupados,
        fuente=fuente,
    )
    return agrupado, reporte
