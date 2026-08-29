"""Tests de la lógica pura (sin matplotlib) de `src/socioeconomia/graficos_eph_iaelap.py`.
"""
import csv

from socioeconomia.graficos_eph_iaelap import (
    _indice_hueco_no_publicado,
    _indice_primer_trimestre_desde,
    datos_iaelap_general,
    datos_iaelap_sectorial,
)


def _escribir_csv(path, filas):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0]))
        writer.writeheader()
        writer.writerows(filas)


def _filas(periodos):
    return [{"anio": str(a), "trimestre": str(t)} for a, t in periodos]


class TestIndiceHuecoNoPublicado:
    def test_sin_hueco_devuelve_none(self):
        filas = _filas([(2011, 1), (2011, 2), (2011, 3)])
        assert _indice_hueco_no_publicado(filas) is None

    def test_detecta_hueco_2015t3_2016t1(self):
        # 2015T2 -> 2016T2: salta 2015T3, 2015T4 y 2016T1 (3 trimestres sin publicar).
        filas = _filas([(2015, 1), (2015, 2), (2016, 2), (2016, 3)])
        assert _indice_hueco_no_publicado(filas) == (1, 2)

    def test_devuelve_el_primer_hueco_si_hay_varios(self):
        filas = _filas([(2011, 1), (2011, 3), (2012, 1), (2012, 4)])
        assert _indice_hueco_no_publicado(filas) == (0, 1)


class TestIndicePrimerTrimestreDesde:
    def test_encuentra_el_primer_trimestre_igual_o_posterior(self):
        filas = _filas([(2019, 3), (2019, 4), (2020, 1), (2020, 2)])
        assert _indice_primer_trimestre_desde(filas, 2020, 1) == 2

    def test_none_si_ningun_trimestre_alcanza_el_valor(self):
        filas = _filas([(2011, 1), (2011, 2)])
        assert _indice_primer_trimestre_desde(filas, 2020, 1) is None

    def test_encuentra_el_indice_exacto_2023t4(self):
        filas = _filas([(2023, 3), (2023, 4), (2024, 1)])
        assert _indice_primer_trimestre_desde(filas, 2023, 4) == 1


class TestDatosIaelapGeneral:
    def test_devuelve_una_fila_por_periodo_con_variacion_interanual(self, tmp_path):
        _escribir_csv(tmp_path / "iaelap_la_plata.csv", [
            {"anio": "2023", "trimestre": "1", "var_interanual_pct": "5.5"},
            {"anio": "2023", "trimestre": "2", "var_interanual_pct": "-2.1"},
        ])
        filas = datos_iaelap_general(tmp_path)
        assert filas == [
            {"anio": 2023, "trimestre": 1, "etiqueta": "2023T1", "var_interanual_pct": 5.5},
            {"anio": 2023, "trimestre": 2, "etiqueta": "2023T2", "var_interanual_pct": -2.1},
        ]

    def test_periodo_sin_publicar_queda_en_none(self, tmp_path):
        _escribir_csv(tmp_path / "iaelap_la_plata.csv", [
            {"anio": "2023", "trimestre": "1", "var_interanual_pct": ""},
        ])
        filas = datos_iaelap_general(tmp_path)
        assert filas[0]["var_interanual_pct"] is None


class TestDatosIaelapSectorial:
    def test_filtra_por_periodo_tipo_anio_y_trimestre(self, tmp_path):
        _escribir_csv(tmp_path / "iaelap_la_plata_ramas.csv", [
            {"periodo_tipo": "trimestral", "anio": "2025", "trimestre": "4", "rama": "Comercio", "var_interanual_pct": "3.0"},
            {"periodo_tipo": "trimestral", "anio": "2025", "trimestre": "3", "rama": "Comercio", "var_interanual_pct": "1.0"},
            {"periodo_tipo": "anual", "anio": "2025", "trimestre": "", "rama": "Comercio", "var_interanual_pct": "2.0"},
        ])
        filas = datos_iaelap_sectorial(tmp_path, "trimestral", 2025, 4)
        assert filas == [{"rama": "Comercio", "var_interanual_pct": 3.0}]

    def test_excluye_la_fila_agregada_iaelap_y_ordena_por_variacion(self, tmp_path):
        _escribir_csv(tmp_path / "iaelap_la_plata_ramas.csv", [
            {"periodo_tipo": "anual", "anio": "2025", "trimestre": "", "rama": "IAELaP", "var_interanual_pct": "2.0"},
            {"periodo_tipo": "anual", "anio": "2025", "trimestre": "", "rama": "Industria", "var_interanual_pct": "4.0"},
            {"periodo_tipo": "anual", "anio": "2025", "trimestre": "", "rama": "Construcción", "var_interanual_pct": "-1.0"},
        ])
        filas = datos_iaelap_sectorial(tmp_path, "anual", 2025)
        assert [f["rama"] for f in filas] == ["Construcción", "Industria"]
