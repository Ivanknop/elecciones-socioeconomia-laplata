"""Tests de `ml_models.construir_calendario.construir_ventanas`: una fila
por transición electoral dentro de cada nivel. Puro, sin red."""
from ml_models.construir_calendario import construir_calendario, construir_ventanas


class TestConstruirVentanas:
    def test_total_31_filas_distribucion_12_12_7(self):
        ventanas = construir_ventanas(construir_calendario())
        assert len(ventanas) == 31
        por_nivel = {}
        for v in ventanas:
            por_nivel[v.nivel] = por_nivel.get(v.nivel, 0) + 1
        assert por_nivel == {"municipal": 12, "provincial": 12, "nacional": 7}

    def test_ids_de_transicion_son_unicos(self):
        ventanas = construir_ventanas(construir_calendario())
        ids = [v.id_transicion for v in ventanas]
        assert len(ids) == len(set(ids))

    def test_primera_ventana_municipal_no_tiene_bloque_largo(self):
        ventanas = construir_ventanas(construir_calendario())
        primera = next(v for v in ventanas if v.nivel == "municipal" and v.anio_t == 2003)
        assert primera.anio_t_menos_1 == 2001
        assert primera.anio_t_menos_2 is None
        assert primera.fecha_inicio_vl is None

    def test_tercera_ventana_municipal_si_tiene_bloque_largo(self):
        ventanas = construir_ventanas(construir_calendario())
        tercera = next(v for v in ventanas if v.nivel == "municipal" and v.anio_t == 2007)
        assert tercera.anio_t_menos_1 == 2005
        assert tercera.anio_t_menos_2 == 2003
        assert tercera.fecha_inicio_vl is not None

    def test_primera_ventana_nacional_arranca_en_2013(self):
        ventanas = construir_ventanas(construir_calendario())
        anios_t_nacional = sorted(v.anio_t for v in ventanas if v.nivel == "nacional")
        assert anios_t_nacional == [2013, 2015, 2017, 2019, 2021, 2023, 2025]

    def test_ventana_corta_usa_fechas_reales_del_calendario(self):
        calendario = construir_calendario()
        ventanas = construir_ventanas(calendario)
        by_key = {(f.anio, f.nivel): f.fecha_eleccion for f in calendario}
        for v in ventanas:
            assert v.fecha_inicio_vc == by_key[(v.anio_t_menos_1, v.nivel)]
            assert v.fecha_fin_vc == by_key[(v.anio_t, v.nivel)]

    def test_tipo_eleccion_t_y_t_menos_1_coherentes_con_calendario(self):
        calendario = construir_calendario()
        ventanas = construir_ventanas(calendario)
        tipo_by_key = {(f.anio, f.nivel): f.tipo_eleccion for f in calendario}
        for v in ventanas:
            assert v.tipo_eleccion_t == tipo_by_key[(v.anio_t, v.nivel)]
            assert v.tipo_eleccion_t_menos_1 == tipo_by_key[(v.anio_t_menos_1, v.nivel)]
