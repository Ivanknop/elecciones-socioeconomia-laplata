"""Tests de `ml_models.construir_calendario`: calendario electoral y
oficialismo por nivel, 2001-2025. Puro -- sin red, sin archivos reales
(usa `clasificacion`/`oficialismos` sintéticos)."""
from ml_models.construir_calendario import (
    construir_calendario,
    construir_oficialismo_por_nivel,
)


class TestConstruirCalendario:
    def test_nacional_solo_desde_2011(self):
        calendario = construir_calendario()
        anios_nacional = sorted(f.anio for f in calendario if f.nivel == "nacional")
        assert anios_nacional == [2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025]

    def test_municipal_y_provincial_cubren_2001_2025(self):
        calendario = construir_calendario()
        for nivel in ("municipal", "provincial"):
            anios = sorted(f.anio for f in calendario if f.nivel == nivel)
            assert anios == [2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025]

    def test_solo_2025_esta_desdoblada(self):
        calendario = construir_calendario()
        desdobladas = {(f.anio, f.nivel) for f in calendario if f.desdoblada}
        assert desdobladas == {(2025, "provincial"), (2025, "municipal")}

    def test_2025_nacional_no_esta_desdoblada(self):
        calendario = construir_calendario()
        fila = next(f for f in calendario if f.nivel == "nacional" and f.anio == 2025)
        assert fila.desdoblada is False

    def test_anios_ejecutivos_tienen_tipo_eleccion_ejecutiva(self):
        calendario = construir_calendario()
        for f in calendario:
            if f.nivel in ("municipal", "provincial") and f.anio in (2003, 2007, 2011, 2015, 2019, 2023):
                assert f.tipo_eleccion == "ejecutiva", f
            elif f.nivel in ("municipal", "provincial"):
                assert f.tipo_eleccion == "legislativa", f

    def test_fechas_no_vacias(self):
        calendario = construir_calendario()
        assert all(f.fecha_eleccion for f in calendario)


class _FilaCalendarioFake:
    def __init__(self, anio, nivel, tipo_eleccion="legislativa"):
        self.anio = anio
        self.nivel = nivel
        self.tipo_eleccion = tipo_eleccion
        self.fecha_eleccion = f"{anio}-01-01"
        self.desdoblada = False
        self.cargos_en_juego = ""


class TestConstruirOficialismoPorNivel:
    def test_agrupacion_oficialismo_es_el_titular_antes_de_la_eleccion_no_el_ganador(self):
        """Bug real encontrado: `agrupacion_oficialismo` no puede ser
        simplemente `agrupacion_ganadora` de esa misma fila -- si no, un
        desafiante que gana igual queda registrado como si ya fuera
        oficialismo (`gana_oficialismo` daría tautológicamente True
        siempre)."""
        calendario = [
            _FilaCalendarioFake(2011, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2013, "municipal", "legislativa"),
        ]
        oficialismos = {
            (2011, "municipal"): {
                "agrupacion_ganadora": "ALIANZA FRENTE PARA LA VICTORIA",
                "era_oficialismo": "true",
            },
            (2013, "municipal"): {
                "agrupacion_ganadora": "FRENTE RENOVADOR",  # gana la banca en juego, pero no es el Ejecutivo
                "era_oficialismo": "false",
            },
        }
        filas = construir_oficialismo_por_nivel(calendario, oficialismos, {})
        por_anio = {f.anio: f for f in filas}
        # el titular de 2013 sigue siendo quien ganó la intendencia en 2011,
        # no "Frente Renovador" (que solo ganó la banca de concejales de 2013)
        assert por_anio[2013].agrupacion_oficialismo == "ALIANZA FRENTE PARA LA VICTORIA"

    def test_era_oficialismo_false_en_ejecutiva_es_ruptura_y_cambia_el_titular(self):
        calendario = [
            _FilaCalendarioFake(2011, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2015, "municipal", "ejecutiva"),
        ]
        oficialismos = {
            (2011, "municipal"): {"agrupacion_ganadora": "ALIANZA FRENTE PARA LA VICTORIA", "era_oficialismo": "true"},
            (2015, "municipal"): {"agrupacion_ganadora": "CAMBIEMOS BUENOS AIRES", "era_oficialismo": "false"},
        }
        filas = construir_oficialismo_por_nivel(calendario, oficialismos, {})
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2015].agrupacion_oficialismo == "ALIANZA FRENTE PARA LA VICTORIA"  # titular ANTES de perder
        assert por_anio[2015].continuidad_oficialismo == "ruptura"

    def test_legislativa_nunca_cambia_el_titular_aunque_pierda_esa_banca(self):
        calendario = [
            _FilaCalendarioFake(2011, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2013, "municipal", "legislativa"),
            _FilaCalendarioFake(2015, "municipal", "ejecutiva"),
        ]
        oficialismos = {
            (2011, "municipal"): {"agrupacion_ganadora": "ALIANZA FRENTE PARA LA VICTORIA", "era_oficialismo": "true"},
            (2013, "municipal"): {"agrupacion_ganadora": "FRENTE RENOVADOR", "era_oficialismo": "false"},
            (2015, "municipal"): {"agrupacion_ganadora": "CAMBIEMOS BUENOS AIRES", "era_oficialismo": "false"},
        }
        filas = construir_oficialismo_por_nivel(calendario, oficialismos, {})
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2013].continuidad_oficialismo == "continua"
        # el 2015 sigue comparándose contra el titular de 2011, no contra
        # "Frente Renovador" (que nunca fue titular del Ejecutivo)
        assert por_anio[2015].agrupacion_oficialismo == "ALIANZA FRENTE PARA LA VICTORIA"
        assert por_anio[2015].continuidad_oficialismo == "ruptura"

    def test_pre_2011_municipal_usa_historia_investigada(self):
        calendario = [
            _FilaCalendarioFake(anio, "municipal", "ejecutiva" if anio in (2003, 2007) else "legislativa")
            for anio in (2001, 2003, 2005, 2007, 2009)
        ]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert len(filas) == 5
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2001].agrupacion_oficialismo == "PARTIDO JUSTICIALISTA"
        assert por_anio[2007].continuidad_oficialismo == "ruptura"
        assert por_anio[2007].agrupacion_oficialismo == "PARTIDO JUSTICIALISTA"  # titular ANTES de perder en 2007
        assert por_anio[2009].agrupacion_oficialismo == "PARTIDO PROGRESO SOCIAL"  # ya con el ganador de 2007

    def test_pre_2011_provincial_usa_historia_investigada(self):
        calendario = [
            _FilaCalendarioFake(anio, "provincial", "ejecutiva" if anio in (2003, 2007) else "legislativa")
            for anio in (2001, 2003, 2005, 2007, 2009)
        ]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2007].continuidad_oficialismo == "continua_renombrada"
        assert por_anio[2009].agrupacion_oficialismo == "ALIANZA FRENTE PARA LA VICTORIA"

    def test_divergencia_provincial_2019_corrige_el_titular_real(self):
        """La Plata votó a JUNTOS POR EL CAMBIO en el gobernador 2019, pero
        Kicillof/FRENTE DE TODOS ganó la gobernación real -- el titular
        para 2021 en adelante debe ser el ganador real, no el voto local."""
        calendario = [
            _FilaCalendarioFake(2015, "provincial", "ejecutiva"),
            _FilaCalendarioFake(2019, "provincial", "ejecutiva"),
            _FilaCalendarioFake(2021, "provincial", "legislativa"),
        ]
        oficialismos = {
            (2015, "provincial"): {"agrupacion_ganadora": "CAMBIEMOS BUENOS AIRES", "era_oficialismo": "false"},
            (2019, "provincial"): {"agrupacion_ganadora": "JUNTOS POR EL CAMBIO", "era_oficialismo": "true"},
        }
        filas = construir_oficialismo_por_nivel(calendario, oficialismos, {})
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2019].continuidad_oficialismo == "ruptura"  # el Ejecutivo real sí cambió
        assert por_anio[2021].agrupacion_oficialismo == "FRENTE DE TODOS"

    def test_nacional_pre_2011_no_genera_filas(self):
        calendario = [_FilaCalendarioFake(2003, "nacional")]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert filas == []

    def test_sin_fila_en_oficialismos_no_genera_fila_huerfana(self):
        calendario = [_FilaCalendarioFake(2025, "provincial", "ejecutiva")]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert filas == []

    def test_join_con_clasificacion_no_duplica_si_falta(self):
        calendario = [_FilaCalendarioFake(2001, "municipal")]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert filas[0].campo_ideologico == ""
        assert "clasificar" in filas[0].nota.lower()

    def test_join_con_clasificacion_usa_el_anio_en_que_el_titular_gano_no_el_de_la_fila(self):
        calendario = [
            _FilaCalendarioFake(2011, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2013, "municipal", "legislativa"),
        ]
        oficialismos = {
            (2011, "municipal"): {"agrupacion_ganadora": "ALIANZA FRENTE PARA LA VICTORIA", "era_oficialismo": "true"},
            (2013, "municipal"): {"agrupacion_ganadora": "FRENTE RENOVADOR", "era_oficialismo": "false"},
        }
        clasificacion = {
            ("2011", "ALIANZA FRENTE PARA LA VICTORIA", "intendente"): {
                "campo_ideologico": "3",
                "filiacion_politica": "peronistas",
                "vparty_economico": "-1.686",
                "vparty_progresismo": "2.097",
                "vparty_populismo": "0.871",
            }
        }
        filas = construir_oficialismo_por_nivel(calendario, oficialismos, clasificacion)
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2013].campo_ideologico == "3"  # heredado del titular, no de "Frente Renovador"
