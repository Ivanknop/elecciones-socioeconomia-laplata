"""Tests de la lógica pura (sin matplotlib) de `src/socioeconomia/graficos_eph_iaelap.py`.
"""
from socioeconomia.graficos_eph_iaelap import (
    _indice_hueco_no_publicado,
    _indice_primer_trimestre_desde,
)


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
