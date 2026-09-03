"""Tests de `visualizacion.trayectorias_economicas`: lógica pura de
armado del payload (extracción de series, label, salario en dólares) --
a diferencia de `mapa_interactivo`/`distribucion_ideologica_interactiva`,
esta lógica es nueva acá, no reusada de un módulo ya testeado, así que sí
se testea directamente (ver skill `laplata-visualizacion`)."""
import csv
from datetime import date

import pytest

from ml_models.construir_calendario import construir_calendario, construir_ventanas
from ml_models.construir_panel_trimestral import calcular_n_trimestres
from constantes import PANEL_TRIMESTRAL_DIR, SERIES_ECONOMICAS_MENSUALES_PATH
from visualizacion.trayectorias_economicas import (
    _label_ventana,
    _salario_real_usd_mensual,
    _serie_variable,
    _variables_de,
    construir_payload,
)


class TestVariablesDe:
    def test_excluye_columnas_fijas(self):
        filas = [{"id_transicion": "x", "nivel": "municipal", "orden": "0", "ipc": "1.0", "desocupacion": "2.0"}]
        assert _variables_de(filas) == ["desocupacion", "ipc"]

    def test_lista_vacia_sin_filas(self):
        assert _variables_de([]) == []


class TestSerieVariable:
    def test_valores_en_orden_vacio_es_none(self):
        filas = [{"ipc": "1.5"}, {"ipc": ""}, {"ipc": "3.0"}]
        assert _serie_variable(filas, "ipc") == [1.5, None, 3.0]


class TestLabelVentana:
    def test_formato(self):
        assert _label_ventana("2001", "2003") == "2001→2003"


class TestSalarioRealUsdMensual:
    def test_reconstruye_nominal_antes_de_dividir_por_tipo_de_cambio(self):
        """Una división directa `salario_real/tc_oficial` da un orden de
        magnitud equivocado: ~15-20 en vez de ~1000-1500 USD/mes."""
        crudas = {
            "salario_real": {date(2020, 1, 1): 500.0},
            "ipc": {date(2020, 1, 1): 200.0},
            "tc_oficial": {date(2020, 1, 1): 4.0},
        }
        resultado = _salario_real_usd_mensual(crudas)
        assert resultado[date(2020, 1, 1)] == pytest.approx(250.0)  # (500*200/100)/4

    def test_none_si_falta_algun_dato(self):
        crudas = {
            "salario_real": {date(2020, 1, 1): 500.0},
            "ipc": {date(2020, 1, 1): None},
            "tc_oficial": {date(2020, 1, 1): 4.0},
        }
        assert _salario_real_usd_mensual(crudas)[date(2020, 1, 1)] is None

    def test_none_si_tc_oficial_es_cero(self):
        crudas = {
            "salario_real": {date(2020, 1, 1): 500.0},
            "ipc": {date(2020, 1, 1): 200.0},
            "tc_oficial": {date(2020, 1, 1): 0.0},
        }
        assert _salario_real_usd_mensual(crudas)[date(2020, 1, 1)] is None


_COLUMNAS_FIXTURE = [
    "id_transicion", "nivel", "anio_t", "anio_t_menos_1", "orden", "tipo_fila",
    "n_meses", "periodo_intervenido", "gana_oficialismo", "share_oficialismo",
    "agrupacion_oficialismo", "x",
]


def _escribir_csv(tmp_path, nombre, filas, columnas=_COLUMNAS_FIXTURE):
    destino = tmp_path / nombre
    with destino.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)


class TestConstruirPayloadSintetico:
    def test_series_no_incluye_columnas_fijas(self, tmp_path):
        comunes = {
            "id_transicion": "municipal_2011_2013",
            "nivel": "municipal",
            "anio_t": "2013",
            "anio_t_menos_1": "2011",
            "n_meses": "",
            "periodo_intervenido": "",
            "share_oficialismo": "",
            "x": "",
        }
        filas = [
            {**comunes, "orden": "0", "tipo_fila": "eleccion_t_menos_1", "gana_oficialismo": "True", "agrupacion_oficialismo": "A"},
            {**comunes, "orden": "1", "tipo_fila": "eleccion_t", "gana_oficialismo": "True", "agrupacion_oficialismo": "A"},
        ]
        _escribir_csv(tmp_path, "panel_trimestral_municipal.csv", filas)
        _escribir_csv(tmp_path, "panel_trimestral_provincial.csv", [])
        _escribir_csv(tmp_path, "panel_trimestral_nacional.csv", [])

        payload = construir_payload(panel_dir=tmp_path)
        assert "x" in payload["variables"]
        assert "orden" not in payload["variables"]
        assert "gana_oficialismo" not in payload["variables"]

    def test_agrupaciones_y_anios_presentes_sin_ruptura(self, tmp_path):
        comunes = {
            "id_transicion": "municipal_2011_2013",
            "nivel": "municipal",
            "anio_t": "2013",
            "anio_t_menos_1": "2011",
            "n_meses": "",
            "periodo_intervenido": "",
            "share_oficialismo": "",
            "x": "",
        }
        filas = [
            {**comunes, "orden": "0", "tipo_fila": "eleccion_t_menos_1", "gana_oficialismo": "True", "agrupacion_oficialismo": "OFICIALISMO"},
            {**comunes, "orden": "1", "tipo_fila": "trimestre", "gana_oficialismo": "", "agrupacion_oficialismo": "", "x": "10.0"},
            {**comunes, "orden": "2", "tipo_fila": "eleccion_t", "gana_oficialismo": "True", "agrupacion_oficialismo": "OTRO"},
        ]
        _escribir_csv(tmp_path, "panel_trimestral_municipal.csv", filas)
        _escribir_csv(tmp_path, "panel_trimestral_provincial.csv", [])
        _escribir_csv(tmp_path, "panel_trimestral_nacional.csv", [])

        payload = construir_payload(panel_dir=tmp_path)
        ventana = payload["trayectorias"]["municipal"]["municipal_2011_2013"]
        assert ventana["agrupacion_inicio"] == "OFICIALISMO"
        assert ventana["agrupacion_t"] == "OTRO"
        assert ventana["anio_t"] == 2013
        assert ventana["anio_inicio_ventana"] == 2011
        assert ventana["series"]["x"] == [10.0]
        assert "ruptura" not in ventana


class TestSalarioRealUsdEnPayload:
    def test_reconstruye_correctamente_desde_series_mensuales(self, tmp_path):
        columnas = _COLUMNAS_FIXTURE + ["fecha_inicio", "fecha_fin", "salario_real"]
        comunes = {
            "id_transicion": "municipal_2011_2013",
            "nivel": "municipal",
            "anio_t": "2013",
            "anio_t_menos_1": "2011",
            "n_meses": "",
            "periodo_intervenido": "",
            "gana_oficialismo": "True",
            "share_oficialismo": "",
            "agrupacion_oficialismo": "A",
            "x": "",
            "salario_real": "",
        }
        filas = [
            {**comunes, "orden": "0", "tipo_fila": "eleccion_t_menos_1", "fecha_inicio": "2011-01-14", "fecha_fin": "2011-01-14"},
            {**comunes, "orden": "1", "tipo_fila": "trimestre", "n_meses": "1", "fecha_inicio": "2011-02-01", "fecha_fin": "2011-02-01"},
            {**comunes, "orden": "2", "tipo_fila": "eleccion_t", "fecha_inicio": "2013-01-14", "fecha_fin": "2013-01-14"},
        ]
        _escribir_csv(tmp_path, "panel_trimestral_municipal.csv", filas, columnas)
        _escribir_csv(tmp_path, "panel_trimestral_provincial.csv", [], columnas)
        _escribir_csv(tmp_path, "panel_trimestral_nacional.csv", [], columnas)

        series_mensuales_path = tmp_path / "series_mensuales.csv"
        with series_mensuales_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["fecha", "ipc", "tc_oficial", "salario_real"])
            writer.writeheader()
            writer.writerow({"fecha": "2011-02-01", "ipc": "200.0", "tc_oficial": "4.0", "salario_real": "500.0"})

        payload = construir_payload(panel_dir=tmp_path, series_mensuales_path=series_mensuales_path)
        ventana = payload["trayectorias"]["municipal"]["municipal_2011_2013"]
        assert ventana["series"]["salario_real_usd"] == [pytest.approx(250.0)]  # (500*200/100)/4
        assert "salario_real" not in ventana["series"]
        assert "salario_real_usd" in payload["variables"]
        assert "salario_real" not in payload["variables"]


class TestIntegracionDatosReales:
    """Contra los CSV ya committeados de data/tfi_data/panel/ y
    data/tfi_data/series_economicas_mensuales.csv (sin red), mismo
    criterio que el test equivalente de test_panel_ventanas.py."""

    def test_31_ventanas_totales(self):
        payload = construir_payload(panel_dir=PANEL_TRIMESTRAL_DIR)
        total = sum(len(v) for v in payload["trayectorias"].values())
        assert total == 31

    def test_largo_de_serie_coincide_con_calcular_n_trimestres(self):
        payload = construir_payload(panel_dir=PANEL_TRIMESTRAL_DIR)
        ventanas_reales = construir_ventanas(construir_calendario())
        for v in ventanas_reales:
            n_esperado = calcular_n_trimestres(v.fecha_inicio_vc, v.fecha_fin_vc)
            ventana = payload["trayectorias"][v.nivel][v.id_transicion]
            alguna_variable = next(iter(ventana["series"]))
            assert len(ventana["series"][alguna_variable]) == n_esperado, v.id_transicion

    def test_variables_coinciden_con_columnas_reales_del_csv_salvo_salario_renombrado(self):
        with open(f"{PANEL_TRIMESTRAL_DIR}/panel_trimestral_municipal.csv", encoding="utf-8") as f:
            columnas = next(csv.reader(f))
        columnas_fijas = {
            "id_transicion", "nivel", "anio_t", "anio_t_menos_1", "orden", "tipo_fila",
            "fecha_inicio", "fecha_fin", "n_meses", "periodo_intervenido",
            "gana_oficialismo", "share_oficialismo", "agrupacion_oficialismo",
        }
        esperadas = {c for c in columnas if c not in columnas_fijas}
        esperadas = sorted((esperadas - {"salario_real"}) | {"salario_real_usd"})

        payload = construir_payload(panel_dir=PANEL_TRIMESTRAL_DIR)
        assert payload["variables"] == esperadas

    def test_unidades_presentes_para_todas_las_variables(self):
        payload = construir_payload(panel_dir=PANEL_TRIMESTRAL_DIR)
        for var in payload["variables"]:
            assert payload["unidades"].get(var), var

    def test_nacional_2023_2025_refleja_el_fix_de_titular(self):
        """Regresión directa del fix de _TITULAR_REAL_DIVERGE_DE_VOTO_LA_PLATA
        para (nacional, 2023) -- ver docs/decisiones_metodologicas.md."""
        payload = construir_payload(panel_dir=PANEL_TRIMESTRAL_DIR)
        ventana = payload["trayectorias"]["nacional"]["nacional_2023_2025"]
        assert ventana["agrupacion_inicio"] == "FRENTE DE TODOS"
        assert ventana["agrupacion_t"] == "ALIANZA LA LIBERTAD AVANZA"

    def test_salario_real_usd_da_ordenes_de_magnitud_plausibles(self):
        """Ver `TestSalarioRealUsdMensual` para el porqué del rango esperado."""
        payload = construir_payload(panel_dir=PANEL_TRIMESTRAL_DIR)
        ventana = payload["trayectorias"]["nacional"]["nacional_2023_2025"]
        valores = [v for v in ventana["series"]["salario_real_usd"] if v is not None]
        assert valores
        assert all(200 < v < 5000 for v in valores)
