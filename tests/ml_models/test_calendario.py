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
    def test_usa_oficialismos_csv_para_2011_en_adelante(self):
        calendario = [_FilaCalendarioFake(2011, "municipal", "ejecutiva")]
        oficialismos = {
            (2011, "municipal"): {
                "agrupacion_ganadora": "ALIANZA FRENTE PARA LA VICTORIA",
                "era_oficialismo": "true",
                "campo_ideologico": "3",
                "filiacion_politica": "peronistas",
                "vparty_economico": "-1.686",
                "vparty_progresismo": "2.097",
                "vparty_populismo": "0.871",
            }
        }
        filas = construir_oficialismo_por_nivel(calendario, oficialismos, {})
        assert len(filas) == 1
        assert filas[0].agrupacion_oficialismo == "ALIANZA FRENTE PARA LA VICTORIA"
        assert filas[0].continuidad_oficialismo == "continua"
        assert filas[0].campo_ideologico == "3"

    def test_era_oficialismo_false_es_ruptura(self):
        calendario = [_FilaCalendarioFake(2013, "municipal", "legislativa")]
        oficialismos = {
            (2013, "municipal"): {
                "agrupacion_ganadora": "FRENTE RENOVADOR",
                "era_oficialismo": "false",
                "campo_ideologico": "4",
                "filiacion_politica": "peronistas",
                "vparty_economico": "",
                "vparty_progresismo": "",
                "vparty_populismo": "",
            }
        }
        filas = construir_oficialismo_por_nivel(calendario, oficialismos, {})
        assert filas[0].continuidad_oficialismo == "ruptura"

    def test_pre_2011_municipal_usa_historia_investigada(self):
        calendario = [_FilaCalendarioFake(anio, "municipal") for anio in (2001, 2003, 2005, 2007, 2009)]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert len(filas) == 5
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2001].agrupacion_oficialismo == "PARTIDO JUSTICIALISTA"
        assert por_anio[2007].continuidad_oficialismo == "ruptura"
        assert por_anio[2007].agrupacion_oficialismo == "PARTIDO PROGRESO SOCIAL"

    def test_pre_2011_provincial_usa_historia_investigada(self):
        calendario = [_FilaCalendarioFake(anio, "provincial") for anio in (2001, 2003, 2005, 2007, 2009)]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2007].continuidad_oficialismo == "continua_renombrada"

    def test_nacional_pre_2011_no_genera_filas(self):
        calendario = [_FilaCalendarioFake(2003, "nacional")]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert filas == []

    def test_sin_fila_en_oficialismos_no_genera_fila_huerfana(self):
        calendario = [_FilaCalendarioFake(2025, "provincial", "legislativa")]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert filas == []

    def test_join_con_clasificacion_no_duplica_si_falta(self):
        calendario = [_FilaCalendarioFake(2001, "municipal")]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert filas[0].campo_ideologico == ""
        assert "sin determinar" in filas[0].nota.lower() or "clasificacion" in filas[0].nota.lower()
