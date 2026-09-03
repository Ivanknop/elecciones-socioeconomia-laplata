"""Tests de `ml_models.construir_panel_bieleccion_trimestral`: mismo criterio
que `test_panel_trimestral.py`, pero sobre el bloque largo (`_vl`, elección
t-2 a t) -- sintéticos en memoria salvo donde se marca "datos reales"."""
from datetime import date

import pytest

from ml_models.cargar_series_economicas import FilaRegistroVariable
from ml_models.construir_panel_bieleccion_trimestral import (
    construir_panel_bieleccion_trimestral,
    generar_csvs,
)
from ml_models.construir_resultado_distrito import FilaResultadoDistrito


def _var(id_variable, es_flujo=False, polaridad="positiva"):
    return FilaRegistroVariable(
        id_variable=id_variable,
        descripcion="",
        fuente="",
        url_fuente="",
        periodicidad_nativa="mensual",
        cobertura_desde="",
        cobertura_hasta="",
        nivel_geografico="nacional",
        polaridad=polaridad,
        es_flujo=es_flujo,
        nominal=False,
        bloque_tematico="real",
        estado="nucleo",
        nota_metodologica="",
    )


def _ventana(id_transicion, nivel, anio_t, anio_t_menos_1, anio_t_menos_2, fecha_inicio_vl, fecha_fin_vc):
    return {
        "id_transicion": id_transicion,
        "nivel": nivel,
        "anio_t": anio_t,
        "anio_t_menos_1": anio_t_menos_1,
        "anio_t_menos_2": anio_t_menos_2,
        "fecha_inicio_vl": fecha_inicio_vl,
        "fecha_fin_vc": fecha_fin_vc,
    }


def _serie(valores: dict[str, float | None]) -> dict[date, float | None]:
    return {date.fromisoformat(f"{k}-01"): v for k, v in valores.items()}


@pytest.fixture
def escenario_basico():
    """Dos transiciones consecutivas del mismo nivel: la primera (t-2=None,
    t-1=2007, t=2009) no tiene bloque largo y se saltea; la segunda
    (t-2=2007, t-1=2009, t=2011) cubre 24 meses (8 trimestres) desde la
    elección t-2."""
    ventanas = [
        _ventana("municipal_2007_2009", "municipal", 2009, 2007, None, None, "2009-01-01"),
        _ventana("municipal_2009_2011", "municipal", 2011, 2009, 2007, "2007-01-01", "2011-01-01"),
    ]
    registro = [_var("x"), _var("ipc", es_flujo=True, polaridad="negativa")]
    anios = (2007, 2008, 2009, 2010, 2011)
    series_mensuales = {
        "x": _serie({f"{a}-{m:02d}": float(m) for a in anios for m in range(1, 13)}),
        "ipc": _serie({f"{a}-{m:02d}": 100.0 + m for a in anios for m in range(1, 13)}),
    }
    periodo_intervenido_por_mes = {date(a, m, 1): False for a in anios for m in range(1, 13)}
    resultado_por_anio_nivel = {
        (2007, "municipal"): FilaResultadoDistrito(2007, "municipal", 100, 2, 90.0, True, 60.0, True),
        (2011, "municipal"): FilaResultadoDistrito(2011, "municipal", 100, 2, 90.0, False, 40.0, True),
    }
    oficialismo_por_nivel = {
        (2007, "municipal"): {"agrupacion_oficialismo": "OFICIALISMO"},
        (2011, "municipal"): {"agrupacion_oficialismo": "OTRO"},
    }
    return ventanas, registro, series_mensuales, periodo_intervenido_por_mes, resultado_por_anio_nivel, oficialismo_por_nivel


class TestConstruirPanelBieleccionTrimestral:
    def test_ventana_sin_bloque_largo_no_genera_filas(self, escenario_basico):
        ventanas, *resto = escenario_basico
        ventanas_sin_vl = [ventanas[0]]
        filas = construir_panel_bieleccion_trimestral(ventanas_sin_vl, *resto, nivel="municipal")
        assert filas == []

    def test_solo_la_ventana_con_bloque_largo_produce_filas(self, escenario_basico):
        filas = construir_panel_bieleccion_trimestral(*escenario_basico, nivel="municipal")
        ids = {f["id_transicion"] for f in filas}
        assert ids == {"municipal_2007_2011"}

    def test_filas_frontera_usan_anio_t_menos_2_no_anio_t_menos_1(self, escenario_basico):
        filas = construir_panel_bieleccion_trimestral(*escenario_basico, nivel="municipal")
        frontera_t_menos_2, frontera_t = filas[0], filas[-1]
        assert frontera_t_menos_2["tipo_fila"] == "eleccion_t_menos_2"
        assert frontera_t["tipo_fila"] == "eleccion_t"
        assert frontera_t_menos_2["anio_t_menos_2"] == 2007
        assert frontera_t["anio_t_menos_2"] == 2007
        assert "anio_t_menos_1" not in frontera_t_menos_2
        for frontera in (frontera_t_menos_2, frontera_t):
            assert frontera["gana_oficialismo"] is not None
            assert frontera["x"] is None
            assert frontera["n_meses"] is None

    def test_filas_trimestre_cubren_los_48_meses_de_t_menos_2_a_t(self, escenario_basico):
        filas = construir_panel_bieleccion_trimestral(*escenario_basico, nivel="municipal")
        trimestres = [f for f in filas if f["tipo_fila"] == "trimestre"]
        assert len(trimestres) == 16  # 48 meses (2007-01 a 2011-01) / 3
        assert trimestres[0]["fecha_inicio"] == "2007-02-01"
        assert trimestres[-1]["fecha_fin"] == "2011-01-01"
        for t in trimestres:
            assert t["gana_oficialismo"] is None
            assert t["x"] is not None

    def test_orden_correlativo_0_a_n_mas_1(self, escenario_basico):
        filas = construir_panel_bieleccion_trimestral(*escenario_basico, nivel="municipal")
        assert [f["orden"] for f in filas] == list(range(18))

    def test_nivel_distinto_no_produce_filas(self, escenario_basico):
        filas = construir_panel_bieleccion_trimestral(*escenario_basico, nivel="provincial")
        assert filas == []


class TestGenerarCsvs:
    def test_escribe_en_destino_dir_no_en_la_carpeta_padre(self, tmp_path):
        destino_dir = tmp_path / "t-2"
        destinos = generar_csvs(destino_dir=destino_dir)
        assert len(destinos) == 3
        for d in destinos:
            assert d.parent == destino_dir

    def test_nombres_de_archivo_por_nivel(self, tmp_path):
        destinos = generar_csvs(destino_dir=tmp_path / "t-2")
        nombres = {d.name for d in destinos}
        assert nombres == {
            "panel_bieleccion_trimestral_municipal.csv",
            "panel_bieleccion_trimestral_provincial.csv",
            "panel_bieleccion_trimestral_nacional.csv",
        }

    def test_ninguna_fila_referencia_una_ventana_sin_bloque_largo(self, tmp_path):
        import csv

        destinos = generar_csvs(destino_dir=tmp_path / "t-2")
        for destino in destinos:
            with destino.open(encoding="utf-8", newline="") as f:
                filas = list(csv.DictReader(f))
            for f_ in filas:
                assert f_["anio_t_menos_2"] != ""

    def test_constante_panel_bieleccion_trimestral_dir_es_la_subcarpeta_t_2(self):
        from constantes import PANEL_BIELECCION_TRIMESTRAL_DIR, PANEL_DIR

        assert PANEL_BIELECCION_TRIMESTRAL_DIR == f"{PANEL_DIR}/t-2"
