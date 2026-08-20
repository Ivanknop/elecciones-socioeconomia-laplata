"""Tests de `src/analisis/serie_temporal.py`: descubrimiento de puntos
(año, cargo) por nivel de gobierno y armado de la serie -- la parte de
renderizado matplotlib (`graficar_serie_temporal`) sigue sin tests
automatizados, se valida corriendo el script contra `data/` real (ver
CLAUDE.md).
"""
import json

import pytest

from analisis.serie_temporal import _anios_disponibles, _puntos_del_nivel, _serie_por_anio


def _circuito(positivos: dict[str, tuple[str, str, int]], electores: int) -> dict:
    return {
        "electores": electores,
        "positivos": {
            id_agr: {"nombre": nombre, "campo_ideologico": campo, "votos": votos}
            for id_agr, (nombre, campo, votos) in positivos.items()
        },
        "otros": {"EN BLANCO": 0, "NULO": 0},
    }


def _escribir_circuito(data_dir, anio, nivel, circuitos):
    contenido = {"anio": anio, "nivel": nivel, "circuitos": circuitos}
    destino = data_dir / str(anio) / nivel / "generales"
    destino.mkdir(parents=True)
    (destino / f"circuito_{nivel}.json").write_text(json.dumps(contenido), encoding="utf-8")


class TestAniosDisponibles:
    def test_encuentra_y_ordena_los_anios(self, tmp_path):
        for anio in (2019, 2011, 2015):
            _escribir_circuito(tmp_path, anio, "presidente", {"1": _circuito({}, electores=10)})
        assert _anios_disponibles(tmp_path, "presidente") == [2011, 2015, 2019]

    def test_vacio_si_no_hay_nada(self, tmp_path):
        assert _anios_disponibles(tmp_path, "presidente") == []

    def test_no_mezcla_niveles_distintos(self, tmp_path):
        _escribir_circuito(tmp_path, 2019, "presidente", {"1": _circuito({}, electores=10)})
        _escribir_circuito(tmp_path, 2019, "gobernador", {"1": _circuito({}, electores=10)})
        assert _anios_disponibles(tmp_path, "presidente") == [2019]


class TestPuntosDelNivel:
    def test_combina_ejecutivo_y_legislativo_ordenado_por_anio(self, tmp_path):
        _escribir_circuito(tmp_path, 2015, "presidente", {"1": _circuito({}, electores=10)})
        _escribir_circuito(tmp_path, 2011, "presidente", {"1": _circuito({}, electores=10)})
        _escribir_circuito(tmp_path, 2013, "nacional", {"1": _circuito({}, electores=10)})

        assert _puntos_del_nivel(tmp_path, "nacional") == [
            (2011, "presidente"),
            (2013, "nacional"),
            (2015, "presidente"),
        ]

    def test_anio_duplicado_entre_ejecutivo_y_legislativo_da_valueerror(self, tmp_path):
        # Mismo año con datos para presidente Y nacional dentro del nivel
        # "nacional" -- no debería poder pasar con datos reales del proyecto
        # (todos los ejecutivos son años impares distintos de los legislativos),
        # pero la función lo detecta en vez de fusionar dos puntos en uno solo.
        _escribir_circuito(tmp_path, 2013, "presidente", {"1": _circuito({}, electores=10)})
        _escribir_circuito(tmp_path, 2013, "nacional", {"1": _circuito({}, electores=10)})

        with pytest.raises(ValueError, match="año duplicado"):
            _puntos_del_nivel(tmp_path, "nacional")

    def test_vacio_si_no_hay_datos_de_ningun_cargo(self, tmp_path):
        assert _puntos_del_nivel(tmp_path, "nacional") == []


class TestSeriePorAnio:
    def test_arma_serie_y_totales_por_punto(self, tmp_path):
        _escribir_circuito(
            tmp_path, 2015, "intendente",
            {"1": _circuito({"1": ("PARTIDO A", "3", 60), "2": ("PARTIDO B", "5", 20)}, electores=100)},
        )
        _escribir_circuito(
            tmp_path, 2017, "municipal",
            {"1": _circuito({"1": ("PARTIDO A", "3", 30)}, electores=50)},
        )

        puntos, serie, totales = _serie_por_anio(tmp_path, "municipal")

        assert puntos == [(2015, "intendente"), (2017, "municipal")]
        assert serie["centro"] == [60, 30]
        assert serie["derecha"] == [20, 0]
        # ausentismo 2015: 100 - 80 - 0(otros) = 20; 2017: 50 - 30 - 0 = 20
        assert serie["ausentismo"] == [20, 20]
        assert totales == [100, 50]  # electores de cada punto, blanco_nulo=0 en ambos

    def test_sin_datos_da_filenotfounderror(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _serie_por_anio(tmp_path, "municipal")
