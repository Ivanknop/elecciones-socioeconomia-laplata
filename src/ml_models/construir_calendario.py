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
class ResultadoEjecutiva:
    """Desenlace conocido de una elección ejecutiva (intendente/gobernador)
    para años sin `oficialismos.csv`: quién ganó y cómo se relaciona con el
    titular saliente."""

    ganadora: str
    continuidad: str  # continua / continua_renombrada / ruptura
    nota: str


# Titular al *entrar* a la ventana del panel (antes de la elección de 2001),
# investigado a mano -- 0221.com.ar, "Desde el 83 hasta la fecha: así fueron
# los resultados de las elecciones a intendente en La Plata" (cita a la
# Junta Electoral de la Provincia de Buenos Aires). Ver
# docs/adquisicion_datos_especializacion.md §1.a.
_TITULAR_INICIAL_2001 = {
    "municipal": (
        "PARTIDO JUSTICIALISTA",
        "Julio Alak (PJ), intendente desde 1991, reelecto 1995 y 1999. "
        "Titular al momento de la elección de 2001 (año legislativo, solo "
        "concejales) -- resultado de esa elección de concejales no "
        "verificado, ver docs/adquisicion_datos_especializacion.md §1.a.",
    ),
    "provincial": (
        "PARTIDO JUSTICIALISTA",
        "Carlos Ruckauf (PJ), gobernador desde dic-1999. Titular al momento "
        "de la elección de 2001 (año legislativo). Ruckauf renuncia en "
        "dic-2001 para ser canciller; asume Felipe Solá, su vicegobernador "
        "(mismo signo político) -- sucesión constitucional, no ruptura.",
    ),
    # `nacional` no genera filas antes de 2011, pero sí necesita un titular
    # de arranque para la fila de 2011 (quién ocupaba la presidencia *antes*
    # de esa elección): Cristina Fernández de Kirchner, presidenta desde
    # 2007 (reusa la etiqueta 2011 porque `clasificacion_ideologica_agrupaciones.csv`
    # no cubre 2007; el título es de historia política real, no del voto de
    # La Plata, y no requiere clasificación propia -- ver nota por fila).
    "nacional": (
        "ALIANZA FRENTE PARA LA VICTORIA",
        "Cristina Fernández de Kirchner, presidenta desde 2007 (reelecta en "
        "2011). Titular al momento de la elección de 2011 -- año anterior a "
        "la ventana del panel para este nivel.",
    ),
}

# `agrupacion_ganadora` de `oficialismos.csv` es quien ganó el voto *en La
# Plata* para esa categoría -- casi siempre coincide con quién asume el
# cargo real (provincia/nación), pero no siempre: en 2019 La Plata votó a
# JUNTOS POR EL CAMBIO para gobernador (45,0% vs 44,77%) mientras que
# Kicillof/FRENTE DE TODOS ganó la gobernación a nivel provincial. Para el
# *titular real* (quién efectivamente gobierna, insumo de continuidad y de
# años siguientes) se corrige acá; para `gana_oficialismo`/`share_oficialismo`
# en `resultado_distrito.csv` el voto de La Plata (correcto, no se toca) ya
# captura ese matiz vía `era_oficialismo=true` (La Plata sí votó por el
# oficialismo saliente). Verificado por conteo real de circuitos de La Plata
# 2011/2015/2019/2023 (gobernador y presidente) -- único caso de divergencia
# encontrado.
_TITULAR_REAL_DIVERGE_DE_VOTO_LA_PLATA = {
    ("provincial", 2019): (
        "FRENTE DE TODOS",
        "ruptura",  # el Ejecutivo sí cambió de manos a nivel real (Vidal -> Kicillof),
        # aunque La Plata haya votado por el saliente -- ver era_oficialismo/
        # gana_oficialismo en resultado_distrito.csv para ese matiz.
        "Divergencia La Plata/provincia: La Plata votó por JUNTOS POR EL CAMBIO "
        "(oficialismos.csv, era_oficialismo=true), pero Kicillof/FRENTE DE TODOS "
        "ganó la gobernación a nivel provincial real -- continuidad_oficialismo "
        "se corrige a 'ruptura' (el Ejecutivo real sí cambió), el titular real "
        "desde dic-2019 es FRENTE DE TODOS.",
    ),
}

# Desenlaces de elecciones ejecutivas 2003/2007 (oficialismos.csv cubre
# 2011+). Fuente municipal: 0221.com.ar (arriba). Fuente provincial:
# pba_gober_gral2003.csv / pba_gober_gral2007.csv, mirror de GitHub
# `PoliticaArgentina/data_warehouse` (scrapeado del Atlas Electoral de Andy
# Tow) -- totales provinciales, suficientes para identidad del ganador
# aunque no para desagregar a La Plata. Ver
# docs/adquisicion_datos_especializacion.md §1.a.
_EJECUTIVA_PRE_2011: dict[str, dict[int, ResultadoEjecutiva]] = {
    "municipal": {
        2003: ResultadoEjecutiva(
            "PARTIDO JUSTICIALISTA", "continua", "Alak (PJ) reelecto, venció a Pablo Bruera por ~30.000 votos."
        ),
        2007: ResultadoEjecutiva(
            "PARTIDO PROGRESO SOCIAL",
            "ruptura",
            "Pablo Bruera (Partido Progreso Social) venció a Alak/PJ -- alternancia real, no continuidad.",
        ),
    },
    "provincial": {
        2003: ResultadoEjecutiva(
            "PARTIDO JUSTICIALISTA",
            "continua",
            "Solá (lista 'Justicialista') electo gobernador -- Solá-Giannettasio, 2.563.136 votos.",
        ),
        2007: ResultadoEjecutiva(
            "ALIANZA FRENTE PARA LA VICTORIA",
            "continua_renombrada",
            "Daniel Scioli (Frente Para La Victoria) sucede a Solá -- mismo espacio "
            "peronista, nueva etiqueta de frente (Scioli-Balestrini, 3.376.795 votos).",
        ),
    },
}


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


def _clasificacion_del_titular(
    clasificacion: dict[tuple[str, str, str], dict], anio_clasificacion: int, titular: str, nivel: str
) -> dict | None:
    """Busca ideología/V-Party del titular por (año en que ganó la
    ejecutiva, agrupación, cargo ejecutivo del nivel) -- ese es el año y la
    boleta bajo la que efectivamente se supo su clasificación, no el año de
    la fila que se está construyendo."""
    cargo = _cargo_ejecutivo(nivel)
    nivel_csv = _nivel_csv_del_cargo(nivel, cargo)
    return clasificacion.get((str(anio_clasificacion), titular, nivel_csv))


def construir_oficialismo_por_nivel(
    calendario: list[FilaCalendario],
    oficialismos_2011_2025: dict[tuple[int, str], dict],
    clasificacion: dict[tuple[str, str, str], dict],
) -> list[FilaOficialismo]:
    """Titular del Ejecutivo *al momento de cada elección* (antes de su
    resultado), llevado como estado que solo cambia en años con elección
    ejecutiva -- en años legislativos el titular no cambia, gane o pierda
    su lista la banca en juego (eso se resuelve aparte, en
    `resultado_distrito.gana_oficialismo`, contra los votos reales). 2011+
    reusa `oficialismos.csv`; 2001-2009 usa la historia investigada a mano
    (`_TITULAR_INICIAL_2001`/`_EJECUTIVA_PRE_2011`). Ideología/V-Party se
    resuelven por join contra `clasificacion_ideologica_agrupaciones.csv`,
    sin duplicar esos atributos a mano. Nivel `nacional` no tiene años
    pre-2011 (no genera filas ahí)."""
    filas = []
    for nivel in NIVELES:
        filas_nivel = sorted((fc for fc in calendario if fc.nivel == nivel), key=lambda fc: fc.anio)
        if nivel == "nacional":
            filas_nivel = [fc for fc in filas_nivel if fc.anio >= 2011]
            if not filas_nivel:
                continue
        titular, nota_inicial = _TITULAR_INICIAL_2001[nivel]
        titular_anio_clasificacion = None  # el titular inicial es pre-ventana, sin ejecutiva propia en el panel

        for fc in filas_nivel:
            agrupacion_oficialismo = titular
            anio_clasificacion_de_esta_fila = titular_anio_clasificacion  # snapshot: año en que *ese* titular ganó, no el de esta fila
            nota_extra = ""

            if fc.tipo_eleccion == "ejecutiva":
                if fc.anio >= 2011:
                    fila_of = oficialismos_2011_2025.get((fc.anio, nivel))
                    if fila_of is None:
                        continue
                    ganadora = fila_of["agrupacion_ganadora"]
                    era_oficialismo = fila_of["era_oficialismo"].strip().lower() == "true"
                    continuidad = "continua" if era_oficialismo else "ruptura"
                    nota_extra = "Fuente: data/agrupaciones/oficialismos.csv (voto de La Plata, ya curado)."
                    divergencia = _TITULAR_REAL_DIVERGE_DE_VOTO_LA_PLATA.get((nivel, fc.anio))
                    if divergencia is not None:
                        ganadora, continuidad, nota_divergencia = divergencia
                        nota_extra = f"{nota_extra} {nota_divergencia}"
                else:
                    resultado = _EJECUTIVA_PRE_2011[nivel][fc.anio]
                    ganadora, continuidad, nota_extra = resultado.ganadora, resultado.continuidad, resultado.nota
                titular = ganadora
                titular_anio_clasificacion = fc.anio
            else:
                continuidad = "continua"
                nota_extra = "Sin elección ejecutiva este año (solo legislativo); el titular del Ejecutivo no cambia."

            if fc.anio == 2001 and nivel != "nacional":
                nota_extra = f"{nota_inicial} {nota_extra}".strip()

            if anio_clasificacion_de_esta_fila is None:
                campo_ideologico = filiacion_politica = ""
                vparty_economico = vparty_progresismo = vparty_populismo = ""
                nota_extra = f"{nota_extra} Titular anterior a la ventana del panel -- sin año de elección propio para clasificar."
            else:
                fila_clas = _clasificacion_del_titular(clasificacion, anio_clasificacion_de_esta_fila, agrupacion_oficialismo, nivel)
                if fila_clas is None:
                    campo_ideologico = filiacion_politica = ""
                    vparty_economico = vparty_progresismo = vparty_populismo = ""
                    nota_extra = f"{nota_extra} Sin fila en clasificacion_ideologica_agrupaciones.csv para {agrupacion_oficialismo!r} -- ideología sin determinar."
                else:
                    campo_ideologico = fila_clas.get("campo_ideologico", "")
                    filiacion_politica = fila_clas.get("filiacion_politica", "")
                    vparty_economico = fila_clas.get("vparty_economico", "")
                    vparty_progresismo = fila_clas.get("vparty_progresismo", "")
                    vparty_populismo = fila_clas.get("vparty_populismo", "")

            filas.append(
                FilaOficialismo(
                    anio=fc.anio,
                    nivel=nivel,
                    agrupacion_oficialismo=agrupacion_oficialismo,
                    campo_ideologico=campo_ideologico,
                    filiacion_politica=filiacion_politica,
                    vparty_economico=vparty_economico,
                    vparty_progresismo=vparty_progresismo,
                    vparty_populismo=vparty_populismo,
                    continuidad_oficialismo=continuidad,
                    nota=nota_extra,
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
