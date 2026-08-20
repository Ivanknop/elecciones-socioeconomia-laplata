"""Cuadro comparativo Municipio / Provincia / Nación por agrupación (+
blanco+nulo), un Markdown por año, a partir de
`totales_por_lista.resultado_total_con_blanco_nulo`.

Compara el % de cada agrupación en los tres cargos disputados el mismo año
(ej. 2019: Intendente=Municipio, Gobernador=Provincia, Presidente=Nación).
Dentro de un mismo año la agrupación corre bajo el mismo nombre en los tres
cargos

Uso:
    PYTHONPATH=src python -m analisis.comparativo_nivel --anio 2019
    PYTHONPATH=src python -m analisis.comparativo_nivel               # todos los años disponibles
"""
from __future__ import annotations

import argparse
from pathlib import Path

from analisis.cuadros_anualizados import NIVELES_POR_ANIO, _niveles_disponibles
from analisis.totales_por_lista import _NOMBRE_BLANCO_NULO, resultado_total_con_blanco_nulo
from constantes import DATA_DISTRITO_DIR

CATEGORIA_NIVEL = {
    "presidente": "Nación",
    "nacional": "Nación",
    "gobernador": "Provincia",
    "provincial": "Provincia",
    "intendente": "Municipio",
    "municipal": "Municipio",
}

COLUMNAS = ["Municipio", "Provincia", "Nación"]


def _porcentajes_por_categoria(data_dir: Path | str, anio: int, niveles: list[str]) -> dict[str, dict[str, float]]:
    """{categoria: {agrupacion: votos_porcentaje}} para las categorías
    disponibles ese año (Municipio/Provincia/Nación)."""
    por_categoria = {}
    for nivel in niveles:
        categoria = CATEGORIA_NIVEL[nivel]
        totales = resultado_total_con_blanco_nulo(data_dir, anio, nivel)
        por_categoria[categoria] = {v.nombre_agrupacion: v.votos_porcentaje for v in totales}
    return por_categoria


def _fmt_pct(v: float | None) -> str:
    return f"{v:.1f}%" if v is not None else "—"


def _fmt_dif(a: float | None, b: float | None) -> str:
    return f"{a - b:+.1f} pp" if a is not None and b is not None else "—"


def tabla_comparativa(data_dir: Path | str, anio: int) -> str | None:
    """Devuelve el Markdown del cuadro, o `None` si ese año no tiene los
    tres niveles disputados (nada que comparar)."""
    niveles = _niveles_disponibles(data_dir, anio)
    categorias_presentes = {CATEGORIA_NIVEL[n] for n in niveles}
    if len(categorias_presentes) < len(COLUMNAS):
        return None

    por_categoria = _porcentajes_por_categoria(data_dir, anio, niveles)

    agrupaciones = sorted(
        {nombre for pct in por_categoria.values() for nombre in pct if nombre != _NOMBRE_BLANCO_NULO},
        key=lambda nombre: por_categoria["Nación"].get(nombre, -1),
        reverse=True,
    )
    filas = [*agrupaciones, _NOMBRE_BLANCO_NULO]  # blanco+nulo siempre al final, no ordenado por voto

    encabezado = ["Agrupación", *COLUMNAS, "Dif Mun-Prov", "Dif Mun-Nac", "Dif Prov-Nac"]
    lineas = [
        f"# Comparativo Municipio / Provincia / Nación — La Plata {anio}",
        "",
        f"% sobre agrupaciones + blanco/nulo de cada categoría por separado "
        f"(`totales_por_lista.resultado_total_con_blanco_nulo`); no incluye ausentismo. "
        f"Diferencias en puntos porcentuales (pp).",
        "",
        "| " + " | ".join(encabezado) + " |",
        "|" + "---|" * len(encabezado),
    ]

    for nombre in filas:
        mun = por_categoria.get("Municipio", {}).get(nombre)
        prov = por_categoria.get("Provincia", {}).get(nombre)
        nac = por_categoria.get("Nación", {}).get(nombre)
        fila = [
            nombre, _fmt_pct(mun), _fmt_pct(prov), _fmt_pct(nac),
            _fmt_dif(mun, prov), _fmt_dif(mun, nac), _fmt_dif(prov, nac),
        ]
        lineas.append("| " + " | ".join(fila) + " |")

    return "\n".join(lineas) + "\n"


def generar_comparativo_nivel(data_dir: Path | str, salida_dir: Path | str, anio: int) -> Path | None:
    tabla = tabla_comparativa(data_dir, anio)
    if tabla is None:
        return None

    salida = Path(salida_dir)
    salida.mkdir(parents=True, exist_ok=True)
    destino = salida / f"{anio}.md"
    destino.write_text(tabla, encoding="utf-8")
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, help="si se omite, corre todos los años disponibles")
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    parser.add_argument("--salida-dir", default="graficos/distrito/totales_por_lista/comparativos_nivel")
    args = parser.parse_args()

    anios = [args.anio] if args.anio else sorted(NIVELES_POR_ANIO)
    generados = []
    for anio in anios:
        destino = generar_comparativo_nivel(args.data_dir, args.salida_dir, anio)
        if destino:
            generados.append(destino)
            print(f"{anio} -> {destino}")
        else:
            print(f"{anio}: un solo cargo disputado ese año, sin comparación posible -- se omite")

    if not generados:
        print("sin datos para los filtros pedidos")


if __name__ == "__main__":
    main()
