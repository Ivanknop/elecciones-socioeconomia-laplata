"""Tests de `src/macroeconomia/series_anuales.py`: normalización pura a
tabla anual (sin red -- `puntos_por_concepto` se arma a mano en cada test).
"""
from datetime import date

from macroeconomia.series import ConceptoCatalogo
from macroeconomia.series_anuales import _valor_exacto_para_anio, construir_tabla_anual


class TestValorExactoParaAnio:
    def test_anio_con_dato_exacto(self):
        puntos = [(date(2011, 1, 1), 10.0), (date(2012, 1, 1), 20.0)]
        assert _valor_exacto_para_anio(puntos, 2012) == 20.0

    def test_no_repite_el_ultimo_dato_si_el_siguiente_anio_no_se_publico_todavia(self):
        puntos = [(date(2011, 1, 1), 100.0)]
        assert _valor_exacto_para_anio(puntos, 2015) is None

    def test_anio_anterior_al_primer_dato_no_tiene_valor(self):
        puntos = [(date(2016, 1, 1), 5.0)]
        assert _valor_exacto_para_anio(puntos, 2011) is None


class TestConstruirTablaAnual:
    def _catalogo(self):
        return [
            ConceptoCatalogo("gasto_deuda_publica_nivel", "id1", "anual", "finanzas_publicas"),
            ConceptoCatalogo("gasto_deuda_publica_pib", "id2", "anual", "finanzas_publicas"),
        ]

    def _puntos(self):
        return {
            "gasto_deuda_publica_nivel": [(date(2011, 1, 1), 100.0), (date(2012, 1, 1), 200.0)],
            "gasto_deuda_publica_pib": [(date(2011, 1, 1), 1.5)],
        }

    def test_una_fila_por_anio_en_el_rango_pedido(self):
        filas, _ = construir_tabla_anual(self._catalogo(), self._puntos(), anio_inicio=2011, anio_fin=2013)
        assert [f["anio"] for f in filas] == [2011, 2012, 2013]

    def test_dato_real_queda_en_su_propio_anio(self):
        filas, _ = construir_tabla_anual(self._catalogo(), self._puntos(), anio_inicio=2011, anio_fin=2013)
        assert filas[0]["gasto_deuda_publica_nivel"] == 100.0
        assert filas[1]["gasto_deuda_publica_nivel"] == 200.0

    def test_anio_sin_dato_queda_vacio_con_observacion(self):
        filas, _ = construir_tabla_anual(self._catalogo(), self._puntos(), anio_inicio=2011, anio_fin=2013)
        anio_2013 = filas[2]
        assert anio_2013["gasto_deuda_publica_nivel"] == ""
        assert "gasto_deuda_publica_nivel: sin dato" in anio_2013["observaciones"]

    def test_no_repite_el_ultimo_valor_publicado(self):
        filas, _ = construir_tabla_anual(self._catalogo(), self._puntos(), anio_inicio=2011, anio_fin=2013)
        assert filas[1]["gasto_deuda_publica_pib"] == ""  # 2012, sin dato propio -- no hereda el de 2011

    def test_concepto_sin_ningun_dato_aparece_en_el_reporte(self):
        catalogo = [ConceptoCatalogo("vacio", "id5", "anual", "dim")]
        filas, reporte = construir_tabla_anual(catalogo, {}, anio_inicio=2011, anio_fin=2013)
        assert reporte.conceptos_sin_ningun_dato == ("vacio",)
        assert all(f["vacio"] == "" for f in filas)

    def test_reporte_de_cobertura_cuenta_celdas_reales_y_vacias(self):
        filas, reporte = construir_tabla_anual(self._catalogo(), self._puntos(), anio_inicio=2011, anio_fin=2013)
        assert reporte.celdas_totales == 3 * 2
        assert reporte.celdas_con_dato_real == 3  # nivel: 2011, 2012; pib: 2011
        assert reporte.celdas_vacias == 3
        assert reporte.celdas_con_dato_real + reporte.celdas_vacias == reporte.celdas_totales

    def test_orden_de_columnas_sigue_el_orden_del_catalogo(self):
        filas, _ = construir_tabla_anual(self._catalogo(), self._puntos(), anio_inicio=2011, anio_fin=2011)
        assert list(filas[0].keys()) == ["anio", "gasto_deuda_publica_nivel", "gasto_deuda_publica_pib", "observaciones"]
