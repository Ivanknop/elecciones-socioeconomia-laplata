"""Calendario electoral 2001-2025, oficialismo por nivel y ventanas de
transición -- Fase 1 del panel temporal de ventanas electorales (ver
`docs/especificacion_panel_temporal.md` §3 y `docs/decisiones_metodologicas.md`).

Fechas de elección y datos de oficialismo 2001-2009 son investigación
propia con fuente citada por fila -- ver
`docs/adquisicion_datos_especializacion.md` §1.a para el detalle de qué se
intentó y qué queda sin verificar. 2011-2025 reusa `data/agrupaciones/oficialismos.csv`,
ya curado.

Uso:
    PYTHONPATH=src python -m ml_models.construir_calendario
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from analisis.serie_temporal import NIVELES as NIVELES_A_CARGOS
from analisis.totales_por_lista import NIVEL_A_NIVEL_CSV
from constantes import (
    CALENDARIO_ELECTORAL_PATH,
    CLASIFICACION_IDEOLOGICA_PATH,
    OFICIALISMOS_PATH,
    OFICIALISMO_POR_NIVEL_PATH,
    VENTANAS_PATH,
)

NIVELES = ("municipal", "provincial", "nacional")

# Fecha de elección por año: (fecha_nacional o None, fecha_provincial_municipal).
# Verificadas por búsqueda (Dirección Nacional Electoral / Junta Electoral PBA /
# prensa), ver docs/adquisicion_datos_especializacion.md. `nacional` solo tiene
# desagregado de La Plata desde 2011 (ver especificacion_panel_temporal.md §3.2).
_FECHAS: dict[int, tuple[str | None, str]] = {
    2001: (None, "2001-10-14"),
    2003: (None, "2003-04-27"),
    2005: (None, "2005-10-23"),
    2007: (None, "2007-10-28"),
    2009: (None, "2009-06-28"),
    2011: ("2011-10-23", "2011-10-23"),
    2013: ("2013-10-27", "2013-10-27"),
    2015: ("2015-10-25", "2015-10-25"),
    2017: ("2017-10-22", "2017-10-22"),
    2019: ("2019-10-27", "2019-10-27"),
    2021: ("2021-11-14", "2021-11-14"),
    2023: ("2023-10-22", "2023-10-22"),
    2025: ("2025-10-26", "2025-09-07"),  # único desdoblamiento del período (D4)
}

_ANIOS_EJECUTIVA_PROV_MUN = {2003, 2007, 2011, 2015, 2019, 2023}
_ANIOS_EJECUTIVA_NACIONAL = {2011, 2015, 2019, 2023}

_CARGOS_EN_JUEGO = {
    ("municipal", True): "intendente, concejales",
    ("municipal", False): "concejales",
    ("provincial", True): "gobernador, diputados provinciales",
    ("provincial", False): "diputados provinciales",
    ("nacional", True): "presidente, diputados nacionales",
    ("nacional", False): "diputados nacionales",
}


@dataclass(frozen=True)
class FilaCalendario:
    anio: int
    nivel: str
    fecha_eleccion: str
    tipo_eleccion: str  # ejecutiva / legislativa
    desdoblada: bool
    cargos_en_juego: str


def construir_calendario() -> list[FilaCalendario]:
    """Una fila por (año, nivel) 2001-2025; `nacional` solo desde 2011."""
    filas = []
    for anio, (fecha_nacional, fecha_prov_mun) in sorted(_FECHAS.items()):
        if fecha_nacional is not None:
            ejecutiva = anio in _ANIOS_EJECUTIVA_NACIONAL
            filas.append(
                FilaCalendario(
                    anio=anio,
                    nivel="nacional",
                    fecha_eleccion=fecha_nacional,
                    tipo_eleccion="ejecutiva" if ejecutiva else "legislativa",
                    desdoblada=False,
                    cargos_en_juego=_CARGOS_EN_JUEGO[("nacional", ejecutiva)],
                )
            )
        for nivel in ("provincial", "municipal"):
            ejecutiva = anio in _ANIOS_EJECUTIVA_PROV_MUN
            filas.append(
                FilaCalendario(
                    anio=anio,
                    nivel=nivel,
                    fecha_eleccion=fecha_prov_mun,
                    tipo_eleccion="ejecutiva" if ejecutiva else "legislativa",
                    desdoblada=(anio == 2025),
                    cargos_en_juego=_CARGOS_EN_JUEGO[(nivel, ejecutiva)],
                )
            )
    return filas


@dataclass(frozen=True)
class HistoriaOficialismo:
    """Un punto de la historia de quién ocupaba el Ejecutivo de un nivel,
    investigado a mano para 2001-2009 (`oficialismos.csv` no llega tan
    atrás). `agrupacion` es quien ocupaba el cargo *al momento* de esa
    elección (antes de su resultado); `continuidad` describe el desenlace
    de esa elección para esa titularidad."""

    anio: int
    agrupacion: str
    continuidad: str  # continua / continua_renombrada / ruptura / sin_oficialismo
    nota: str


# Fuente: 0221.com.ar, "Desde el 83 hasta la fecha: así fueron los resultados
# de las elecciones a intendente en La Plata" (cita a la Junta Electoral de
# la Provincia de Buenos Aires como fuente primaria). Ver
# docs/adquisicion_datos_especializacion.md §1.a.
_HISTORIA_MUNICIPAL_PRE_2011 = [
    HistoriaOficialismo(
        2001,
        "PARTIDO JUSTICIALISTA",
        "continua",
        "Julio Alak (PJ), intendente desde 1991, reelecto 1995/1999. Sin "
        "elección ejecutiva en 2001 (año legislativo, solo concejales); "
        "resultado de esa elección de concejales no verificado (ver 1.a).",
    ),
    HistoriaOficialismo(
        2003,
        "PARTIDO JUSTICIALISTA",
        "continua",
        "Alak (PJ) reelecto, venció a Pablo Bruera por ~30.000 votos.",
    ),
    HistoriaOficialismo(
        2005,
        "PARTIDO JUSTICIALISTA",
        "continua",
        "Sin elección ejecutiva en 2005; Alak continúa. Resultado de la "
        "elección de concejales de ese año no verificado (ver 1.a).",
    ),
    HistoriaOficialismo(
        2007,
        "PARTIDO PROGRESO SOCIAL",
        "ruptura",
        "Pablo Bruera (Partido Progreso Social) venció a Alak/PJ -- "
        "alternancia real, no continuidad.",
    ),
    HistoriaOficialismo(
        2009,
        "PARTIDO PROGRESO SOCIAL",
        "continua",
        "Sin elección ejecutiva en 2009; Bruera continúa. Etiqueta electoral "
        "exacta de 2009 no verificada -- para 2011, el mismo espacio "
        "(Bruera) ya figura en oficialismos.csv como ALIANZA FRENTE PARA LA "
        "VICTORIA, con era_oficialismo=true, consistente con esta cadena.",
    ),
]

# Fuente: pba_gober_gral2003.csv / pba_gober_gral2007.csv, mirror de GitHub
# `PoliticaArgentina/data_warehouse` (scrapeado del Atlas Electoral de Andy
# Tow) -- totales provinciales de la elección de gobernador, suficientes
# para identidad de ganador aunque no para desagregar a La Plata. Ver
# docs/adquisicion_datos_especializacion.md §1.a.
_HISTORIA_PROVINCIAL_PRE_2011 = [
    HistoriaOficialismo(
        2001,
        "PARTIDO JUSTICIALISTA",
        "continua",
        "Carlos Ruckauf (PJ), gobernador desde dic-1999. Sin elección "
        "ejecutiva en 2001. Ruckauf renuncia en dic-2001 para ser canciller; "
        "asume Felipe Solá (su vicegobernador, mismo signo político) -- "
        "sucesión constitucional, no ruptura.",
    ),
    HistoriaOficialismo(
        2003,
        "PARTIDO JUSTICIALISTA",
        "continua",
        "Solá (lista 'Justicialista') electo gobernador -- "
        "Solá-Giannettasio, 2.563.136 votos.",
    ),
    HistoriaOficialismo(
        2005,
        "PARTIDO JUSTICIALISTA",
        "continua",
        "Sin elección ejecutiva en 2005; Solá continúa.",
    ),
    HistoriaOficialismo(
        2007,
        "ALIANZA FRENTE PARA LA VICTORIA",
        "continua_renombrada",
        "Daniel Scioli (Frente Para La Victoria) sucede a Solá -- mismo "
        "espacio peronista, nueva etiqueta de frente (Scioli-Balestrini, "
        "3.376.795 votos).",
    ),
    HistoriaOficialismo(
        2009,
        "ALIANZA FRENTE PARA LA VICTORIA",
        "continua",
        "Sin elección ejecutiva en 2009; Scioli continúa.",
    ),
]

_HISTORIA_PRE_2011 = {"municipal": _HISTORIA_MUNICIPAL_PRE_2011, "provincial": _HISTORIA_PROVINCIAL_PRE_2011}


def _cargar_clasificacion(path: Path | str) -> dict[tuple[str, str, str], dict]:
    """(anio, agrupacion, nivel_csv) -> fila de clasificacion_ideologica_agrupaciones.csv."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {(fila["anio"], fila["agrupacion"], fila["nivel"]): fila for fila in csv.DictReader(f)}


def _cargar_oficialismos(path: Path | str) -> dict[tuple[int, str], dict]:
    """(anio, nivel) -> fila de oficialismos.csv (2011-2025, ya curado)."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {(int(fila["anio"]), fila["nivel"]): fila for fila in csv.DictReader(f)}


def _nivel_csv_del_cargo(nivel: str, cargo: str) -> str:
    """Traduce (nivel unificado, cargo específico) al valor de `nivel` usado
    en `clasificacion_ideologica_agrupaciones.csv` -- reusa el mismo mapeo
    que `totales_por_lista` para el único caso irregular (gobernador->gobernacion)."""
    return NIVEL_A_NIVEL_CSV.get(cargo, cargo)


def _cargo_ejecutivo(nivel: str) -> str:
    return NIVELES_A_CARGOS[nivel][0]


@dataclass(frozen=True)
class FilaOficialismo:
    anio: int
    nivel: str
    agrupacion_oficialismo: str
    campo_ideologico: str
    filiacion_politica: str
    vparty_economico: str
    vparty_progresismo: str
    vparty_populismo: str
    continuidad_oficialismo: str
    nota: str


def construir_oficialismo_por_nivel(
    calendario: list[FilaCalendario],
    oficialismos_2011_2025: dict[tuple[int, str], dict],
    clasificacion: dict[tuple[str, str, str], dict],
) -> list[FilaOficialismo]:
    """Une la historia investigada 2001-2009 con `oficialismos.csv` 2011-2025;
    resuelve campo_ideologico/filiacion_politica/V-Party por join contra
    `clasificacion_ideologica_agrupaciones.csv`, sin duplicar esos atributos
    a mano. Nivel `nacional` no tiene años pre-2011 (no genera filas ahí)."""
    filas = []
    for fc in calendario:
        if fc.nivel == "nacional" and fc.anio < 2011:
            continue

        if fc.anio >= 2011:
            fila_of = oficialismos_2011_2025.get((fc.anio, fc.nivel))
            if fila_of is None:
                continue
            agrupacion = fila_of["agrupacion_ganadora"]
            era_oficialismo = fila_of["era_oficialismo"].strip().lower() == "true"
            continuidad = "continua" if era_oficialismo else "ruptura"
            nota = "Fuente: data/agrupaciones/oficialismos.csv (ya curado)."
            campo_ideologico = fila_of.get("campo_ideologico", "")
            filiacion_politica = fila_of.get("filiacion_politica", "")
            vparty_economico = fila_of.get("vparty_economico", "")
            vparty_progresismo = fila_of.get("vparty_progresismo", "")
            vparty_populismo = fila_of.get("vparty_populismo", "")
        else:
            historia = {h.anio: h for h in _HISTORIA_PRE_2011.get(fc.nivel, [])}
            punto = historia.get(fc.anio)
            if punto is None:
                continue
            agrupacion = punto.agrupacion
            continuidad = punto.continuidad
            nota = punto.nota

            cargo = _cargo_ejecutivo(fc.nivel) if fc.tipo_eleccion == "ejecutiva" else fc.nivel
            nivel_csv = _nivel_csv_del_cargo(fc.nivel, cargo)
            clave = (str(fc.anio), agrupacion, nivel_csv)
            fila_clas = clasificacion.get(clave)
            if fila_clas is None:
                campo_ideologico = filiacion_politica = ""
                vparty_economico = vparty_progresismo = vparty_populismo = ""
                nota = f"{nota} Sin fila en clasificacion_ideologica_agrupaciones.csv (no cubre pre-2011) -- ideología sin determinar."
            else:
                campo_ideologico = fila_clas.get("campo_ideologico", "")
                filiacion_politica = fila_clas.get("filiacion_politica", "")
                vparty_economico = fila_clas.get("vparty_economico", "")
                vparty_progresismo = fila_clas.get("vparty_progresismo", "")
                vparty_populismo = fila_clas.get("vparty_populismo", "")

        filas.append(
            FilaOficialismo(
                anio=fc.anio,
                nivel=fc.nivel,
                agrupacion_oficialismo=agrupacion,
                campo_ideologico=campo_ideologico,
                filiacion_politica=filiacion_politica,
                vparty_economico=vparty_economico,
                vparty_progresismo=vparty_progresismo,
                vparty_populismo=vparty_populismo,
                continuidad_oficialismo=continuidad,
                nota=nota,
            )
        )
    return sorted(filas, key=lambda f: (f.nivel, f.anio))


@dataclass(frozen=True)
class FilaVentana:
    id_transicion: str
    nivel: str
    anio_t: int
    anio_t_menos_1: int
    anio_t_menos_2: int | None
    fecha_inicio_vc: str
    fecha_fin_vc: str
    fecha_inicio_vl: str | None
    tipo_eleccion_t: str
    tipo_eleccion_t_menos_1: str


def construir_ventanas(calendario: list[FilaCalendario]) -> list[FilaVentana]:
    """Una fila por transición (elección t-1 -> t) dentro de cada nivel.
    Ventana corta = [fecha t-1, fecha t]; bloque largo arranca en fecha t-2
    si existe (D3: el bloque largo no es una observación aparte, ver
    features_ventana.py). 12 municipal + 12 provincial + 7 nacional = 31."""
    por_nivel: dict[str, list[FilaCalendario]] = {nivel: [] for nivel in NIVELES}
    for fc in calendario:
        por_nivel[fc.nivel].append(fc)
    for nivel in por_nivel:
        por_nivel[nivel].sort(key=lambda fc: fc.anio)

    ventanas = []
    for nivel, filas in por_nivel.items():
        for i in range(1, len(filas)):
            actual, anterior = filas[i], filas[i - 1]
            anterior_2 = filas[i - 2] if i >= 2 else None
            ventanas.append(
                FilaVentana(
                    id_transicion=f"{nivel}_{anterior.anio}_{actual.anio}",
                    nivel=nivel,
                    anio_t=actual.anio,
                    anio_t_menos_1=anterior.anio,
                    anio_t_menos_2=anterior_2.anio if anterior_2 else None,
                    fecha_inicio_vc=anterior.fecha_eleccion,
                    fecha_fin_vc=actual.fecha_eleccion,
                    fecha_inicio_vl=anterior_2.fecha_eleccion if anterior_2 else None,
                    tipo_eleccion_t=actual.tipo_eleccion,
                    tipo_eleccion_t_menos_1=anterior.tipo_eleccion,
                )
            )
    return ventanas


def _escribir_csv(path: Path | str, filas: list, columnas: list[str]) -> Path:
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columnas)
        for fila in filas:
            writer.writerow([getattr(fila, col) if getattr(fila, col, None) is not None else "" for col in columnas])
    return destino


def generar_csvs(
    calendario_path: Path | str = CALENDARIO_ELECTORAL_PATH,
    oficialismo_path: Path | str = OFICIALISMO_POR_NIVEL_PATH,
    ventanas_path: Path | str = VENTANAS_PATH,
    oficialismos_existente_path: Path | str = OFICIALISMOS_PATH,
    clasificacion_path: Path | str = CLASIFICACION_IDEOLOGICA_PATH,
) -> tuple[Path, Path, Path]:
    calendario = construir_calendario()
    destino_calendario = _escribir_csv(
        calendario_path, calendario, ["anio", "nivel", "fecha_eleccion", "tipo_eleccion", "desdoblada", "cargos_en_juego"]
    )

    oficialismos_2011_2025 = _cargar_oficialismos(oficialismos_existente_path)
    clasificacion = _cargar_clasificacion(clasificacion_path)
    oficialismo = construir_oficialismo_por_nivel(calendario, oficialismos_2011_2025, clasificacion)
    destino_oficialismo = _escribir_csv(
        oficialismo_path,
        oficialismo,
        [
            "anio",
            "nivel",
            "agrupacion_oficialismo",
            "campo_ideologico",
            "filiacion_politica",
            "vparty_economico",
            "vparty_progresismo",
            "vparty_populismo",
            "continuidad_oficialismo",
            "nota",
        ],
    )

    ventanas = construir_ventanas(calendario)
    destino_ventanas = _escribir_csv(
        ventanas_path,
        ventanas,
        [
            "id_transicion",
            "nivel",
            "anio_t",
            "anio_t_menos_1",
            "anio_t_menos_2",
            "fecha_inicio_vc",
            "fecha_fin_vc",
            "fecha_inicio_vl",
            "tipo_eleccion_t",
            "tipo_eleccion_t_menos_1",
        ],
    )

    return destino_calendario, destino_oficialismo, destino_ventanas


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    args = parser.parse_args()
    calendario_p, oficialismo_p, ventanas_p = generar_csvs()
    print(f"calendario -> {calendario_p}")
    print(f"oficialismo -> {oficialismo_p}")
    print(f"ventanas -> {ventanas_p}")


if __name__ == "__main__":
    main()
