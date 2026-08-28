"""Tests de `ml_models.features_ventana`: fórmulas puras y reglas de
aplicabilidad del §5.4.1 de la especificación. Sin red, sin CSV reales."""
from datetime import date

import pytest

from ml_models.cargar_series_economicas import FilaRegistroVariable
from ml_models.features_ventana import (
    _acum,
    _final,
    _meses_en_ventana,
    _nivel,
    _pendiente,
    _volatilidad,
    calcular_features_interventana_variable,
    calcular_features_ventana_variable,
)


def _var(id_variable="x", periodicidad_nativa="mensual", es_flujo=False, polaridad="positiva"):
    return FilaRegistroVariable(
        id_variable=id_variable,
        descripcion="",
        fuente="",
        url_fuente="",
        periodicidad_nativa=periodicidad_nativa,
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


class TestMesesEnVentana:
    def test_incluye_ambos_extremos(self):
        meses = _meses_en_ventana("2011-10-23", "2013-10-27")
        assert meses[0] == date(2011, 10, 1)
        assert meses[-1] == date(2013, 10, 1)
        assert len(meses) == 25  # oct-2011 a oct-2013 inclusive

    def test_cruza_fin_de_anio_correctamente(self):
        meses = _meses_en_ventana("2023-11-01", "2024-02-01")
        assert meses == [date(2023, 11, 1), date(2023, 12, 1), date(2024, 1, 1), date(2024, 2, 1)]


class TestFormulas:
    def test_nivel_es_el_promedio(self):
        assert _nivel([10.0, 20.0, 30.0]) == pytest.approx(20.0)

    def test_nivel_vacio_sin_valores(self):
        assert _nivel([]) is None

    def test_pendiente_positiva_con_serie_creciente(self):
        assert _pendiente([1.0, 2.0, 3.0, 4.0]) == pytest.approx(1.0)

    def test_pendiente_none_con_menos_de_2_puntos(self):
        assert _pendiente([5.0]) is None

    def test_volatilidad_cero_con_serie_constante(self):
        assert _volatilidad([5.0, 5.0, 5.0]) == pytest.approx(0.0)

    def test_acum_variacion_porcentual(self):
        meses = [date(2023, 1, 1), date(2023, 2, 1), date(2023, 3, 1)]
        serie = {date(2023, 1, 1): 100.0, date(2023, 2, 1): 110.0, date(2023, 3, 1): 150.0}
        assert _acum(serie, meses) == pytest.approx(50.0)  # 150/100 - 1

    def test_acum_none_con_un_solo_valor(self):
        meses = [date(2023, 1, 1)]
        serie = {date(2023, 1, 1): 100.0}
        assert _acum(serie, meses) is None

    def test_final_promedia_los_ultimos_6_meses_de_la_ventana(self):
        meses = [date(2023, m, 1) for m in range(1, 9)]  # 8 meses
        serie = {date(2023, m, 1): float(m) for m in range(1, 9)}
        # últimos 6: marzo(3)..agosto(8) -> promedio (3+4+5+6+7+8)/6 = 5.5
        assert _final(serie, meses) == pytest.approx(5.5)


class TestCalcularFeaturesVentanaVariable:
    def test_sin_bloque_largo_en_la_primera_transicion(self):
        var = _var()
        serie = {date(2011, m, 1): 1.0 for m in range(10, 13)} | {date(2013, m, 1): 1.0 for m in range(1, 11)}
        resultado = calcular_features_ventana_variable(var, serie, "2011-10-23", "2013-10-27", None)
        assert "x_nivel_vc" in resultado
        assert "x_nivel_vl" not in resultado

    def test_con_bloque_largo_cuando_hay_anio_t_menos_2(self):
        var = _var()
        serie = {date(2007, m, 1): 1.0 for m in range(1, 13)} | {date(2011, m, 1): 1.0 for m in range(1, 13)}
        resultado = calcular_features_ventana_variable(var, serie, "2009-06-28", "2011-10-23", "2007-10-28")
        assert "x_nivel_vl" in resultado

    def test_anual_solo_calcula_nivel(self):
        var = _var(periodicidad_nativa="anual")
        serie = {date(2011, m, 1): 5.0 for m in range(1, 13)} | {date(2012, m, 1): 6.0 for m in range(1, 13)}
        resultado = calcular_features_ventana_variable(var, serie, "2011-01-01", "2012-12-01", None)
        assert "x_nivel_vc" in resultado
        assert "x_pendiente_vc" not in resultado
        assert "x_volatilidad_vc" not in resultado
        assert "x_final_vc" not in resultado

    def test_es_flujo_false_omite_acum(self):
        var = _var(es_flujo=False)
        serie = {date(2011, 1, 1): 1.0, date(2011, 2, 1): 2.0}
        resultado = calcular_features_ventana_variable(var, serie, "2011-01-01", "2011-02-01", None)
        assert "x_acum_vc" not in resultado

    def test_es_flujo_true_incluye_acum(self):
        var = _var(es_flujo=True)
        serie = {date(2011, 1, 1): 1.0, date(2011, 2, 1): 2.0}
        resultado = calcular_features_ventana_variable(var, serie, "2011-01-01", "2011-02-01", None)
        assert "x_acum_vc" in resultado

    def test_cobertura_parcial_true_si_faltan_meses(self):
        var = _var()
        serie = {date(2011, 1, 1): 1.0}  # falta febrero
        resultado = calcular_features_ventana_variable(var, serie, "2011-01-01", "2011-02-01", None)
        assert resultado["x_cobertura_parcial"] is True

    def test_cobertura_parcial_false_si_esta_todo(self):
        var = _var()
        serie = {date(2011, 1, 1): 1.0, date(2011, 2, 1): 2.0}
        resultado = calcular_features_ventana_variable(var, serie, "2011-01-01", "2011-02-01", None)
        assert resultado["x_cobertura_parcial"] is False

    def test_variable_totalmente_sin_dato_no_falla_y_marca_cobertura_parcial(self):
        var = _var()
        resultado = calcular_features_ventana_variable(var, {}, "2011-01-01", "2011-02-01", None)
        assert resultado["x_nivel_vc"] is None
        assert resultado["x_cobertura_parcial"] is True

    def test_polaridad_invalida_falla_explicitamente(self):
        var = _var(polaridad="")
        with pytest.raises(ValueError):
            calcular_features_ventana_variable(var, {}, "2011-01-01", "2011-02-01", None)


class TestCalcularFeaturesInterventanaVariable:
    def test_delta_nivel_y_pendiente(self):
        var = _var(polaridad="positiva")
        actual = {"x_nivel_vc": 10.0, "x_pendiente_vc": 1.0}
        anterior = {"x_nivel_vc": 6.0, "x_pendiente_vc": 0.5}
        resultado = calcular_features_interventana_variable(var, actual, anterior)
        assert resultado["x_delta_nivel"] == pytest.approx(4.0)
        assert resultado["x_delta_pendiente"] == pytest.approx(0.5)

    def test_none_sin_transicion_anterior(self):
        var = _var()
        actual = {"x_nivel_vc": 10.0, "x_pendiente_vc": 1.0}
        resultado = calcular_features_interventana_variable(var, actual, None)
        assert resultado["x_delta_nivel"] is None
        assert resultado["x_delta_pendiente"] is None

    def test_mejoro_true_si_positiva_y_sube(self):
        var = _var(polaridad="positiva")
        actual = {"x_nivel_vc": 10.0}
        anterior = {"x_nivel_vc": 5.0}
        resultado = calcular_features_interventana_variable(var, actual, anterior)
        assert resultado["x_mejoro"] is True

    def test_mejoro_true_si_negativa_y_baja(self):
        var = _var(polaridad="negativa")
        actual = {"x_nivel_vc": 5.0}
        anterior = {"x_nivel_vc": 10.0}
        resultado = calcular_features_interventana_variable(var, actual, anterior)
        assert resultado["x_mejoro"] is True

    def test_mejoro_omitido_si_ambigua(self):
        var = _var(polaridad="ambigua")
        actual = {"x_nivel_vc": 10.0}
        anterior = {"x_nivel_vc": 5.0}
        resultado = calcular_features_interventana_variable(var, actual, anterior)
        assert "x_mejoro" not in resultado

    def test_polaridad_invalida_falla_explicitamente(self):
        var = _var(polaridad="mala")
        with pytest.raises(ValueError):
            calcular_features_interventana_variable(var, {}, None)
