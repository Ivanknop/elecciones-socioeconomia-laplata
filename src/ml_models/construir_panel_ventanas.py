"""Orquestador final -- Fase 4 del panel temporal de ventanas electorales:
une `ventanas.csv` + `resultado_distrito.csv`/`voto_partido_distrito.csv`/
`oficialismo_por_nivel.csv` + los features de `features_ventana.py` en
`data/tfi_data/panel_ventanas.csv`, 31 filas (12 municipal + 12
provincial + 7 nacional).

Uso:
    PYTHONPATH=src python -m ml_models.construir_panel_ventanas
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from datetime import date

from constantes import (
    CALENDARIO_ELECTORAL_PATH,
    ELECCIONES_RESUMEN_PATH,
    OFICIALISMO_POR_NIVEL_PATH,
    PANEL_VENTANAS_PATH,
    REGISTRO_VARIABLES_PATH,
    RESULTADO_DISTRITO_PATH,
    SERIES_ECONOMICAS_MENSUALES_PATH,
    VENTANAS_PATH,
    VOTO_PARTIDO_DISTRITO_PATH,
    CLASIFICACION_IDEOLOGICA_PATH,
)
from ml_models.construir_calendario import FilaCalendario, _nivel_csv_del_cargo
from ml_models.construir_elecciones_resumen import (
    FilaEleccion,
    calcular_cobertura_minima,
    calcular_delta_dispersion,
    cargar_elecciones,
)
from ml_models.construir_resultado_distrito import (
    FilaResultadoDistrito,
    FilaVotoPartido,
    _cargo_de_eleccion,
    calcular_delta_posicion_ideologica,
    calcular_delta_v,
    calcular_distancia_oficialismo_alternativa,
)
from ml_models.cargar_series_economicas import FilaRegistroVariable, cargar_registro
from ml_models.features_ventana import calcular_features_interventana_variable, calcular_features_ventana_variable


def clasificar_cuadrante_desplazamiento(delta_economico: float | None, delta_progresismo: float | None) -> str | None:
    # Mismo signo que las etiquetas de analisis.vparty_cuadrantes: econ>0=derecha, prog>0=progresista.
    if delta_economico is None or delta_progresismo is None:
        return None
    if delta_economico == 0 or delta_progresismo == 0:
        return None
    lado_economico = "derecha" if delta_economico > 0 else "izquierda"
    lado_progresismo = "progresista" if delta_progresismo > 0 else "conservador"
    return f"{lado_economico}_{lado_progresismo}"


def _leer_dicts(path: Path | str) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _cargar_ventanas(path: Path | str) -> list[dict]:
    filas = _leer_dicts(path)
    for f in filas:
        f["anio_t"] = int(f["anio_t"])
        f["anio_t_menos_1"] = int(f["anio_t_menos_1"])
        f["anio_t_menos_2"] = int(f["anio_t_menos_2"]) if f["anio_t_menos_2"] else None
        f["fecha_inicio_vl"] = f["fecha_inicio_vl"] or None
    return filas


def _cargar_series_mensuales(path: Path | str, registro: list[FilaRegistroVariable]) -> dict[str, dict[date, float | None]]:
    filas = _leer_dicts(path)
    series: dict[str, dict[date, float | None]] = {var.id_variable: {} for var in registro}
    for fila in filas:
        mes = date.fromisoformat(fila["fecha"])
        for var in registro:
            crudo = fila.get(var.id_variable, "")
            series[var.id_variable][mes] = float(crudo) if crudo not in ("", None) else None
    return series


def _cargar_resultado_distrito(path: Path | str) -> dict[tuple[int, str], FilaResultadoDistrito]:
    filas = _leer_dicts(path)
    resultado = {}
    for r in filas:
        resultado[(int(r["anio"]), r["nivel"])] = FilaResultadoDistrito(
            anio=int(r["anio"]),
            nivel=r["nivel"],
            votos_validos=int(r["votos_validos"]) if r["votos_validos"] else None,
            votos_blanco=int(r["votos_blanco"]) if r["votos_blanco"] else None,
            participacion=float(r["participacion"]) if r["participacion"] else None,
            gana_oficialismo=(r["gana_oficialismo"] == "True") if r["gana_oficialismo"] else None,
            share_oficialismo=float(r["share_oficialismo"]) if r["share_oficialismo"] else None,
            resultado_disponible=r["resultado_disponible"] == "True",
        )
    return resultado


def _cargar_voto_partido(path: Path | str) -> tuple[list[FilaVotoPartido], dict[tuple[int, str], list[FilaVotoPartido]]]:
    filas = _leer_dicts(path)
    voto_partido = [
        FilaVotoPartido(int(r["anio"]), r["nivel"], r["id_agrupacion"], r["agrupacion"], int(r["votos"]), float(r["share"]))
        for r in filas
    ]
    por_anio_nivel: dict[tuple[int, str], list[FilaVotoPartido]] = {}
    for v in voto_partido:
        por_anio_nivel.setdefault((v.anio, v.nivel), []).append(v)
    return voto_partido, por_anio_nivel


def _cargar_oficialismo_por_nivel(path: Path | str) -> dict[tuple[int, str], dict]:
    return {(int(r["anio"]), r["nivel"]): r for r in _leer_dicts(path)}


def _construir_posiciones(
    voto_partido_por_anio_nivel: dict[tuple[int, str], list[FilaVotoPartido]],
    calendario: dict[tuple[int, str], str],
    clasificacion: dict[tuple[str, str, str], dict],
) -> dict[tuple[int, str, str], float]:
    """(año, nivel, AGRUPACION en mayúsculas) -> `vparty_economico`, para
    toda agrupación que compitió ese año y tiene score conocido -- nunca
    se le atribuye al distrito la ideología de una sola agrupación (la
    ganadora), se guarda el universo entero para ponderar después."""
    posiciones: dict[tuple[int, str, str], float] = {}
    for (anio, nivel), filas in voto_partido_por_anio_nivel.items():
        tipo_eleccion = calendario.get((anio, nivel))
        if tipo_eleccion is None:
            continue
        cargo = _cargo_de_eleccion(nivel, tipo_eleccion)
        nivel_csv = _nivel_csv_del_cargo(nivel, cargo)
        for v in filas:
            fila_clas = clasificacion.get((str(anio), v.agrupacion, nivel_csv))
            if fila_clas is None or not fila_clas.get("vparty_economico"):
                continue
            posiciones[(anio, nivel, v.agrupacion.strip().upper())] = float(fila_clas["vparty_economico"])
    return posiciones


def construir_panel(
    ventanas: list[dict],
    registro: list[FilaRegistroVariable],
    series_mensuales: dict[str, dict[date, float | None]],
    resultado_por_anio_nivel: dict[tuple[int, str], FilaResultadoDistrito],
    voto_partido_por_anio_nivel: dict[tuple[int, str], list[FilaVotoPartido]],
    oficialismo_por_nivel: dict[tuple[int, str], dict],
    posiciones: dict[tuple[int, str, str], float],
    elecciones_por_anio_nivel: dict[tuple[int, str], FilaEleccion],
) -> list[dict]:
    """Pura -- todo ya cargado en memoria."""
    por_nivel: dict[str, list[dict]] = {}
    for v in ventanas:
        por_nivel.setdefault(v["nivel"], []).append(v)
    for nivel in por_nivel:
        por_nivel[nivel].sort(key=lambda v: v["anio_t"])

    filas_panel = []
    features_vc_previas: dict[tuple[str, str], dict] = {}  # (nivel, id_variable) -> features _vc de la transición anterior

    for nivel, ventanas_nivel in por_nivel.items():
        for v in ventanas_nivel:
            fila: dict = {
                "id_transicion": v["id_transicion"],
                "nivel": nivel,
                "anio_t": v["anio_t"],
                "anio_t_menos_1": v["anio_t_menos_1"],
                "anio_t_menos_2": v["anio_t_menos_2"],
                "fecha_inicio_vc": v["fecha_inicio_vc"],
                "fecha_fin_vc": v["fecha_fin_vc"],
                "fecha_inicio_vl": v["fecha_inicio_vl"],
                "tipo_eleccion_t": v["tipo_eleccion_t"],
                "tipo_eleccion_t_menos_1": v["tipo_eleccion_t_menos_1"],
            }

            resultado_t = resultado_por_anio_nivel.get((v["anio_t"], nivel))
            resultado_t1 = resultado_por_anio_nivel.get((v["anio_t_menos_1"], nivel))
            fila["resultado_disponible"] = bool(
                resultado_t and resultado_t1 and resultado_t.resultado_disponible and resultado_t1.resultado_disponible
            )
            fila["delta_v"] = calcular_delta_v(resultado_por_anio_nivel, nivel, v["anio_t"], v["anio_t_menos_1"])
            fila["gana_oficialismo"] = resultado_t.gana_oficialismo if resultado_t else None
            fila["share_oficialismo"] = resultado_t.share_oficialismo if resultado_t else None

            of_t = oficialismo_por_nivel.get((v["anio_t"], nivel))
            fila["agrupacion_oficialismo"] = of_t["agrupacion_oficialismo"] if of_t else ""
            fila["continuidad_oficialismo"] = of_t["continuidad_oficialismo"] if of_t else ""

            fila["delta_posicion_ideologica"] = calcular_delta_posicion_ideologica(
                voto_partido_por_anio_nivel, posiciones, nivel, v["anio_t"], v["anio_t_menos_1"]
            )
            posiciones_t = {
                agr: score for (anio, niv, agr), score in posiciones.items() if anio == v["anio_t"] and niv == nivel
            }
            # DEPRECADA (D18): matchea oficialismo por nombre, no por identidad
            # -- 17/31 filas vacías por eso. Sucedida por distancias_ideologicas.csv.
            fila["distancia_oficialismo_alternativa"] = (
                calcular_distancia_oficialismo_alternativa(
                    voto_partido_por_anio_nivel.get((v["anio_t"], nivel), []), posiciones_t, of_t["agrupacion_oficialismo"]
                )
                if of_t
                else None
            )

            delta_dispersion_economico_mu = calcular_delta_dispersion(
                elecciones_por_anio_nivel, nivel, v["anio_t"], v["anio_t_menos_1"], "economico"
            )
            delta_dispersion_progresismo_mu = calcular_delta_dispersion(
                elecciones_por_anio_nivel, nivel, v["anio_t"], v["anio_t_menos_1"], "progresismo"
            )
            fila["delta_dispersion_economico_mu"] = delta_dispersion_economico_mu
            fila["delta_dispersion_progresismo_mu"] = delta_dispersion_progresismo_mu
            fila["delta_sigma2_economico"] = calcular_delta_dispersion(
                elecciones_por_anio_nivel, nivel, v["anio_t"], v["anio_t_menos_1"], "economico", estadistico="sigma2"
            )
            fila["delta_sigma2_progresismo"] = calcular_delta_dispersion(
                elecciones_por_anio_nivel, nivel, v["anio_t"], v["anio_t_menos_1"], "progresismo", estadistico="sigma2"
            )
            fila["magnitud_desplazamiento_ideologico"] = (
                math.sqrt(delta_dispersion_economico_mu**2 + delta_dispersion_progresismo_mu**2)
                if delta_dispersion_economico_mu is not None and delta_dispersion_progresismo_mu is not None
                else None
            )
            fila["cuadrante_desplazamiento"] = clasificar_cuadrante_desplazamiento(
                delta_dispersion_economico_mu, delta_dispersion_progresismo_mu
            )
            fila["dispersion_cobertura_share_min"] = calcular_cobertura_minima(
                elecciones_por_anio_nivel, nivel, v["anio_t"], v["anio_t_menos_1"]
            )

            for var in registro:
                serie = series_mensuales.get(var.id_variable, {})
                features_vc_vl = calcular_features_ventana_variable(
                    var, serie, v["fecha_inicio_vc"], v["fecha_fin_vc"], v["fecha_inicio_vl"]
                )
                fila.update(features_vc_vl)

                anterior = features_vc_previas.get((nivel, var.id_variable))
                fila.update(calcular_features_interventana_variable(var, features_vc_vl, anterior))
                features_vc_previas[(nivel, var.id_variable)] = features_vc_vl

            filas_panel.append(fila)

    return filas_panel


def generar_csv(
    ventanas_path: Path | str = VENTANAS_PATH,
    registro_path: Path | str = REGISTRO_VARIABLES_PATH,
    series_path: Path | str = SERIES_ECONOMICAS_MENSUALES_PATH,
    resultado_path: Path | str = RESULTADO_DISTRITO_PATH,
    voto_partido_path: Path | str = VOTO_PARTIDO_DISTRITO_PATH,
    oficialismo_path: Path | str = OFICIALISMO_POR_NIVEL_PATH,
    calendario_path: Path | str = CALENDARIO_ELECTORAL_PATH,
    clasificacion_path: Path | str = CLASIFICACION_IDEOLOGICA_PATH,
    elecciones_path: Path | str = ELECCIONES_RESUMEN_PATH,
    destino: Path | str = PANEL_VENTANAS_PATH,
) -> Path:
    ventanas = _cargar_ventanas(ventanas_path)
    registro = cargar_registro(registro_path)
    series_mensuales = _cargar_series_mensuales(series_path, registro)
    resultado_por_anio_nivel = _cargar_resultado_distrito(resultado_path)
    voto_partido, voto_partido_por_anio_nivel = _cargar_voto_partido(voto_partido_path)
    oficialismo_por_nivel = _cargar_oficialismo_por_nivel(oficialismo_path)
    elecciones_por_anio_nivel = cargar_elecciones(elecciones_path)

    calendario_tipo = {(int(r["anio"]), r["nivel"]): r["tipo_eleccion"] for r in _leer_dicts(calendario_path)}
    with Path(clasificacion_path).open(encoding="utf-8", newline="") as f:
        clasificacion = {(r["anio"], r["agrupacion"], r["nivel"]): r for r in csv.DictReader(f)}
    posiciones = _construir_posiciones(voto_partido_por_anio_nivel, calendario_tipo, clasificacion)

    filas = construir_panel(
        ventanas, registro, series_mensuales, resultado_por_anio_nivel, voto_partido_por_anio_nivel,
        oficialismo_por_nivel, posiciones, elecciones_por_anio_nivel,
    )

    columnas_id = [
        "id_transicion", "nivel", "anio_t", "anio_t_menos_1", "anio_t_menos_2",
        "fecha_inicio_vc", "fecha_fin_vc", "fecha_inicio_vl", "tipo_eleccion_t", "tipo_eleccion_t_menos_1",
        "resultado_disponible", "delta_v", "gana_oficialismo", "share_oficialismo",
        "agrupacion_oficialismo", "continuidad_oficialismo",
        "delta_posicion_ideologica", "distancia_oficialismo_alternativa",
        "delta_dispersion_economico_mu", "delta_dispersion_progresismo_mu",
        "delta_sigma2_economico", "delta_sigma2_progresismo",
        "magnitud_desplazamiento_ideologico", "cuadrante_desplazamiento",
        "dispersion_cobertura_share_min",
    ]
    columnas_features: list[str] = []
    vistas = set()
    for fila in filas:
        for col in fila:
            if col not in columnas_id and col not in vistas:
                vistas.add(col)
                columnas_features.append(col)
    columnas = columnas_id + sorted(columnas_features)

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    with destino_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for fila in filas:
            writer.writerow({col: (fila.get(col) if fila.get(col) is not None else "") for col in columnas})
    return destino_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    args = parser.parse_args()
    destino = generar_csv()
    print(destino)


if __name__ == "__main__":
    main()
