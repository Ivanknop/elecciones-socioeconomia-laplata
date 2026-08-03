"""Cuadros de votos por localidad de La Plata, agregando los resultados por
circuito ya existentes en `data/distrito/<anio>/<nivel>/<etapa>/circuito_<nivel>.json`.

Uso:
    python -m analisis.cuadros_por_localidad --anio 2023 --nivel intendente
    python -m analisis.cuadros_por_localidad                    # todo lo disponible
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from analisis.cuadros_anualizados import NIVELES_POR_ANIO
from analisis.graficos import IDEOLOGIAS
from electoral.localidades import (
    NIVEL_OFICIAL,
    NIVEL_PERIODISTICO,
    agrupar_resultados_por_localidad,
    cargar_crosswalk,
)

ETAPAS = ["generales", "paso", "balotaje"]

CROSSWALK_PATH = "data/fuentes_extra/circuito_localidad.csv"
AUDITORIA_PATH = "data/fuentes_extra/AUDITORIA_DISCREPANCIAS.md"

COLUMNA_TOTAL = "votos"


def _clasificar_no_positivo(nombre_categoria: str) -> str:
    """Blanco y nulo son votos de gente que fue a votar y deliberadamente no eligió ninguna
    agrupación.
    """
    clave = nombre_categoria.upper()
    if "BLANCO" in clave or "NULO" in clave:
        return "blanco_nulo"
    return "otros"


def _votos_por_circuito(contenido: dict) -> dict[str, dict[str, float]]:
    """Ninguna de las claves de `circuito["otros"]` participa del eje
    izquierda-derecha que sí aplica a `positivos`, pero no se suman todas
    juntas: `blanco_nulo` (gente que votó y no eligió agrupación) queda
    separada de `otros`.
    """
    resultados = {}
    for circuito_id, circuito in contenido["circuitos"].items():
        fila = {ideologia: 0 for ideologia in IDEOLOGIAS.values()}
        for info in circuito["positivos"].values():
            fila[IDEOLOGIAS[info["campo_ideologico"]]] += info["votos"]
        fila["blanco_nulo"] = 0
        fila["otros"] = 0
        for categoria, votos in circuito["otros"].items():
            fila[_clasificar_no_positivo(categoria)] += votos
        fila[COLUMNA_TOTAL] = sum(v for k, v in fila.items() if k != COLUMNA_TOTAL)
        fila["ausentismo"] = circuito["electores"] - fila[COLUMNA_TOTAL]
        resultados[circuito_id] = fila
    return resultados


def generar_cuadro_localidad(
    data_dir: Path | str,
    salida_dir: Path | str,
    anio: int,
    nivel: str,
    etapa: str,
    crosswalk_path: Path | str = CROSSWALK_PATH,
) -> Path | None:
    circuito_json = Path(data_dir) / str(anio) / nivel / etapa / f"circuito_{nivel}.json"
    if not circuito_json.exists():
        return None

    contenido = json.loads(circuito_json.read_text(encoding="utf-8"))
    resultados = _votos_por_circuito(contenido)
    crosswalk = cargar_crosswalk(crosswalk_path)

    agrupado, reporte = agrupar_resultados_por_localidad(
        resultados, crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_PERIODISTICO),
    )

    salida_dir = Path(salida_dir)
    salida_dir.mkdir(parents=True, exist_ok=True)
    salida = salida_dir / f"{anio}_{nivel}_{etapa}_localidad.csv"

    sin_determinar = ", ".join(reporte.circuitos_sin_determinar) or "(ninguno)"
    encabezado = "\n".join([
        f"# Cuadro de votos por localidad -- La Plata, {nivel} {etapa} {anio}",
        f"# Fuente de votos: {circuito_json.as_posix()}",
        f"# Crosswalk circuito->localidad: {crosswalk_path} (niveles: {NIVEL_OFICIAL} + {NIVEL_PERIODISTICO}, {NIVEL_OFICIAL} prevalece)",
        f"# Cobertura circuitos: {reporte.circuitos_agrupados}/{reporte.circuitos_totales} ({reporte.porcentaje_circuitos:.1f}%)",
        f"# Cobertura votos: {reporte.votos_agrupados:,.0f}/{reporte.votos_totales:,.0f} ({reporte.porcentaje_votos:.1f}%)",
        "# Columna blanco_nulo: votos en blanco + nulos",
        "# Columna ausentismo: electores (padron) - votos (positivos + blanco_nulo + otros)",
        f"# Circuitos sin determinar: {sin_determinar}",
        f"# Confiabilidad de la clasificación por localidad: ver {AUDITORIA_PATH}",
    ])
    with salida.open("w", encoding="utf-8", newline="") as f:
        f.write(encabezado + "\n")
        agrupado.to_csv(f, index=False)

    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, help="si se omite, corre todos los años disponibles")
    parser.add_argument("--nivel", help="si se omite, corre todos los niveles disputados ese año")
    parser.add_argument("--data-dir", default="data/distrito")
    parser.add_argument("--salida-dir", default="data/por_localidad")
    args = parser.parse_args()

    anios = [args.anio] if args.anio else sorted(NIVELES_POR_ANIO)
    generados = []
    for anio in anios:
        niveles = [args.nivel] if args.nivel else NIVELES_POR_ANIO.get(anio, [])
        for nivel in niveles:
            for etapa in ETAPAS:
                salida = generar_cuadro_localidad(args.data_dir, args.salida_dir, anio, nivel, etapa)
                if salida:
                    generados.append(salida)
                    print(f"{anio} {nivel} {etapa} -> {salida}")

    if not generados:
        print("sin datos para los filtros pedidos")


if __name__ == "__main__":
    main()
