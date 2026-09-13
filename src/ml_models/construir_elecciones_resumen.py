"""Resumen electoral por (nivel, año) -- estructura de la oferta partidaria
y ausentismo, sucede a `resultado_distrito.csv`/`voto_partido_distrito.csv`
como insumo del panel trimestral (D17, `docs/decisiones_metodologicas.md`).

Escribe `data/tfi_data/elecciones.csv` -- no confundir con el directorio
`data/tfi_data/elecciones/` (un CSV por partido, generado por
`ml_models.construir_elecciones`), que es la fuente que este módulo lee.

`ausentismo`: en años con `circuito_<cargo>.json` usa la fórmula oficial
del repo (`electores - positivos - otros_total`, que no cuenta como
ausentes a "recurridos/impugnados/comando"); sin circuito (2001-2009, 2025
municipal/provincial) se resta sobre `votantes_habilitados`, sin poder
distinguir esas categorías -- ver D17 para la limitación.

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
    votos_blancos_y_nulos: int | None
    participacion_pct: float | None
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
    dispersion_cobertura_share: float
    resultado_disponible: bool


def _totales_y_vparty_desde_tfi(
    path: Path | str,
) -> tuple[dict[str, int], dict[str, tuple[float, float]]]:
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
    peso_total = sum(peso for peso, _ in pares)
    mu = sum(peso * valor for peso, valor in pares) / peso_total
    sigma2 = sum(peso * (valor - mu) ** 2 for peso, valor in pares) / peso_total
    return mu, sigma2


def _estructura_oferta(
    del_anio: list[FilaVotoPartido], entrada_oficialismo: FilaVotoPartido | None
) -> tuple[int, float, float | None, float]:
    # share_marginal_acumulado + share_oposicion_principal + share_otras_fuerzas_viables
    # + share_oficialismo (si es viable) = 100 -- D17.
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
    votos_positivos = sum(v.votos for v in del_anio)

    votos_blancos = totales.get("blanco")
    votos_nulos = totales.get("nulo")
    votantes_habilitados = totales.get("habilitados")
    votos_blancos_y_nulos = votos_blancos + (votos_nulos or 0) if votos_blancos is not None else None
    participacion_pct = (
        (votos_positivos + votos_blancos_y_nulos) / votantes_habilitados * 100
        if votantes_habilitados is not None and votos_blancos_y_nulos is not None
        else None
    )

    gana_oficialismo, entrada_oficialismo = _entrada_oficialismo(del_anio, of, fila_of_curada, alias_lista)
    share_oficialismo = entrada_oficialismo.share if entrada_oficialismo is not None else None
    agrupacion_oficialismo = of["agrupacion_oficialismo"] if of else None

    n_fuerzas_viables, share_marginal_acumulado, share_oposicion_principal, share_otras_fuerzas_viables = (
        _estructura_oferta(del_anio, entrada_oficialismo)
    )

    viables = [v for v in del_anio if v.share >= UMBRAL_VIABLE]
    con_score = [(v.votos, vparty[v.agrupacion.strip().upper()]) for v in viables if v.agrupacion.strip().upper() in vparty]
    dispersion_cobertura_share = (sum(peso for peso, _ in con_score) / votos_positivos * 100) if votos_positivos else 0.0
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
        votantes_habilitados=votantes_habilitados,
        votos_positivos=votos_positivos,
        votos_blancos=votos_blancos,
        votos_nulos=votos_nulos,
        ausentismo=ausentismo,
        votos_blancos_y_nulos=votos_blancos_y_nulos,
        participacion_pct=participacion_pct,
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
        dispersion_cobertura_share=dispersion_cobertura_share,
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
        elif totales.get("habilitados") is not None:
            votos_positivos = sum(v.votos for v in del_anio)
            # nulo=None (2025 prov/municipal, Ley 5.109 -- D17/D19): tratado
            # como 0 solo en esta resta, nunca en la columna votos_nulos misma.
            nulo = totales.get("nulo") or 0
            ausentismo = totales["habilitados"] - votos_positivos - totales.get("blanco", 0) - nulo
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
    "votos_blancos_y_nulos",
    "participacion_pct",
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
    "dispersion_cobertura_share",
    "resultado_disponible",
]
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
                votos_blancos_y_nulos=_parse_int(r["votos_blancos_y_nulos"]),
                participacion_pct=_parse_float(r["participacion_pct"]),
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
                dispersion_cobertura_share=float(r["dispersion_cobertura_share"]),
                resultado_disponible=_parse_bool(r["resultado_disponible"]),
            )
            filas[(fila.anio, fila.nivel)] = fila
        return filas


def calcular_delta_dispersion(
    elecciones_por_anio_nivel: dict[tuple[int, str], FilaEleccion],
    nivel: str,
    anio_t: int,
    anio_t_menos_1: int,
    eje: str,
    estadistico: str = "mu",
) -> float | None:
    """`eje`: `"economico"` o `"progresismo"`. `estadistico`: `"mu"` (centro,
    D17) o `"sigma2"` (varianza -- no cancela cuando fuerzas de polos
    opuestos ganan votos parecidos, D18)."""
    actual = elecciones_por_anio_nivel.get((anio_t, nivel))
    anterior = elecciones_por_anio_nivel.get((anio_t_menos_1, nivel))
    if actual is None or anterior is None:
        return None
    valor_actual = getattr(actual, f"dispersion_{eje}_{estadistico}")
    valor_anterior = getattr(anterior, f"dispersion_{eje}_{estadistico}")
    if valor_actual is None or valor_anterior is None:
        return None
    return valor_actual - valor_anterior


def calcular_cobertura_minima(
    elecciones_por_anio_nivel: dict[tuple[int, str], FilaEleccion], nivel: str, anio_t: int, anio_t_menos_1: int
) -> float | None:
    actual = elecciones_por_anio_nivel.get((anio_t, nivel))
    anterior = elecciones_por_anio_nivel.get((anio_t_menos_1, nivel))
    if actual is None or anterior is None:
        return None
    return min(actual.dispersion_cobertura_share, anterior.dispersion_cobertura_share)


# Participación electoral promedio nacional, presidenciales+legislativas,
# 1983-2023, todo el país (D19) -- Chequeado, 26/10/2025, "la participación
# electoral de este domingo fue la más baja desde 1983" (DNE/Ministerio del
# Interior). Benchmark externo: la participación real de La Plata 2001-2025
# (34 elecciones, 3 niveles) da 75.7%, no comparable 1 a 1 (otra población,
# otro período) -- ver D19 en docs/decisiones_metodologicas.md.
PARTICIPACION_BENCHMARK_NACIONAL_PCT = 79.0


@dataclass(frozen=True)
class ParticipacionVotoExit:
    participacion_pct: float | None
    voto_exit_ausentismo_pct: float | None
    voto_exit_blanco_nulo_pct: float | None
    voto_exit_total_pct: float | None
    participacion_relevante: bool | None


def calcular_participacion_voto_exit(
    elecciones_por_anio_nivel: dict[tuple[int, str], FilaEleccion], nivel: str, anio: int
) -> ParticipacionVotoExit | None:
    fila = elecciones_por_anio_nivel.get((anio, nivel))
    if fila is None:
        return None

    voto_exit_blanco_nulo_pct = (
        fila.votos_blancos_y_nulos / fila.votantes_habilitados * 100
        if fila.votos_blancos_y_nulos is not None and fila.votantes_habilitados is not None
        else None
    )
    voto_exit_ausentismo_pct = (
        fila.ausentismo / fila.votantes_habilitados * 100
        if fila.ausentismo is not None and fila.votantes_habilitados is not None
        else None
    )
    voto_exit_total_pct = (
        voto_exit_ausentismo_pct + voto_exit_blanco_nulo_pct
        if voto_exit_ausentismo_pct is not None and voto_exit_blanco_nulo_pct is not None
        else None
    )
    participacion_relevante = (
        fila.participacion_pct > PARTICIPACION_BENCHMARK_NACIONAL_PCT if fila.participacion_pct is not None else None
    )
    return ParticipacionVotoExit(
        participacion_pct=fila.participacion_pct,
        voto_exit_ausentismo_pct=voto_exit_ausentismo_pct,
        voto_exit_blanco_nulo_pct=voto_exit_blanco_nulo_pct,
        voto_exit_total_pct=voto_exit_total_pct,
        participacion_relevante=participacion_relevante,
    )


def calcular_delta_participacion(
    elecciones_por_anio_nivel: dict[tuple[int, str], FilaEleccion], nivel: str, anio_t: int, anio_t_menos_1: int
) -> float | None:
    actual = calcular_participacion_voto_exit(elecciones_por_anio_nivel, nivel, anio_t)
    anterior = calcular_participacion_voto_exit(elecciones_por_anio_nivel, nivel, anio_t_menos_1)
    if actual is None or anterior is None:
        return None
    if actual.participacion_pct is None or anterior.participacion_pct is None:
        return None
    return actual.participacion_pct - anterior.participacion_pct


def calcular_delta_voto_exit_total(
    elecciones_por_anio_nivel: dict[tuple[int, str], FilaEleccion], nivel: str, anio_t: int, anio_t_menos_1: int
) -> float | None:
    actual = calcular_participacion_voto_exit(elecciones_por_anio_nivel, nivel, anio_t)
    anterior = calcular_participacion_voto_exit(elecciones_por_anio_nivel, nivel, anio_t_menos_1)
    if actual is None or anterior is None:
        return None
    if actual.voto_exit_total_pct is None or anterior.voto_exit_total_pct is None:
        return None
    return actual.voto_exit_total_pct - anterior.voto_exit_total_pct


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
