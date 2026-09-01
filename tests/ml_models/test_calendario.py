"""Tests de `ml_models.construir_calendario`: calendario electoral y
oficialismo por nivel, 2001-2025. Puro -- sin red, sin archivos reales
(usa `clasificacion`/`oficialismos` sintéticos)."""
import csv

from ml_models.construir_calendario import (
    ALIAS_VPARTY,
    _cargar_vparty_directo,
    _vparty_directo,
    construir_calendario,
    construir_oficialismo_por_nivel,
)

_VPARTY_CAMPOS = [
    "v2paenname", "year", "v2pariglef", "v2pawomlab", "v2palgbt", "v2paimmig", "v2parelig", "v2xpa_popul",
]


def _escribir_vparty_csv(tmp_path, filas):
    path = tmp_path / "vparty.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_VPARTY_CAMPOS)
        writer.writeheader()
        for fila in filas:
            writer.writerow(fila)
    return path


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


class TestCargarVpartyDirecto:
    def test_calcula_economico_progresismo_populismo(self, tmp_path):
        path = _escribir_vparty_csv(tmp_path, [
            {
                "v2paenname": "Front for Victory", "year": "2011.0", "v2pariglef": "-1.686",
                "v2pawomlab": "3.292", "v2palgbt": "3.622", "v2paimmig": "3.333", "v2parelig": "3.482",
                "v2xpa_popul": "0.871",
            },
        ])
        vparty = _cargar_vparty_directo(path)
        econ, prog, pop = vparty[(2011, "Front for Victory")]
        assert econ == "-1.686"
        assert prog == "3.432"  # promedio de 3.292/3.622/3.333/3.482
        assert pop == "0.871"

    def test_descarta_filas_sin_cobertura_completa(self, tmp_path):
        path = _escribir_vparty_csv(tmp_path, [
            {
                "v2paenname": "Socialist Party", "year": "2011.0", "v2pariglef": "",
                "v2pawomlab": "", "v2palgbt": "", "v2paimmig": "", "v2parelig": "", "v2xpa_popul": "",
            },
        ])
        vparty = _cargar_vparty_directo(path)
        assert vparty == {}


class TestVpartyDirecto:
    def test_sin_alias_devuelve_none(self):
        assert _vparty_directo({(2003, "Justicialist [Peronist] Party"): ("1", "2", "3")}, 2003, "PARTIDO SIN ALIAS") is None

    def test_con_alias_pero_sin_cobertura_ese_anio_devuelve_none(self):
        assert _vparty_directo({}, 2003, "PARTIDO JUSTICIALISTA") is None

    def test_con_alias_y_cobertura_devuelve_la_tupla(self):
        vparty = {(2003, ALIAS_VPARTY["PARTIDO JUSTICIALISTA"]): ("-0.416", "0.268", "0.658")}
        assert _vparty_directo(vparty, 2003, "PARTIDO JUSTICIALISTA") == ("-0.416", "0.268", "0.658")


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

    def test_titular_inicial_municipal_usa_ola_1999_real(self):
        """El titular inicial de municipal/provincial (Alak/Ruckauf, PJ) sí
        tiene ola V-Party real anterior a la ventana (1999) -- se completa
        con CLASIFICACION_TITULAR_INICIAL, no queda en blanco."""
        calendario = [_FilaCalendarioFake(2001, "municipal")]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert filas[0].campo_ideologico == "3"
        assert filas[0].filiacion_politica == "peronistas"
        assert filas[0].vparty_economico == "0.838"

    def test_titular_inicial_sin_ola_conocida_queda_sin_clasificar(self, monkeypatch):
        """Sin entrada en CLASIFICACION_TITULAR_INICIAL para ese nivel, el
        titular inicial (pre-ventana) queda sin clasificar -- no se inventa."""
        import ml_models.construir_calendario as mod

        monkeypatch.setattr(mod, "CLASIFICACION_TITULAR_INICIAL", {})
        calendario = [_FilaCalendarioFake(2001, "municipal")]
        filas = construir_oficialismo_por_nivel(calendario, {}, {})
        assert filas[0].campo_ideologico == ""
        assert "clasificar" in filas[0].nota.lower()

    def test_fallback_vparty_directo_completa_cuando_falta_clasificacion(self):
        """2001-2009 no tiene fila en clasificacion_ideologica_agrupaciones.csv
        -- V-Party cubre 2001-2019, el fallback completa vparty_* y, si hay
        alias conocido, también ideología."""
        calendario = [
            _FilaCalendarioFake(2003, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2005, "municipal", "legislativa"),
        ]
        vparty_directo = {(2003, "Justicialist [Peronist] Party"): ("-0.416", "0.268", "0.658")}
        filas = construir_oficialismo_por_nivel(calendario, {}, {}, vparty_directo)
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2005].agrupacion_oficialismo == "PARTIDO JUSTICIALISTA"
        assert por_anio[2005].vparty_economico == "-0.416"
        assert por_anio[2005].vparty_progresismo == "0.268"
        assert por_anio[2005].vparty_populismo == "0.658"
        assert por_anio[2005].campo_ideologico == "3"
        assert por_anio[2005].filiacion_politica == "peronistas"

    def test_fallback_vparty_directo_sin_clasificacion_conocida_deja_ideologia_vacia(self, monkeypatch):
        """Sin fila en CLASIFICACION_VPARTY_DIRECTO, vparty_* se completa
        igual pero ideología queda sin determinar -- nunca inventada."""
        import ml_models.construir_calendario as mod

        monkeypatch.setattr(mod, "CLASIFICACION_VPARTY_DIRECTO", {})
        calendario = [
            _FilaCalendarioFake(2003, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2005, "municipal", "legislativa"),
        ]
        vparty_directo = {(2003, "Justicialist [Peronist] Party"): ("-0.416", "0.268", "0.658")}
        filas = construir_oficialismo_por_nivel(calendario, {}, {}, vparty_directo)
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2005].vparty_economico == "-0.416"
        assert por_anio[2005].campo_ideologico == ""
        assert por_anio[2005].filiacion_politica == ""

    def test_fallback_vparty_directo_sin_alias_usa_aprox_manual(self):
        """PARTIDO PROGRESO SOCIAL (Bruera) no tiene alias en ALIAS_VPARTY
        -- cae a CLASIFICACION_APROX_MANUAL, mismo valor que ya usan los CSV
        de data/tfi_data/elecciones/ para esta agrupación."""
        calendario = [
            _FilaCalendarioFake(2007, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2009, "municipal", "legislativa"),
        ]
        vparty_directo = {(2007, "Justicialist [Peronist] Party"): ("-0.4", "0.2", "0.6")}
        filas = construir_oficialismo_por_nivel(calendario, {}, {}, vparty_directo)
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2009].agrupacion_oficialismo == "PARTIDO PROGRESO SOCIAL"
        assert por_anio[2009].campo_ideologico == "3"
        assert por_anio[2009].filiacion_politica == "peronistas"
        assert por_anio[2009].vparty_economico == "-0.416"

    def test_fallback_sin_clasificacion_ni_aprox_manual_queda_vacio(self, monkeypatch):
        """PARTIDO PROGRESO SOCIAL sin fila en CLASIFICACION_APROX_MANUAL
        (además de sin alias V-Party) -- no se inventa un match."""
        import ml_models.construir_calendario as mod

        monkeypatch.setattr(mod, "CLASIFICACION_APROX_MANUAL", {})
        calendario = [
            _FilaCalendarioFake(2007, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2009, "municipal", "legislativa"),
        ]
        vparty_directo = {(2007, "Justicialist [Peronist] Party"): ("-0.4", "0.2", "0.6")}
        filas = construir_oficialismo_por_nivel(calendario, {}, {}, vparty_directo)
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2009].agrupacion_oficialismo == "PARTIDO PROGRESO SOCIAL"
        assert por_anio[2009].vparty_economico == ""
        assert por_anio[2009].campo_ideologico == ""

    def test_clasificacion_tiene_prioridad_sobre_vparty_directo(self):
        calendario = [
            _FilaCalendarioFake(2011, "municipal", "ejecutiva"),
            _FilaCalendarioFake(2013, "municipal", "legislativa"),
        ]
        oficialismos = {
            (2011, "municipal"): {"agrupacion_ganadora": "ALIANZA FRENTE PARA LA VICTORIA", "era_oficialismo": "true"},
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
        vparty_directo = {(2011, "Front for Victory"): ("-9.999", "-9.999", "-9.999")}
        filas = construir_oficialismo_por_nivel(calendario, oficialismos, clasificacion, vparty_directo)
        por_anio = {f.anio: f for f in filas}
        assert por_anio[2013].vparty_economico == "-1.686"  # de clasificacion, no del fallback

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
