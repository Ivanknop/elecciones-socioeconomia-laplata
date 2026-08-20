"""Tests de `src/analisis/cuadros_anualizados.py`: descubrimiento de qué
niveles de un año ya tienen `circuito_<nivel>.json` -- la parte de
renderizado matplotlib (`graficar_cuadro_anual`) sigue sin tests
automatizados, se valida corriendo el script contra `data/` real (ver
CLAUDE.md).
"""
import json

from analisis.cuadros_anualizados import _niveles_disponibles


def _escribir_circuito_vacio(data_dir, anio, nivel):
    contenido = {"anio": anio, "nivel": nivel, "circuitos": {}}
    destino = data_dir / str(anio) / nivel / "generales"
    destino.mkdir(parents=True)
    (destino / f"circuito_{nivel}.json").write_text(json.dumps(contenido), encoding="utf-8")


class TestNivelesDisponibles:
    def test_devuelve_solo_los_niveles_con_datos_en_disco(self, tmp_path):
        # 2011 espera presidente/gobernador/intendente (NIVELES_POR_ANIO) --
        # acá solo dejamos presidente e intendente en disco.
        _escribir_circuito_vacio(tmp_path, 2011, "presidente")
        _escribir_circuito_vacio(tmp_path, 2011, "intendente")

        assert _niveles_disponibles(tmp_path, 2011) == ["presidente", "intendente"]

    def test_vacio_si_no_hay_nada_en_disco(self, tmp_path):
        assert _niveles_disponibles(tmp_path, 2011) == []

    def test_anio_fuera_del_catalogo_da_vacio(self, tmp_path):
        _escribir_circuito_vacio(tmp_path, 2011, "presidente")
        assert _niveles_disponibles(tmp_path, 1999) == []

    def test_2025_solo_espera_nacional(self, tmp_path):
        _escribir_circuito_vacio(tmp_path, 2025, "nacional")
        assert _niveles_disponibles(tmp_path, 2025) == ["nacional"]
