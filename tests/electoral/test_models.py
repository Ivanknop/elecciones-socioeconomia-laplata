"""Tests de `src/electoral/models.py`: parseo del JSON crudo de la API a
dataclasses tipadas, y las tres propiedades derivadas de `ResultadoElectoral`.

"""
from electoral.models import (
    EstadoRecuento,
    Lista,
    ResultadoElectoral,
    ValoresOtros,
    ValorAgrupacion,
    totalizar_agrupaciones,
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
    def test_from_json_parsea_campos_basicos_listas_y_extra(self, raw_valor_agrupacion):
        assert "listas" not in raw_valor_agrupacion
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.id_agrupacion == "0131"
        assert valor.votos == 160079
        assert valor.votos_porcentaje == 45.44
        assert valor.nombre_agrupacion == "Alianza Frente para la Victoria"
        assert valor.listas == []
        assert valor.extra == {"idAgrupacionTelegrama": "", "urlLogo": ""}
        conocidos = {"idAgrupacion", "nombreAgrupacion", "votos", "votosPorcentaje", "listas"}
        assert conocidos.isdisjoint(valor.extra)

    def test_id_agrupacion_se_castea_a_str(self, raw_valor_agrupacion):
        raw_valor_agrupacion["idAgrupacion"] = 131  # la API real ya lo manda como string
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.id_agrupacion == "131"
        assert isinstance(valor.id_agrupacion, str)

    def test_listas_se_parsean_si_estan_presentes(self, raw_valor_agrupacion, raw_lista):
        raw_valor_agrupacion["listas"] = [raw_lista]
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.listas == [Lista(nombre="LISTA 3 - UNIDAD", votos=1234, numero="3")]

    def test_extra_detecta_campo_nuevo_no_documentado(self, raw_valor_agrupacion):
        raw_valor_agrupacion["campoQueLaApiAgregueMañana"] = 42
        valor = ValorAgrupacion.from_json(raw_valor_agrupacion)
        assert valor.extra["campoQueLaApiAgregueMañana"] == 42


class TestTotalizarAgrupaciones:
    def test_totaliza_suma_ordena_y_recalcula_porcentaje(self):
        valores = [
            ValorAgrupacion("0131", "Frente A", 40, 99.0),  # porcentaje viejo, de otra consulta
            ValorAgrupacion("0131", "Frente A", 35, 99.0),  # mismo id que el anterior: se suman
            ValorAgrupacion("0047", "Frente B", 25, 1.0),
        ]
        totales = totalizar_agrupaciones(valores)
        assert {v.id_agrupacion: v.votos for v in totales} == {"0131": 75, "0047": 25}
        assert [v.id_agrupacion for v in totales] == ["0131", "0047"]  # mayor a menor
        por_id = {v.id_agrupacion: v.votos_porcentaje for v in totales}
        assert por_id["0131"] == 75.0  # recalculado sobre el nuevo total, no el 99.0 viejo
        assert por_id["0047"] == 25.0
        assert totales[0].nombre_agrupacion == "Frente A"

    def test_lista_vacia_no_rompe(self):
        assert totalizar_agrupaciones([]) == []


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
    def test_from_json_parsea_estructura_completa(self, raw_resultado_electoral):
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.fecha_totalizacion == "2026-07-26T15:28:11.171Z"
        assert isinstance(resultado.estado_recuento, EstadoRecuento)
        assert resultado.estado_recuento.mesas_totalizadas == 1429
        assert isinstance(resultado.valores_totalizados_otros, ValoresOtros)
        assert len(resultado.valores_totalizados_positivos) == 2
        assert all(isinstance(v, ValorAgrupacion) for v in resultado.valores_totalizados_positivos)
        assert resultado.consulta == {}
        assert resultado.ganador.nombre_agrupacion == "Alianza Frente para la Victoria"
        assert resultado.ganador.votos == 160079
        assert resultado.total_votos_positivos == 160079 + 13177

    def test_consulta_se_guarda_si_se_pasa(self, raw_resultado_electoral):
        consulta = {"anio_eleccion": 2011, "nivel": "intendente"}
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral, consulta=consulta)
        assert resultado.consulta == consulta

    def test_extra_guarda_campo_de_nivel_superior_no_documentado(self, raw_resultado_electoral):
        raw_resultado_electoral["nuevoCampoDeLaApi"] = "x"
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.extra == {"nuevoCampoDeLaApi": "x"}

    def test_ganador_en_empate_devuelve_el_primero_de_la_lista(self, raw_resultado_electoral):
        # documenta el comportamiento real de max(): con empate exacto en votos,
        # gana el primer elemento en el orden de valoresTotalizadosPositivos.
        raw_resultado_electoral["valoresTotalizadosPositivos"][1]["votos"] = (
            raw_resultado_electoral["valoresTotalizadosPositivos"][0]["votos"]
        )
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.ganador.id_agrupacion == "0131"

    def test_sin_agrupaciones_positivas_ganador_none_y_total_cero(self, raw_resultado_electoral):
        raw_resultado_electoral["valoresTotalizadosPositivos"] = []
        resultado = ResultadoElectoral.from_json(raw_resultado_electoral)
        assert resultado.ganador is None
        assert resultado.total_votos_positivos == 0

    def test_es_mesa_segun_presencia_de_mesa_id_en_consulta(self, raw_resultado_electoral):
        assert ResultadoElectoral.from_json(raw_resultado_electoral).es_mesa is False
        sin_mesa_id = ResultadoElectoral.from_json(raw_resultado_electoral, consulta={"anio_eleccion": 2011})
        assert sin_mesa_id.es_mesa is False
        con_mesa_id = ResultadoElectoral.from_json(raw_resultado_electoral, consulta={"mesa_id": 5})
        assert con_mesa_id.es_mesa is True
