"""Tests de `src/geolocalizacion/catalogo.py`: normalización de nombres,
deduplicación de asentamientos y armado del catálogo -- todo puro, sin red
(los asentamientos y el listado del Ministerio se arman a mano en cada
test)."""
from geolocalizacion.catalogo import (
    LocalidadMinisterio,
    _deduplicar_asentamientos,
    _haversine_metros,
    _normalizar,
    construir_catalogo,
    generar_reporte,
)


class TestNormalizar:
    def test_quita_acentos_y_pasa_a_mayusculas(self):
        assert _normalizar("José Melchor Romero") == "JOSE MELCHOR ROMERO"

    def test_quita_parentesis_y_puntos(self):
        assert _normalizar("Barrio El Carmen (Oeste)") == "BARRIO EL CARMEN OESTE"

    def test_colapsa_espacios_repetidos(self):
        assert _normalizar("Villa   Elisa") == "VILLA ELISA"


class TestHaversineMetros:
    def test_mismo_punto_da_distancia_cero(self):
        assert _haversine_metros(-34.9, -57.9, -34.9, -57.9) == 0.0

    def test_un_grado_de_latitud_son_aproximadamente_111_km(self):
        d = _haversine_metros(-34.9, -57.9, -35.9, -57.9)
        assert 110_000 < d < 112_000


class TestDeduplicarAsentamientos:
    def test_conserva_el_id_mas_largo_cuando_dos_comparten_nombre(self):
        asentamientos = [
            {"id": "06441030", "nombre": "La Plata", "lat": -34.92, "lon": -57.95},
            {"id": "0644103015", "nombre": "La Plata", "lat": -34.915, "lon": -57.948},
        ]
        resultado = _deduplicar_asentamientos(asentamientos)
        assert len(resultado) == 1
        assert resultado[0]["id"] == "0644103015"

    def test_no_toca_nombres_unicos(self):
        asentamientos = [
            {"id": "0644103003", "nombre": "Arana", "lat": -35.0, "lon": -57.89},
            {"id": "0644103009", "nombre": "City Bell", "lat": -34.87, "lon": -58.05},
        ]
        assert len(_deduplicar_asentamientos(asentamientos)) == 2


class TestConstruirCatalogo:
    def test_match_por_nombre_calcula_delta_y_marca_ambas_fuentes(self):
        asentamientos = [{"id": "0644103003", "nombre": "Arana", "lat": -35.0, "lon": -57.89}]
        ministerio = [
            LocalidadMinisterio(
                nombre="ARANA", uta_2020="064410441030003", uta_2010="000410441030003",
                lat=-35.03, lon=-57.8865,
            )
        ]
        catalogo = construir_catalogo(asentamientos, ministerio)
        assert len(catalogo) == 1
        loc = catalogo[0]
        assert loc.fuentes == "georef+ministerio"
        assert loc.delta_metros is not None and loc.delta_metros > 0
        assert loc.uta_2020 == "064410441030003"
        assert loc.uta_2010 == "000410441030003"

    def test_alias_isla_martin_garcia(self):
        asentamientos = [{"id": "06441A03", "nombre": "Martín García", "lat": -34.19, "lon": -58.25}]
        ministerio = [
            LocalidadMinisterio(
                nombre="ISLA MARTIN GARCIA", uta_2020="064410441000022", uta_2010="064410441000022",
                lat=-34.187, lon=-58.2526,
            )
        ]
        catalogo = construir_catalogo(asentamientos, ministerio)
        assert catalogo[0].fuentes == "georef+ministerio"

    def test_sin_match_queda_solo_georef_y_no_se_descarta(self):
        asentamientos = [{"id": "06441A00", "nombre": "Buchanan", "lat": -34.976, "lon": -58.226}]
        catalogo = construir_catalogo(asentamientos, ministerio=[])
        assert len(catalogo) == 1
        assert catalogo[0].fuentes == "solo_georef"
        assert catalogo[0].nota != ""

    def test_ordena_alfabeticamente_por_nombre(self):
        asentamientos = [
            {"id": "1", "nombre": "Villa Elisa", "lat": -34.87, "lon": -58.09},
            {"id": "2", "nombre": "Abasto", "lat": -35.01, "lon": -58.11},
        ]
        catalogo = construir_catalogo(asentamientos, ministerio=[])
        assert [loc.nombre for loc in catalogo] == ["Abasto", "Villa Elisa"]


class TestGenerarReporte:
    def test_separa_confirmadas_de_solo_georef(self):
        asentamientos = [
            {"id": "1", "nombre": "Arana", "lat": -35.0, "lon": -57.89},
            {"id": "2", "nombre": "Buchanan", "lat": -34.976, "lon": -58.226},
        ]
        ministerio = [
            LocalidadMinisterio(nombre="ARANA", uta_2020="x", uta_2010="x", lat=-35.03, lon=-57.8865)
        ]
        catalogo = construir_catalogo(asentamientos, ministerio)
        reporte = generar_reporte(catalogo)
        assert reporte.total == 2
        assert reporte.confirmadas_por_ambas_fuentes == 1
        assert reporte.solo_georef == ("Buchanan",)
