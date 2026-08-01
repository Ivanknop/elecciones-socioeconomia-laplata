"""Tests de `src/socioeconomia/eph_client.py`.
"""
import pandas as pd
import pytest

from socioeconomia.eph_client import (
    TrimestreNoPublicado,
    UrlDesconocida,
    _nombre_archivo,
    _nombre_archivo_historico,
    agregados_gran_la_plata,
    agregados_por_edad,
    agregados_por_sexo,
)


class TestNombreArchivo:
    def test_patron_regular_desde_2017_t2(self):
        assert _nombre_archivo(2017, 2) == "EPH_usu_2_Trim_2017_txt.zip"

    def test_patron_regular_anios_recientes(self):
        assert _nombre_archivo(2023, 4) == "EPH_usu_4_Trim_2023_txt.zip"

    def test_nombre_irregular_confirmado(self):
        assert _nombre_archivo(2016, 3) == "EPH_usu_3erTrim_2016_txt.zip"

    def test_trimestre_sin_patron_confirmado_levanta_url_desconocida(self):
        with pytest.raises(UrlDesconocida):
            _nombre_archivo(2012, 1)


class TestNombreArchivoHistorico:
    def test_2011_2013_es_zip(self):
        assert _nombre_archivo_historico(2011, 1) == "t111_dbf.zip"
        assert _nombre_archivo_historico(2013, 4) == "t413_dbf.zip"

    def test_2014_2015_es_rar(self):
        assert _nombre_archivo_historico(2014, 1) == "t114_dbf.rar"
        assert _nombre_archivo_historico(2015, 1) == "t115_dbf.rar"

    def test_2014_t2_es_la_excepcion_confirmada_en_zip(self):
        # único trimestre de 2014-2015 que no sigue la regla general
        assert _nombre_archivo_historico(2014, 2) == "t214_dbf.zip"


# --- Fixtures individual/hogar --------------------------------------------
#
# 5 personas en Gran La Plata (aglomerado 2), PONDERA=100 c/u, más 1 persona
# en aglomerado 33 (PONDERA=500, valores absurdos) para verificar que el
# filtro por aglomerado excluye todo lo demás:
#
#   P1 varón   30a  ocupado    asalariado    formal    secund. compl.  cobertura sí
#   P2 mujer   20a  ocupado    cuentapropia  informal  secund. incompl. sin cobertura, asiste
#   P3 varón   45a  desocupado                          primaria compl.
#   P4 mujer   15a  inactivo (estudiante)                analfabeta, asiste
#   P5 varón    5a  menor de 10 (ESTADO=4)                no asiste
#
# Población de referencia (ESTADO en 1,2,3) = P1-P4 = 400 ponderado.
# PEA (1,2) = P1,P2,P3 = 300. Ocupados (1) = P1,P2 = 200.


@pytest.fixture
def individual_gran_la_plata():
    aglomerado2 = {
        "AGLOMERADO": [2, 2, 2, 2, 2],
        "PONDERA": [100, 100, 100, 100, 100],
        "CH04": [1, 2, 1, 2, 1],
        "CH06": [30, 20, 45, 15, 5],
        "ESTADO": [1, 1, 2, 3, 4],
        "CAT_OCUP": [3, 2, None, None, None],
        "PP07H": [1, 2, None, None, None],
        "PP07G1": [1, 2, None, None, None],
        "PP07G2": [1, 2, None, None, None],
        "PP07G4": [1, 2, None, None, None],
        "CH08": [1, 4, 1, 1, 1],
        "NIVEL_ED": [4, 3, 2, 2, None],
        "CH09": [1, 1, 1, 2, None],
        "CH10": [2, 1, 2, 1, 2],
        "P21": [50000, 20000, 0, 0, 0],
        "P47T": [50000, 20000, 0, 0, 0],
    }
    fuera = {
        "AGLOMERADO": [33],
        "PONDERA": [500],
        "CH04": [1],
        "CH06": [99],
        "ESTADO": [1],
        "CAT_OCUP": [3],
        "PP07H": [1],
        "PP07G1": [1],
        "PP07G2": [1],
        "PP07G4": [1],
        "CH08": [1],
        "NIVEL_ED": [6],
        "CH09": [1],
        "CH10": [2],
        "P21": [99999],
        "P47T": [99999],
    }
    filas = {k: aglomerado2[k] + fuera[k] for k in aglomerado2}
    filas["ANO4"] = [2018] * 6
    filas["TRIMESTRE"] = [1] * 6
    return pd.DataFrame(filas)


@pytest.fixture
def hogar_gran_la_plata():
    return pd.DataFrame(
        {
            "AGLOMERADO": [2, 2, 33],
            "PONDIH": [100, 100, 500],
            "IPCF": [20000, 40000, 99999],
            "IX_TOT": [4, 2, 1],
            "II1": [2, 2, 1],
            "IV7": [1, 2, 1],
            "II7": [1, 3, 1],
            "V5": [1, 2, 1],
            "V15": [2, 1, 1],
            "V17": [2, 1, 1],
        }
    )


class TestAgregadosGranLaPlataNucleoLaboral:
    def test_filtra_por_aglomerado_gran_la_plata(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["ingreso_ocupacion_principal_medio"] < 99999
        assert agregados["ipcf_medio"] < 99999

    def test_tasa_actividad(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["tasa_actividad"] == pytest.approx(0.75)  # PEA 300 / pob.ref. 400

    def test_tasa_empleo(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["tasa_empleo"] == pytest.approx(0.5)  # ocupados 200 / pob.ref. 400

    def test_tasa_desocupacion_sobre_pea(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["tasa_desocupacion"] == pytest.approx(1 / 3)

    def test_tasa_informalidad_sobre_ocupados(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["tasa_informalidad"] == pytest.approx(0.5)

    def test_ingreso_ocupacion_principal_medio(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["ingreso_ocupacion_principal_medio"] == pytest.approx(35000)

    def test_anio_y_trimestre_se_propagan(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["anio"] == 2018
        assert agregados["trimestre"] == 1


class TestAgregadosGranLaPlataOcupacionYEducacion:
    def test_composicion_ocupacional(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["pct_asalariado"] == pytest.approx(0.5)
        assert agregados["pct_cuentapropia"] == pytest.approx(0.5)
        assert agregados["pct_patron"] == pytest.approx(0.0)
        assert agregados["pct_trabajador_familiar"] == pytest.approx(0.0)

    def test_calidad_empleo_asalariado(self, individual_gran_la_plata, hogar_gran_la_plata):
        # único asalariado (P1) tiene los 3 beneficios -> 100%; la cuentapropista
        # (P2) no entra en la base de asalariados aunque sus PP07G* sean 2.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["pct_con_obra_social"] == pytest.approx(1.0)
        assert agregados["pct_con_aguinaldo"] == pytest.approx(1.0)
        assert agregados["pct_con_vacaciones_pagas"] == pytest.approx(1.0)

    def test_pct_sin_cobertura_salud(self, individual_gran_la_plata, hogar_gran_la_plata):
        # sobre las 5 personas de Gran La Plata (500 ponderado), solo P2 sin cobertura.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["pct_sin_cobertura_salud"] == pytest.approx(0.2)

    def test_pct_secundario_completo_o_mas(self, individual_gran_la_plata, hogar_gran_la_plata):
        # población 25+: P1 (secund. completo) y P3 (primaria completa) -> 1 de 2.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["pct_secundario_completo_o_mas"] == pytest.approx(0.5)

    def test_tasa_analfabetismo(self, individual_gran_la_plata, hogar_gran_la_plata):
        # población 10+: P1,P2,P3,P4 -> solo P4 analfabeta -> 1 de 4.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["tasa_analfabetismo"] == pytest.approx(0.25)

    def test_tasa_asistencia_escolar(self, individual_gran_la_plata, hogar_gran_la_plata):
        # población 5-24: P2,P4,P5 -> asisten P2 y P4 -> 2 de 3.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["tasa_asistencia_escolar"] == pytest.approx(2 / 3)

    def test_ingreso_total_individual_medio(self, individual_gran_la_plata, hogar_gran_la_plata):
        # sobre la población de referencia (400 ponderado), incluye ceros de P3/P4.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["ingreso_total_individual_medio"] == pytest.approx(17500)


class TestAgregadosGranLaPlataViviendaYEstrategias:
    def test_hacinamiento_medio(self, individual_gran_la_plata, hogar_gran_la_plata):
        # hogar A: 4 personas / 2 ambientes = 2.0; hogar B: 2/2 = 1.0; pesos iguales.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["hacinamiento_medio"] == pytest.approx(1.5)

    def test_pct_agua_red_publica(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["pct_agua_red_publica"] == pytest.approx(0.5)

    def test_pct_vivienda_propia(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["pct_vivienda_propia"] == pytest.approx(0.5)

    def test_estrategias_de_subsistencia(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["pct_hogares_ayuda_social_gobierno"] == pytest.approx(0.5)
        assert agregados["pct_hogares_prestamo_bancario"] == pytest.approx(0.5)
        assert agregados["pct_hogares_vendio_pertenencias"] == pytest.approx(0.5)

    def test_ipcf_medio_ponderado(self, individual_gran_la_plata, hogar_gran_la_plata):
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["ipcf_medio"] == pytest.approx(30000)

    def test_v5_dividida_desde_2023t4_se_reconstruye(self, individual_gran_la_plata, hogar_gran_la_plata):
        # desde 2023 T4 INDEC reemplazó V5 por V5_01/V5_02/V5_03 -- "Sí" en
        # cualquiera de las tres debe contar igual que V5=1 antes de la división.
        hogar_dividido = hogar_gran_la_plata.drop(columns=["V5"]).assign(
            V5_01=[1, 2, 2], V5_02=[2, 2, 2], V5_03=[2, 2, 2]
        )
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_dividido)
        assert agregados["pct_hogares_ayuda_social_gobierno"] == pytest.approx(0.5)

    def test_hogar_sin_pondih_usa_pondera(self, individual_gran_la_plata, hogar_gran_la_plata):
        # esquema de las bases DBF históricas (2011-2015): la base hogar no tiene PONDIH.
        hogar_historico = hogar_gran_la_plata.rename(columns={"PONDIH": "PONDERA"})
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_historico)
        assert agregados["ipcf_medio"] == pytest.approx(30000)


class TestAgregadosPorSexo:
    def test_una_fila_por_sexo(self, individual_gran_la_plata):
        filas = agregados_por_sexo(individual_gran_la_plata)
        assert {f["sexo"] for f in filas} == {"varon", "mujer"}
        assert len(filas) == 2

    def test_tasa_desocupacion_varon(self, individual_gran_la_plata):
        # varones en Gran La Plata: P1 (ocupado), P3 (desocupado), P5 (menor, fuera de PEA).
        filas = {f["sexo"]: f for f in agregados_por_sexo(individual_gran_la_plata)}
        assert filas["varon"]["tasa_desocupacion"] == pytest.approx(0.5)  # 1 de 2 en la PEA

    def test_tasa_desocupacion_mujer(self, individual_gran_la_plata):
        # mujeres en Gran La Plata: P2 (ocupada), P4 (inactiva) -> PEA = solo P2, 0% desocupación.
        filas = {f["sexo"]: f for f in agregados_por_sexo(individual_gran_la_plata)}
        assert filas["mujer"]["tasa_desocupacion"] == pytest.approx(0.0)

    def test_no_incluye_indicadores_de_hogar(self, individual_gran_la_plata):
        filas = agregados_por_sexo(individual_gran_la_plata)
        assert "ipcf_medio" not in filas[0]
        assert "hacinamiento_medio" not in filas[0]


class TestAgregadosPorEdad:
    def test_una_fila_por_tramo(self, individual_gran_la_plata):
        filas = agregados_por_edad(individual_gran_la_plata)
        assert {f["tramo_etario"] for f in filas} == {"10-24", "25-39", "40-59", "60+"}
        assert len(filas) == 4

    def test_tramo_10_24_incluye_solo_p2_y_p4(self, individual_gran_la_plata):
        # P2 (20a, ocupada) y P4 (15a, inactiva) -> PEA = solo P2 -> desocupación 0%.
        filas = {f["tramo_etario"]: f for f in agregados_por_edad(individual_gran_la_plata)}
        assert filas["10-24"]["tasa_desocupacion"] == pytest.approx(0.0)
        assert filas["10-24"]["tasa_empleo"] == pytest.approx(0.5)  # 1 ocupada de 2 en el tramo

    def test_tramo_40_59_incluye_solo_p3(self, individual_gran_la_plata):
        # P3 (45a, desocupado) es el único en el tramo -> desocupación 100%.
        filas = {f["tramo_etario"]: f for f in agregados_por_edad(individual_gran_la_plata)}
        assert filas["40-59"]["tasa_desocupacion"] == pytest.approx(1.0)

    def test_tramo_60_mas_vacio(self, individual_gran_la_plata):
        # nadie en el fixture tiene 60+ -> todas las tasas None (denominador cero).
        filas = {f["tramo_etario"]: f for f in agregados_por_edad(individual_gran_la_plata)}
        assert filas["60+"]["tasa_actividad"] is None
