"""Resultado electoral agregado del Partido de La Plata por (año, nivel) --
Fase 2 del panel temporal de ventanas electorales (ver
`docs/especificacion_panel_temporal.md` §4 y §6). Reusa
`electoral.totales.resultado_total_por_agrupacion` (ya suma los circuitos de
`circuito_<cargo>.json`) y `analisis.graficos._votos_no_ideologicos`/
`_cargar_circuito` (misma fórmula de ausentismo que el resto del repo) --
no reimplementa ninguna de las dos.

Años sin `circuito_<cargo>.json` cacheado (2001-2009 completo, y 2025 para
municipal/provincial -- ver `docs/adquisicion_datos_especializacion.md`
§1.a/§1.c) quedan con `resultado_disponible=false` (`participacion` exacta,
vía la fórmula de ausentismo por circuito, no se puede derivar sin ese
detalle), pero desde que `data/tfi_data/elecciones/<año>_<nivel>.csv` cubre
2001-2009 sí se completan `votos_validos`/`votos_blanco`
(`_votos_validos_blanco_participacion_desde_tfi`) y, vía
`construir_voto_partido_distrito`'s fallback a ese mismo CSV
(`_voto_partido_desde_tfi`), también `gana_oficialismo`/`share_oficialismo`
(`_resolver_oficialismo`, mismo emparejamiento por nombre contra
`oficialismo_por_nivel.csv` que usan los años con circuito) -- nunca
imputados, `None` si el emparejamiento por nombre falla (relabeling, ver
`_resolver_oficialismo`). `participacion` solo se completa si además la fila
`VOTANTES_HABILITADOS` de ese CSV (ver `ml_models.construir_elecciones`)
tiene el padrón cargado -- para 2001-2009/2025 municipal-provincial esa fila
arranca vacía (nadie encontró el padrón real todavía, ver
`docs/adquisicion_datos_especializacion.md`), así que `participacion` sigue
en blanco hasta que se cargue a mano.

`oficialismos.csv` (D15, `docs/decisiones_metodologicas.md`) cubre
`municipal`/`provincial` 2001-2025 -- ya no hace falta el fallback de
`_resolver_oficialismo` por nombre contra `oficialismo_por_nivel.csv` para
esos años (el que sigue existiendo, y sigue testeado, es el que atiende un
`(año, nivel)` sin fila en `oficialismos.csv`, hoy solo `nacional`
2001-2009, que ni siquiera aparece en `calendario_electoral.csv`).

Usa siempre la etapa `generales` (primera vuelta), nunca `balotaje` --
misma convención que `analisis.graficos._cargar_circuito`. Para presidente
2015 y 2023 (los dos años con balotaje) esto significa que
`gana_oficialismo`/`share_oficialismo` describen la primera vuelta en La
Plata, no el resultado final de la elección (decidido en balotaje) --
documentado en `docs/decisiones_metodologicas.md`.

Uso:
    PYTHONPATH=src python -m ml_models.construir_resultado_distrito
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from analisis.graficos import _cargar_circuito, _votos_no_ideologicos
from analisis.serie_temporal import NIVELES as NIVELES_A_CARGOS
from constantes import (
    CALENDARIO_ELECTORAL_PATH,
    DATA_DISTRITO_DIR,
    ELECCIONES_DIR,
    OFICIALISMOS_PATH,
    OFICIALISMO_POR_NIVEL_PATH,
    RESULTADO_DISTRITO_PATH,
    VOTO_PARTIDO_DISTRITO_PATH,
)
from electoral.totales import resultado_total_por_agrupacion
from ml_models.construir_calendario import FilaCalendario, _cargar_oficialismos


def _cargo_de_eleccion(nivel: str, tipo_eleccion: str) -> str:
    ejecutivo, legislativo = NIVELES_A_CARGOS[nivel]
    return ejecutivo if tipo_eleccion == "ejecutiva" else legislativo


def _circuito_disponible(data_dir: Path | str, anio: int, cargo: str) -> bool:
    return (Path(data_dir) / str(anio) / cargo / "generales" / f"circuito_{cargo}.json").exists()


@dataclass(frozen=True)
class FilaVotoPartido:
    anio: int
    nivel: str
    id_agrupacion: str
    agrupacion: str
    votos: int
    share: float


def _voto_partido_desde_tfi(path: Path | str) -> list[tuple[str, str, int]]:
    """(id_agrupacion, agrupacion, votos) por agrupación real desde un
    `<año>_<nivel>.csv` de `data/tfi_data/elecciones/` -- excluye
    BLANCO/NULO/VOTANTES_HABILITADOS, mismo recorte que
    `resultado_total_por_agrupacion` hace sobre `circuito["positivos"]`
    (nunca `circuito["otros"]`). Lista vacía si el archivo no existe."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        f.readline()  # comentario "# Total de votos, ...", no es el header
        filas = list(csv.DictReader(f))
    return [
        (r["id_agrupacion"], r["agrupacion"], int(r["votos"]))
        for r in filas
        if r["agrupacion"] not in ("BLANCO", "NULO", "VOTANTES_HABILITADOS")
    ]


def construir_voto_partido_distrito(
    calendario: list[FilaCalendario],
    data_dir: Path | str = DATA_DISTRITO_DIR,
    elecciones_dir: Path | str = ELECCIONES_DIR,
) -> list[FilaVotoPartido]:
    """Grano año×nivel×agrupación. Preferí `circuito_<cargo>.json` cacheado;
    si no existe, cae a `data/tfi_data/elecciones/<año>_<nivel>.csv`
    (`_voto_partido_desde_tfi`), recalculando `share` sobre el total de
    agrupaciones de ese CSV para que sea comparable con el `share` de
    `resultado_total_por_agrupacion` (ambos excluyen BLANCO/NULO del
    denominador). Sin filas si ninguna de las dos fuentes existe para ese
    (año, nivel)."""
    filas = []
    for fc in calendario:
        cargo = _cargo_de_eleccion(fc.nivel, fc.tipo_eleccion)
        if _circuito_disponible(data_dir, fc.anio, cargo):
            for v in resultado_total_por_agrupacion(data_dir, fc.anio, cargo, etapa="generales"):
                filas.append(
                    FilaVotoPartido(
                        anio=fc.anio,
                        nivel=fc.nivel,
                        id_agrupacion=v.id_agrupacion,
                        agrupacion=v.nombre_agrupacion,
                        votos=v.votos,
                        share=v.votos_porcentaje,
                    )
                )
            continue

        crudos = _voto_partido_desde_tfi(Path(elecciones_dir) / f"{fc.anio}_{fc.nivel}.csv")
        total = sum(votos for _, _, votos in crudos)
        for id_agrupacion, agrupacion, votos in crudos:
            filas.append(
                FilaVotoPartido(
                    anio=fc.anio,
                    nivel=fc.nivel,
                    id_agrupacion=id_agrupacion,
                    agrupacion=agrupacion,
                    votos=votos,
                    share=(votos / total * 100) if total else 0.0,
                )
            )
    return filas


@dataclass(frozen=True)
class FilaResultadoDistrito:
    anio: int
    nivel: str
    votos_validos: int | None
    votos_blanco: int | None
    participacion: float | None
    gana_oficialismo: bool | None
    share_oficialismo: float | None
    resultado_disponible: bool


def _match_oficialismo(
    voto_partido_del_anio: list[FilaVotoPartido], agrupacion_oficialismo: str
) -> FilaVotoPartido | None:
    """Empareja por nombre de agrupación (mayúsculas, misma convención que
    el resto del repo) -- no por id_agrupacion, que no es estable entre años."""
    objetivo = agrupacion_oficialismo.strip().upper()
    for v in voto_partido_del_anio:
        if v.agrupacion.strip().upper() == objetivo:
            return v
    return None


# Alias manual: en estos (año, nivel) la lista real de
# `data/tfi_data/elecciones/<año>_<nivel>.csv` no aparece con el mismo
# nombre que `agrupacion_oficialismo` de `oficialismo_por_nivel.csv` --
# relabeling de frentes pre-2011 (ese campo describe la identidad partidaria
# del titular, no el nombre de lista exacto de cada año). Sigue en uso tras
# D15 (`oficialismos.csv` ya cubre estos años): `_resolver_oficialismo`
# también lo usa para resolver `share_oficialismo` cuando `era_oficialismo`
# curado da `false`, mismo mecanismo que ya aplicaba en 2011-2025. Cada
# entrada citada, nunca adivinada -- ver
# `docs/adquisicion_datos_especializacion.md` §1.a para el criterio general
# de fuentes de esta ventana.
ALIAS_LISTA_OFICIALISMO: dict[tuple[int, str], str] = {
    # 2005: interna PJ Kirchner vs. Duhalde -- "el sector duhaldista compitió
    # bajo la etiqueta oficial del PJ, mientras el kirchnerista lo hizo como
    # Frente para la Victoria" (es.wikipedia.org/wiki/Elecciones_legislativas_de_Argentina_de_2005);
    # el gobernador Solá (PJ, titular real) estaba alineado con Kirchner ese
    # año -- la lista oficialista (la del Ejecutivo que gobierna) es FRENTE
    # PARA LA VICTORIA, no la etiqueta histórica "PARTIDO JUSTICIALISTA" de
    # oficialismo_por_nivel.csv. Ambas boletas de La Plata (municipal y
    # provincial) traen las dos listas, mismo patrón -- se asume la misma
    # alineación en concejales que en gobernador/legisladores provinciales,
    # sin cita municipal específica.
    (2005, "municipal"): "FRENTE PARA LA VICTORIA",
    (2005, "provincial"): "FRENTE PARA LA VICTORIA",
    # 2007 provincial: Scioli (Frente Para La Victoria) sucede a Solá,
    # continuidad_oficialismo="continua_renombrada" -- ya citado en
    # `construir_calendario._EJECUTIVA_PRE_2011["provincial"][2007]`. La fila
    # "PARTIDO JUSTICIALISTA" del CSV de 2007 provincial tiene 0 votos (lista
    # que no compitió esa categoría ese año, no la boleta real del oficialismo).
    (2007, "provincial"): "FRENTE PARA LA VICTORIA",
    # 2009: lista de gobierno de Scioli a nivel provincial -- nota de prensa
    # sobre el desafío de UCR/ARI/GEN a las candidaturas de Scioli/Massa por
    # el "Frente Justicialista para la Victoria" en la Pcia. de Buenos Aires,
    # elección legislativa 2009 (es.wikipedia.org/wiki/Elecciones_legislativas_de_Argentina_de_2009).
    # Bruera (intendente electo 2007, "luego PJ/FpV" -- ver
    # docs/adquisicion_datos_especializacion.md §1.a) se asume alineado a la
    # misma lista a nivel municipal -- inferencia más débil que el resto de
    # este dict, sin cita directa de la lista de concejales de La Plata.
    (2009, "municipal"): "FRENTE JUSTICIALISTA PARA LA VICTORIA. (*)",
    (2009, "provincial"): "FRENTE JUSTICIALISTA PARA LA VICTORIA",
}


def _resolver_oficialismo(
    del_anio: list[FilaVotoPartido],
    of: dict | None,
    fila_of_curada: dict | None,
    alias_lista: str | None = None,
) -> tuple[bool | None, float | None]:
    """`gana_oficialismo`/`share_oficialismo` para un (año, nivel): prioriza
    `oficialismos.csv` curado (`era_oficialismo` tal cual, D15 -- ya cubre
    `municipal`/`provincial` 2001-2025); sin curado (hoy solo `nacional`
    2001-2009), empareja por nombre contra `oficialismo_por_nivel.csv`
    (`_match_oficialismo`), o contra `alias_lista` si viene provisto (ver
    `ALIAS_LISTA_OFICIALISMO`, relabeling pre-2011). `None`/`None` si no hay
    ninguna fila de oficialismo, o si el emparejamiento por nombre falla --
    nunca se asume que perdió solo porque no matcheó (posible relabeling sin
    alias todavía)."""
    ganador = max(del_anio, key=lambda v: v.votos) if del_anio else None

    if fila_of_curada is not None:
        gana_oficialismo = fila_of_curada["era_oficialismo"].strip().lower() == "true"
        if of is None:
            return gana_oficialismo, None
        nombre_lista = alias_lista or of["agrupacion_oficialismo"]
        if gana_oficialismo:
            share_oficialismo = ganador.share if ganador is not None else None
        else:
            fila_oficialismo = _match_oficialismo(del_anio, nombre_lista)
            share_oficialismo = fila_oficialismo.share if fila_oficialismo is not None else None
        return gana_oficialismo, share_oficialismo

    if of is None:
        return None, None

    nombre_lista = alias_lista or of["agrupacion_oficialismo"]
    fila_oficialismo = _match_oficialismo(del_anio, nombre_lista)
    if fila_oficialismo is None:
        return None, None
    gana_oficialismo = ganador is not None and ganador.id_agrupacion == fila_oficialismo.id_agrupacion
    share_oficialismo = ganador.share if gana_oficialismo and ganador is not None else fila_oficialismo.share
    return gana_oficialismo, share_oficialismo


def _votos_validos_blanco_participacion_desde_tfi(path: Path | str) -> tuple[int, int, float | None] | None:
    """`votos_validos` (agrupaciones, sin BLANCO/NULO), `votos_blanco`
    (BLANCO+NULO) y `participacion` (si la fila VOTANTES_HABILITADOS tiene
    padrón cargado) desde un `<año>_<nivel>.csv` de
    `data/tfi_data/elecciones/` -- fallback para años sin
    `circuito_<cargo>.json` (2001-2009, 2025 municipal/provincial) que sí
    tienen ese CSV cargado a mano. None si el archivo no existe."""
    path = Path(path)
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as f:
        f.readline()  # comentario "# Total de votos, ...", no es el header
        todas = list(csv.DictReader(f))
    filas = [r for r in todas if r["agrupacion"] != "VOTANTES_HABILITADOS"]
    votos_validos = sum(int(r["votos"]) for r in filas if r["agrupacion"] not in ("BLANCO", "NULO"))
    votos_blanco = sum(int(r["votos"]) for r in filas if r["agrupacion"] in ("BLANCO", "NULO"))
    fila_electores = next((r for r in todas if r["agrupacion"] == "VOTANTES_HABILITADOS"), None)
    if fila_electores is not None and fila_electores["votos"]:
        electores = int(fila_electores["votos"])
        participacion = ((votos_validos + votos_blanco) / electores * 100) if electores else None
    else:
        participacion = None
    return votos_validos, votos_blanco, participacion


def construir_resultado_distrito(
    calendario: list[FilaCalendario],
    voto_partido: list[FilaVotoPartido],
    oficialismo_por_nivel: dict[tuple[int, str], dict],
    oficialismos_curados: dict[tuple[int, str], dict],
    data_dir: Path | str = DATA_DISTRITO_DIR,
    elecciones_dir: Path | str = ELECCIONES_DIR,
) -> list[FilaResultadoDistrito]:
    """`gana_oficialismo`/`share_oficialismo` se resuelven en
    `_resolver_oficialismo`, igual para años con y sin `circuito_<cargo>.json`
    cacheado (lo único que cambia entre ramas es de dónde sale `votos_validos`/
    `votos_blanco`/`participacion`). Reusa `era_oficialismo` de
    `oficialismos.csv` tal cual -- ya es exactamente "¿el voto de La Plata en
    esta categoría favoreció al Ejecutivo real que gobierna?", tanto en años
    ejecutivos como legislativos; no se re-deriva emparejando nombres de
    lista, que puede fallar cuando el oficialismo se presenta con una
    etiqueta nueva ese mismo año (ver `continua_renombrada`). Esto cubre
    `municipal`/`provincial` 2001-2025 desde D15 -- solo queda sin curado
    `nacional` 2001-2009 (ni siquiera está en `calendario_electoral.csv`,
    ver `construir_calendario.py`), donde se empareja por nombre contra
    `agrupacion_oficialismo` de `oficialismo_por_nivel.csv` -- `None`/`None`
    si no matchea, nunca se asume que perdió (posible relabeling, mismo caso
    que arriba pero sin `oficialismos.csv` para resolverlo)."""
    voto_partido_por_anio_nivel: dict[tuple[int, str], list[FilaVotoPartido]] = {}
    for v in voto_partido:
        voto_partido_por_anio_nivel.setdefault((v.anio, v.nivel), []).append(v)

    filas = []
    for fc in calendario:
        cargo = _cargo_de_eleccion(fc.nivel, fc.tipo_eleccion)
        disponible = _circuito_disponible(data_dir, fc.anio, cargo)

        of = oficialismo_por_nivel.get((fc.anio, fc.nivel))
        fila_of_curada = oficialismos_curados.get((fc.anio, fc.nivel))
        alias_lista = ALIAS_LISTA_OFICIALISMO.get((fc.anio, fc.nivel))

        if not disponible:
            del_anio = voto_partido_por_anio_nivel.get((fc.anio, fc.nivel), [])
            votos_tfi = _votos_validos_blanco_participacion_desde_tfi(Path(elecciones_dir) / f"{fc.anio}_{fc.nivel}.csv")
            if votos_tfi is not None:
                votos_validos, votos_blanco, participacion = votos_tfi
            else:
                votos_validos = votos_blanco = None
                participacion = None
            gana_oficialismo, share_oficialismo = _resolver_oficialismo(del_anio, of, fila_of_curada, alias_lista)
            filas.append(
                FilaResultadoDistrito(
                    anio=fc.anio,
                    nivel=fc.nivel,
                    votos_validos=votos_validos,
                    votos_blanco=votos_blanco,
                    participacion=participacion,
                    gana_oficialismo=gana_oficialismo,
                    share_oficialismo=share_oficialismo,
                    resultado_disponible=False,
                )
            )
            continue

        del_anio = voto_partido_por_anio_nivel.get((fc.anio, fc.nivel), [])
        votos_validos = sum(v.votos for v in del_anio)

        contenido = _cargar_circuito(data_dir, fc.anio, cargo)
        no_ideologicos = _votos_no_ideologicos(contenido, circuito_id=None)
        electores = sum(c["electores"] for c in contenido["circuitos"].values())
        ausentismo = no_ideologicos["ausentismo"]
        votantes = electores - ausentismo
        participacion = (votantes / electores * 100) if electores else None

        gana_oficialismo, share_oficialismo = _resolver_oficialismo(del_anio, of, fila_of_curada, alias_lista)

        filas.append(
            FilaResultadoDistrito(
                anio=fc.anio,
                nivel=fc.nivel,
                votos_validos=votos_validos,
                votos_blanco=no_ideologicos["blanco_nulo"],
                participacion=participacion,
                gana_oficialismo=gana_oficialismo,
                share_oficialismo=share_oficialismo,
                resultado_disponible=True,
            )
        )
    return filas


def calcular_delta_v(
    resultado_por_anio_nivel: dict[tuple[int, str], FilaResultadoDistrito], nivel: str, anio_t: int, anio_t_menos_1: int
) -> float | None:
    """share_oficialismo(t) - share_oficialismo(t-1); None si falta
    cualquiera de los dos (nunca imputado)."""
    actual = resultado_por_anio_nivel.get((anio_t, nivel))
    anterior = resultado_por_anio_nivel.get((anio_t_menos_1, nivel))
    if actual is None or anterior is None:
        return None
    if actual.share_oficialismo is None or anterior.share_oficialismo is None:
        return None
    return actual.share_oficialismo - anterior.share_oficialismo


def calcular_delta_posicion_ideologica(
    voto_partido_por_anio_nivel: dict[tuple[int, str], list[FilaVotoPartido]],
    posiciones: dict[tuple[int, str, str], float],
    nivel: str,
    anio_t: int,
    anio_t_menos_1: int,
) -> float | None:
    """Cambio en la posición ideológica ponderada del electorado (share de
    voto de cada agrupación x su score V-Party), nunca la ideología del
    ganador atribuida al distrito entero. `posiciones` mapea
    (anio, nivel, agrupacion) -> score V-Party (ej. vparty_economico); solo
    promedia sobre agrupaciones con score conocido, ponderando por su share
    dentro de ese subconjunto (no se rellena el resto con 0)."""

    def _posicion_ponderada(anio: int) -> float | None:
        filas = voto_partido_por_anio_nivel.get((anio, nivel), [])
        con_score = [(v, posiciones[(anio, nivel, v.agrupacion.strip().upper())]) for v in filas if (anio, nivel, v.agrupacion.strip().upper()) in posiciones]
        peso_total = sum(v.votos for v, _ in con_score)
        if not con_score or not peso_total:
            return None
        return sum(v.votos * score for v, score in con_score) / peso_total

    pos_t = _posicion_ponderada(anio_t)
    pos_t_menos_1 = _posicion_ponderada(anio_t_menos_1)
    if pos_t is None or pos_t_menos_1 is None:
        return None
    return pos_t - pos_t_menos_1


def calcular_distancia_oficialismo_alternativa(
    voto_partido_del_anio: list[FilaVotoPartido],
    posiciones_del_anio: dict[str, float],
    agrupacion_oficialismo: str,
) -> float | None:
    """Distancia (valor absoluto) entre el score del oficialismo y el de la
    principal fuerza opositora (mayor cantidad de votos entre las demás
    agrupaciones con score conocido). None si no hay score para el
    oficialismo o ninguna oposición con score."""
    objetivo = agrupacion_oficialismo.strip().upper()
    if objetivo not in posiciones_del_anio:
        return None
    oposicion = [v for v in voto_partido_del_anio if v.agrupacion.strip().upper() != objetivo and v.agrupacion.strip().upper() in posiciones_del_anio]
    if not oposicion:
        return None
    principal = max(oposicion, key=lambda v: v.votos)
    return abs(posiciones_del_anio[objetivo] - posiciones_del_anio[principal.agrupacion.strip().upper()])


def _cargar_oficialismo_por_nivel(path: Path | str) -> dict[tuple[int, str], dict]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {(int(fila["anio"]), fila["nivel"]): fila for fila in csv.DictReader(f)}


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
    data_dir: Path | str = DATA_DISTRITO_DIR,
    calendario_path: Path | str = CALENDARIO_ELECTORAL_PATH,
    oficialismo_path: Path | str = OFICIALISMO_POR_NIVEL_PATH,
    oficialismos_curado_path: Path | str = OFICIALISMOS_PATH,
    voto_partido_destino: Path | str = VOTO_PARTIDO_DISTRITO_PATH,
    resultado_destino: Path | str = RESULTADO_DISTRITO_PATH,
    elecciones_dir: Path | str = ELECCIONES_DIR,
) -> tuple[Path, Path]:
    with Path(calendario_path).open(encoding="utf-8", newline="") as f:
        calendario = [
            FilaCalendario(
                anio=int(r["anio"]),
                nivel=r["nivel"],
                fecha_eleccion=r["fecha_eleccion"],
                tipo_eleccion=r["tipo_eleccion"],
                desdoblada=r["desdoblada"].strip().lower() == "true",
                cargos_en_juego=r["cargos_en_juego"],
            )
            for r in csv.DictReader(f)
        ]

    voto_partido = construir_voto_partido_distrito(calendario, data_dir, elecciones_dir)
    destino_voto_partido = _escribir_csv(
        voto_partido_destino, voto_partido, ["anio", "nivel", "id_agrupacion", "agrupacion", "votos", "share"]
    )

    oficialismo = _cargar_oficialismo_por_nivel(oficialismo_path)
    oficialismos_curado = _cargar_oficialismos(oficialismos_curado_path)
    resultado = construir_resultado_distrito(calendario, voto_partido, oficialismo, oficialismos_curado, data_dir, elecciones_dir)
    destino_resultado = _escribir_csv(
        resultado_destino,
        resultado,
        [
            "anio",
            "nivel",
            "votos_validos",
            "votos_blanco",
            "participacion",
            "gana_oficialismo",
            "share_oficialismo",
            "resultado_disponible",
        ],
    )
    return destino_voto_partido, destino_resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    args = parser.parse_args()
    voto_p, resultado_p = generar_csvs()
    print(f"voto_partido_distrito -> {voto_p}")
    print(f"resultado_distrito -> {resultado_p}")


if __name__ == "__main__":
    main()
