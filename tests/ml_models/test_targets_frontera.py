"""Tests de `ml_models.targets_frontera`."""
import pandas as pd
import pytest

from ml_models.targets_frontera import calcular_targets, delta, delta_min, voto_exit


def _frontera(share_oficialismo=40.0, participacion_pct=75.0, ausentismo=15.0,
              votos_blancos_y_nulos=15.0, votantes_habilitados=100.0,
              dispersion_economico_mu=0.1, dispersion_progresismo_mu=0.2, dispersion_cobertura_share=90.0):
    return pd.Series({
        "share_oficialismo": share_oficialismo, "participacion_pct": participacion_pct,
        "ausentismo": ausentismo, "votos_blancos_y_nulos": votos_blancos_y_nulos,
        "votantes_habilitados": votantes_habilitados, "dispersion_economico_mu": dispersion_economico_mu,
        "dispersion_progresismo_mu": dispersion_progresismo_mu, "dispersion_cobertura_share": dispersion_cobertura_share,
    })


class TestVotoExit:
    def test_calcula_participacion_y_voto_exit(self):
        resultado = voto_exit(_frontera(participacion_pct=75.0, ausentismo=15.0, votos_blancos_y_nulos=15.0, votantes_habilitados=100.0))
        assert resultado["participacion_pct"] == pytest.approx(75.0)
        assert resultado["voto_exit_ausentismo_pct"] == pytest.approx(15.0)
        assert resultado["voto_exit_blanco_nulo_pct"] == pytest.approx(15.0)

    def test_none_si_falta_votantes_habilitados(self):
        resultado = voto_exit(_frontera(votantes_habilitados=None))
        assert resultado == {"participacion_pct": None, "voto_exit_ausentismo_pct": None, "voto_exit_blanco_nulo_pct": None}


class TestDeltaYDeltaMin:
    def test_delta_resta_o_none_si_falta_algun_lado(self):
        assert delta(10.0, 4.0) == pytest.approx(6.0)
        assert delta(None, 4.0) is None
        assert delta(10.0, None) is None

    def test_delta_min_toma_el_minimo_o_none_si_falta_algun_lado(self):
        assert delta_min(95.0, 90.0) == pytest.approx(90.0)
        assert delta_min(float("nan"), 90.0) is None


class TestCalcularTargets:
    def test_targets_completos_con_frontera_normal(self):
        frontera_t = _frontera(share_oficialismo=40.0, participacion_pct=75.0, ausentismo=15.0,
                                votos_blancos_y_nulos=15.0, dispersion_economico_mu=0.1, dispersion_progresismo_mu=0.2,
                                dispersion_cobertura_share=90.0)
        frontera_anterior = _frontera(share_oficialismo=30.0, participacion_pct=70.0, ausentismo=20.0,
                                       votos_blancos_y_nulos=10.0, dispersion_economico_mu=-0.2, dispersion_progresismo_mu=0.5,
                                       dispersion_cobertura_share=95.0)
        targets = calcular_targets(frontera_t, frontera_anterior)

        assert targets["delta_v"] == pytest.approx(10.0)
        assert targets["delta_participacion_pct"] == pytest.approx(5.0)
        assert targets["delta_voto_exit_ausentismo_pct"] == pytest.approx(-5.0)
        assert targets["delta_voto_exit_blanco_nulo_pct"] == pytest.approx(5.0)
        assert targets["delta_dispersion_economico_mu"] == pytest.approx(0.3)
        assert targets["delta_dispersion_progresismo_mu"] == pytest.approx(-0.3)
        assert targets["magnitud_desplazamiento_ideologico"] == pytest.approx((0.3 ** 2 + 0.3 ** 2) ** 0.5)
        assert targets["cuadrante_desplazamiento"] == "derecha_conservador"
        assert targets["dispersion_cobertura_share_min"] == pytest.approx(90.0)

    def test_delta_v_y_magnitud_none_si_falta_un_extremo(self):
        frontera_t = _frontera(share_oficialismo=None, dispersion_economico_mu=None, dispersion_progresismo_mu=None)
        frontera_anterior = _frontera()
        targets = calcular_targets(frontera_t, frontera_anterior)
        assert targets["delta_v"] is None
        assert targets["magnitud_desplazamiento_ideologico"] is None
        assert targets["cuadrante_desplazamiento"] is None
