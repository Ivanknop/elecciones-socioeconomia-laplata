"""Tests de `ml_models.construir_panel_lasso_bieleccion`."""
import pandas as pd
import pytest

from ml_models.construir_panel_lasso_bieleccion import construir_fila_transicion, construir_panel, generar_csv


def _frontera(tipo_fila, share_oficialismo, participacion_pct=None, ausentismo=None,
              votos_blancos_y_nulos=None, votantes_habilitados=None,
              dispersion_economico_mu=None, dispersion_progresismo_mu=None, dispersion_cobertura_share=None):
    return {
        "id_transicion": "municipal_2001_2005", "nivel": "municipal", "anio_t": 2005, "anio_t_menos_2": 2001,
        "tipo_fila": tipo_fila, "gana_oficialismo": True, "share_oficialismo": share_oficialismo, "ipc": None,
        "participacion_pct": participacion_pct, "ausentismo": ausentismo,
        "votos_blancos_y_nulos": votos_blancos_y_nulos, "votantes_habilitados": votantes_habilitados,
        "dispersion_economico_mu": dispersion_economico_mu, "dispersion_progresismo_mu": dispersion_progresismo_mu,
        "dispersion_cobertura_share": dispersion_cobertura_share,
    }


def _filas_transicion(ipc_valores, share_t=40.0, share_t_menos_2=30.0, **kwargs_frontera):
    filas = [_frontera(
        "eleccion_t_menos_2", share_t_menos_2,
        participacion_pct=70.0, ausentismo=20.0, votos_blancos_y_nulos=10.0, votantes_habilitados=100.0,
        dispersion_economico_mu=-0.2, dispersion_progresismo_mu=0.5, dispersion_cobertura_share=95.0,
    )]
    for v in ipc_valores:
        filas.append({
            "id_transicion": "municipal_2001_2005", "nivel": "municipal", "anio_t": 2005, "anio_t_menos_2": 2001,
            "tipo_fila": "trimestre", "gana_oficialismo": None, "share_oficialismo": None, "ipc": v,
            "participacion_pct": None, "ausentismo": None, "votos_blancos_y_nulos": None,
            "votantes_habilitados": None, "dispersion_economico_mu": None, "dispersion_progresismo_mu": None,
            "dispersion_cobertura_share": None,
        })
    base_t = {
        "participacion_pct": 75.0, "ausentismo": 15.0, "votos_blancos_y_nulos": 15.0, "votantes_habilitados": 100.0,
        "dispersion_economico_mu": 0.1, "dispersion_progresismo_mu": 0.2, "dispersion_cobertura_share": 90.0,
    }
    filas.append(_frontera("eleccion_t", share_t, **{**base_t, **kwargs_frontera}))
    return pd.DataFrame(filas)


class TestConstruirFilaTransicion:
    def test_delta_v_features_de_trayectoria_y_targets_de_participacion_y_desplazamiento(self):
        df = _filas_transicion([1.0, 2.0, 3.0, 4.0], share_t=40.0, share_t_menos_2=30.0)
        fila = construir_fila_transicion(df, ["ipc"])

        assert fila["id_transicion"] == "municipal_2001_2005"
        assert fila["nivel"] == "municipal"
        assert fila["anio_t"] == 2005 and fila["anio_t_menos_2"] == 2001
        assert fila["delta_v"] == pytest.approx(10.0)  # 40 - 30
        assert fila["ipc_nivel_trim"] == pytest.approx(2.5)  # media(1,2,3,4)
        assert fila["ipc_pendiente_trim"] == pytest.approx(1.0)  # sube 1 por trimestre
        assert fila["ipc_volatilidad_trim"] == pytest.approx(1.2909944, rel=1e-5)  # std ddof=1
        assert fila["ipc_final_trim"] == pytest.approx(3.5)  # media de los últimos 2 (3,4)
        assert fila["ipc_cobertura_parcial"] is False

        # participación/voto exit (D19): t=75%/15%/15%, t_menos_2=70%/20%/10% (sobre habilitados=100)
        assert fila["delta_participacion_pct"] == pytest.approx(5.0)
        assert fila["delta_voto_exit_ausentismo_pct"] == pytest.approx(-5.0)  # 15-20
        assert fila["delta_voto_exit_blanco_nulo_pct"] == pytest.approx(5.0)  # 15-10

        # desplazamiento ideológico (D18): t=(0.1, 0.2), t_menos_2=(-0.2, 0.5)
        assert fila["delta_dispersion_economico_mu"] == pytest.approx(0.3)
        assert fila["delta_dispersion_progresismo_mu"] == pytest.approx(-0.3)
        assert fila["magnitud_desplazamiento_ideologico"] == pytest.approx((0.3**2 + 0.3**2) ** 0.5)
        assert fila["cuadrante_desplazamiento"] == "derecha_conservador"
        assert fila["dispersion_cobertura_share_min"] == pytest.approx(90.0)  # min(95.0, 90.0)

    def test_delta_v_none_si_falta_un_extremo(self):
        df = _filas_transicion([1.0, 2.0], share_t=None, share_t_menos_2=30.0)
        fila = construir_fila_transicion(df, ["ipc"])
        assert fila["delta_v"] is None

    def test_cobertura_parcial_true_si_falta_algun_trimestre(self):
        df = _filas_transicion([1.0, None, 3.0])
        fila = construir_fila_transicion(df, ["ipc"])
        assert fila["ipc_cobertura_parcial"] is True
        assert fila["ipc_nivel_trim"] == pytest.approx(2.0)  # media(1,3), ignora el faltante

    def test_targets_derivados_none_si_falta_votantes_habilitados_o_dispersion(self):
        df = _filas_transicion([1.0, 2.0], votantes_habilitados=None, dispersion_economico_mu=None, dispersion_progresismo_mu=None)
        fila = construir_fila_transicion(df, ["ipc"])
        assert fila["delta_voto_exit_ausentismo_pct"] is None
        assert fila["delta_voto_exit_blanco_nulo_pct"] is None
        assert fila["magnitud_desplazamiento_ideologico"] is None
        assert fila["cuadrante_desplazamiento"] is None


class TestConstruirPanelYGenerarCsv:
    def test_una_fila_por_transicion_combinando_niveles(self, tmp_path):
        for nivel in ("municipal", "provincial"):
            df = _filas_transicion([1.0, 2.0])
            df["id_transicion"] = f"{nivel}_2001_2005"
            df["nivel"] = nivel
            df.to_csv(tmp_path / f"panel_bieleccion_trimestral_{nivel}.csv", index=False)

        panel = construir_panel(niveles=("municipal", "provincial"), panel_dir=tmp_path)
        assert sorted(panel["nivel"]) == ["municipal", "provincial"]
        assert set(panel["id_transicion"]) == {"municipal_2001_2005", "provincial_2001_2005"}
        assert "ipc_nivel_trim" in panel.columns
        assert "magnitud_desplazamiento_ideologico" in panel.columns

    def test_generar_csv_escribe_el_panel_combinado(self, tmp_path):
        for nivel in ("municipal", "provincial", "nacional"):
            df = _filas_transicion([1.0, 2.0])
            df["id_transicion"] = f"{nivel}_2001_2005"
            df["nivel"] = nivel
            df.to_csv(tmp_path / f"panel_bieleccion_trimestral_{nivel}.csv", index=False)
        destino = generar_csv(destino=tmp_path / "salida" / "panel_ventanas_bieleccion.csv", panel_dir=tmp_path)
        assert destino.exists()
        assert len(pd.read_csv(destino)) == 3
