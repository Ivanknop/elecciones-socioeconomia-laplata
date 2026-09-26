"""Tests de `ml_models.panel_k` (D32)."""
import csv

import pandas as pd
import pytest

from ml_models.cargar_series_economicas import FilaRegistroVariable
from ml_models.panel_k import (
    COLUMNAS_METADATA_PANEL_K,
    PREFIJOS_EPH,
    _acum_compuesto,
    _transiciones_ordenadas_y_anterior,
    _ventana_k,
    columnas_candidatas_k,
    construir_fila_k,
    construir_panel_k,
)


def _var(id_variable, es_flujo=False, paquete_atributos="completo"):
    return FilaRegistroVariable(
        id_variable=id_variable, descripcion="", fuente="", url_fuente="",
        periodicidad_nativa="trimestral", cobertura_desde="2001-01", cobertura_hasta="2025-12",
        nivel_geografico="nacional", polaridad="ambigua", es_flujo=es_flujo, nominal=False,
        bloque_tematico="", estado="activa", paquete_atributos=paquete_atributos,
    )


REGISTRO = [
    _var("ipc", es_flujo=True),
    _var("eph_var", paquete_atributos="reducido"),
    _var("macro_var"),
]


def _trimestres_df(id_transicion, nivel, anio_t, anio_t_menos_1, filas_valores):
    filas = []
    for i, valores in enumerate(filas_valores, start=1):
        fila = {
            "id_transicion": id_transicion, "nivel": nivel, "anio_t": anio_t, "anio_t_menos_1": anio_t_menos_1,
            "orden": i, "tipo_fila": "trimestre", "n_meses": 3,
        }
        fila.update(valores)
        filas.append(fila)
    return pd.DataFrame(filas)


def _frontera_series(tipo_fila, id_transicion, nivel, anio_t, anio_t_menos_1, share_oficialismo,
                      gana_oficialismo=True, participacion_pct=70.0, ausentismo=20.0,
                      votos_blancos_y_nulos=10.0, votantes_habilitados=100.0,
                      dispersion_economico_mu=0.0, dispersion_progresismo_mu=0.0,
                      dispersion_cobertura_share=90.0):
    return pd.Series({
        "id_transicion": id_transicion, "nivel": nivel, "anio_t": anio_t, "anio_t_menos_1": anio_t_menos_1,
        "tipo_fila": tipo_fila, "gana_oficialismo": gana_oficialismo, "share_oficialismo": share_oficialismo,
        "participacion_pct": participacion_pct, "ausentismo": ausentismo,
        "votos_blancos_y_nulos": votos_blancos_y_nulos, "votantes_habilitados": votantes_habilitados,
        "dispersion_economico_mu": dispersion_economico_mu, "dispersion_progresismo_mu": dispersion_progresismo_mu,
        "dispersion_cobertura_share": dispersion_cobertura_share,
    })


class TestAcumCompuesto:
    def test_compone_tasas_trimestrales(self):
        # (1.10 * 0.95 * 1.02 - 1) * 100
        esperado = (1.10 * 0.95 * 1.02 - 1) * 100
        assert _acum_compuesto([10.0, -5.0, 2.0]) == pytest.approx(esperado)

    def test_vacio_da_none(self):
        assert _acum_compuesto([]) is None


class TestVentanaK:
    # tasa_informalidad real de nacional_2003_2005 (verificado contra
    # panel_trimestral_nacional.csv, ver plan) -- últimos 4 y últimos 8 de
    # los 10 trimestres reales.
    _INFORMALIDAD_10 = [0.422827, 0.394356, 0.401817, 0.405286, 0.426941, 0.427727, 0.409277, 0.412225]
    _QUARTERS_10 = [(v, 3) for v in [0.399950, 0.413150] + _INFORMALIDAD_10]

    def test_nivel_con_datos_reales_k4_y_k8(self):
        r4 = _ventana_k(self._QUARTERS_10, k=4, es_flujo=False, reducido=False)
        assert r4["nivel"] == pytest.approx(0.41904223038732014)
        assert r4["k_efectivo"] == 4
        assert r4["ventana_truncada"] is False

        r8 = _ventana_k(self._QUARTERS_10, k=8, es_flujo=False, reducido=False)
        assert r8["nivel"] == pytest.approx(0.41255681381941434)
        assert r8["k_efectivo"] == 8
        assert r8["ventana_truncada"] is False

    def test_pendiente_volatilidad_y_final(self):
        quarters = [(1.0, 3), (2.0, 3), (3.0, 3), (4.0, 3)]
        r = _ventana_k(quarters, k=4, es_flujo=False, reducido=False)
        assert r["pendiente"] == pytest.approx(1.0)
        assert r["volatilidad"] == pytest.approx(1.2909944, rel=1e-5)
        assert r["final"] == pytest.approx(3.5)  # media de los últimos 2 (3, 4)

    def test_final_omitido_si_k_efectivo_menor_o_igual_a_2(self):
        quarters = [(1.0, 3), (2.0, 3)]
        r = _ventana_k(quarters, k=2, es_flujo=False, reducido=False)
        assert r["k_efectivo"] == 2
        assert r["final"] is None

    def test_reducido_solo_devuelve_nivel_y_metadata(self):
        quarters = [(0.40, 3), (0.41, 3), (0.42, 3), (0.43, 3)]
        r = _ventana_k(quarters, k=4, es_flujo=False, reducido=True)
        assert r["nivel"] == pytest.approx(0.415)
        assert set(r) == {"nivel", "k_efectivo", "meses_efectivos", "ventana_truncada", "cobertura_parcial"}

    def test_es_flujo_agrega_acum_compuesto(self):
        quarters = [(10.0, 3), (-5.0, 3), (2.0, 3)]
        r = _ventana_k(quarters, k=3, es_flujo=True, reducido=False)
        assert r["acum"] == pytest.approx((1.10 * 0.95 * 1.02 - 1) * 100)

    def test_ventana_truncada_si_hay_menos_trimestres_que_k(self):
        quarters = [(1.0, 3), (2.0, 3), (3.0, 3)]
        r = _ventana_k(quarters, k=8, es_flujo=False, reducido=False)
        assert r["k_efectivo"] == 3
        assert r["ventana_truncada"] is True
        assert r["meses_efectivos"] == 9

    def test_cobertura_parcial_true_si_hay_none_en_la_ventana(self):
        quarters = [(1.0, 3), (None, 3), (3.0, 3)]
        r = _ventana_k(quarters, k=3, es_flujo=False, reducido=False)
        assert r["cobertura_parcial"] is True
        assert r["nivel"] == pytest.approx(2.0)

    def test_todo_none_da_nivel_none_y_cobertura_parcial(self):
        quarters = [(None, 3), (None, 3), (None, 3)]
        r = _ventana_k(quarters, k=3, es_flujo=False, reducido=True)
        assert r["nivel"] is None
        assert r["cobertura_parcial"] is True


class TestTransicionesOrdenadasYAnterior:
    def test_ordena_por_anio_t_y_mapea_la_anterior(self):
        panel = pd.DataFrame([
            {"id_transicion": "nacional_2003_2005", "anio_t": 2005, "tipo_fila": "eleccion_t"},
            {"id_transicion": "nacional_2001_2003", "anio_t": 2003, "tipo_fila": "eleccion_t"},
            {"id_transicion": "nacional_2005_2007", "anio_t": 2007, "tipo_fila": "eleccion_t"},
        ])
        orden, anterior = _transiciones_ordenadas_y_anterior(panel)
        assert orden == ["nacional_2001_2003", "nacional_2003_2005", "nacional_2005_2007"]
        assert anterior == {
            "nacional_2001_2003": None,
            "nacional_2003_2005": "nacional_2001_2003",
            "nacional_2005_2007": "nacional_2003_2005",
        }


class TestConstruirFilaK:
    """`nacional_2001_2003` imita la ventana real pre-EPH (D32/D33): `eph_var`
    (paquete reducido, como las 6 EPH reales) sin ningún dato, mientras
    `ipc`/`macro_var` sí tienen dato. `nacional_2003_2005` imita la ventana
    real donde la EPH ya cubre todo el trimestre."""

    TRIMESTRES = {
        "nacional_2001_2003": _trimestres_df(
            "nacional_2001_2003", "nacional", 2003, 2001,
            [
                {"ipc": 0.5, "eph_var": None, "macro_var": 8.0},
                {"ipc": 0.6, "eph_var": None, "macro_var": 8.5},
                {"ipc": 0.7, "eph_var": None, "macro_var": 9.0},
            ],
        ),
        "nacional_2003_2005": _trimestres_df(
            "nacional_2003_2005", "nacional", 2005, 2003,
            [
                {"ipc": 1.0, "eph_var": 0.40, "macro_var": 10.0},
                {"ipc": 2.0, "eph_var": 0.41, "macro_var": 11.0},
                {"ipc": 3.0, "eph_var": 0.42, "macro_var": 12.0},
                {"ipc": 4.0, "eph_var": 0.43, "macro_var": 13.0},
            ],
        ),
    }
    FRONTERAS = {
        "nacional_2001_2003": (
            _frontera_series("eleccion_t_menos_1", "nacional_2001_2003", "nacional", 2003, 2001, share_oficialismo=20.0),
            _frontera_series("eleccion_t", "nacional_2001_2003", "nacional", 2003, 2001, share_oficialismo=30.0),
        ),
        "nacional_2003_2005": (
            _frontera_series("eleccion_t_menos_1", "nacional_2003_2005", "nacional", 2005, 2003, share_oficialismo=30.0),
            _frontera_series("eleccion_t", "nacional_2003_2005", "nacional", 2005, 2003, share_oficialismo=40.0),
        ),
    }
    ANTERIOR = {"nacional_2001_2003": None, "nacional_2003_2005": "nacional_2001_2003"}

    def test_modo_nivel_primera_transicion_no_necesita_anterior(self):
        fila = construir_fila_k(
            "nacional_2001_2003", "nivel", k=4, politica_truncado="truncar",
            trimestres_por_transicion=self.TRIMESTRES, fronteras_por_transicion=self.FRONTERAS,
            transicion_anterior=self.ANTERIOR, registro=REGISTRO,
        )
        assert fila is not None
        assert fila["delta_v"] == pytest.approx(10.0)  # 30 - 20
        assert fila["eph_var_nivel_kt"] is None  # pre-EPH, D32/D33
        assert fila["ipc_nivel_kt"] == pytest.approx((0.5 + 0.6 + 0.7) / 3)
        assert "eph_var_nivel_kt1" not in fila  # modo nivel: nunca columnas de W_{t-1}
        assert "k_efectivo_t_menos_1" not in fila

    def test_modo_delta_primera_transicion_da_none(self):
        fila = construir_fila_k(
            "nacional_2001_2003", "delta", k=4, politica_truncado="truncar",
            trimestres_por_transicion=self.TRIMESTRES, fronteras_por_transicion=self.FRONTERAS,
            transicion_anterior=self.ANTERIOR, registro=REGISTRO,
        )
        assert fila is None

    def test_modo_delta_recupera_kt_aunque_kt1_no_tenga_dato(self):
        fila = construir_fila_k(
            "nacional_2003_2005", "delta", k=4, politica_truncado="truncar",
            trimestres_por_transicion=self.TRIMESTRES, fronteras_por_transicion=self.FRONTERAS,
            transicion_anterior=self.ANTERIOR, registro=REGISTRO,
        )
        assert fila is not None
        # eph_var: kt real (ventana 2003-2005, con EPH), kt1/kd en None (ventana
        # 2001-2003, pre-EPH) -- el resto de la fila no se pierde por esto.
        assert fila["eph_var_nivel_kt"] == pytest.approx(0.415)
        assert fila["eph_var_nivel_kt1"] is None
        assert fila["eph_var_nivel_kd"] is None
        assert fila["eph_var_cobertura_parcial"] is True
        # ipc y macro_var sí tienen los dos lados
        assert fila["ipc_nivel_kt"] == pytest.approx(2.5)
        assert fila["ipc_nivel_kt1"] == pytest.approx(0.6)
        assert fila["ipc_nivel_kd"] == pytest.approx(2.5 - 0.6)
        assert fila["macro_var_nivel_kt"] == pytest.approx(11.5)
        assert fila["macro_var_nivel_kt1"] == pytest.approx(8.5)
        # ventana t-1 truncada (3 trimestres disponibles, k=4 pedido)
        assert fila["k_efectivo_t"] == 4 and fila["ventana_truncada_t"] is False
        assert fila["k_efectivo_t_menos_1"] == 3 and fila["ventana_truncada_t_menos_1"] is True
        assert fila["ventana_truncada"] is True
        assert fila["delta_v"] == pytest.approx(10.0)  # 40 - 30, igual que en modo nivel

    def test_politica_descartar_excluye_fila_truncada(self):
        fila = construir_fila_k(
            "nacional_2003_2005", "delta", k=4, politica_truncado="descartar",
            trimestres_por_transicion=self.TRIMESTRES, fronteras_por_transicion=self.FRONTERAS,
            transicion_anterior=self.ANTERIOR, registro=REGISTRO,
        )
        assert fila is None

    def test_targets_iguales_entre_modo_nivel_y_delta(self):
        fila_nivel = construir_fila_k(
            "nacional_2003_2005", "nivel", k=4, politica_truncado="truncar",
            trimestres_por_transicion=self.TRIMESTRES, fronteras_por_transicion=self.FRONTERAS,
            transicion_anterior=self.ANTERIOR, registro=REGISTRO,
        )
        fila_delta = construir_fila_k(
            "nacional_2003_2005", "delta", k=4, politica_truncado="truncar",
            trimestres_por_transicion=self.TRIMESTRES, fronteras_por_transicion=self.FRONTERAS,
            transicion_anterior=self.ANTERIOR, registro=REGISTRO,
        )
        for col in ("delta_v", "gana_oficialismo", "share_oficialismo", "delta_participacion_pct"):
            assert fila_nivel[col] == fila_delta[col]


def _escribir_registro_csv(path, variables):
    columnas = [
        "id_variable", "descripcion", "fuente", "url_fuente", "periodicidad_nativa",
        "cobertura_desde", "cobertura_hasta", "nivel_geografico", "polaridad", "es_flujo",
        "nominal", "bloque_tematico", "estado", "paquete_atributos", "nota_metodologica",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for var in variables:
            fila = {c: getattr(var, c) for c in columnas}
            fila["es_flujo"] = str(fila["es_flujo"]).lower()
            fila["nominal"] = str(fila["nominal"]).lower()
            writer.writerow(fila)


class TestConstruirPanelK:
    def test_arma_el_panel_completo_saltando_la_primera_transicion_en_modo_delta(self, tmp_path):
        filas = []
        for id_transicion, df in TestConstruirFilaK.TRIMESTRES.items():
            filas.append(df)
        frontera_t_menos_1_2001_2003 = TestConstruirFilaK.FRONTERAS["nacional_2001_2003"][0].to_frame().T
        frontera_t_2001_2003 = TestConstruirFilaK.FRONTERAS["nacional_2001_2003"][1].to_frame().T
        frontera_t_menos_1_2003_2005 = TestConstruirFilaK.FRONTERAS["nacional_2003_2005"][0].to_frame().T
        frontera_t_2003_2005 = TestConstruirFilaK.FRONTERAS["nacional_2003_2005"][1].to_frame().T

        panel = pd.concat([
            frontera_t_menos_1_2001_2003, TestConstruirFilaK.TRIMESTRES["nacional_2001_2003"], frontera_t_2001_2003,
            frontera_t_menos_1_2003_2005, TestConstruirFilaK.TRIMESTRES["nacional_2003_2005"], frontera_t_2003_2005,
        ], ignore_index=True)
        panel.to_csv(tmp_path / "panel_trimestral_nacional.csv", index=False)
        _escribir_registro_csv(tmp_path / "registro_variables.csv", REGISTRO)

        panel_nivel = construir_panel_k("nacional", k=4, modo="nivel", panel_dir=tmp_path, registro_path=tmp_path / "registro_variables.csv")
        assert len(panel_nivel) == 2  # las 2 transiciones, modo nivel no descarta ninguna
        assert set(panel_nivel["id_transicion"]) == {"nacional_2001_2003", "nacional_2003_2005"}

        panel_delta = construir_panel_k("nacional", k=4, modo="delta", panel_dir=tmp_path, registro_path=tmp_path / "registro_variables.csv")
        assert len(panel_delta) == 1  # nacional_2001_2003 se saltea (sin transición anterior)
        assert panel_delta["id_transicion"].tolist() == ["nacional_2003_2005"]

    def test_nivel_invalido_da_error(self, tmp_path):
        with pytest.raises(ValueError):
            construir_panel_k("invalido", k=4, modo="nivel", panel_dir=tmp_path)


class TestColumnasCandidatasK:
    def test_excluye_metadata_y_outcome_electoral(self):
        df = pd.DataFrame([{
            "id_transicion": "x", "k": 4, "modo": "nivel",
            "delta_v": 1.0, "gana_oficialismo": True,
            "ipc_nivel_kt": 2.5, "eph_var_nivel_kt": 0.4,
        }])
        candidatas = columnas_candidatas_k(df)
        assert "ipc_nivel_kt" in candidatas
        assert "eph_var_nivel_kt" in candidatas
        assert "delta_v" not in candidatas
        assert "id_transicion" not in candidatas  # no numérica, pero además es metadata
        for col in COLUMNAS_METADATA_PANEL_K:
            assert col not in candidatas

    def test_universo_sin_eph_excluye_los_6_prefijos_y_sus_sufijos(self):
        df = pd.DataFrame([{
            "ipc_nivel_kt": 2.5,
            "tasa_informalidad_nivel_kt": 0.4, "tasa_informalidad_nivel_kt1": 0.3, "tasa_informalidad_nivel_kd": 0.1,
            "pct_sin_cobertura_salud_nivel_kt": 0.2,
            "hacinamiento_medio_final_kt": 1.1,
            "pct_hogares_ayuda_social_gobierno_cobertura_parcial": 1.0,
            "pct_hogares_prestamo_bancario_nivel_kt": 0.05,
            "pct_hogares_vendio_pertenencias_nivel_kt": 0.03,
        }])
        completo = columnas_candidatas_k(df, universo="completo")
        sin_eph = columnas_candidatas_k(df, universo="sin_eph")

        assert set(completo) == set(df.columns)  # nada de esto es metadata/outcome
        assert sin_eph == ["ipc_nivel_kt"]
        for prefijo in PREFIJOS_EPH:
            assert not any(c.startswith(prefijo) for c in sin_eph)

    def test_universo_invalido_da_error(self):
        with pytest.raises(ValueError):
            columnas_candidatas_k(pd.DataFrame({"ipc_nivel_kt": [1.0]}), universo="invalido")
