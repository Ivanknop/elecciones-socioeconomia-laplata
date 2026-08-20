"""Tests de `src/electoral/localidades.py`: dos formas de construir el mapa
circuito -> localidad (crosswalk geolocalizado y crosswalk histórico por
nombre de barrio) y la agregación de resultados por localidad, agnóstica de
cuál de las dos se use.
"""
import pytest

from electoral.localidades import (
    NIVEL_NO_AGRUPABLE,
    NIVEL_OFICIAL,
    NIVEL_PERIODISTICO,
    NIVEL_REVISION_WEB,
    SIN_DETERMINAR,
    FilaCrosswalk,
    agrupar_resultados_por_localidad,
    cargar_circuito_localidad_geo,
    cargar_crosswalk,
    circuitos_con_discrepancia,
    mapa_localidad_por_circuito,
)


@pytest.fixture
def crosswalk():
    return [
        FilaCrosswalk("100", "BARRIO_A", "resolucion", NIVEL_OFICIAL),
        FilaCrosswalk("100", "BARRIO_A", "eldia", NIVEL_PERIODISTICO),
        FilaCrosswalk("101", "BARRIO_A", "resolucion", NIVEL_OFICIAL),
        FilaCrosswalk("101", "BARRIO_MONTORO", "eldia", NIVEL_PERIODISTICO),  # discrepa con oficial
        FilaCrosswalk("102", "BARRIO_A", "resolucion", NIVEL_OFICIAL),
        FilaCrosswalk("102", "BARRIO_D", "revision", NIVEL_REVISION_WEB),  # discrepa con oficial
        FilaCrosswalk("103", "BARRIO_E", "revision", NIVEL_REVISION_WEB),  # solo revisión web
        FilaCrosswalk("104", "BARRIO_F", "eldia", NIVEL_PERIODISTICO),
        FilaCrosswalk("104", "BARRIO_G", "revision", NIVEL_REVISION_WEB),  # revisión web pisa periodístico
        FilaCrosswalk("200", "BARRIO_B", "eldia", NIVEL_PERIODISTICO),  # solo periodístico
        FilaCrosswalk("300", "MULTIPLE_SIN_DOMINANTE", "resolucion", NIVEL_NO_AGRUPABLE),
        FilaCrosswalk("300", "BARRIO_C", "eldia", NIVEL_PERIODISTICO),  # no debe pisar el no_agrupable
        # 400 no tiene ninguna fila: sin fuente de ningún tipo
    ]


class TestCargarCrosswalk:
    def test_lee_las_filas_del_csv(self, tmp_path):
        csv_path = tmp_path / "crosswalk.csv"
        csv_path.write_text(
            "circuito_id,localidad,fuente,cobertura\n100,BARRIO_A,resolucion,oficial_confirmada\n",
            encoding="utf-8",
        )
        filas = cargar_crosswalk(csv_path)
        assert filas == [FilaCrosswalk("100", "BARRIO_A", "resolucion", "oficial_confirmada")]


class TestCargarCircuitoLocalidadGeo:
    def test_lee_el_mapa_del_csv_con_separador_punto_y_coma(self, tmp_path):
        csv_path = tmp_path / "circuitos_por_localidad.csv"
        csv_path.write_text(
            "circuito;localidad;distancia_metros\n100;La Plata;137.4\n101;Los Hornos;1323.2\n",
            encoding="utf-8",
        )
        mapa = cargar_circuito_localidad_geo(csv_path)
        assert mapa == {"100": "La Plata", "101": "Los Hornos"}


class TestMapaLocalidadPorCircuito:
    def test_oficial_y_revision_web_por_defecto(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk)
        assert mapa == {
            "100": "BARRIO_A",
            "101": "BARRIO_A",
            "102": "BARRIO_A",
            "103": "BARRIO_E",
            "104": "BARRIO_G",  # solo tiene periodístico + revisión web; revisión web ya entra por defecto
        }

    def test_periodistico_cubre_circuitos_sin_fuente_oficial_ni_revision_web(self, crosswalk):
        mapa = mapa_localidad_por_circuito(
            crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_REVISION_WEB, NIVEL_PERIODISTICO)
        )
        assert mapa["200"] == "BARRIO_B"

    def test_oficial_prevalece_sobre_periodistico_cuando_ambos_existen(self, crosswalk):
        mapa = mapa_localidad_por_circuito(
            crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_REVISION_WEB, NIVEL_PERIODISTICO)
        )
        assert mapa["101"] == "BARRIO_A"

    def test_oficial_prevalece_sobre_revision_web_cuando_ambos_existen(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_REVISION_WEB))
        assert mapa["102"] == "BARRIO_A"

    def test_revision_web_prevalece_sobre_periodistico_cuando_ambos_existen(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk, niveles_cobertura=(NIVEL_REVISION_WEB, NIVEL_PERIODISTICO))
        assert mapa["104"] == "BARRIO_G"

    def test_circuito_cubierto_solo_por_revision_web(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk, niveles_cobertura=(NIVEL_REVISION_WEB,))
        assert mapa["103"] == "BARRIO_E"

    def test_no_agrupable_nunca_se_agrupa_aunque_periodistico_tenga_etiqueta(self, crosswalk):
        mapa = mapa_localidad_por_circuito(
            crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_REVISION_WEB, NIVEL_PERIODISTICO)
        )
        assert "300" not in mapa

    def test_circuito_sin_ninguna_fila_no_aparece_en_el_mapa(self, crosswalk):
        mapa = mapa_localidad_por_circuito(
            crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_REVISION_WEB, NIVEL_PERIODISTICO)
        )
        assert "400" not in mapa


class TestCircuitosConDiscrepancia:
    def test_detecta_el_circuito_donde_oficial_y_periodistico_difieren(self, crosswalk):
        discrepancias = circuitos_con_discrepancia(crosswalk)
        assert [d["circuito_id"] for d in discrepancias] == ["101"]

    def test_no_incluye_circuitos_donde_coinciden(self, crosswalk):
        discrepancias = circuitos_con_discrepancia(crosswalk)
        assert "100" not in [d["circuito_id"] for d in discrepancias]


class TestAgruparResultadosPorLocalidad:
    """`mapa` acá es siempre un `dict[str, str]` circuito_id -> localidad ya
    resuelto -- da igual si salió de `mapa_localidad_por_circuito` (crosswalk
    de barrio) o de `cargar_circuito_localidad_geo` (crosswalk geolocalizado):
    la función de agregación no distingue la fuente."""

    @pytest.fixture
    def mapa(self, crosswalk):
        return mapa_localidad_por_circuito(
            crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_REVISION_WEB, NIVEL_PERIODISTICO)
        )

    def test_suma_los_votos_de_circuitos_de_la_misma_localidad(self, mapa):
        resultados = {"100": 50, "101": 30}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, mapa)
        fila = agrupado.set_index("localidad").loc["BARRIO_A"]
        assert fila["votos"] == 80

    def test_ningun_voto_se_pierde_incluyendo_sin_determinar(self, mapa):
        resultados = {"100": 50, "101": 30, "200": 10, "300": 5, "400": 7}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, mapa)
        assert agrupado["votos"].sum() == sum(resultados.values())

    def test_circuitos_sin_localidad_van_a_sin_determinar(self, mapa):
        resultados = {"300": 5, "400": 7}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, mapa)
        fila = agrupado.set_index("localidad").loc[SIN_DETERMINAR]
        assert fila["votos"] == 12

    def test_sin_determinar_esta_presente_aunque_no_haya_circuitos_sin_asignar(self, mapa):
        resultados = {"100": 50}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, mapa)
        assert SIN_DETERMINAR in agrupado["localidad"].values

    def test_sin_determinar_en_cero_cuando_todo_esta_asignado(self, mapa):
        resultados = {"100": 50}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, mapa)
        fila = agrupado.set_index("localidad").loc[SIN_DETERMINAR]
        assert fila["votos"] == 0

    def test_acepta_resultados_con_varias_columnas_por_circuito(self, mapa):
        resultados = {"100": {"votos": 50, "izquierda": 10, "derecha": 40}}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, mapa)
        fila = agrupado.set_index("localidad").loc["BARRIO_A"]
        assert fila["izquierda"] == 10 and fila["derecha"] == 40

    def test_reporte_cuenta_circuitos_agrupados_y_totales(self, mapa):
        resultados = {"100": 50, "101": 30, "400": 7}
        _, reporte = agrupar_resultados_por_localidad(resultados, mapa)
        assert (reporte.circuitos_agrupados, reporte.circuitos_totales) == (2, 3)

    def test_reporte_calcula_porcentaje_de_votos_agrupados(self, mapa):
        resultados = {"100": 75, "400": 25}
        _, reporte = agrupar_resultados_por_localidad(resultados, mapa)
        assert reporte.porcentaje_votos == 75.0

    def test_reporte_lista_los_circuitos_sin_determinar(self, mapa):
        resultados = {"300": 5, "400": 7}
        _, reporte = agrupar_resultados_por_localidad(resultados, mapa)
        assert reporte.circuitos_sin_determinar == ("300", "400")

    def test_reporte_incluye_la_etiqueta_de_fuente_pasada(self, mapa):
        resultados = {"100": 50}
        _, reporte = agrupar_resultados_por_localidad(resultados, mapa, fuente="crosswalk_de_prueba.csv")
        assert reporte.fuente == "crosswalk_de_prueba.csv"

    def test_funciona_igual_con_un_mapa_geolocalizado(self):
        mapa_geo = {"100": "La Plata", "101": "La Plata", "200": "Los Hornos"}
        resultados = {"100": 50, "101": 30, "200": 10}
        agrupado, reporte = agrupar_resultados_por_localidad(resultados, mapa_geo)
        assert agrupado.set_index("localidad").loc["La Plata", "votos"] == 80
        assert reporte.circuitos_sin_determinar == ()
