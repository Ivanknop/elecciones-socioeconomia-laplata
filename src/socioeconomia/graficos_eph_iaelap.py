"""Gráficos de EPH Gran La Plata e IAELaP Partido de La Plata, a partir de
`data/socioeconomia/eph_gran_la_plata.csv` e `iaelap_la_plata*.csv` (ver
`notebooks/05_capa_socioeconomica.ipynb` y `notebooks/06_graficos_eph_iaelap.ipynb`).
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

_AZUL = "#2a78d6"
_NARANJA = "#eb6834"
_AGUA = "#1baf7a"
_ROJO = "#e34948"

_TRIMESTRE_ETIQUETA = {1: "T1", 2: "T2", 3: "T3", 4: "T4"}


def _leer_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _etiqueta_trimestre(anio: str, trimestre: str) -> str:
    return f"{anio}{_TRIMESTRE_ETIQUETA[int(trimestre)]}"


def _quitar_spines(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)


def graficar_desocupacion_informalidad(data_dir: Path | str, ax=None):
    """Desocupación e informalidad, EPH Gran La Plata, 2011-2025. Dos
    líneas sobre un único eje (ambas son %, comparables sin normalizar).
    """
    filas = _leer_csv(Path(data_dir) / "eph_gran_la_plata.csv")
    etiquetas = [_etiqueta_trimestre(f["anio"], f["trimestre"]) for f in filas]
    desocupacion = [float(f["tasa_desocupacion"]) * 100 for f in filas]
    informalidad = [float(f["tasa_informalidad"]) * 100 for f in filas]

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 4.5))
    x = range(len(filas))
    ax.plot(x, desocupacion, color=_AZUL, linewidth=2, marker="o", markersize=4, label="Desocupación")
    ax.plot(x, informalidad, color=_NARANJA, linewidth=2, marker="o", markersize=4, label="Informalidad")
    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels(etiquetas[::2], rotation=45, ha="right")
    ax.set_ylabel("%")
    ax.set_title("EPH Gran La Plata — desocupación e informalidad")
    _quitar_spines(ax)
    ax.legend(frameon=False)
    ax.figure.tight_layout()
    return ax.figure


def _graficar_series_eph(
    data_dir: Path | str,
    columnas: dict[str, str],
    colores: list[str],
    titulo: str,
    ylabel: str,
    escala_pct: bool = True,
    ax=None,
):
    """Helper compartido: N series de línea (`columnas` = {columna_csv: etiqueta})
    desde `eph_gran_la_plata.csv`, sobre un único eje. `colores` debe tener
    tantos elementos como `columnas` y venir ya validado 
    """
    filas = _leer_csv(Path(data_dir) / "eph_gran_la_plata.csv")
    etiquetas = [_etiqueta_trimestre(f["anio"], f["trimestre"]) for f in filas]
    x = range(len(filas))
    escala = 100 if escala_pct else 1

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 4.5))
    for (columna, etiqueta_serie), color in zip(columnas.items(), colores):
        valores = [float(f[columna]) * escala for f in filas]
        ax.plot(x, valores, color=color, linewidth=2, marker="o", markersize=4, label=etiqueta_serie)
    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels(etiquetas[::2], rotation=45, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(titulo)
    _quitar_spines(ax)
    if len(columnas) > 1:
        ax.legend(frameon=False)
    ax.figure.tight_layout()
    return ax.figure


def graficar_tasas_actividad_empleo(data_dir: Path | str, ax=None):
    """Tasa de actividad y tasa de empleo, EPH Gran La Plata, 2011-2025."""
    return _graficar_series_eph(
        data_dir,
        {"tasa_actividad": "Actividad", "tasa_empleo": "Empleo"},
        [_AZUL, _NARANJA],
        "EPH Gran La Plata — tasa de actividad y de empleo",
        "%",
        ax=ax,
    )


def graficar_calidad_empleo(data_dir: Path | str, ax=None):
    """% de asalariados con obra social/aguinaldo/vacaciones pagas, EPH Gran
    La Plata, 2011-2025 — calidad del empleo, no solo el binario formal/informal.
    """
    return _graficar_series_eph(
        data_dir,
        {
            "pct_con_obra_social": "Obra social",
            "pct_con_aguinaldo": "Aguinaldo",
            "pct_con_vacaciones_pagas": "Vacaciones pagas",
        },
        [_AZUL, _NARANJA, _AGUA],
        "EPH Gran La Plata — calidad del empleo asalariado",
        "% de asalariados",
        ax=ax,
    )


def graficar_cobertura_salud(data_dir: Path | str, ax=None):
    """% de la población sin cobertura de salud, EPH Gran La Plata, 2011-2025."""
    return _graficar_series_eph(
        data_dir,
        {"pct_sin_cobertura_salud": "Sin cobertura de salud"},
        [_ROJO],
        "EPH Gran La Plata — población sin cobertura de salud",
        "%",
        ax=ax,
    )


def graficar_educacion(data_dir: Path | str, ax=None):
    """% con secundario completo o más (25+) y tasa de asistencia escolar
    (5-24), EPH Gran La Plata, 2011-2025.
    """
    return _graficar_series_eph(
        data_dir,
        {
            "pct_secundario_completo_o_mas": "Secundario completo o más (25+)",
            "tasa_asistencia_escolar": "Asistencia escolar (5-24)",
        },
        [_AZUL, _AGUA],
        "EPH Gran La Plata — educación",
        "%",
        ax=ax,
    )


def graficar_hacinamiento(data_dir: Path | str, ax=None):
    """Personas por cuarto (hacinamiento medio de los hogares), EPH Gran La
    Plata, 2011-2025.
    """
    return _graficar_series_eph(
        data_dir,
        {"hacinamiento_medio": "Personas por cuarto"},
        [_NARANJA],
        "EPH Gran La Plata — hacinamiento medio de los hogares",
        "Personas por cuarto",
        escala_pct=False,
        ax=ax,
    )


def graficar_estrategias_subsistencia(data_dir: Path | str, ax=None):
    """% de hogares que recurrió a cada estrategia en los últimos 3 meses,
    EPH Gran La Plata, 2011-2025.
    """
    return _graficar_series_eph(
        data_dir,
        {
            "pct_hogares_ayuda_social_gobierno": "Ayuda social del gobierno",
            "pct_hogares_prestamo_bancario": "Préstamo bancario",
            "pct_hogares_vendio_pertenencias": "Vendió pertenencias",
        },
        [_AZUL, _NARANJA, _AGUA],
        "EPH Gran La Plata — estrategias de subsistencia del hogar",
        "% de hogares",
        ax=ax,
    )


def graficar_desocupacion(data_dir: Path | str, ax=None):
    """Tasa de desocupación, EPH Gran La Plata, 2011-2025 — serie general
    (población total), sin desagregar por sexo. Contraparte de
    `graficar_brecha_genero(data_dir, "tasa_desocupacion", ...)`, que abre
    este mismo indicador en varones/mujeres.
    """
    return _graficar_series_eph(
        data_dir,
        {"tasa_desocupacion": "Desocupación"},
        [_AZUL],
        "EPH Gran La Plata — tasa de desocupación",
        "%",
        ax=ax,
    )


def graficar_informalidad(data_dir: Path | str, ax=None):
    """Tasa de informalidad laboral, EPH Gran La Plata, 2011-2025 — serie
    general (población total), sin desagregar por sexo. Contraparte de
    `graficar_brecha_genero(data_dir, "tasa_informalidad", ...)`.
    """
    return _graficar_series_eph(
        data_dir,
        {"tasa_informalidad": "Informalidad"},
        [_NARANJA],
        "EPH Gran La Plata — informalidad laboral",
        "%",
        ax=ax,
    )


def graficar_actividad(data_dir: Path | str, ax=None):
    """Tasa de actividad, EPH Gran La Plata, 2011-2025 — serie general
    (población total), sin desagregar por sexo. Contraparte de
    `graficar_brecha_genero(data_dir, "tasa_actividad", ...)`.
    """
    return _graficar_series_eph(
        data_dir,
        {"tasa_actividad": "Actividad"},
        [_AZUL],
        "EPH Gran La Plata — tasa de actividad",
        "%",
        ax=ax,
    )


def graficar_brecha_genero(data_dir: Path | str, indicador: str, titulo: str, ax=None):
    """Un indicador del núcleo laboral (`tasa_actividad`, `tasa_empleo`,
    `tasa_desocupacion`, `tasa_informalidad`) para varones y mujeres,
    `eph_gran_la_plata_por_sexo.csv`, 2011-2025. `ingreso_ocupacion_principal_medio`
    también está disponible en ese CSV pero no es %, no usar `escala_pct` con eso.
    """
    filas = _leer_csv(Path(data_dir) / "eph_gran_la_plata_por_sexo.csv")
    trimestres = sorted({(f["anio"], f["trimestre"]) for f in filas}, key=lambda t: (int(t[0]), int(t[1])))
    etiquetas = [_etiqueta_trimestre(a, t) for a, t in trimestres]
    x = range(len(trimestres))

    por_sexo = {"varon": {}, "mujer": {}}
    for f in filas:
        por_sexo[f["sexo"]][(f["anio"], f["trimestre"])] = float(f[indicador])

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 4.5))
    for sexo, etiqueta_serie, color in (("varon", "Varones", _AZUL), ("mujer", "Mujeres", _NARANJA)):
        valores = [por_sexo[sexo][t] * 100 for t in trimestres]
        ax.plot(x, valores, color=color, linewidth=2, marker="o", markersize=4, label=etiqueta_serie)
    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels(etiquetas[::2], rotation=45, ha="right")
    ax.set_ylabel("%")
    ax.set_title(f"EPH Gran La Plata — {titulo}, por sexo")
    _quitar_spines(ax)
    ax.legend(frameon=False)
    ax.figure.tight_layout()
    return ax.figure


def graficar_desocupacion_por_edad(data_dir: Path | str):
    """Tasa de desocupación por tramo etario.
    """
    filas = _leer_csv(Path(data_dir) / "eph_gran_la_plata_por_edad.csv")
    tramos = ["10-24", "25-39", "40-59", "60+"]
    trimestres = sorted({(f["anio"], f["trimestre"]) for f in filas}, key=lambda t: (int(t[0]), int(t[1])))
    etiquetas = [_etiqueta_trimestre(a, t) for a, t in trimestres]
    x = range(len(trimestres))

    por_tramo = {tramo: {} for tramo in tramos}
    for f in filas:
        por_tramo[f["tramo_etario"]][(f["anio"], f["trimestre"])] = float(f["tasa_desocupacion"])

    fig, ejes = plt.subplots(2, 2, figsize=(13, 8), sharex=True, sharey=True)
    for tramo, ax in zip(tramos, ejes.flat):
        valores = [por_tramo[tramo][t] * 100 for t in trimestres]
        ax.plot(x, valores, color=_AZUL, linewidth=2)
        ax.set_xticks(list(x)[::4])
        ax.set_xticklabels(etiquetas[::4], rotation=45, ha="right", fontsize="small")
        ax.set_title(f"{tramo} años", fontsize="small")
        ax.set_ylabel("% desocupación")
        _quitar_spines(ax)
    fig.suptitle("EPH Gran La Plata — tasa de desocupación por tramo etario")
    fig.tight_layout()
    return fig


def graficar_iaelap_general(data_dir: Path | str, ax=None):
    """Variación % interanual del índice IAELaP, Partido de La Plata,
    2018T1-2025T4. Barras, un eje. No incluye el nivel del índice (2018=100)
    en el mismo gráfico.
    """
    filas = _leer_csv(Path(data_dir) / "iaelap_la_plata.csv")
    etiquetas = [_etiqueta_trimestre(f["anio"], f["trimestre"]) for f in filas]
    valores = [float(f["var_interanual_pct"]) if f["var_interanual_pct"] else None for f in filas]
    colores = [_AZUL if v is not None and v >= 0 else _ROJO for v in valores]
    valores_graf = [v if v is not None else 0 for v in valores]

    if ax is None:
        _, ax = plt.subplots(figsize=(13, 4.5))
    x = range(len(filas))
    ax.bar(x, valores_graf, color=colores, width=0.7)
    for i, v in enumerate(valores):
        if v is None:
            ax.text(i, 0, "s/d", ha="center", va="bottom", fontsize="x-small", color="gray", rotation=90)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels([etiquetas[i] for i in x][::2], rotation=45, ha="right")
    ax.set_ylabel("Var. % interanual")
    ax.set_title("IAELaP — Partido de La Plata, variación % interanual")
    _quitar_spines(ax)
    ax.figure.tight_layout()
    return ax.figure


def graficar_iaelap_sectorial(
    data_dir: Path | str, periodo_tipo: str, anio: int, trimestre: int | None = None, ax=None
):
    """Desagregación sectorial IAELaP para un período puntual (`periodo_tipo`
    'trimestral' u 'anual'). Barras horizontales, coloreadas por signo
    (positivo/negativo).
    """
    filas = _leer_csv(Path(data_dir) / "iaelap_la_plata_ramas.csv")
    filas = [
        f
        for f in filas
        if f["periodo_tipo"] == periodo_tipo
        and f["anio"] == str(anio)
        and (trimestre is None or f["trimestre"] == str(trimestre))
        and f["rama"] != "IAELaP"
    ]
    filas.sort(key=lambda f: float(f["var_interanual_pct"]))
    ramas = [f["rama"] for f in filas]
    valores = [float(f["var_interanual_pct"]) for f in filas]
    colores = [_AZUL if v >= 0 else _ROJO for v in valores]

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))
    y = range(len(filas))
    barras = ax.barh(y, valores, color=colores)
    ax.set_yticks(list(y))
    ax.set_yticklabels(ramas, fontsize="small")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.margins(x=0.12)  # deja lugar para las etiquetas de valor más allá de la barra más larga
    ax.set_xlabel("Var. % interanual")
    periodo = f"{anio}" if periodo_tipo == "anual" else _etiqueta_trimestre(str(anio), str(trimestre))
    ax.set_title(f"IAELaP — desagregación sectorial, {periodo}")
    ax.bar_label(barras, fmt="%.1f%%", padding=3, fontsize="x-small")
    _quitar_spines(ax)
    ax.figure.tight_layout()
    return ax.figure


def graficar_contraste_eph_iaelap(eph_dir: Path | str, iaelap_dir: Path | str = None):
    """Desocupación EPH (Gran La Plata) y variación % interanual IAELaP
    (Partido de La Plata) en paneles apilados con el mismo eje temporal —
    nunca superpuestos en un dual-axis: son unidades y geografías distintas
    (aglomerado vs. partido), compartir un solo eje sugeriría una
    comparabilidad que no existe.
    """
    iaelap_dir = iaelap_dir or eph_dir
    eph = _leer_csv(Path(eph_dir) / "eph_gran_la_plata.csv")
    iaelap = _leer_csv(Path(iaelap_dir) / "iaelap_la_plata.csv")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=False)

    etiquetas_eph = [_etiqueta_trimestre(f["anio"], f["trimestre"]) for f in eph]
    desocupacion = [float(f["tasa_desocupacion"]) * 100 for f in eph]
    ax1.plot(range(len(eph)), desocupacion, color=_AZUL, linewidth=2, marker="o", markersize=4)
    ax1.set_xticks(range(len(eph))[::2])
    ax1.set_xticklabels(etiquetas_eph[::2], rotation=45, ha="right", fontsize="small")
    ax1.set_ylabel("% desocupación")
    ax1.set_title("EPH Gran La Plata — tasa de desocupación")
    _quitar_spines(ax1)

    etiquetas_iaelap = [_etiqueta_trimestre(f["anio"], f["trimestre"]) for f in iaelap]
    var_pct = [float(f["var_interanual_pct"]) if f["var_interanual_pct"] else None for f in iaelap]
    colores = [_AZUL if v is not None and v >= 0 else _ROJO for v in var_pct]
    ax2.bar(range(len(iaelap)), [v if v is not None else 0 for v in var_pct], color=colores, width=0.7)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_xticks(range(len(iaelap))[::2])
    ax2.set_xticklabels(etiquetas_iaelap[::2], rotation=45, ha="right", fontsize="small")
    ax2.set_ylabel("Var. % i.a.")
    ax2.set_title("IAELaP Partido de La Plata — variación % interanual")
    _quitar_spines(ax2)

    fig.suptitle(
        "EPH (Gran La Plata) vs. IAELaP (Partido de La Plata) — geografías distintas",
        fontsize="small",
        y=1.0,
    )
    fig.tight_layout()
    return fig
