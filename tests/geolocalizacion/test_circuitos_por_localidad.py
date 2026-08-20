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
    def test_una_fila_por_circuito(self, circuitos, localidades):
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades)
        assert sorted(asignacion["circuito_id"]) == ["1", "2", "3"]

    def test_circuito_que_contiene_el_punto_se_asigna_a_esa_localidad(self, circuitos, localidades):
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades).set_index("circuito_id")
        assert asignacion.loc["1", "localidad"] == "A"
        assert asignacion.loc["3", "localidad"] == "B"

    def test_circuito_intermedio_va_a_la_localidad_geometricamente_mas_cercana(self, circuitos, localidades):
        # el circuito 2 no contiene ningún punto, pero su centroide está a
        # mitad de camino entre A y B -- debe quedar con alguna de las dos,
        # nunca con C (la lejana).
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades).set_index("circuito_id")
        assert asignacion.loc["2", "localidad"] in {"A", "B"}

    def test_distancia_metros_es_no_negativa(self, circuitos, localidades):
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades)
        assert (asignacion["distancia_metros"] >= 0).all()

    def test_localidad_lejana_sin_ningun_circuito_asignado(self, circuitos, localidades):
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades)
        assert "C" not in set(asignacion["localidad"])


class TestGenerarReporte:
    def test_localidades_sin_circuito_incluye_la_no_usada(self, circuitos, localidades):
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades)
        reporte = generar_reporte(asignacion, {"A", "B", "C"})
        assert reporte.localidades_sin_circuito == ("C",)
        assert reporte.localidades_totales == 3
        assert reporte.total_circuitos == 3

    def test_localidades_utilizadas_cuenta_nombres_distintos(self, circuitos, localidades):
        asignacion = asignar_localidad_mas_cercana(circuitos, localidades)
        reporte = generar_reporte(asignacion, {"A", "B", "C"})
        assert reporte.localidades_utilizadas == len(set(asignacion["localidad"]))
