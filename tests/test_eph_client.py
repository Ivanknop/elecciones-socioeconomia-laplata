"""Tests de `src/socioeconomia/eph_client.py`.
"""
import pandas as pd
import pytest

from socioeconomia.eph_client import (
    TrimestreNoPublicado,
    UrlDesconocida,
    _indicadores_laborales_core,
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
#
# PP07H de P2 vale 0 ("no corresponde"), no 2 -- P2 es cuentapropista
# (CAT_OCUP=2), y esa pregunta solo se le hace a asalariados. Es el patrón
# real confirmado en datos de INDEC (2011T1 y 2023T4): a los no-asalariados
# nunca se les pregunta, no quedan con un valor de "informal" espurio.
# PONDIIO/PONDII igual a PONDERA en este fixture (sin no-respuesta de
# ingreso) -- el caso con no-respuesta tiene su propio fixture dedicado
# más abajo.


@pytest.fixture
def individual_gran_la_plata():
    aglomerado2 = {
        "AGLOMERADO": [2, 2, 2, 2, 2],
        "PONDERA": [100, 100, 100, 100, 100],
        "PONDIIO": [100, 100, 100, 100, 100],
        "PONDII": [100, 100, 100, 100, 100],
        "CH04": [1, 2, 1, 2, 1],
        "CH06": [30, 20, 45, 15, 5],
        "ESTADO": [1, 1, 2, 3, 4],
        "CAT_OCUP": [3, 2, None, None, None],
        "PP07H": [1, 0, None, None, None],
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
        "PONDIIO": [500],
        "PONDII": [500],
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
        assert agregados["ingreso_ocupacion_principal_medio_todos_ocupados"] < 99999
        assert agregados["ingreso_ocupacion_principal_medio_perceptores"] < 99999
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

    def test_tasa_informalidad_sobre_asalariados_validos(self, individual_gran_la_plata, hogar_gran_la_plata):
        # único asalariado (P1) es formal (PP07H=1) -> 0% informalidad. P2
        # (cuentapropista, PP07H=0 "no corresponde") no entra en el
        # denominador -- antes sí entraba (denominador = todos los
        # ocupados), lo que subestimaba/distorsionaba la tasa.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["tasa_informalidad"] == pytest.approx(0.0)

    def test_ingreso_ocupacion_principal_medio_dos_estimandos(self, individual_gran_la_plata, hogar_gran_la_plata):
        # sin no-respuesta en este fixture, ambos estimandos coinciden:
        # (50000+20000)*100 / 200 ponderado = 35000.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["ingreso_ocupacion_principal_medio_todos_ocupados"] == pytest.approx(35000)
        assert agregados["ingreso_ocupacion_principal_medio_perceptores"] == pytest.approx(35000)

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

    def test_ingreso_total_individual_medio_dos_estimandos(self, individual_gran_la_plata, hogar_gran_la_plata):
        # sobre la población de referencia (400 ponderado), incluye ceros
        # válidos de P3/P4 (no hay no-respuesta en este fixture, así que
        # ambos estimandos coinciden).
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["ingreso_total_individual_medio_todos"] == pytest.approx(17500)
        assert agregados["ingreso_total_individual_medio_perceptores"] == pytest.approx(17500)


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

    def test_pct_inquilino(self, individual_gran_la_plata, hogar_gran_la_plata):
        # II7 en Gran La Plata: hogar A=1 (propietario), hogar B=3 (inquilino).
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["pct_inquilino"] == pytest.approx(0.5)

    def test_tamanio_hogar_medio(self, individual_gran_la_plata, hogar_gran_la_plata):
        # IX_TOT en Gran La Plata: hogar A=4, hogar B=2, pesos iguales -> 3.0.
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_gran_la_plata)
        assert agregados["tamanio_hogar_medio"] == pytest.approx(3.0)

    def test_distribucion_hacinamiento_incluye_los_tres_buckets(self, individual_gran_la_plata, hogar_gran_la_plata):
        # agrega dos hogares sintéticos Gran La Plata (ratio 3.0 "moderado" y
        # 4.0 "crítico") sin tocar los hogares A/B del fixture compartido
        # (que ya cubren "bajo": ratios 2.0 y 1.0).
        extra = pd.DataFrame(
            {
                "AGLOMERADO": [2, 2],
                "PONDIH": [100, 100],
                "IPCF": [10000, 10000],
                "IX_TOT": [6, 8],
                "II1": [2, 2],
                "IV7": [1, 1],
                "II7": [1, 1],
                "V5": [2, 2],
                "V15": [2, 2],
                "V17": [2, 2],
            }
        )
        hogar_extendido = pd.concat([hogar_gran_la_plata, extra], ignore_index=True)
        agregados = agregados_gran_la_plata(individual_gran_la_plata, hogar_extendido)
        # 4 hogares Gran La Plata, pesos iguales: ratios 2.0, 1.0, 3.0, 4.0.
        assert agregados["pct_hacinamiento_bajo"] == pytest.approx(0.5)  # 2.0 y 1.0
        assert agregados["pct_hacinamiento_moderado"] == pytest.approx(0.25)  # 3.0
        assert agregados["pct_hacinamiento_critico"] == pytest.approx(0.25)  # 4.0
        suma = (
            agregados["pct_hacinamiento_bajo"]
            + agregados["pct_hacinamiento_moderado"]
            + agregados["pct_hacinamiento_critico"]
        )
        assert suma == pytest.approx(1.0)

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


# --- Fixtures dedicadas a los dos bugs de INDEC corregidos -----------------
#
# Patrones confirmados contra microdatos reales (2023T4 y 2011T1, Gran La
# Plata): P21==-9 (no respuesta) coincide siempre con PONDIIO==0 en la base;
# PP07H vale 0 ("no corresponde") para patrón/cuentapropia, y también puede
# venir en 0 como no-respuesta de ítem dentro de asalariados (visto en
# 2011T1 histórico). Ninguna de las dos fixtures toca `individual_gran_la_plata`.


@pytest.fixture
def individual_con_no_respuesta_ingreso():
    """3 ocupados: 2 asalariados con ingreso válido y PONDIIO==PONDERA, 1
    con P21==-9 (no responde) y PONDIIO==0 -- patrón real de 2023T4."""
    return pd.DataFrame(
        {
            "ESTADO": [1, 1, 1],
            "CAT_OCUP": [3, 3, 3],
            "PP07H": [1, 1, 1],
            "PONDERA": [100, 100, 100],
            "PONDIIO": [100, 100, 0],
            "P21": [30000, 50000, -9],
        }
    )


class TestIngresoOcupacionPrincipalDosEstimandos:
    def test_todos_ocupados_trata_no_respuesta_como_cero(self, individual_con_no_respuesta_ingreso):
        core = _indicadores_laborales_core(individual_con_no_respuesta_ingreso)
        # (30000+50000+0)*100 / 300 ponderado = 26666.67
        assert core["ingreso_ocupacion_principal_medio_todos_ocupados"] == pytest.approx(80000 / 3)

    def test_perceptores_excluye_no_respuesta_y_usa_pondiio(self, individual_con_no_respuesta_ingreso):
        core = _indicadores_laborales_core(individual_con_no_respuesta_ingreso)
        # (30000*100 + 50000*100) / (100+100) pondiio = 40000 -- el no
        # respondente (PONDIIO=0) queda fuera de numerador y denominador.
        assert core["ingreso_ocupacion_principal_medio_perceptores"] == pytest.approx(40000)

    def test_perceptores_usa_pondera_si_no_hay_pondiio(self, individual_con_no_respuesta_ingreso):
        # esquema histórico (2011-2015): la base individual no tiene PONDIIO.
        sin_pondiio = individual_con_no_respuesta_ingreso.drop(columns=["PONDIIO"])
        core = _indicadores_laborales_core(sin_pondiio)
        assert core["ingreso_ocupacion_principal_medio_perceptores"] == pytest.approx(40000)


@pytest.fixture
def individual_con_no_asalariados_y_pp07h_cero():
    """Patrón y cuentapropista con PP07H==0 ('no corresponde'), más un
    asalariado formal y uno informal -- replica CAT_OCUP 1/2/3 con PP07H
    real confirmado en 2023T4 y 2011T1."""
    return pd.DataFrame(
        {
            "ESTADO": [1, 1, 1, 1],
            "CAT_OCUP": [1, 2, 3, 3],
            "PP07H": [0, 0, 1, 2],
            "PONDERA": [100, 100, 100, 100],
            "PONDIIO": [100, 100, 100, 100],
            "P21": [10000, 10000, 10000, 10000],
        }
    )


@pytest.fixture
def individual_asalariados_con_no_respuesta_item():
    """3 asalariados: formal, informal, y uno con PP07H==0 -- no-respuesta
    de ítem real (no "no corresponde", la pregunta sí les aplica)."""
    return pd.DataFrame(
        {
            "ESTADO": [1, 1, 1],
            "CAT_OCUP": [3, 3, 3],
            "PP07H": [1, 2, 0],
            "PONDERA": [100, 100, 100],
            "PONDIIO": [100, 100, 100],
            "P21": [10000, 10000, 10000],
        }
    )


class TestTasaInformalidadDenominadorCorrecto:
    def test_excluye_patron_y_cuentapropia_del_denominador(self, individual_con_no_asalariados_y_pp07h_cero):
        # denominador correcto = solo asalariados con PP07H válido (200
        # ponderado: formal+informal), no los 400 de todos los ocupados.
        # Antes el patrón/cuentapropista (PP07H==0, nunca puede ser ==2)
        # inflaban el denominador sin poder entrar nunca al numerador.
        core = _indicadores_laborales_core(individual_con_no_asalariados_y_pp07h_cero)
        assert core["tasa_informalidad"] == pytest.approx(0.5)  # 100 informal / 200 asalariados válidos

    def test_excluye_asalariado_con_pp07h_no_respondido(self, individual_asalariados_con_no_respuesta_item):
        # denominador = solo los 2 asalariados con PP07H en {1,2} (200
        # ponderado), no los 3 asalariados totales (300) -- el residual de
        # no-respuesta de ítem no se puede clasificar ni como formal ni
        # como informal, así que se excluye de ambos.
        core = _indicadores_laborales_core(individual_asalariados_con_no_respuesta_item)
        assert core["tasa_informalidad"] == pytest.approx(0.5)  # 100 informal / 200 válidos, no / 300


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
