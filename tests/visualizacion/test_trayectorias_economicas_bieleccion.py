"""Tests de `visualizacion.trayectorias_economicas_bieleccion`: mismo
criterio que `test_trayectorias_economicas.py`, pero sobre el esquema de
columnas `anio_t_menos_2`/`eleccion_t_menos_2` del bloque largo (ver
`ml_models.construir_panel_bieleccion_trimestral`)."""
import csv

import pytest

from constantes import PANEL_BIELECCION_TRIMESTRAL_DIR
from ml_models.construir_calendario import construir_calendario, construir_ventanas
from ml_models.construir_panel_trimestral import calcular_n_trimestres
from visualizacion.trayectorias_economicas_bieleccion import construir_payload

_COLUMNAS_FIXTURE = [
    "id_transicion", "nivel", "anio_t", "anio_t_menos_2", "orden", "tipo_fila",
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
            "id_transicion": "municipal_2009_2013",
            "nivel": "municipal",
            "anio_t": "2013",
            "anio_t_menos_2": "2009",
            "n_meses": "",
            "periodo_intervenido": "",
            "share_oficialismo": "",
            "x": "",
        }
        filas = [
            {**comunes, "orden": "0", "tipo_fila": "eleccion_t_menos_2", "gana_oficialismo": "True", "agrupacion_oficialismo": "A"},
            {**comunes, "orden": "1", "tipo_fila": "eleccion_t", "gana_oficialismo": "True", "agrupacion_oficialismo": "A"},
        ]
        _escribir_csv(tmp_path, "panel_bieleccion_trimestral_municipal.csv", filas)
        _escribir_csv(tmp_path, "panel_bieleccion_trimestral_provincial.csv", [])
        _escribir_csv(tmp_path, "panel_bieleccion_trimestral_nacional.csv", [])

        payload = construir_payload(panel_dir=tmp_path)
        assert "x" in payload["variables"]
        assert "orden" not in payload["variables"]
        assert "anio_t_menos_2" not in payload["variables"]

    def test_agrupaciones_y_anios_presentes_usa_anio_t_menos_2(self, tmp_path):
        comunes = {
            "id_transicion": "municipal_2009_2013",
            "nivel": "municipal",
            "anio_t": "2013",
            "anio_t_menos_2": "2009",
            "n_meses": "",
            "periodo_intervenido": "",
            "share_oficialismo": "",
            "x": "",
        }
        filas = [
            {**comunes, "orden": "0", "tipo_fila": "eleccion_t_menos_2", "gana_oficialismo": "True", "agrupacion_oficialismo": "OFICIALISMO"},
            {**comunes, "orden": "1", "tipo_fila": "trimestre", "gana_oficialismo": "", "agrupacion_oficialismo": "", "x": "10.0"},
            {**comunes, "orden": "2", "tipo_fila": "eleccion_t", "gana_oficialismo": "True", "agrupacion_oficialismo": "OTRO"},
        ]
        _escribir_csv(tmp_path, "panel_bieleccion_trimestral_municipal.csv", filas)
        _escribir_csv(tmp_path, "panel_bieleccion_trimestral_provincial.csv", [])
        _escribir_csv(tmp_path, "panel_bieleccion_trimestral_nacional.csv", [])

        payload = construir_payload(panel_dir=tmp_path)
        ventana = payload["trayectorias"]["municipal"]["municipal_2009_2013"]
        assert ventana["agrupacion_inicio"] == "OFICIALISMO"
        assert ventana["agrupacion_t"] == "OTRO"
        assert ventana["anio_t"] == 2013
        assert ventana["anio_inicio_ventana"] == 2009
        assert ventana["label"] == "2009→2013"
        assert ventana["series"]["x"] == [10.0]


class TestIntegracionDatosReales:
    """Contra los CSV ya committeados de data/tfi_data/panel/t-2/ (sin
    red), mismo criterio que el equivalente en test_trayectorias_economicas.py."""

    def test_28_transiciones_totales(self):
        """12 municipal + 12 provincial + 7 nacional ventanas `_vc`, menos
        una por nivel sin bloque largo (la primera transición de cada
        nivel) = 11 + 11 + 6 = 28."""
        payload = construir_payload(panel_dir=PANEL_BIELECCION_TRIMESTRAL_DIR)
        total = sum(len(v) for v in payload["trayectorias"].values())
        assert total == 28

    def test_largo_de_serie_coincide_con_calcular_n_trimestres_del_bloque_largo(self):
        payload = construir_payload(panel_dir=PANEL_BIELECCION_TRIMESTRAL_DIR)
        ventanas_reales = [v for v in construir_ventanas(construir_calendario()) if v.fecha_inicio_vl is not None]
        for v in ventanas_reales:
            n_esperado = calcular_n_trimestres(v.fecha_inicio_vl, v.fecha_fin_vc)
            id_transicion = f"{v.nivel}_{v.anio_t_menos_2}_{v.anio_t}"
            ventana = payload["trayectorias"][v.nivel][id_transicion]
            alguna_variable = next(iter(ventana["series"]))
            assert len(ventana["series"][alguna_variable]) == n_esperado, id_transicion

    def test_unidades_presentes_para_todas_las_variables(self):
        payload = construir_payload(panel_dir=PANEL_BIELECCION_TRIMESTRAL_DIR)
        for var in payload["variables"]:
            assert payload["unidades"].get(var), var
