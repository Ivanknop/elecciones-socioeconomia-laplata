"""Tests de `ml_models.cargar_panel`: la interfaz D10 que impide apilar
los tres niveles por accidente."""
import pandas as pd
import pytest

from ml_models.cargar_panel import cargar_panel, cargar_panel_apilado


@pytest.fixture
def panel_csv(tmp_path):
    destino = tmp_path / "panel_ventanas.csv"
    pd.DataFrame(
        {
            "id_transicion": ["municipal_2011_2013", "provincial_2011_2013", "nacional_2011_2013"],
            "nivel": ["municipal", "provincial", "nacional"],
            "delta_v": [1.0, 2.0, 3.0],
        }
    ).to_csv(destino, index=False)
    return destino


class TestCargarPanel:
    def test_nivel_es_obligatorio(self):
        with pytest.raises(TypeError):
            cargar_panel()  # sin argumento -- debe fallar, no traer todo

    def test_filtra_por_nivel(self, panel_csv):
        df = cargar_panel("municipal", panel_csv)
        assert len(df) == 1
        assert df.iloc[0]["nivel"] == "municipal"

    def test_nivel_invalido_falla_explicitamente(self, panel_csv):
        with pytest.raises(ValueError):
            cargar_panel("invalido", panel_csv)


class TestCargarPanelApilado:
    def test_requiere_justificacion_no_vacia(self, panel_csv):
        with pytest.raises(ValueError):
            cargar_panel_apilado("", panel_csv)

    def test_requiere_justificacion_argumento(self):
        with pytest.raises(TypeError):
            cargar_panel_apilado()

    def test_con_justificacion_trae_los_tres_niveles(self, panel_csv):
        df = cargar_panel_apilado("comparar pooling completo vs. parcial (D7)", panel_csv)
        assert set(df["nivel"]) == {"municipal", "provincial", "nacional"}
