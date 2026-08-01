"""Tests de `src/electoral/localidades.py`: crosswalk circuito -> localidad y
agregación de resultados por localidad.
"""
import pytest

from electoral.localidades import (
    NIVEL_NO_AGRUPABLE,
    NIVEL_OFICIAL,
    NIVEL_PERIODISTICO,
    SIN_DETERMINAR,
    FilaCrosswalk,
    agrupar_resultados_por_localidad,
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


class TestMapaLocalidadPorCircuito:
    def test_solo_oficial_por_defecto(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk)
        assert mapa == {"100": "BARRIO_A", "101": "BARRIO_A"}

    def test_periodistico_cubre_circuitos_sin_fuente_oficial(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_PERIODISTICO))
        assert mapa["200"] == "BARRIO_B"

    def test_oficial_prevalece_sobre_periodistico_cuando_ambos_existen(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_PERIODISTICO))
        assert mapa["101"] == "BARRIO_A"

    def test_no_agrupable_nunca_se_agrupa_aunque_periodistico_tenga_etiqueta(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_PERIODISTICO))
        assert "300" not in mapa

    def test_circuito_sin_ninguna_fila_no_aparece_en_el_mapa(self, crosswalk):
        mapa = mapa_localidad_por_circuito(crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_PERIODISTICO))
        assert "400" not in mapa


class TestCircuitosConDiscrepancia:
    def test_detecta_el_circuito_donde_oficial_y_periodistico_difieren(self, crosswalk):
        discrepancias = circuitos_con_discrepancia(crosswalk)
        assert [d["circuito_id"] for d in discrepancias] == ["101"]

    def test_no_incluye_circuitos_donde_coinciden(self, crosswalk):
        discrepancias = circuitos_con_discrepancia(crosswalk)
        assert "100" not in [d["circuito_id"] for d in discrepancias]


class TestAgruparResultadosPorLocalidad:
    def test_suma_los_votos_de_circuitos_de_la_misma_localidad(self, crosswalk):
        resultados = {"100": 50, "101": 30}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, crosswalk)
        fila = agrupado.set_index("localidad").loc["BARRIO_A"]
        assert fila["votos"] == 80

    def test_ningun_voto_se_pierde_incluyendo_sin_determinar(self, crosswalk):
        resultados = {"100": 50, "101": 30, "200": 10, "300": 5, "400": 7}
        agrupado, _ = agrupar_resultados_por_localidad(
            resultados, crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_PERIODISTICO),
        )
        assert agrupado["votos"].sum() == sum(resultados.values())

    def test_circuitos_sin_localidad_van_a_sin_determinar(self, crosswalk):
        resultados = {"300": 5, "400": 7}
        agrupado, _ = agrupar_resultados_por_localidad(
            resultados, crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_PERIODISTICO),
        )
        fila = agrupado.set_index("localidad").loc[SIN_DETERMINAR]
        assert fila["votos"] == 12

    def test_sin_determinar_esta_presente_aunque_no_haya_circuitos_sin_asignar(self, crosswalk):
        resultados = {"100": 50}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, crosswalk)
        assert SIN_DETERMINAR in agrupado["localidad"].values

    def test_sin_determinar_en_cero_cuando_todo_esta_asignado(self, crosswalk):
        resultados = {"100": 50}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, crosswalk)
        fila = agrupado.set_index("localidad").loc[SIN_DETERMINAR]
        assert fila["votos"] == 0

    def test_acepta_resultados_con_varias_columnas_por_circuito(self, crosswalk):
        resultados = {"100": {"votos": 50, "izquierda": 10, "derecha": 40}}
        agrupado, _ = agrupar_resultados_por_localidad(resultados, crosswalk)
        fila = agrupado.set_index("localidad").loc["BARRIO_A"]
        assert fila["izquierda"] == 10 and fila["derecha"] == 40

    def test_reporte_cuenta_circuitos_agrupados_y_totales(self, crosswalk):
        resultados = {"100": 50, "101": 30, "400": 7}
        _, reporte = agrupar_resultados_por_localidad(resultados, crosswalk)
        assert (reporte.circuitos_agrupados, reporte.circuitos_totales) == (2, 3)

    def test_reporte_calcula_porcentaje_de_votos_agrupados(self, crosswalk):
        resultados = {"100": 75, "400": 25}
        _, reporte = agrupar_resultados_por_localidad(resultados, crosswalk)
        assert reporte.porcentaje_votos == 75.0

    def test_reporte_lista_los_circuitos_sin_determinar(self, crosswalk):
        resultados = {"300": 5, "400": 7}
        _, reporte = agrupar_resultados_por_localidad(
            resultados, crosswalk, niveles_cobertura=(NIVEL_OFICIAL, NIVEL_PERIODISTICO),
        )
        assert reporte.circuitos_sin_determinar == ("300", "400")
