"""Tests de `src/macroeconomia/series.py`: normalización pura a tabla
mensual (sin red -- `puntos_por_concepto` se arma a mano en cada test).
"""
from datetime import date

from macroeconomia.series import (
    ConceptoCatalogo,
    _parsear_puntos,
    _valor_exacto_para_mes,
    _valor_para_mes_diario,
    construir_tabla_mensual,
)


class TestParsearPuntos:
    def test_descarta_nulos_y_ordena_ascendente(self):
        cruda = [["2023-03-01", 3.0], ["2023-01-01", 1.0], ["2023-02-01", None]]
        assert _parsear_puntos(cruda) == [(date(2023, 1, 1), 1.0), (date(2023, 3, 1), 3.0)]


class TestValorExactoParaMes:
    def test_mes_con_dato_exacto(self):
        puntos = [(date(2023, 1, 1), 10.0), (date(2023, 2, 1), 20.0)]
        assert _valor_exacto_para_mes(puntos, date(2023, 2, 1)) == 20.0

    def test_trimestral_no_tiene_valor_en_los_meses_siguientes_del_trimestre(self):
        puntos = [(date(2023, 1, 1), 100.0), (date(2023, 4, 1), 110.0)]
        # febrero y marzo (dentro del trimestre de enero) NO toman el valor de enero
        assert _valor_exacto_para_mes(puntos, date(2023, 2, 1)) is None
        assert _valor_exacto_para_mes(puntos, date(2023, 3, 1)) is None

    def test_no_repite_el_ultimo_dato_si_el_siguiente_periodo_no_se_publico_todavia(self):
        puntos = [(date(2023, 1, 1), 100.0)]
        assert _valor_exacto_para_mes(puntos, date(2023, 6, 1)) is None

    def test_mes_anterior_al_primer_dato_no_tiene_valor(self):
        puntos = [(date(2016, 12, 1), 5.0)]
        assert _valor_exacto_para_mes(puntos, date(2016, 1, 1)) is None


class TestValorParaMesDiario:
    def test_usa_el_ultimo_dia_habil_del_mes_si_tiene_dato(self):
        # 2023-01-31 es martes (hábil)
        puntos = {date(2023, 1, 31): 350.0, date(2023, 1, 30): 349.0}
        valor, fecha, ajustado = _valor_para_mes_diario(puntos, date(2023, 1, 1))
        assert (valor, fecha, ajustado) == (350.0, date(2023, 1, 31), False)

    def test_cae_al_habil_anterior_si_el_cierre_no_tiene_dato_feriado(self):
        # 2023-01-31 (hábil) sin dato -> usa 2023-01-30 (lunes hábil anterior)
        puntos = {date(2023, 1, 30): 349.0}
        valor, fecha, ajustado = _valor_para_mes_diario(puntos, date(2023, 1, 1))
        assert (valor, fecha, ajustado) == (349.0, date(2023, 1, 30), True)

    def test_fin_de_semana_no_cuenta_como_ajuste(self):
        # 2023-04-30 es domingo; el hábil de cierre real es 2023-04-28 (viernes)
        puntos = {date(2023, 4, 28): 220.0}
        valor, fecha, ajustado = _valor_para_mes_diario(puntos, date(2023, 4, 1))
        assert (valor, fecha, ajustado) == (220.0, date(2023, 4, 28), False)

    def test_ningun_habil_del_mes_con_dato_devuelve_none(self):
        puntos = {date(2023, 2, 1): 1.0}  # ninguna fecha de enero
        valor, fecha, ajustado = _valor_para_mes_diario(puntos, date(2023, 1, 1))
        assert (valor, fecha, ajustado) == (None, None, False)


class TestConstruirTablaMensual:
    def _catalogo(self):
        return [
            ConceptoCatalogo("mensual_x", "id1", "mensual", "dim"),
            ConceptoCatalogo("trimestral_x", "id2", "trimestral", "dim"),
            ConceptoCatalogo("diaria_x", "id3", "diaria", "dim"),
        ]

    def _puntos(self):
        return {
            "mensual_x": [(date(2023, 1, 1), 1.0), (date(2023, 2, 1), 2.0)],
            "trimestral_x": [(date(2023, 1, 1), 100.0)],
            # 2023-01-31 es martes hábil
            "diaria_x": [(date(2023, 1, 31), 350.0)],
        }

    def test_una_fila_por_mes_en_el_rango_pedido(self):
        filas, _ = construir_tabla_mensual(self._catalogo(), self._puntos(), anio_inicio=2023, anio_fin=2023)
        assert [f["fecha"] for f in filas] == [date(2023, m, 1).isoformat() for m in range(1, 13)]

    def test_dato_real_no_genera_observacion_de_repetido(self):
        filas, _ = construir_tabla_mensual(self._catalogo(), self._puntos(), anio_inicio=2023, anio_fin=2023)
        enero = filas[0]
        assert enero["mensual_x"] == 1.0
        assert "repetido" not in enero["observaciones"]

    def test_trimestral_queda_vacio_en_meses_2_y_3_del_trimestre(self):
        filas, _ = construir_tabla_mensual(self._catalogo(), self._puntos(), anio_inicio=2023, anio_fin=2023)
        febrero, marzo = filas[1], filas[2]
        assert febrero["trimestral_x"] == ""
        assert "trimestral_x: sin dato" in febrero["observaciones"]
        assert marzo["trimestral_x"] == ""
        assert "trimestral_x: sin dato" in marzo["observaciones"]

    def test_diaria_sin_ningun_dia_habil_con_dato_en_el_mes_queda_vacia_no_repite(self):
        # diaria_x solo tiene dato en enero; febrero no tiene ningún día hábil con dato
        filas, _ = construir_tabla_mensual(self._catalogo(), self._puntos(), anio_inicio=2023, anio_fin=2023)
        febrero = filas[1]
        assert febrero["diaria_x"] == ""
        assert "diaria_x: sin dato" in febrero["observaciones"]

    def test_mes_anterior_al_primer_dato_queda_vacio_con_observacion(self):
        catalogo = [ConceptoCatalogo("tardia", "id4", "mensual", "dim")]
        puntos = {"tardia": [(date(2023, 6, 1), 9.0)]}
        filas, reporte = construir_tabla_mensual(catalogo, puntos, anio_inicio=2023, anio_fin=2023)
        enero = filas[0]
        assert enero["tardia"] == ""
        assert "tardia: sin dato" in enero["observaciones"]
        assert reporte.celdas_vacias == 11  # todos los meses salvo junio

    def test_concepto_sin_ningun_dato_aparece_en_el_reporte(self):
        catalogo = [ConceptoCatalogo("vacio", "id5", "mensual", "dim")]
        filas, reporte = construir_tabla_mensual(catalogo, {}, anio_inicio=2023, anio_fin=2023)
        assert reporte.conceptos_sin_ningun_dato == ("vacio",)
        assert all(f["vacio"] == "" for f in filas)

    def test_reporte_de_cobertura_cuenta_celdas_reales_y_vacias(self):
        filas, reporte = construir_tabla_mensual(self._catalogo(), self._puntos(), anio_inicio=2023, anio_fin=2023)
        assert reporte.celdas_totales == 12 * 3
        # mensual_x: 2 reales (ene, feb), 10 vacías
        # trimestral_x: 1 real (ene), 11 vacías
        # diaria_x: 1 real (ene), 11 vacías
        assert reporte.celdas_con_dato_real == 4
        assert reporte.celdas_vacias == reporte.celdas_totales - 4
        assert reporte.celdas_con_dato_real + reporte.celdas_vacias == reporte.celdas_totales
        assert reporte.porcentaje_dato_real > 0

    def test_orden_de_columnas_sigue_el_orden_del_catalogo(self):
        filas, _ = construir_tabla_mensual(self._catalogo(), self._puntos(), anio_inicio=2023, anio_fin=2023)
        assert list(filas[0].keys()) == ["fecha", "mensual_x", "trimestral_x", "diaria_x", "observaciones"]
