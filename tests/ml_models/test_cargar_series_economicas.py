"""Tests de `ml_models.cargar_series_economicas`: homogeneización mensual,
deflactación y construcción de la tabla, todo puro (sin red, sin `.dta` ni
microdatos reales -- `puntos_por_variable` viene sintético)."""
from datetime import date

import pytest

from constantes import REGISTRO_VARIABLES_PATH
from ml_models.cargar_series_economicas import (
    FilaRegistroVariable,
    _deflactar,
    _homogeneizar_mensual,
    cargar_registro,
    construir_tabla_mensual,
)


def _var(id_variable, periodicidad_nativa="mensual", nominal=False, es_flujo=False, polaridad="positiva"):
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
        nominal=nominal,
        bloque_tematico="real",
        estado="nucleo",
        nota_metodologica="",
    )


_MESES_2023 = [date(2023, m, 1) for m in range(1, 13)]


class TestHomogeneizarMensualMensual:
    def test_solo_toma_el_mes_exacto(self):
        puntos = [(date(2023, 3, 1), 10.0), (date(2023, 5, 1), 20.0)]
        resultado = _homogeneizar_mensual(puntos, "mensual", _MESES_2023)
        assert resultado[date(2023, 3, 1)] == 10.0
        assert resultado[date(2023, 4, 1)] is None  # no repite el de marzo
        assert resultado[date(2023, 5, 1)] == 20.0


class TestHomogeneizarMensualDiaria:
    def test_toma_el_ultimo_dia_habil_publicado_del_mes(self):
        puntos = [(date(2023, 3, 10), 1.0), (date(2023, 3, 28), 2.0), (date(2023, 4, 3), 3.0)]
        resultado = _homogeneizar_mensual(puntos, "diaria", _MESES_2023)
        assert resultado[date(2023, 3, 1)] == 2.0
        assert resultado[date(2023, 4, 1)] == 3.0

    def test_vacio_si_ningun_dia_del_mes_tiene_dato(self):
        puntos = [(date(2023, 3, 10), 1.0)]
        resultado = _homogeneizar_mensual(puntos, "diaria", _MESES_2023)
        assert resultado[date(2023, 4, 1)] is None


class TestHomogeneizarMensualTrimestral:
    def test_repite_el_valor_trimestral_dentro_del_propio_trimestre(self):
        puntos = [(date(2023, 1, 1), 100.0), (date(2023, 4, 1), 200.0)]
        resultado = _homogeneizar_mensual(puntos, "trimestral", _MESES_2023)
        assert resultado[date(2023, 1, 1)] == 100.0
        assert resultado[date(2023, 2, 1)] == 100.0
        assert resultado[date(2023, 3, 1)] == 100.0
        assert resultado[date(2023, 4, 1)] == 200.0

    def test_no_repite_mas_alla_de_su_propia_periodicidad(self):
        puntos = [(date(2023, 1, 1), 100.0)]  # la fuente dejó de publicar
        resultado = _homogeneizar_mensual(puntos, "trimestral", _MESES_2023)
        assert resultado[date(2023, 3, 1)] == 100.0  # dentro del trimestre
        assert resultado[date(2023, 4, 1)] is None  # ya pasaron 3 meses, no se repite más

    def test_prefiere_un_punto_exacto_mas_reciente_dentro_del_lookback(self):
        """Caso `resultado_fiscal`: parte de la serie es trimestral, parte
        mensual real -- el punto exacto más nuevo siempre gana."""
        puntos = [(date(2023, 1, 1), 100.0), (date(2023, 2, 1), 150.0)]
        resultado = _homogeneizar_mensual(puntos, "trimestral", _MESES_2023)
        assert resultado[date(2023, 2, 1)] == 150.0
        assert resultado[date(2023, 3, 1)] == 150.0  # sigue vigente el de febrero, no marzo


class TestDeflactar:
    def test_divide_por_ipc_y_escala_por_100(self):
        nominal = {date(2023, 1, 1): 1000.0}
        ipc = {date(2023, 1, 1): 200.0}
        resultado = _deflactar(nominal, ipc)
        assert resultado[date(2023, 1, 1)] == pytest.approx(500.0)

    def test_none_si_falta_el_ipc_ese_mes(self):
        nominal = {date(2023, 1, 1): 1000.0}
        ipc = {date(2023, 1, 1): None}
        assert _deflactar(nominal, ipc)[date(2023, 1, 1)] is None

    def test_none_si_falta_el_nominal_ese_mes(self):
        nominal = {date(2023, 1, 1): None}
        ipc = {date(2023, 1, 1): 200.0}
        assert _deflactar(nominal, ipc)[date(2023, 1, 1)] is None


class TestCargarRegistro:
    def test_lee_el_registro_real_del_repo(self):
        registro = cargar_registro(REGISTRO_VARIABLES_PATH)
        ids = {v.id_variable for v in registro}
        assert {"icg", "desocupacion", "ipc", "icc", "resultado_fiscal", "salario_real", "tc_oficial", "reservas"} <= ids

    def test_toda_variable_nucleo_tiene_polaridad_o_es_explicitamente_ambigua(self):
        """La especificación exige que toda variable declare polaridad --
        'ambigua' es válida (excluye `_mejoro`), lo que no puede pasar es
        que quede vacía."""
        registro = cargar_registro(REGISTRO_VARIABLES_PATH)
        for v in registro:
            assert v.polaridad in ("positiva", "negativa", "ambigua"), v


class TestConstruirTablaMensual:
    def test_una_fila_por_mes_del_rango(self):
        registro = [_var("x")]
        filas = construir_tabla_mensual(registro, {"x": []}, anio_inicio=2023, anio_fin=2023)
        assert len(filas) == 12

    def test_variable_sin_puntos_queda_vacia_no_falla(self):
        registro = [_var("x")]
        filas = construir_tabla_mensual(registro, {}, anio_inicio=2023, anio_fin=2023)
        assert all(f["x"] == "" for f in filas)

    def test_periodo_intervenido_marca_2007_2015(self):
        registro = [_var("x")]
        filas = construir_tabla_mensual(registro, {"x": []}, anio_inicio=2006, anio_fin=2016)
        por_fecha = {f["fecha"]: f["periodo_intervenido"] for f in filas}
        assert por_fecha["2006-12-01"] is False
        assert por_fecha["2007-01-01"] is True
        assert por_fecha["2015-12-01"] is True
        assert por_fecha["2016-01-01"] is False

    def test_variable_nominal_se_deflacta_por_ipc_automaticamente(self):
        registro = [_var("ipc"), _var("salario_real", nominal=True)]
        puntos = {
            "ipc": [(date(2023, 1, 1), 200.0)],
            "salario_real": [(date(2023, 1, 1), 1000.0)],
        }
        filas = construir_tabla_mensual(registro, puntos, anio_inicio=2023, anio_fin=2023)
        fila_enero = next(f for f in filas if f["fecha"] == "2023-01-01")
        assert fila_enero["salario_real"] == pytest.approx(500.0)

    def test_variable_nominal_hereda_el_hueco_del_ipc(self):
        registro = [_var("ipc"), _var("salario_real", nominal=True)]
        puntos = {"ipc": [], "salario_real": [(date(2023, 1, 1), 1000.0)]}
        filas = construir_tabla_mensual(registro, puntos, anio_inicio=2023, anio_fin=2023)
        fila_enero = next(f for f in filas if f["fecha"] == "2023-01-01")
        assert fila_enero["salario_real"] == ""  # el nominal existe pero no hay ipc -- nunca se imputa

    def test_variable_no_nominal_no_se_toca(self):
        registro = [_var("ipc"), _var("icg", nominal=False)]
        puntos = {"ipc": [], "icg": [(date(2023, 1, 1), 2.5)]}
        filas = construir_tabla_mensual(registro, puntos, anio_inicio=2023, anio_fin=2023)
        fila_enero = next(f for f in filas if f["fecha"] == "2023-01-01")
        assert fila_enero["icg"] == 2.5
