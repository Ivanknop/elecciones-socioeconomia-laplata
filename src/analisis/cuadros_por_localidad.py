"""Cuadros de votos por localidad de La Plata, agregando los resultados por
circuito ya existentes en `data/<anio>/<nivel>/<etapa>/circuito_<nivel>.json`
(la misma fuente que usa el resto del pipeline electoral -- no se consulta la
API ni se traen datos de otro lado) con el crosswalk circuito -> localidad de
`data/fuentes_extras/circuito_localidad.csv`.

Usa los dos niveles de cobertura juntos (`NIVEL_OFICIAL` + `NIVEL_PERIODISTICO`,
oficial prevaleciendo), ver `electoral.localidades`. Cada cuadro generado:

- reporta la cobertura de circuitos y de votos lograda (como comentario `#`
  al inicio del CSV, además de estar implícita en la fila `SIN_DETERMINAR`);
- incluye siempre la fila `SIN_DETERMINAR`, nunca oculta ni redistribuida;
- referencia `data/fuentes_extras/AUDITORIA_DISCREPANCIAS.md` para que quien
  lea el cuadro pueda evaluar qué tan sólida es la localidad de cada fila.

Solo se procesan los (año, nivel, etapa) para los que ya existe el
`circuito_<nivel>.json` derivado por el notebook 04 -- hoy eso es únicamente
`generales`; `paso`/`balotaje` no tienen ese derivado en el repo (ver
CLAUDE.md) y se omiten en silencio, igual que hace `cuadros_anualizados.py`
con los niveles no disputados en un año dado.

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

CROSSWALK_PATH = "data/fuentes_extras/circuito_localidad.csv"
AUDITORIA_PATH = "data/fuentes_extras/AUDITORIA_DISCREPANCIAS.md"

COLUMNA_TOTAL = "votos"


def _votos_por_circuito(contenido: dict) -> dict[str, dict[str, float]]:
    """`circuito["otros"]` (blanco/nulo/impugnado/recurrido/comando) no
    participa del eje izquierda-derecha que sí aplica a `positivos`, así que
    se suma entera en una sola columna "otros". Se suman **todas** sus claves
    sin filtrar por nombre a propósito: la API nombra esas categorías
    distinto según el año (p.ej. "NULO" en 2019 vs. "NULOS" en 2021), y una
    lista fija de nombres conocidos pierde votos en silencio para el año que
    no coincide.
    """
    resultados = {}
    for circuito_id, circuito in contenido["circuitos"].items():
        fila = {ideologia: 0 for ideologia in IDEOLOGIAS.values()}
        for info in circuito["positivos"].values():
            fila[IDEOLOGIAS[info["campo_ideologico"]]] += info["votos"]
        fila["otros"] = sum(circuito["otros"].values())
        fila[COLUMNA_TOTAL] = sum(fila.values())
        resultados[circuito_id] = fila
    return resultados


def generar_cuadro_localidad(
    data_dir: Path | str,
    graficos_dir: Path | str,
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

    salida_dir = Path(graficos_dir) / "cuadros_por_localidad"
    salida_dir.mkdir(parents=True, exist_ok=True)
    salida = salida_dir / f"{anio}_{nivel}_{etapa}_localidad.csv"

    sin_determinar = ", ".join(reporte.circuitos_sin_determinar) or "(ninguno)"
    encabezado = "\n".join([
        f"# Cuadro de votos por localidad -- La Plata, {nivel} {etapa} {anio}",
        f"# Fuente de votos: {circuito_json.as_posix()}",
        f"# Crosswalk circuito->localidad: {crosswalk_path} (niveles: {NIVEL_OFICIAL} + {NIVEL_PERIODISTICO}, {NIVEL_OFICIAL} prevalece)",
        f"# Cobertura circuitos: {reporte.circuitos_agrupados}/{reporte.circuitos_totales} ({reporte.porcentaje_circuitos:.1f}%)",
        f"# Cobertura votos: {reporte.votos_agrupados:,.0f}/{reporte.votos_totales:,.0f} ({reporte.porcentaje_votos:.1f}%)",
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
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--graficos-dir", default="graficos")
    args = parser.parse_args()

    anios = [args.anio] if args.anio else sorted(NIVELES_POR_ANIO)
    generados = []
    for anio in anios:
        niveles = [args.nivel] if args.nivel else NIVELES_POR_ANIO.get(anio, [])
        for nivel in niveles:
            for etapa in ETAPAS:
                salida = generar_cuadro_localidad(args.data_dir, args.graficos_dir, anio, nivel, etapa)
                if salida:
                    generados.append(salida)
                    print(f"{anio} {nivel} {etapa} -> {salida}")

    if not generados:
        print("sin datos para los filtros pedidos")


if __name__ == "__main__":
    main()
