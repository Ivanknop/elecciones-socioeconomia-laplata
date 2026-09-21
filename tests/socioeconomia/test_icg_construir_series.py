"""Tests de `src/socioeconomia/icg_construir_series.py`. Trabaja siempre
sobre `DataFrame` armados a mano -- pura lógica de agregación, sin `.dta`
ni red.
"""
import pandas as pd
import pytest

from socioeconomia.icg_construir_series import construir_serie_headline, construir_series_demograficas


class TestConstruirSerieHeadline:
    def test_promedio_ponderado_y_brecha(self):
        # país = las 3 filas (incluye La Plata), La Plata = solo Ciudad==7.
        df = pd.DataFrame({
            "año": [2011, 2011, 2011],
            "mes": [1, 1, 1],
            "Ciudad": [7, 7, 3],
            "ICG": [2.0, 4.0, 1.0],
            "ponderacion_UTDT": [2.0, 1.0, 1.0],
        })

        salida = construir_serie_headline(df)

        fila = salida.iloc[0]
        assert fila["icg_la_plata"] == pytest.approx((2 * 2 + 4 * 1) / 3)
        assert fila["icg_pais"] == pytest.approx((2 * 2 + 4 * 1 + 1 * 1) / 4)
        assert fila["n_la_plata"] == 2
        assert fila["n_pais"] == 3
        assert fila["brecha"] == pytest.approx(fila["icg_la_plata"] - fila["icg_pais"])

    def test_anio_hasta_none_resuelve_al_maximo_real(self):
        df = pd.DataFrame({
            "año": [2011, 2013],
            "mes": [1, 1],
            "Ciudad": [7, 7],
            "ICG": [2.0, 3.0],
            "ponderacion_UTDT": [1.0, 1.0],
        })

        salida = construir_serie_headline(df)

        assert sorted(salida["año"].unique()) == [2011, 2013]

    def test_anio_desde_filtra_anios_anteriores(self):
        df = pd.DataFrame({
            "año": [2005, 2011],
            "mes": [1, 1],
            "Ciudad": [7, 7],
            "ICG": [2.0, 3.0],
            "ponderacion_UTDT": [1.0, 1.0],
        })

        salida = construir_serie_headline(df, anio_desde=2011)

        assert list(salida["año"]) == [2011]

    def test_default_anio_desde_es_2008(self):
        # 2008 es el piso real: La Plata entra al panel UTDT recién en 2008T1
        # (ver data/socioeconomia/ICG.md) -- 2007 debe quedar afuera por default.
        df = pd.DataFrame({
            "año": [2007, 2008],
            "mes": [1, 1],
            "Ciudad": [7, 7],
            "ICG": [2.0, 3.0],
            "ponderacion_UTDT": [1.0, 1.0],
        })

        salida = construir_serie_headline(df)

        assert list(salida["año"]) == [2008]


class TestConstruirSeriesDemograficas:
    def _df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "año": [2011, 2011, 2011, 2011],
            "mes": [1, 1, 2, 2],
            "ICG": [2.0, 4.0, 1.0, 3.0],
            "ponderacion_UTDT": [1.0, 1.0, 1.0, 1.0],
            "sexo": [0, 1, 0, 1],
            "edad": [1, 2, 1, 2],
            "edu": [1.0, 2.0, float("nan"), 2.0],
        })

    def test_resolucion_mensual_agrupa_por_anio_y_mes(self):
        salida = construir_series_demograficas(self._df(), corte="sexo", resolucion="mensual")

        assert set(salida.columns) >= {"año", "mes", "sexo", "icg", "n"}
        assert len(salida) == 4  # 2 meses x 2 categorías de sexo

    def test_resolucion_anual_agrupa_solo_por_anio(self):
        salida = construir_series_demograficas(self._df(), corte="sexo", resolucion="anual")

        assert "mes" not in salida.columns
        assert len(salida) == 2  # 1 año x 2 categorías de sexo
        fila_sexo0 = salida[salida["sexo"] == 0].iloc[0]
        # combina los dos meses: filas con sexo==0 son ICG 2.0 y 1.0, peso 1 cada una.
        assert fila_sexo0["icg"] == pytest.approx((2.0 + 1.0) / 2)
        assert fila_sexo0["n"] == 2

    def test_default_anio_desde_es_2008(self):
        df = pd.DataFrame({
            "año": [2007, 2008],
            "mes": [1, 1],
            "ICG": [2.0, 3.0],
            "ponderacion_UTDT": [1.0, 1.0],
            "sexo": [0, 0],
        })

        salida = construir_series_demograficas(df, corte="sexo", resolucion="anual")

        assert list(salida["año"]) == [2008]

    def test_edu_descarta_nulos_sin_afectar_sexo(self):
        df = self._df()

        salida_edu = construir_series_demograficas(df, corte="edu", resolucion="mensual")
        salida_sexo = construir_series_demograficas(df, corte="sexo", resolucion="mensual")

        assert salida_edu["n"].sum() == 3  # la fila con edu nulo queda afuera
        assert salida_sexo["n"].sum() == 4  # sexo no tiene nulos, entran las 4
