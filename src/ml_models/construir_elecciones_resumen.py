"""Resumen electoral por (nivel, año) -- fuente de verdad única con la
estructura de la oferta partidaria (fuerzas viables, marginal, oposición
principal, dispersión ideológica ponderada por voto), reemplazando a
`resultado_distrito.csv`/`voto_partido_distrito.csv` como insumo del panel
trimestral (ver `docs/decisiones_metodologicas.md` D17 y
`docs/especificacion_panel_temporal.md` "Diccionario de columnas de
elecciones.csv"). Esos dos archivos quedan congelados, sin código que los
regenere modificado -- no se eliminan ni se tocan.

Escribe `data/tfi_data/elecciones.csv`, un CSV por (nivel, año) -- no
confundir con el directorio `data/tfi_data/elecciones/`, un CSV por
partido por (año, nivel), generado por `ml_models.construir_elecciones`.
Este módulo lee ese directorio como fuente principal (ya trae
BLANCO/NULO/VOTANTES_HABILITADOS y `vparty_economico`/`vparty_progresismo`
por partido, sincronizados con `clasificacion_ideologica_agrupaciones.csv`)
y reusa `ml_models.construir_resultado_distrito.construir_voto_partido_distrito`/
`_entrada_oficialismo` para `votos_positivos`/`share` por partido y para
identificar la fila exacta del oficialismo -- mismo denominador
(`votos_positivos`) en las dos ramas con/sin `circuito_<cargo>.json`
cacheado, verificado antes de escribir este módulo (D17).

`ausentismo` es la única columna que no sale de `elecciones/<año>_<nivel>.csv`:
en años con `circuito_<cargo>.json` reusa la fórmula oficial del repo
(`electores - positivos - otros_total`, vía `analisis.graficos._votos_no_ideologicos`),
que neteda categorías "recurridos/impugnados/comando" que
`elecciones/<año>_<nivel>.csv` no conserva; en años sin circuito
(2001-2009, 2025 municipal/provincial) se resta sobre `votantes_habilitados`
-- ver D17 para la limitación metodológica de esa segunda rama.

Uso:
    PYTHONPATH=src python -m ml_models.construir_elecciones_resumen
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from analisis.graficos import _cargar_circuito, _votos_no_ideologicos
from constantes import (
    CALENDARIO_ELECTORAL_PATH,
    DATA_DISTRITO_DIR,
    ELECCIONES_DIR,
    ELECCIONES_RESUMEN_PATH,
    OFICIALISMOS_PATH,
    OFICIALISMO_POR_NIVEL_PATH,
)
from ml_models.construir_calendario import FilaCalendario, _cargar_oficialismos
from ml_models.construir_resultado_distrito import (
    ALIAS_LISTA_OFICIALISMO,
    FilaVotoPartido,
    _cargar_oficialismo_por_nivel,
    _cargo_de_eleccion,
    _circuito_disponible,
    _entrada_oficialismo,
    construir_voto_partido_distrito,
)

UMBRAL_VIABLE = 1.5  # % sobre votos_positivos -- piso Ley 26.571 (2011)


@dataclass(frozen=True)
class FilaEleccion:
    nivel: str
    anio: int
    votantes_habilitados: int | None
    votos_positivos: int
    votos_blancos: int | None
    votos_nulos: int | None
    ausentismo: int | None
    gana_oficialismo: bool | None
    share_oficialismo: float | None
    agrupacion_oficialismo: str | None
    n_fuerzas_viables: int
    share_marginal_acumulado: float
    share_oposicion_principal: float | None
    share_otras_fuerzas_viables: float
    dispersion_economico_mu: float | None
    dispersion_economico_sigma2: float | None
    dispersion_progresismo_mu: float | None
    dispersion_progresismo_sigma2: float | None
    resultado_disponible: bool


def _totales_y_vparty_desde_tfi(
    path: Path | str,
) -> tuple[dict[str, int], dict[str, tuple[float, float]]]:
    """De `elecciones/<año>_<nivel>.csv`: totales BLANCO/NULO/VOTANTES_HABILITADOS
    (clave ausente si esa fila no está -- 2025 municipal/provincial no
    tiene NULO) y `vparty_economico`/`vparty_progresismo` por nombre de
    agrupación en mayúsculas (no por `id_agrupacion`, que no es estable
    entre años -- mismo criterio que `_match_oficialismo`), solo para las
    filas con V-Party cargado."""
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as f:
        f.readline()  # comentario "# Total de votos, ...", no es el header
        filas = list(csv.DictReader(f))

    totales: dict[str, int] = {}
    vparty: dict[str, tuple[float, float]] = {}
    for r in filas:
        if r["agrupacion"] == "BLANCO":
            totales["blanco"] = int(r["votos"])
        elif r["agrupacion"] == "NULO":
            totales["nulo"] = int(r["votos"])
        elif r["agrupacion"] == "VOTANTES_HABILITADOS":
            totales["habilitados"] = int(r["votos"])
        elif r.get("vparty_economico"):
            totales_nombre = r["agrupacion"].strip().upper()
            vparty[totales_nombre] = (float(r["vparty_economico"]), float(r["vparty_progresismo"]))
    return totales, vparty


def _dispersion_ponderada(pares: list[tuple[int, float]]) -> tuple[float, float]:
    """Media y varianza de `valor` ponderadas por `peso` -- función aislada
    a propósito (pedido explícito): hoy solo 388/557 filas de
    `clasificacion_ideologica_agrupaciones.csv` tienen V-Party cargado, así
    que este cálculo cambia de cobertura sin tocar el resto del módulo a
    medida que se complete esa clasificación."""
    peso_total = sum(peso for peso, _ in pares)
    mu = sum(peso * valor for peso, valor in pares) / peso_total
    sigma2 = sum(peso * (valor - mu) ** 2 for peso, valor in pares) / peso_total
    return mu, sigma2


def _estructura_oferta(
    del_anio: list[FilaVotoPartido], entrada_oficialismo: FilaVotoPartido | None
) -> tuple[int, float, float | None, float]:
    """`n_fuerzas_viables`, `share_marginal_acumulado`,
    `share_oposicion_principal`, `share_otras_fuerzas_viables` -- las 4
    últimas cierran la identidad con `share_oficialismo` documentada en
    `docs/decisiones_metodologicas.md` D17. Si el oficialismo no es viable
    (`share_oficialismo < 1.5`), su fila ya cae dentro de
    `share_marginal_acumulado` como cualquier otra fuerza sub-umbral -- no
    se la excluye de esa suma ni se la cuenta en `n_fuerzas_viables`."""
    viables = [v for v in del_anio if v.share >= UMBRAL_VIABLE]
    marginales = [v for v in del_anio if v.share < UMBRAL_VIABLE]
    share_marginal_acumulado = sum(v.share for v in marginales)

    otras_viables = [v for v in viables if v is not entrada_oficialismo]
    oposicion_principal = max(otras_viables, key=lambda v: v.votos) if otras_viables else None
    share_oposicion_principal = oposicion_principal.share if oposicion_principal is not None else None
    share_otras_fuerzas_viables = sum(v.share for v in otras_viables if v is not oposicion_principal)

    return len(viables), share_marginal_acumulado, share_oposicion_principal, share_otras_fuerzas_viables


def construir_fila_eleccion(
    nivel: str,
    anio: int,
    del_anio: list[FilaVotoPartido],
    totales: dict[str, int],
    vparty: dict[str, tuple[float, float]],
    of: dict | None,
    fila_of_curada: dict | None,
    alias_lista: str | None,
    resultado_disponible: bool,
    ausentismo: int | None,
) -> FilaEleccion:
    """Pura -- todo ya cargado/resuelto por el llamador (`generar_csv`),
    para que la lógica de estructura de oferta + dispersión sea testeable
    sin tocar disco."""
    votos_positivos = sum(v.votos for v in del_anio)

    gana_oficialismo, entrada_oficialismo = _entrada_oficialismo(del_anio, of, fila_of_curada, alias_lista)
    share_oficialismo = entrada_oficialismo.share if entrada_oficialismo is not None else None
    agrupacion_oficialismo = of["agrupacion_oficialismo"] if of else None

    n_fuerzas_viables, share_marginal_acumulado, share_oposicion_principal, share_otras_fuerzas_viables = (
        _estructura_oferta(del_anio, entrada_oficialismo)
    )

    viables = [v for v in del_anio if v.share >= UMBRAL_VIABLE]
    con_score = [(v.votos, vparty[v.agrupacion.strip().upper()]) for v in viables if v.agrupacion.strip().upper() in vparty]
    if con_score:
        dispersion_economico_mu, dispersion_economico_sigma2 = _dispersion_ponderada(
            [(peso, score[0]) for peso, score in con_score]
        )
        dispersion_progresismo_mu, dispersion_progresismo_sigma2 = _dispersion_ponderada(
            [(peso, score[1]) for peso, score in con_score]
        )
    else:
        dispersion_economico_mu = dispersion_economico_sigma2 = None
        dispersion_progresismo_mu = dispersion_progresismo_sigma2 = None

    return FilaEleccion(
        nivel=nivel,
        anio=anio,
        votantes_habilitados=totales.get("habilitados"),
        votos_positivos=votos_positivos,
        votos_blancos=totales.get("blanco"),
        votos_nulos=totales.get("nulo"),
        ausentismo=ausentismo,
        gana_oficialismo=gana_oficialismo,
        share_oficialismo=share_oficialismo,
        agrupacion_oficialismo=agrupacion_oficialismo,
        n_fuerzas_viables=n_fuerzas_viables,
        share_marginal_acumulado=share_marginal_acumulado,
        share_oposicion_principal=share_oposicion_principal,
        share_otras_fuerzas_viables=share_otras_fuerzas_viables,
        dispersion_economico_mu=dispersion_economico_mu,
        dispersion_economico_sigma2=dispersion_economico_sigma2,
        dispersion_progresismo_mu=dispersion_progresismo_mu,
        dispersion_progresismo_sigma2=dispersion_progresismo_sigma2,
        resultado_disponible=resultado_disponible,
    )


def _cargar_calendario(path: Path | str) -> list[FilaCalendario]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return [
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


def construir_elecciones(
    calendario: list[FilaCalendario],
    voto_partido: list[FilaVotoPartido],
    oficialismo_por_nivel: dict[tuple[int, str], dict],
    oficialismos_curados: dict[tuple[int, str], dict],
    data_dir: Path | str = DATA_DISTRITO_DIR,
    elecciones_dir: Path | str = ELECCIONES_DIR,
) -> list[FilaEleccion]:
    voto_partido_por_anio_nivel: dict[tuple[int, str], list[FilaVotoPartido]] = {}
    for v in voto_partido:
        voto_partido_por_anio_nivel.setdefault((v.anio, v.nivel), []).append(v)

    filas = []
    for fc in calendario:
        cargo = _cargo_de_eleccion(fc.nivel, fc.tipo_eleccion)
        disponible = _circuito_disponible(data_dir, fc.anio, cargo)
        del_anio = voto_partido_por_anio_nivel.get((fc.anio, fc.nivel), [])

        totales, vparty = _totales_y_vparty_desde_tfi(Path(elecciones_dir) / f"{fc.anio}_{fc.nivel}.csv")

        if disponible:
            contenido = _cargar_circuito(data_dir, fc.anio, cargo)
            ausentismo = _votos_no_ideologicos(contenido, circuito_id=None)["ausentismo"]
        elif totales.get("nulo") is not None and totales.get("habilitados") is not None:
            votos_positivos = sum(v.votos for v in del_anio)
            ausentismo = totales["habilitados"] - votos_positivos - totales.get("blanco", 0) - totales["nulo"]
        else:
            ausentismo = None

        filas.append(
            construir_fila_eleccion(
                nivel=fc.nivel,
                anio=fc.anio,
                del_anio=del_anio,
                totales=totales,
                vparty=vparty,
                of=oficialismo_por_nivel.get((fc.anio, fc.nivel)),
                fila_of_curada=oficialismos_curados.get((fc.anio, fc.nivel)),
                alias_lista=ALIAS_LISTA_OFICIALISMO.get((fc.anio, fc.nivel)),
                resultado_disponible=disponible,
                ausentismo=ausentismo,
            )
        )
    return filas


_COLUMNAS = [
    "nivel",
    "anio",
    "votantes_habilitados",
    "votos_positivos",
    "votos_blancos",
    "votos_nulos",
    "ausentismo",
    "gana_oficialismo",
    "share_oficialismo",
    "agrupacion_oficialismo",
    "n_fuerzas_viables",
    "share_marginal_acumulado",
    "share_oposicion_principal",
    "share_otras_fuerzas_viables",
    "dispersion_economico_mu",
    "dispersion_economico_sigma2",
    "dispersion_progresismo_mu",
    "dispersion_progresismo_sigma2",
    "resultado_disponible",
]

# Subconjunto que se agrega a las filas frontera (`eleccion_t`/`eleccion_t_menos_1`
# y `eleccion_t`/`eleccion_t_menos_2`) de `construir_panel_trimestral.py`/
# `construir_panel_bieleccion_trimestral.py` -- `nivel`/`anio` quedan afuera
# porque esas filas ya los tienen bajo otro nombre (`anio_t`/`anio_t_menos_1`).
COLUMNAS_ELECCION_PANEL = [col for col in _COLUMNAS if col not in ("nivel", "anio")]


def _escribir_csv(path: Path | str, filas: list[FilaEleccion]) -> Path:
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(_COLUMNAS)
        for fila in filas:
            writer.writerow([getattr(fila, col) if getattr(fila, col) is not None else "" for col in _COLUMNAS])
    return destino


def _parse_bool(valor: str) -> bool | None:
    if not valor:
        return None
    return valor.strip().lower() == "true"


def _parse_int(valor: str) -> int | None:
    return int(valor) if valor else None


def _parse_float(valor: str) -> float | None:
    return float(valor) if valor else None


def cargar_elecciones(path: Path | str = ELECCIONES_RESUMEN_PATH) -> dict[tuple[int, str], FilaEleccion]:
    """(anio, nivel) -> `FilaEleccion`, para `construir_panel_trimestral.py`/
    `construir_panel_bieleccion_trimestral.py` -- mismo patrón que
    `construir_panel_ventanas._cargar_resultado_distrito`."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        filas = {}
        for r in csv.DictReader(f):
            fila = FilaEleccion(
                nivel=r["nivel"],
                anio=int(r["anio"]),
                votantes_habilitados=_parse_int(r["votantes_habilitados"]),
                votos_positivos=int(r["votos_positivos"]),
                votos_blancos=_parse_int(r["votos_blancos"]),
                votos_nulos=_parse_int(r["votos_nulos"]),
                ausentismo=_parse_int(r["ausentismo"]),
                gana_oficialismo=_parse_bool(r["gana_oficialismo"]),
                share_oficialismo=_parse_float(r["share_oficialismo"]),
                agrupacion_oficialismo=r["agrupacion_oficialismo"] or None,
                n_fuerzas_viables=int(r["n_fuerzas_viables"]),
                share_marginal_acumulado=float(r["share_marginal_acumulado"]),
                share_oposicion_principal=_parse_float(r["share_oposicion_principal"]),
                share_otras_fuerzas_viables=float(r["share_otras_fuerzas_viables"]),
                dispersion_economico_mu=_parse_float(r["dispersion_economico_mu"]),
                dispersion_economico_sigma2=_parse_float(r["dispersion_economico_sigma2"]),
                dispersion_progresismo_mu=_parse_float(r["dispersion_progresismo_mu"]),
                dispersion_progresismo_sigma2=_parse_float(r["dispersion_progresismo_sigma2"]),
                resultado_disponible=_parse_bool(r["resultado_disponible"]),
            )
            filas[(fila.anio, fila.nivel)] = fila
        return filas


def generar_csv(
    calendario_path: Path | str = CALENDARIO_ELECTORAL_PATH,
    oficialismo_path: Path | str = OFICIALISMO_POR_NIVEL_PATH,
    oficialismos_curado_path: Path | str = OFICIALISMOS_PATH,
    data_dir: Path | str = DATA_DISTRITO_DIR,
    elecciones_dir: Path | str = ELECCIONES_DIR,
    destino: Path | str = ELECCIONES_RESUMEN_PATH,
) -> Path:
    calendario = _cargar_calendario(calendario_path)
    voto_partido = construir_voto_partido_distrito(calendario, data_dir, elecciones_dir)
    oficialismo_por_nivel = _cargar_oficialismo_por_nivel(oficialismo_path)
    oficialismos_curados = _cargar_oficialismos(oficialismos_curado_path)

    filas = construir_elecciones(calendario, voto_partido, oficialismo_por_nivel, oficialismos_curados, data_dir, elecciones_dir)
    return _escribir_csv(destino, filas)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    print(generar_csv())


if __name__ == "__main__":
    main()
