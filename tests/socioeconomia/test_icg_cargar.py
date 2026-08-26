"""Tests de `icg_cargar.py`; nunca carga el `.dta` real (22 MB) --
monkeypatchea `pandas.read_stata` con un DataFrame sintético (Stata no
acepta `ñ` en nombres de columna, un roundtrip real no serviría)."""
import pandas as pd
import pytest

from socioeconomia.icg_cargar import CIUDAD_LA_PLATA, cargar_microdatos


def _df_base(**overrides) -> pd.DataFrame:
    base = pd.DataFrame({
        "año": [2011.0, 2011.0, 2011.0],
        "mes": [1.0, 1.0, 2.0],
        "Ciudad": [7, 3, 7],
        "ICG": [2.0, 3.0, 1.0],
        "ponderacion_UTDT": [1.0, 1.0, 1.0],
    })
    for col, valores in overrides.items():
        base[col] = valores
    return base


class TestCargarMicrodatos:
    def test_normaliza_anio_mes_a_int(self, monkeypatch):
        monkeypatch.setattr(pd, "read_stata", lambda *a, **k: _df_base())

        df = cargar_microdatos("ruta/no/usada.dta")

        assert df["año"].dtype.kind == "i"
        assert df["mes"].dtype.kind == "i"
        assert list(df["año"]) == [2011, 2011, 2011]

    def test_ciudad_la_plata_es_7(self):
        assert CIUDAD_LA_PLATA == 7

    def test_descarta_filas_sin_anio_o_mes(self, monkeypatch):
        df = _df_base()
        df.loc[1, "año"] = float("nan")
        monkeypatch.setattr(pd, "read_stata", lambda *a, **k: df)

        resultado = cargar_microdatos("ruta/no/usada.dta")

        assert len(resultado) == 2
        assert resultado["año"].isna().sum() == 0

    def test_icg_fuera_de_rango_lanza_valueerror(self, monkeypatch):
        df = _df_base(ICG=[2.0, 5.5, 1.0])
        monkeypatch.setattr(pd, "read_stata", lambda *a, **k: df)

        with pytest.raises(ValueError, match="ICG"):
            cargar_microdatos("ruta/no/usada.dta")

    def test_icg_negativo_lanza_valueerror(self, monkeypatch):
        df = _df_base(ICG=[2.0, -1.0, 1.0])
        monkeypatch.setattr(pd, "read_stata", lambda *a, **k: df)

        with pytest.raises(ValueError, match="ICG"):
            cargar_microdatos("ruta/no/usada.dta")

    def test_ponderacion_nula_lanza_valueerror(self, monkeypatch):
        df = _df_base(ponderacion_UTDT=[1.0, None, 1.0])
        monkeypatch.setattr(pd, "read_stata", lambda *a, **k: df)

        with pytest.raises(ValueError, match="ponderacion_UTDT"):
            cargar_microdatos("ruta/no/usada.dta")
