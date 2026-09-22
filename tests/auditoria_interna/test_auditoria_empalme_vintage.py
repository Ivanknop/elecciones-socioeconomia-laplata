"""Tests de `auditoria_interna.auditoria_empalme_vintage`."""
from datetime import date

import pandas as pd

from auditoria_interna.auditoria_empalme_vintage import (
    auditar_panel_trimestral,
    auditar_ventanas_mensuales,
    huecos_internos,
    saltos_de_nivel,
)


def _fechas(*valores):
    return [(date(2020, i + 1, 1), v) for i, v in enumerate(valores)]


class TestHuecosInternos:
    def test_detecta_un_hueco_interno_con_dato_real_de_ambos_lados(self):
        ordenados = _fechas(1.0, None, None, 4.0)
        huecos = huecos_internos(ordenados)
        assert len(huecos) == 1
        inicio, fin, n = huecos[0]
        assert inicio == date(2020, 2, 1) and fin == date(2020, 3, 1) and n == 2

    def test_sin_hueco_si_los_datos_son_consecutivos(self):
        assert huecos_internos(_fechas(1.0, 2.0, 3.0)) == []

    def test_ignora_huecos_en_los_bordes(self):
        # None al principio y al final -- no son "cruce de corte", son cobertura faltante en el borde.
        assert huecos_internos(_fechas(None, 1.0, 2.0, None)) == []

    def test_menos_de_dos_valores_reales_no_da_hueco(self):
        assert huecos_internos(_fechas(None, 1.0, None, None)) == []


class TestAuditarVentanasMensuales:
    def test_detecta_hueco_en_vc_y_en_vl(self):
        ventanas = [{
            "id_transicion": "municipal_2013_2017", "nivel": "municipal",
            "fecha_inicio_vc": "2015-01-01", "fecha_fin_vc": "2017-06-01",
            "fecha_inicio_vl": "2013-01-01",
        }]
        # Serie con hueco real 2015-06 a 2016-05 (dentro de vc y de vl).
        serie_ipc = {date(2013, m, 1): 100.0 for m in range(1, 13)}
        serie_ipc.update({date(2014, m, 1): 100.0 for m in range(1, 13)})
        serie_ipc.update({date(2015, m, 1): (100.0 if m < 6 else None) for m in range(1, 13)})
        serie_ipc.update({date(2016, m, 1): (None if m < 6 else 50.0) for m in range(1, 13)})
        serie_ipc.update({date(2017, m, 1): 50.0 for m in range(1, 7)})
        series = {"ipc": serie_ipc, "salario_real": {}, "resultado_fiscal": {}}

        resultado = auditar_ventanas_mensuales(ventanas, series)
        assert set(resultado["ventana"]) == {"vc", "vl"}
        assert (resultado[(resultado["ventana"] == "vc") & (resultado["variable"] == "ipc")]["n_meses_hueco"] == 12).all()

    def test_sin_bloque_largo_no_audita_vl(self):
        ventanas = [{
            "id_transicion": "municipal_2001_2003", "nivel": "municipal",
            "fecha_inicio_vc": "2001-01-01", "fecha_fin_vc": "2003-01-01", "fecha_inicio_vl": None,
        }]
        series = {"ipc": {date(2001, 1, 1): 1.0, date(2003, 1, 1): 2.0}, "salario_real": {}, "resultado_fiscal": {}}
        resultado = auditar_ventanas_mensuales(ventanas, series)
        assert "vl" not in set(resultado.get("ventana", []))


class TestSaltosDeNivel:
    def _panel(self, valores_municipal, valores_provincial=None):
        anios = [2003, 2005, 2007, 2009]
        filas = []
        for anio, v in zip(anios, valores_municipal):
            filas.append({"nivel": "municipal", "id_transicion": f"municipal_{anio}", "anio_t": anio, "resultado_fiscal_nivel_vc": v})
        if valores_provincial:
            for anio, v in zip(anios, valores_provincial):
                filas.append({"nivel": "provincial", "id_transicion": f"provincial_{anio}", "anio_t": anio, "resultado_fiscal_nivel_vc": v})
        return pd.DataFrame(filas)

    def test_detecta_salto_por_encima_del_umbral_alto(self):
        # salto x4.7: mismo patrón que salario_real_nivel_vc en D33 §3.1
        df = self._panel([4560.66, 5267.12, 21062.98, 19654.62])
        resultado = saltos_de_nivel(df, variables=("resultado_fiscal",))
        assert len(resultado) == 1
        fila = resultado.iloc[0]
        assert fila["id_transicion_anterior"] == "municipal_2005" and fila["id_transicion_actual"] == "municipal_2007"
        assert fila["razon_abs"] > 2.0
        assert not fila["cambia_signo"]

    def test_sin_salto_si_la_razon_queda_dentro_del_umbral(self):
        df = self._panel([-7847, -9000, -10500, -11000])
        assert saltos_de_nivel(df, variables=("resultado_fiscal",)).empty

    def test_detecta_cambio_de_signo_sin_calcular_razon_cruda(self):
        df = self._panel([-100.0, 50.0, 60.0, 70.0])
        resultado = saltos_de_nivel(df, variables=("resultado_fiscal",))
        assert len(resultado) == 1
        assert resultado.iloc[0]["cambia_signo"]
        assert resultado.iloc[0]["razon_abs"] is None or pd.notna(resultado.iloc[0]["razon_abs"])

    def test_ignora_nan_y_respeta_umbral_bajo(self):
        df = self._panel([100.0, None, 40.0, 39.0])
        resultado = saltos_de_nivel(df, variables=("resultado_fiscal",), umbral_bajo=0.5)
        # 40.0 vs 100.0 (fila anterior real) esta a distancia 2 filas pero NaN de por medio
        # se compara fila a fila consecutiva del dataframe, no salteando el NaN.
        assert resultado[(resultado["id_transicion_actual"] == "municipal_2009")].empty

    def test_agrupa_por_nivel_independientemente(self):
        df = self._panel([100.0, 105.0, 110.0, 115.0], valores_provincial=[100.0, 500.0, 510.0, 520.0])
        resultado = saltos_de_nivel(df, variables=("resultado_fiscal",))
        assert set(resultado["nivel"]) == {"provincial"}


class TestAuditarPanelTrimestral:
    def test_detecta_hueco_interno_en_las_filas_trimestre(self):
        panel = pd.DataFrame([
            {"id_transicion": "municipal_2013_2017", "nivel": "municipal", "orden": 0, "tipo_fila": "eleccion_t_menos_2", "ipc": None},
            {"id_transicion": "municipal_2013_2017", "nivel": "municipal", "orden": 1, "tipo_fila": "trimestre", "ipc": 2.0},
            {"id_transicion": "municipal_2013_2017", "nivel": "municipal", "orden": 2, "tipo_fila": "trimestre", "ipc": None},
            {"id_transicion": "municipal_2013_2017", "nivel": "municipal", "orden": 3, "tipo_fila": "trimestre", "ipc": None},
            {"id_transicion": "municipal_2013_2017", "nivel": "municipal", "orden": 4, "tipo_fila": "trimestre", "ipc": -39.1},
            {"id_transicion": "municipal_2013_2017", "nivel": "municipal", "orden": 5, "tipo_fila": "eleccion_t", "ipc": None},
        ])
        resultado = auditar_panel_trimestral(panel, variables=("ipc",))
        assert len(resultado) == 1
        fila = resultado.iloc[0]
        assert fila["n_trimestres_hueco"] == 2
        assert fila["orden_inicio_hueco"] == 2 and fila["orden_fin_hueco"] == 3
