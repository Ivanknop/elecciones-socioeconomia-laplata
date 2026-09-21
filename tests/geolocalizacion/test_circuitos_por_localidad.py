"""Tests de `src/geolocalizacion/circuitos_por_localidad.py` sobre polígonos
y puntos sintéticos (no pega a los archivos reales) -- mismo patrón que
`tests/socioeconomia/test_geo.py`."""
import geopandas as gpd
import pytest
from shapely.geometry import Point, box

from geolocalizacion.circuitos_por_localidad import (
    asignar_localidad_mas_cercana,
    generar_reporte,
)


@pytest.fixture
def circuitos():
    return gpd.GeoDataFrame(
        {
            "circuito_id": ["1", "2", "3"],
            "geometry": [
                box(-58.00, -34.95, -57.96, -34.91),  # circuito 1, centrado cerca de A
                box(-57.96, -34.95, -57.92, -34.91),  # circuito 2, centrado cerca de B
                box(-57.92, -34.95, -57.88, -34.91),  # circuito 3, también más cerca de B que de A
            ],
        },
        crs="EPSG:4326",
    )


@pytest.fixture
def localidades():
    return gpd.GeoDataFrame(
        {
            "nombre": ["A", "B", "C"],
            "geometry": [
                Point(-57.98, -34.93),  # dentro del circuito 1
                Point(-57.90, -34.93),  # dentro del circuito 3
                Point(-56.00, -34.93),  # lejos de todo -- nunca va a quedar más cerca que A o B
            ],
        },
        crs="EPSG:4326",
    )


class TestAsignarLocalidadMasCercana:
    def test_asignacion_completa_correcta(self, circuitos, localidades):
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades)
        assert sorted(asignacion["circuito_id"]) == ["1", "2", "3"]
        por_circuito = asignacion.set_index("circuito_id")
        assert por_circuito.loc["1", "localidad"] == "A"
        assert por_circuito.loc["3", "localidad"] == "B"
        # el circuito 2 no contiene ningún punto, pero su centroide está a
        # mitad de camino entre A y B -- debe quedar con alguna de las dos,
        # nunca con C (la lejana).
        assert por_circuito.loc["2", "localidad"] in {"A", "B"}
        assert (asignacion["distancia_metros"] >= 0).all()
        assert "C" not in set(asignacion["localidad"])


class TestGenerarReporte:
    def test_reporte_completo(self, circuitos, localidades):
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades)
        reporte = generar_reporte(asignacion, {"A", "B", "C"})
        assert reporte.localidades_sin_circuito == ("C",)
        assert reporte.localidades_totales == 3
        assert reporte.total_circuitos == 3
        assert reporte.localidades_utilizadas == len(set(asignacion["localidad"]))
