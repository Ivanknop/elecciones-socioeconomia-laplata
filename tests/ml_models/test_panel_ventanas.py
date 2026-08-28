"""Tests de `ml_models.construir_panel_ventanas`: estructura del panel
final y prueba de extensibilidad (D9) -- todo con datos sintéticos en
memoria, sin tocar los CSV reales del repo."""
from datetime import date

import pytest

from ml_models.cargar_series_economicas import FilaRegistroVariable
from ml_models.construir_panel_ventanas import construir_panel
from ml_models.construir_resultado_distrito import FilaResultadoDistrito, FilaVotoPartido


def _var(id_variable, periodicidad_nativa="mensual", es_flujo=False, nominal=False, polaridad="positiva"):
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


def _ventana(id_transicion, nivel, anio_t, anio_t_menos_1, anio_t_menos_2=None, fecha_inicio_vl=None):
    return {
        "id_transicion": id_transicion,
        "nivel": nivel,
        "anio_t": anio_t,
        "anio_t_menos_1": anio_t_menos_1,
        "anio_t_menos_2": anio_t_menos_2,
        "fecha_inicio_vc": f"{anio_t_menos_1}-01-01",
        "fecha_fin_vc": f"{anio_t}-01-01",
        "fecha_inicio_vl": fecha_inicio_vl,
        "tipo_eleccion_t": "ejecutiva",
        "tipo_eleccion_t_menos_1": "ejecutiva",
    }


def _serie_constante(anio_inicio, anio_fin, valor):
    return {date(a, m, 1): valor for a in range(anio_inicio, anio_fin + 1) for m in range(1, 13)}


@pytest.fixture
def escenario_basico():
    ventanas = [_ventana("municipal_2011_2013", "municipal", 2013, 2011)]
    registro = [_var("x")]
    series_mensuales = {"x": _serie_constante(2011, 2013, 10.0)}
    resultado_por_anio_nivel = {
        (2011, "municipal"): FilaResultadoDistrito(2011, "municipal", 100, 2, 90.0, True, 60.0, True, ""),
        (2013, "municipal"): FilaResultadoDistrito(2013, "municipal", 100, 2, 90.0, False, 40.0, True, ""),
    }
    voto_partido_por_anio_nivel = {
        (2011, "municipal"): [FilaVotoPartido(2011, "municipal", "1", "OFICIALISMO", 60, 60.0)],
        (2013, "municipal"): [FilaVotoPartido(2013, "municipal", "1", "OFICIALISMO", 40, 40.0)],
    }
    oficialismo_por_nivel = {
        (2011, "municipal"): {"agrupacion_oficialismo": "OFICIALISMO", "continuidad_oficialismo": "continua"},
        (2013, "municipal"): {"agrupacion_oficialismo": "OFICIALISMO", "continuidad_oficialismo": "ruptura"},
    }
    posiciones = {}
    return ventanas, registro, series_mensuales, resultado_por_anio_nivel, voto_partido_por_anio_nivel, oficialismo_por_nivel, posiciones


class TestConstruirPanel:
    def test_una_fila_por_ventana(self, escenario_basico):
        filas = construir_panel(*escenario_basico)
        assert len(filas) == 1
        assert filas[0]["id_transicion"] == "municipal_2011_2013"

    def test_delta_v_share_gana_oficialismo(self, escenario_basico):
        filas = construir_panel(*escenario_basico)
        assert filas[0]["delta_v"] == pytest.approx(40.0 - 60.0)
        assert filas[0]["gana_oficialismo"] is False
        assert filas[0]["share_oficialismo"] == 40.0

    def test_nombres_de_columna_canonicos(self, escenario_basico):
        """gana_oficialismo (no gano_oficialismo); filiacion_politica se
        resuelve por join, acá se verifica que el nombre de columna del
        panel sea el canónico."""
        filas = construir_panel(*escenario_basico)
        assert "gana_oficialismo" in filas[0]
        assert "gano_oficialismo" not in filas[0]

    def test_columnas_de_features_de_la_variable_del_registro(self, escenario_basico):
        filas = construir_panel(*escenario_basico)
        assert filas[0]["x_nivel_vc"] == pytest.approx(10.0)
        assert filas[0]["x_pendiente_vc"] == pytest.approx(0.0)

    def test_31_filas_distribucion_12_12_7_con_calendario_real(self):
        """Extremo a extremo con el calendario/ventanas reales (sin red,
        sin depender de resultado_distrito -- solo estructura)."""
        from ml_models.construir_calendario import construir_calendario, construir_ventanas

        ventanas_reales = construir_ventanas(construir_calendario())
        ventanas_dict = [
            {
                "id_transicion": v.id_transicion,
                "nivel": v.nivel,
                "anio_t": v.anio_t,
                "anio_t_menos_1": v.anio_t_menos_1,
                "anio_t_menos_2": v.anio_t_menos_2,
                "fecha_inicio_vc": v.fecha_inicio_vc,
                "fecha_fin_vc": v.fecha_fin_vc,
                "fecha_inicio_vl": v.fecha_inicio_vl,
                "tipo_eleccion_t": v.tipo_eleccion_t,
                "tipo_eleccion_t_menos_1": v.tipo_eleccion_t_menos_1,
            }
            for v in ventanas_reales
        ]
        filas = construir_panel(ventanas_dict, [], {}, {}, {}, {}, {})
        assert len(filas) == 31
        por_nivel = {}
        for f in filas:
            por_nivel[f["nivel"]] = por_nivel.get(f["nivel"], 0) + 1
        assert por_nivel == {"municipal": 12, "provincial": 12, "nacional": 7}


class TestExtensibilidad:
    def test_variable_ficticia_agregada_al_registro_produce_sus_features_solo(self, escenario_basico):
        """D9: agregar una fila al registro + su serie produce sus
        features en el panel sin tocar `features_ventana.py` ni
        `construir_panel_ventanas.py` -- se agrega acá una variable nueva
        con un nombre inventado y se verifica que aparezca sola."""
        ventanas, registro, series_mensuales, *resto = escenario_basico
        registro_extendido = registro + [_var("variable_ficticia_nueva", polaridad="negativa", es_flujo=True)]
        series_extendida = dict(series_mensuales, variable_ficticia_nueva=_serie_constante(2011, 2013, 42.0))

        filas = construir_panel(ventanas, registro_extendido, series_extendida, *resto)

        assert filas[0]["variable_ficticia_nueva_nivel_vc"] == pytest.approx(42.0)
        assert "variable_ficticia_nueva_acum_vc" in filas[0]  # es_flujo=true
        assert "variable_ficticia_nueva_mejoro" in filas[0]  # polaridad != ambigua
        # la variable preexistente sigue intacta, sin efectos cruzados
        assert filas[0]["x_nivel_vc"] == pytest.approx(10.0)
