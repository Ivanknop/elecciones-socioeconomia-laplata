"""Distancias ideológicas por fuerza viable -- grano (nivel, año,
agrupación), para H2/H3 (ver `docs/decisiones_metodologicas.md` D18 y
`docs/especificaciones/especificacion_panel_temporal.md` "Diccionario de columnas de
distancias_ideologicas.csv").

Uso:
    PYTHONPATH=src python -m ml_models.construir_distancias_ideologicas
"""
from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

from constantes import (
    CALENDARIO_ELECTORAL_PATH,
    DATA_DISTRITO_DIR,
    DISTANCIAS_IDEOLOGICAS_PATH,
    ELECCIONES_DIR,
    OFICIALISMOS_PATH,
    OFICIALISMO_POR_NIVEL_PATH,
)
from ml_models.construir_calendario import FilaCalendario, _cargar_oficialismos
from ml_models.construir_elecciones_resumen import UMBRAL_VIABLE, _cargar_calendario, _totales_y_vparty_desde_tfi
from ml_models.construir_resultado_distrito import (
    ALIAS_LISTA_OFICIALISMO,
    FilaVotoPartido,
    _cargar_oficialismo_por_nivel,
    _entrada_oficialismo,
    construir_voto_partido_distrito,
)


@dataclass(frozen=True)
class FilaDistanciaIdeologica:
    nivel: str
    anio: int
    agrupacion: str
    votos: int
    share: float
    es_oficialismo: bool
    vparty_economico: float | None
    vparty_progresismo: float | None
    distancia_economico_al_oficialismo: float | None
    distancia_progresismo_al_oficialismo: float | None
    distancia_euclidea_al_oficialismo: float | None


def construir_distancias_eleccion(
    del_anio: list[FilaVotoPartido],
    vparty: dict[str, tuple[float, float]],
    of: dict | None,
    fila_of_curada: dict | None,
    alias_lista: str | None,
) -> list[FilaDistanciaIdeologica]:
    viables = [v for v in del_anio if v.share >= UMBRAL_VIABLE]
    if not viables:
        return []

    _, entrada_oficialismo = _entrada_oficialismo(del_anio, of, fila_of_curada, alias_lista)
    score_oficialismo = (
        vparty.get(entrada_oficialismo.agrupacion.strip().upper()) if entrada_oficialismo is not None else None
    )

    filas = []
    for v in viables:
        es_oficialismo = v is entrada_oficialismo  # identidad, no nombre -- D18
        score = vparty.get(v.agrupacion.strip().upper())

        if es_oficialismo:
            d_econ = d_prog = d_eucl = 0.0
        elif score is None or score_oficialismo is None:
            d_econ = d_prog = d_eucl = None
        else:
            d_econ = score[0] - score_oficialismo[0]
            d_prog = score[1] - score_oficialismo[1]
            d_eucl = math.sqrt(d_econ**2 + d_prog**2)

        filas.append(
            FilaDistanciaIdeologica(
                nivel=v.nivel,
                anio=v.anio,
                agrupacion=v.agrupacion,
                votos=v.votos,
                share=v.share,
                es_oficialismo=es_oficialismo,
                vparty_economico=score[0] if score is not None else None,
                vparty_progresismo=score[1] if score is not None else None,
                distancia_economico_al_oficialismo=d_econ,
                distancia_progresismo_al_oficialismo=d_prog,
                distancia_euclidea_al_oficialismo=d_eucl,
            )
        )
    return filas


def construir_distancias(
    calendario: list[FilaCalendario],
    voto_partido: list[FilaVotoPartido],
    oficialismo_por_nivel: dict[tuple[int, str], dict],
    oficialismos_curados: dict[tuple[int, str], dict],
    elecciones_dir: Path | str = ELECCIONES_DIR,
) -> list[FilaDistanciaIdeologica]:
    voto_partido_por_anio_nivel: dict[tuple[int, str], list[FilaVotoPartido]] = {}
    for v in voto_partido:
        voto_partido_por_anio_nivel.setdefault((v.anio, v.nivel), []).append(v)

    filas = []
    for fc in calendario:
        del_anio = voto_partido_por_anio_nivel.get((fc.anio, fc.nivel), [])
        _, vparty = _totales_y_vparty_desde_tfi(Path(elecciones_dir) / f"{fc.anio}_{fc.nivel}.csv")
        filas.extend(
            construir_distancias_eleccion(
                del_anio,
                vparty,
                oficialismo_por_nivel.get((fc.anio, fc.nivel)),
                oficialismos_curados.get((fc.anio, fc.nivel)),
                ALIAS_LISTA_OFICIALISMO.get((fc.anio, fc.nivel)),
            )
        )
    return filas


_COLUMNAS = [
    "nivel",
    "anio",
    "agrupacion",
    "votos",
    "share",
    "es_oficialismo",
    "vparty_economico",
    "vparty_progresismo",
    "distancia_economico_al_oficialismo",
    "distancia_progresismo_al_oficialismo",
    "distancia_euclidea_al_oficialismo",
]


def _escribir_csv(path: Path | str, filas: list[FilaDistanciaIdeologica]) -> Path:
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(_COLUMNAS)
        for fila in filas:
            writer.writerow([getattr(fila, col) if getattr(fila, col) is not None else "" for col in _COLUMNAS])
    return destino


def generar_csv(
    calendario_path: Path | str = CALENDARIO_ELECTORAL_PATH,
    oficialismo_path: Path | str = OFICIALISMO_POR_NIVEL_PATH,
    oficialismos_curado_path: Path | str = OFICIALISMOS_PATH,
    data_dir: Path | str = DATA_DISTRITO_DIR,
    elecciones_dir: Path | str = ELECCIONES_DIR,
    destino: Path | str = DISTANCIAS_IDEOLOGICAS_PATH,
) -> Path:
    calendario = _cargar_calendario(calendario_path)
    voto_partido = construir_voto_partido_distrito(calendario, data_dir, elecciones_dir)
    oficialismo_por_nivel = _cargar_oficialismo_por_nivel(oficialismo_path)
    oficialismos_curados = _cargar_oficialismos(oficialismos_curado_path)

    filas = construir_distancias(calendario, voto_partido, oficialismo_por_nivel, oficialismos_curados, elecciones_dir)
    return _escribir_csv(destino, filas)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    print(generar_csv())


if __name__ == "__main__":
    main()
