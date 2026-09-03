"""Tests de `ml_models.construir_panel_trimestral`: partición de meses,
agregación mensual->trimestral y estructura del panel largo -- sintéticos
en memoria salvo donde se marca explícitamente "datos reales" (lectura de
CSV ya committeados, sin red)."""
from datetime import date

import pytest

from ml_models.cargar_series_economicas import FilaRegistroVariable, cargar_registro
from ml_models.construir_panel_trimestral import (
    _ancla_inicial,
    _cargar_periodo_intervenido,
    _parsear_bool_csv,
    _particionar_meses,
    _promedio_trimestre,
    _variables_con_datos,
    _variacion_flujo_trimestre,
    calcular_n_trimestres,
    construir_panel_trimestral,
    generar_csvs,
)
from ml_models.construir_panel_ventanas import _cargar_series_mensuales
from ml_models.construir_resultado_distrito import FilaResultadoDistrito
from constantes import REGISTRO_VARIABLES_PATH, SERIES_ECONOMICAS_MENSUALES_PATH, VENTANAS_PATH


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


def _ventana(id_transicion, nivel, anio_t, anio_t_menos_1, fecha_inicio_vc, fecha_fin_vc):
    return {
        "id_transicion": id_transicion,
        "nivel": nivel,
        "anio_t": anio_t,
        "anio_t_menos_1": anio_t_menos_1,
        "fecha_inicio_vc": fecha_inicio_vc,
        "fecha_fin_vc": fecha_fin_vc,
    }


def _serie(valores: dict[str, float | None]) -> dict[date, float | None]:
    return {date.fromisoformat(f"{k}-01"): v for k, v in valores.items()}


class TestCalcularNTrimestres:
    @pytest.mark.parametrize(
        "fecha_inicio,fecha_fin,n_esperado",
        [
            ("2001-10-14", "2003-04-27", 6),  # 18 meses -- municipal/provincial_2001_2003 real
            ("2005-10-23", "2007-10-28", 8),  # 24 meses -- caso típico
            ("2009-06-28", "2011-10-23", 9),  # 28 meses -- municipal/provincial_2009_2011 real
            ("2003-04-27", "2005-10-23", 10),  # 30 meses -- municipal/provincial_2003_2005 real
        ],
    )
    def test_casos_conocidos(self, fecha_inicio, fecha_fin, n_esperado):
        assert calcular_n_trimestres(fecha_inicio, fecha_fin) == n_esperado

    def test_contra_las_31_ventanas_reales(self):
        """Sin red, sin depender de resultado_distrito -- solo el
        calendario real de ventanas.csv, mismo criterio que el test
        equivalente de test_panel_ventanas.py."""
        from ml_models.construir_calendario import construir_calendario, construir_ventanas

        ventanas_reales = construir_ventanas(construir_calendario())
        ns = [calcular_n_trimestres(v.fecha_inicio_vc, v.fecha_fin_vc) for v in ventanas_reales]
        assert len(ns) == 31
        assert min(ns) == 6
        assert max(ns) == 10


class TestParticionarMeses:
    def test_reconstruye_la_lista_original(self):
        meses = [date(2020, m, 1) for m in range(1, 13)]
        grupos = _particionar_meses(meses, 4)
        reconstruido = [m for grupo in grupos for m in grupo]
        assert reconstruido == meses

    def test_20_meses_en_7_grupos_da_un_grupo_de_dos(self):
        meses = [date(2020 + (m - 1) // 12, (m - 1) % 12 + 1, 1) for m in range(1, 21)]
        grupos = _particionar_meses(meses, 7)
        tamanos = sorted(len(g) for g in grupos)
        assert tamanos == [2, 3, 3, 3, 3, 3, 3]

    def test_28_meses_en_9_grupos_da_un_grupo_de_cuatro(self):
        meses = [date(2020 + (m - 1) // 12, (m - 1) % 12 + 1, 1) for m in range(1, 29)]
        grupos = _particionar_meses(meses, 9)
        tamanos = sorted(len(g) for g in grupos)
        assert tamanos == [3, 3, 3, 3, 3, 3, 3, 3, 4]


class TestParsearBoolCsv:
    @pytest.mark.parametrize("valor,esperado", [("True", True), ("true", True), ("False", False), ("false", False)])
    def test_valores_conocidos(self, valor, esperado):
        assert _parsear_bool_csv(valor) is esperado

    def test_vacio_es_none(self):
        assert _parsear_bool_csv("") is None


class TestPromedioTrimestre:
    def test_promedio_simple_ignorando_none(self):
        serie = _serie({"2020-01": 10.0, "2020-02": None, "2020-03": 20.0})
        meses = list(serie.keys())
        assert _promedio_trimestre(serie, meses) == pytest.approx(15.0)

    def test_none_si_ningun_mes_tiene_dato(self):
        serie = _serie({"2020-01": None, "2020-02": None})
        assert _promedio_trimestre(serie, list(serie.keys())) is None


class TestAnclaYVariacionFlujo:
    def test_ancla_inicial_toma_el_ultimo_valor_conocido_antes_del_mes(self):
        serie = _serie({"2020-01": 100.0, "2020-02": 105.0, "2020-04": 110.0})
        ancla = _ancla_inicial(serie, date(2020, 3, 1))
        assert ancla == pytest.approx(105.0)  # 02 es el último <= mes 03, 04 es posterior

    def test_ancla_none_si_no_hay_valor_previo(self):
        serie = _serie({"2020-05": 100.0})
        assert _ancla_inicial(serie, date(2020, 1, 1)) is None

    def test_variacion_porcentual_contra_ancla(self):
        serie = _serie({"2020-04": 110.0, "2020-05": None, "2020-06": 121.0})
        meses = [date(2020, 4, 1), date(2020, 5, 1), date(2020, 6, 1)]
        valor, nueva_ancla = _variacion_flujo_trimestre(serie, meses, ancla=100.0)
        assert valor == pytest.approx(21.0)  # (121/100 - 1) * 100
        assert nueva_ancla == pytest.approx(121.0)

    def test_ancla_persiste_si_el_trimestre_no_tiene_dato_real(self):
        serie = _serie({"2020-04": None, "2020-05": None})
        meses = [date(2020, 4, 1), date(2020, 5, 1)]
        valor, nueva_ancla = _variacion_flujo_trimestre(serie, meses, ancla=100.0)
        assert valor is None
        assert nueva_ancla == pytest.approx(100.0)  # sin dato real, el ancla no se mueve

    def test_none_si_falta_el_ancla(self):
        serie = _serie({"2020-04": 110.0})
        valor, _ = _variacion_flujo_trimestre(serie, [date(2020, 4, 1)], ancla=None)
        assert valor is None


class TestVariablesConDatos:
    def test_excluye_variable_enteramente_vacia(self):
        registro = [_var("x"), _var("vacia")]
        series = {"x": _serie({"2020-01": 1.0}), "vacia": _serie({"2020-01": None, "2020-02": None})}
        resultado = _variables_con_datos(registro, series)
        assert [v.id_variable for v in resultado] == ["x"]

    def test_conserva_variable_con_al_menos_un_dato_real(self):
        registro = [_var("x")]
        series = {"x": _serie({"2020-01": None, "2020-02": 5.0})}
        assert [v.id_variable for v in _variables_con_datos(registro, series)] == ["x"]


@pytest.fixture
def escenario_basico():
    """Una ventana chica: 6 meses de ventana (2 trimestres de 3), con una
    variable normal (`x`) y una de flujo (`ipc`)."""
    ventanas = [_ventana("municipal_2011_2013", "municipal", 2013, 2011, "2011-01-01", "2011-07-01")]
    registro = [_var("x"), _var("ipc", es_flujo=True, polaridad="negativa")]
    series_mensuales = {
        "x": _serie({f"2011-{m:02d}": float(m) for m in range(1, 8)}),
        "ipc": _serie({f"2011-{m:02d}": 100.0 + m for m in range(1, 8)}),
    }
    periodo_intervenido_por_mes = {date(2011, m, 1): False for m in range(1, 8)}
    resultado_por_anio_nivel = {
        (2011, "municipal"): FilaResultadoDistrito(2011, "municipal", 100, 2, 90.0, True, 60.0, True),
        (2013, "municipal"): FilaResultadoDistrito(2013, "municipal", 100, 2, 90.0, False, 40.0, True),
    }
    oficialismo_por_nivel = {
        (2011, "municipal"): {"agrupacion_oficialismo": "OFICIALISMO"},
        (2013, "municipal"): {"agrupacion_oficialismo": "OTRO"},
    }
    return ventanas, registro, series_mensuales, periodo_intervenido_por_mes, resultado_por_anio_nivel, oficialismo_por_nivel


class TestConstruirPanelTrimestral:
    def test_filas_frontera_tienen_gana_oficialismo_no_nulo_y_columnas_economicas_nulas(self, escenario_basico):
        filas = construir_panel_trimestral(*escenario_basico, nivel="municipal")
        frontera_t_menos_1, frontera_t = filas[0], filas[-1]
        assert frontera_t_menos_1["tipo_fila"] == "eleccion_t_menos_1"
        assert frontera_t["tipo_fila"] == "eleccion_t"
        for frontera in (frontera_t_menos_1, frontera_t):
            assert frontera["gana_oficialismo"] is not None
            assert frontera["x"] is None
            assert frontera["ipc"] is None
            assert frontera["n_meses"] is None

    def test_filas_trimestre_tienen_columnas_electorales_nulas(self, escenario_basico):
        filas = construir_panel_trimestral(*escenario_basico, nivel="municipal")
        trimestres = [f for f in filas if f["tipo_fila"] == "trimestre"]
        assert len(trimestres) == 2  # 6 meses de ventana / 3
        for t in trimestres:
            assert t["gana_oficialismo"] is None
            assert t["share_oficialismo"] is None
            assert t["agrupacion_oficialismo"] is None
            assert t["x"] is not None

    def test_orden_correlativo_0_a_n_mas_1(self, escenario_basico):
        filas = construir_panel_trimestral(*escenario_basico, nivel="municipal")
        assert [f["orden"] for f in filas] == [0, 1, 2, 3]

    def test_nivel_distinto_no_produce_filas(self, escenario_basico):
        filas = construir_panel_trimestral(*escenario_basico, nivel="provincial")
        assert filas == []


class TestIntegracionDatosReales:
    """Contra los CSV ya committeados (sin red) -- mismo criterio que
    test_31_filas_distribucion... de test_panel_ventanas.py."""

    def test_ipc_none_en_el_hueco_real_y_no_none_afuera(self):
        registro = cargar_registro(REGISTRO_VARIABLES_PATH)
        series_mensuales = _cargar_series_mensuales(SERIES_ECONOMICAS_MENSUALES_PATH, registro)
        periodo_intervenido = _cargar_periodo_intervenido(SERIES_ECONOMICAS_MENSUALES_PATH)
        resultado_por_anio_nivel: dict = {}
        oficialismo_por_nivel: dict = {}

        from ml_models.construir_panel_ventanas import _cargar_ventanas

        ventanas = _cargar_ventanas(VENTANAS_PATH)
        filas = construir_panel_trimestral(
            ventanas, registro, series_mensuales, periodo_intervenido, resultado_por_anio_nivel, oficialismo_por_nivel, "nacional"
        )
        trimestres = [f for f in filas if f["tipo_fila"] == "trimestre"]

        dentro_del_hueco = [t for t in trimestres if "2014-03" <= t["fecha_inicio"] <= "2016-08"]
        fuera_del_hueco = [t for t in trimestres if t["fecha_fin"] < "2013-01" or t["fecha_inicio"] > "2017-06"]
        assert dentro_del_hueco  # el hueco real cae dentro de la ventana nacional 2013-2015/2015-2017
        assert all(t["ipc"] is None for t in dentro_del_hueco)
        assert fuera_del_hueco
        assert all(t["ipc"] is not None for t in fuera_del_hueco)

    def test_variables_exploratorias_sin_dato_no_generan_columna(self):
        registro = cargar_registro(REGISTRO_VARIABLES_PATH)
        series_mensuales = _cargar_series_mensuales(SERIES_ECONOMICAS_MENSUALES_PATH, registro)
        variables = _variables_con_datos(registro, series_mensuales)
        ids = {v.id_variable for v in variables}
        assert ids.isdisjoint({"pobreza", "gini", "brecha_cambiaria", "empleo_registrado_pba"})


class TestGenerarCsvs:
    def test_escribe_en_destino_dir_no_en_la_carpeta_padre(self, tmp_path):
        destino_dir = tmp_path / "panel"
        destinos = generar_csvs(destino_dir=destino_dir)
        assert len(destinos) == 3
        for d in destinos:
            assert d.parent == destino_dir
            assert not (tmp_path / d.name).exists()  # no quedó nada en la carpeta padre de destino_dir

    def test_cada_archivo_contiene_solo_su_nivel(self, tmp_path):
        import csv

        destinos = generar_csvs(destino_dir=tmp_path / "panel")
        for destino in destinos:
            nivel_esperado = destino.stem.replace("panel_trimestral_", "")
            with destino.open(encoding="utf-8", newline="") as f:
                niveles = {r["nivel"] for r in csv.DictReader(f)}
            assert niveles == {nivel_esperado}

    def test_nombres_de_archivo_por_nivel(self, tmp_path):
        destinos = generar_csvs(destino_dir=tmp_path / "panel")
        nombres = {d.name for d in destinos}
        assert nombres == {
            "panel_trimestral_municipal.csv",
            "panel_trimestral_provincial.csv",
            "panel_trimestral_nacional.csv",
        }

    def test_constante_panel_trimestral_dir_es_la_subcarpeta_t_1(self):
        from constantes import PANEL_DIR, PANEL_TRIMESTRAL_DIR, TFI_DATA_DIR

        assert PANEL_TRIMESTRAL_DIR == f"{PANEL_DIR}/t-1"
        assert PANEL_DIR == f"{TFI_DATA_DIR}/panel"
        assert PANEL_TRIMESTRAL_DIR != TFI_DATA_DIR
