"""Tests de `ml_models.construir_panel_ventanas`: estructura del panel
final y prueba de extensibilidad (D9) -- todo con datos sintéticos en
memoria, sin tocar los CSV reales del repo."""
from datetime import date

import pytest

from ml_models.cargar_series_economicas import FilaRegistroVariable
from ml_models.construir_elecciones_resumen import FilaEleccion
from ml_models.construir_panel_ventanas import clasificar_cuadrante_desplazamiento, construir_panel
from ml_models.construir_resultado_distrito import FilaResultadoDistrito, FilaVotoPartido


def _var(id_variable, periodicidad_nativa="mensual", es_flujo=False, nominal=False, polaridad="positiva", paquete_atributos="completo"):
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
        paquete_atributos=paquete_atributos,
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


def _eleccion(
    anio, nivel, dispersion_economico_mu, dispersion_progresismo_mu, cobertura,
    dispersion_economico_sigma2=0.0, dispersion_progresismo_sigma2=0.0,
) -> FilaEleccion:
    return FilaEleccion(
        nivel=nivel, anio=anio, votantes_habilitados=100, votos_positivos=90, votos_blancos=8, votos_nulos=2,
        ausentismo=10, votos_blancos_y_nulos=10, participacion_pct=98.0,
        gana_oficialismo=True, share_oficialismo=60.0, agrupacion_oficialismo="OFICIALISMO",
        n_fuerzas_viables=2, share_marginal_acumulado=0.0, share_oposicion_principal=40.0,
        share_otras_fuerzas_viables=0.0, dispersion_economico_mu=dispersion_economico_mu,
        dispersion_economico_sigma2=dispersion_economico_sigma2, dispersion_progresismo_mu=dispersion_progresismo_mu,
        dispersion_progresismo_sigma2=dispersion_progresismo_sigma2, dispersion_cobertura_share=cobertura,
        resultado_disponible=True,
    )


def _eleccion_con_participacion(anio, nivel, habilitados, positivos, blanco, nulo, ausentismo) -> FilaEleccion:
    blancos_y_nulos = blanco + (nulo or 0) if blanco is not None else None
    participacion_pct = (
        (positivos + blancos_y_nulos) / habilitados * 100
        if habilitados is not None and blancos_y_nulos is not None
        else None
    )
    return FilaEleccion(
        nivel=nivel, anio=anio, votantes_habilitados=habilitados, votos_positivos=positivos,
        votos_blancos=blanco, votos_nulos=nulo, ausentismo=ausentismo,
        votos_blancos_y_nulos=blancos_y_nulos, participacion_pct=participacion_pct,
        gana_oficialismo=None, share_oficialismo=None, agrupacion_oficialismo=None,
        n_fuerzas_viables=0, share_marginal_acumulado=0.0, share_oposicion_principal=None,
        share_otras_fuerzas_viables=0.0, dispersion_economico_mu=None, dispersion_economico_sigma2=None,
        dispersion_progresismo_mu=None, dispersion_progresismo_sigma2=None, dispersion_cobertura_share=0.0,
        resultado_disponible=False,
    )


@pytest.fixture
def escenario_basico():
    ventanas = [_ventana("municipal_2011_2013", "municipal", 2013, 2011)]
    registro = [_var("x")]
    series_mensuales = {"x": _serie_constante(2011, 2013, 10.0)}
    resultado_por_anio_nivel = {
        (2011, "municipal"): FilaResultadoDistrito(2011, "municipal", 100, 2, 90.0, True, 60.0, True),
        (2013, "municipal"): FilaResultadoDistrito(2013, "municipal", 100, 2, 90.0, False, 40.0, True),
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
    elecciones_por_anio_nivel = {
        (2011, "municipal"): _eleccion(2011, "municipal", 1.0, -1.0, 40.0, dispersion_economico_sigma2=1.0, dispersion_progresismo_sigma2=0.5),
        (2013, "municipal"): _eleccion(2013, "municipal", 3.0, 2.0, 90.0, dispersion_economico_sigma2=4.0, dispersion_progresismo_sigma2=2.0),
    }
    return (
        ventanas, registro, series_mensuales, resultado_por_anio_nivel, voto_partido_por_anio_nivel,
        oficialismo_por_nivel, posiciones, elecciones_por_anio_nivel,
    )


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
        filas = construir_panel(ventanas_dict, [], {}, {}, {}, {}, {}, {})
        assert len(filas) == 31
        por_nivel = {}
        for f in filas:
            por_nivel[f["nivel"]] = por_nivel.get(f["nivel"], 0) + 1
        assert por_nivel == {"municipal": 12, "provincial": 12, "nacional": 7}


class TestColumnasDeDesplazamientoIdeologico:
    def test_deltas_magnitud_y_cuadrante(self, escenario_basico):
        filas = construir_panel(*escenario_basico)
        fila = filas[0]
        assert fila["delta_dispersion_economico_mu"] == pytest.approx(2.0)  # 3.0 - 1.0
        assert fila["delta_dispersion_progresismo_mu"] == pytest.approx(3.0)  # 2.0 - (-1.0)
        assert fila["magnitud_desplazamiento_ideologico"] == pytest.approx((2.0**2 + 3.0**2) ** 0.5)
        assert fila["cuadrante_desplazamiento"] == "derecha_progresista"
        assert fila["dispersion_cobertura_share_min"] == pytest.approx(40.0)  # min(40, 90)
        assert fila["delta_sigma2_economico"] == pytest.approx(3.0)  # 4.0 - 1.0
        assert fila["delta_sigma2_progresismo"] == pytest.approx(1.5)  # 2.0 - 0.5

    def test_sin_eleccion_correspondiente_todo_none(self, escenario_basico):
        *resto, _ = escenario_basico
        filas = construir_panel(*resto, {})
        fila = filas[0]
        assert fila["delta_dispersion_economico_mu"] is None
        assert fila["magnitud_desplazamiento_ideologico"] is None
        assert fila["cuadrante_desplazamiento"] is None
        assert fila["dispersion_cobertura_share_min"] is None
        assert fila["delta_sigma2_economico"] is None
        assert fila["delta_sigma2_progresismo"] is None


class TestColumnasDeParticipacionVotoExit:
    def test_columnas_t_y_t_menos_1_con_ambos_anios_iguales(self, escenario_basico):
        # _eleccion() usa los mismos valores en 2011 y 2013 (habilitados=100,
        # positivos=90, blanco=8, nulo=2, ausentismo=10) -- t y t_menos_1
        # coinciden y los deltas dan 0.
        filas = construir_panel(*escenario_basico)
        fila = filas[0]
        assert fila["participacion_pct_t"] == pytest.approx(98.0)
        assert fila["participacion_pct_t_menos_1"] == pytest.approx(98.0)
        assert fila["participacion_relevante_t"] is True  # 98.0 > 79.0
        assert fila["voto_exit_blanco_nulo_pct_t"] == pytest.approx(10.0)  # 10/100*100
        assert fila["voto_exit_ausentismo_pct_t"] == pytest.approx(10.0)  # 10/100*100
        assert fila["delta_participacion_pct"] == pytest.approx(0.0)
        assert fila["delta_voto_exit_ausentismo_pct"] == pytest.approx(0.0)
        assert fila["delta_voto_exit_blanco_nulo_pct"] == pytest.approx(0.0)

    def test_sin_eleccion_correspondiente_todo_none(self, escenario_basico):
        *resto, _ = escenario_basico
        filas = construir_panel(*resto, {})
        fila = filas[0]
        assert fila["participacion_pct_t"] is None
        assert fila["participacion_relevante_t"] is None
        assert fila["voto_exit_blanco_nulo_pct_t"] is None
        assert fila["voto_exit_ausentismo_pct_t"] is None
        assert fila["delta_participacion_pct"] is None
        assert fila["delta_voto_exit_ausentismo_pct"] is None
        assert fila["delta_voto_exit_blanco_nulo_pct"] is None

    def test_transicion_real_hacia_2025_provincial_ya_no_da_none_en_voto_exit(self):
        # Con la corrección a D17 (ausentismo ya no depende de votos_nulos
        # presente), esta transición real deja de tener voto_exit_*_t en
        # None -- a diferencia del diseño anterior (panel-only), que
        # dependía de un fallback ad hoc para este caso.
        ventanas = [_ventana("provincial_2023_2025", "provincial", 2025, 2023)]
        elecciones_por_anio_nivel = {
            (2023, "provincial"): _eleccion_con_participacion(2023, "provincial", 500000, 400000, 60000, 20000, 20000),
            (2025, "provincial"): _eleccion_con_participacion(2025, "provincial", 639839, 393945, 15186, None, 230708),
        }
        filas = construir_panel(
            ventanas, [], {}, {}, {}, {}, {}, elecciones_por_anio_nivel,
        )
        fila = filas[0]
        assert fila["voto_exit_ausentismo_pct_t"] == pytest.approx(230708 / 639839 * 100)
        assert fila["delta_voto_exit_ausentismo_pct"] is not None
        assert fila["delta_voto_exit_blanco_nulo_pct"] is not None


class TestClasificarCuadranteDesplazamiento:
    @pytest.mark.parametrize(
        "delta_econ,delta_prog,esperado",
        [
            (1.0, 1.0, "derecha_progresista"),
            (1.0, -1.0, "derecha_conservador"),
            (-1.0, 1.0, "izquierda_progresista"),
            (-1.0, -1.0, "izquierda_conservador"),
        ],
    )
    def test_los_cuatro_cuadrantes(self, delta_econ, delta_prog, esperado):
        assert clasificar_cuadrante_desplazamiento(delta_econ, delta_prog) == esperado

    def test_none_si_falta_un_delta(self):
        assert clasificar_cuadrante_desplazamiento(None, 1.0) is None
        assert clasificar_cuadrante_desplazamiento(1.0, None) is None

    def test_none_si_algun_delta_es_exactamente_cero(self):
        assert clasificar_cuadrante_desplazamiento(0.0, 1.0) is None
        assert clasificar_cuadrante_desplazamiento(1.0, 0.0) is None


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
        assert "variable_ficticia_nueva_mejoro" not in filas[0]  # _mejoro se retiró (D25)
        # la variable preexistente sigue intacta, sin efectos cruzados
        assert filas[0]["x_nivel_vc"] == pytest.approx(10.0)

    def test_variable_ficticia_con_paquete_reducido_produce_solo_3_atributos(self, escenario_basico):
        """D26: paquete_atributos='reducido' en el registro alcanza para
        que una variable nueva traiga solo nivel_vc/delta_nivel/
        cobertura_parcial en el panel, sin tocar código."""
        ventanas, registro, series_mensuales, *resto = escenario_basico
        registro_extendido = registro + [_var("variable_reducida_nueva", paquete_atributos="reducido")]
        series_extendida = dict(series_mensuales, variable_reducida_nueva=_serie_constante(2011, 2013, 7.0))

        filas = construir_panel(ventanas, registro_extendido, series_extendida, *resto)

        claves_variable = {k for k in filas[0] if k.startswith("variable_reducida_nueva")}
        assert claves_variable == {
            "variable_reducida_nueva_nivel_vc",
            "variable_reducida_nueva_delta_nivel",
            "variable_reducida_nueva_cobertura_parcial",
        }
        assert filas[0]["variable_reducida_nueva_nivel_vc"] == pytest.approx(7.0)
