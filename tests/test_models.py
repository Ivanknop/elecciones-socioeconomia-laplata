"""Tests de `src/electoral/models.py`: parseo del JSON crudo de la API a
dataclasses tipadas, y las tres propiedades derivadas de `ResultadoElectoral`.

No pega a la API: todo corre sobre fixtures en `conftest.py` recortadas de
JSON real ya cacheado en `data/`.
"""
from electoral.models import (
    EstadoRecuento,
    Lista,
    ResultadoElectoral,
    ValoresOtros,
    ValorAgrupacion,
)


class TestLista:
    def test_from_json_con_numero(self, raw_lista):
        lista = Lista.from_json(raw_lista)
        assert lista.nombre == "LISTA 3 - UNIDAD"
        assert lista.votos == 1234
        assert lista.numero == "3"

    def test_from_json_sin_numero(self):
        lista = Lista.from_json({"nombre": "LISTA UNICA", "votos": 10})
        assert lista.numero is None


class TestValorAgrupacion:
    def test_from_json_campos_basicos(self, raw_valor_agrupacion):
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.id_agrupacion == "0131"
        assert valor.votos == 160079
        assert valor.votos_porcentaje == 45.44

    def test_from_json_recorta_espacios_del_nombre(self, raw_valor_agrupacion):
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.nombre_agrupacion == "Alianza Frente para la Victoria"

    def test_id_agrupacion_se_castea_a_str(self, raw_valor_agrupacion):
        raw_valor_agrupacion["idAgrupacion"] = 131  # la API real ya lo manda como string
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.id_agrupacion == "131"
        assert isinstance(valor.id_agrupacion, str)

    def test_listas_por_defecto_vacia_si_falta_la_clave(self, raw_valor_agrupacion):
        assert "listas" not in raw_valor_agrupacion
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.listas == []

    def test_listas_se_parsean_si_estan_presentes(self, raw_valor_agrupacion, raw_lista):
        raw_valor_agrupacion["listas"] = [raw_lista]
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.listas == [Lista(nombre="LISTA 3 - UNIDAD", votos=1234, numero="3")]

    def test_extra_guarda_campos_no_modelados(self, raw_valor_agrupacion):
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.extra == {"idAgrupacionTelegrama": "", "urlLogo": ""}

    def test_extra_no_repite_campos_conocidos(self, raw_valor_agrupacion):
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        conocidos = {"idAgrupacion", "nombreAgrupacion", "votos", "votosPorcentaje", "listas"}
        assert conocidos.isdisjoint(valor.extra)

    def test_extra_detecta_campo_nuevo_no_documentado(self, raw_valor_agrupacion):
        raw_valor_agrupacion["campoQueLaApiAgregueMañana"] = 42
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.extra["campoQueLaApiAgregueMañana"] == 42


class TestEstadoRecuento:
    def test_from_json_mapea_todos_los_campos(self, raw_estado_recuento):
        estado = EstadoRecuento.from_json(raw_estado_recuento)
        assert estado.mesas_esperadas == 0
        assert estado.mesas_totalizadas == 1429
        assert estado.mesas_totalizadas_porcentaje == 0
        assert estado.cantidad_electores == 493225
        assert estado.cantidad_votantes == 384273
        assert estado.participacion_porcentaje == 77.91

    def test_extra_guarda_campo_no_documentado(self, raw_estado_recuento):
        raw_estado_recuento["tipoRecuento"] = "Provisorio"
        estado = EstadoRecuento.from_json(raw_estado_recuento)
        assert estado.extra == {"tipoRecuento": "Provisorio"}


class TestValoresOtros:
    def test_from_json_mapea_todos_los_campos(self, raw_valores_otros):
        otros = ValoresOtros.from_json(raw_valores_otros)
        assert otros.votos_nulos == 2941
        assert otros.votos_nulos_porcentaje == 0.77
        assert otros.votos_en_blanco == 28864
        assert otros.votos_en_blanco_porcentaje == 7.51
        assert otros.votos_recurridos_comando_impugnados == 184
        assert otros.votos_recurridos_comando_impugnados_porcentaje == 0.05

    def test_extra_guarda_campo_no_documentado(self, raw_valores_otros):
        raw_valores_otros["votosComando"] = 3
        otros = ValoresOtros.from_json(raw_valores_otros)
        assert otros.extra == {"votosComando": 3}


class TestResultadoElectoral:
    def test_from_json_parsea_estructura_anidada(self, raw_resultado_electoral):
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.fecha_totalizacion == "2026-07-26T15:28:11.171Z"
        assert isinstance(resultado.estado_recuento, EstadoRecuento)
        assert resultado.estado_recuento.mesas_totalizadas == 1429
        assert isinstance(resultado.valores_totalizados_otros, ValoresOtros)
        assert len(resultado.valores_totalizados_positivos) == 2
        assert all(isinstance(v, ValorAgrupacion) for v in resultado.valores_totalizados_positivos)

    def test_consulta_por_defecto_vacia(self, raw_resultado_electoral):
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.consulta == {}

    def test_consulta_se_guarda_si_se_pasa(self, raw_resultado_electoral):
        consulta = {"anio_eleccion": 2011, "nivel": "intendente"}
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral, consulta=consulta)
        assert resultado.consulta == consulta

    def test_extra_guarda_campo_de_nivel_superior_no_documentado(self, raw_resultado_electoral):
        raw_resultado_electoral["nuevoCampoDeLaApi"] = "x"
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.extra == {"nuevoCampoDeLaApi": "x"}

    def test_ganador_devuelve_la_agrupacion_con_mas_votos(self, raw_resultado_electoral):
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.ganador.nombre_agrupacion == "Alianza Frente para la Victoria"
        assert resultado.ganador.votos == 160079

    def test_ganador_es_none_si_no_hay_positivos(self, raw_resultado_electoral):
        raw_resultado_electoral["valoresTotalizadosPositivos"] = []
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.ganador is None

    def test_ganador_en_empate_devuelve_el_primero_de_la_lista(self, raw_resultado_electoral):
        # documenta el comportamiento real de max(): con empate exacto en votos,
        # gana el primer elemento en el orden de valoresTotalizadosPositivos.
        raw_resultado_electoral["valoresTotalizadosPositivos"][1]["votos"] = (
            raw_resultado_electoral["valoresTotalizadosPositivos"][0]["votos"]
        )
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.ganador.id_agrupacion == "0131"

    def test_total_votos_positivos_suma_todas_las_agrupaciones(self, raw_resultado_electoral):
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.total_votos_positivos == 160079 + 13177

    def test_total_votos_positivos_es_cero_sin_agrupaciones(self, raw_resultado_electoral):
        raw_resultado_electoral["valoresTotalizadosPositivos"] = []
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.total_votos_positivos == 0

    def test_es_mesa_false_sin_consulta(self, raw_resultado_electoral):
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.es_mesa is False

    def test_es_mesa_false_si_consulta_no_tiene_mesa_id(self, raw_resultado_electoral):
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral, consulta={"anio_eleccion": 2011})
        assert resultado.es_mesa is False

    def test_es_mesa_true_si_consulta_trae_mesa_id(self, raw_resultado_electoral):
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral, consulta={"mesa_id": 5})
        assert resultado.es_mesa is True
