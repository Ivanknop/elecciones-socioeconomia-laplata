"""Tests de `src/geolocalizacion/geo.py` sobre polígonos sintéticos (no pega a
ningún archivo real de circuitos/radios). Circuitos y radios se arman a mano
con `shapely.box`, en grados cerca de La Plata, para que `estimate_utm_crs`
elija una proyección real.
"""
import geopandas as gpd
import pytest
from shapely.geometry import box

from geolocalizacion.geo import calcular_correspondencia, canonicalizar_circuito_id


class TestCanonicalizarCircuitoId:
    def test_canonicaliza_ceros_y_sufijo(self):
        assert canonicalizar_circuito_id("0063") == "63"
        assert canonicalizar_circuito_id("0496f") == "496F"
        assert canonicalizar_circuito_id("496F") == "496F"


@pytest.fixture
def circuitos():
    return gpd.GeoDataFrame(
        {
            "circuito_id": ["1", "2"],
            "geometry": [
                box(-58.00, -34.95, -57.90, -34.85),  # circuito 1
                box(-57.90, -34.95, -57.80, -34.85),  # circuito 2, linda con el 1 en lon=-57.90
            ],
        },
        crs="EPSG:4326",
    )


@pytest.fixture
def radios():
    return gpd.GeoDataFrame(
        {
            "radio_censal_id": ["A", "B"],
            "censo_anio": [2022, 2022],
            "geometry": [
                box(-57.99, -34.94, -57.95, -34.86),  # A: entero adentro del circuito 1
                box(-57.92, -34.94, -57.88, -34.86),  # B: a caballo entre circuito 1 y 2
            ],
        },
        crs="EPSG:4326",
    )


class TestCalcularCorrespondencia:
    def test_radio_interior_match_limpio_y_estructura(self, circuitos, radios):
        correspondencia = calcular_correspondencia(circuitos, radios)
        fila_a = correspondencia[correspondencia["radio_censal_id"] == "A"]
        assert len(fila_a) == 1
        assert fila_a.iloc[0]["circuito_id"] == "1"
        assert fila_a.iloc[0]["match_limpio"]
        assert fila_a.iloc[0]["peso_area"] == pytest.approx(1.0, abs=1e-6)
        # ningún radio de este fixture toca por fuera de circuitos 1/2
        assert set(correspondencia["circuito_id"]) <= {"1", "2"}

    def test_radio_a_caballo_reparte_correctamente(self, circuitos, radios):
        correspondencia = calcular_correspondencia(circuitos, radios)
        filas_b = correspondencia[correspondencia["radio_censal_id"] == "B"]
        assert set(filas_b["circuito_id"]) == {"1", "2"}
        assert not filas_b["match_limpio"].any()
        assert filas_b["peso_area"].sum() == pytest.approx(1.0, rel=1e-3)
        # B tiene el mismo ancho de longitud a cada lado del límite y la misma
        # franja de latitud de los dos lados, así que el prorrateo real por
        # área proyectada debe quedar cerca de 50/50 aunque no sea exacto.
        pesos_b = filas_b.set_index("circuito_id")["peso_area"]
        assert pesos_b["1"] == pytest.approx(0.5, abs=0.02)
        assert pesos_b["2"] == pytest.approx(0.5, abs=0.02)
