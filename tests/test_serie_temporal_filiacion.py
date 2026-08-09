"""Tests de `src/analisis/serie_temporal_filiacion.py`: unión de votos contra
`filiacion_politica` (no contra `campo_ideologico`, que ya viene embebido en
`circuito_<nivel>.json`) -- la parte de renderizado matplotlib
(`graficar_serie_temporal_filiacion`) sigue sin tests automatizados, se
valida corriendo el script contra `data/` real (ver CLAUDE.md).
"""
import csv
import json

import pytest

from analisis.serie_temporal_filiacion import (
    _cargar_filiaciones,
    _serie_por_anio_filiacion,
    _votos_por_filiacion,
)


def _circuito(positivos: dict[str, tuple[str, int]], electores: int) -> dict:
    """`positivos` mapea id_agrupacion -> (nombre, votos) -- `filiacion_politica`
    se resuelve por nombre, no viene embebido en el circuito como
    `campo_ideologico`."""
    return {
        "electores": electores,
        "positivos": {
            id_agr: {"nombre": nombre, "campo_ideologico": "3", "votos": votos}
            for id_agr, (nombre, votos) in positivos.items()
        },
        "otros": {"EN BLANCO": 0, "NULO": 0},
    }


@pytest.fixture
def contenido():
    return {
        "anio": 2023,
        "nivel": "intendente",
        "circuitos": {
            "100": _circuito({"1": ("PARTIDO A", 60), "2": ("PARTIDO B", 20)}, electores=100),
            "101": _circuito({"1": ("PARTIDO A", 30), "2": ("PARTIDO B", 15)}, electores=60),
        },
    }


@pytest.fixture
def filiaciones():
    return {"PARTIDO A": "peronistas", "PARTIDO B": "liberales"}


@pytest.fixture
def agrupaciones_dir(tmp_path):
    archivo = tmp_path / "clasificacion_ideologica_agrupaciones.csv"
    with archivo.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["anio", "nivel", "agrupacion", "campo_ideologico", "filiacion_politica"])
        writer.writerow(["2023", "intendente", "PARTIDO A", "3", "peronistas"])
        writer.writerow(["2023", "intendente", "PARTIDO B", "5", "liberales"])
    return tmp_path


class TestCargarFiliaciones:
    def test_lee_agrupacion_a_filiacion(self, agrupaciones_dir):
        assert _cargar_filiaciones(agrupaciones_dir) == {"PARTIDO A": "peronistas", "PARTIDO B": "liberales"}


class TestVotosPorFiliacion:
    def test_suma_por_filiacion_todos_los_circuitos(self, contenido, filiaciones):
        assert _votos_por_filiacion(contenido, filiaciones, circuito_id=None) == {
            "peronistas": 90,  # 60+30
            "liberales": 35,  # 20+15
        }

    def test_un_solo_circuito(self, contenido, filiaciones):
        assert _votos_por_filiacion(contenido, filiaciones, circuito_id="100") == {
            "peronistas": 60,
            "liberales": 20,
        }

    def test_circuito_inexistente_da_keyerror(self, contenido, filiaciones):
        with pytest.raises(KeyError):
            _votos_por_filiacion(contenido, filiaciones, circuito_id="999")

    def test_agrupacion_sin_filiacion_asignada_da_keyerror(self, contenido):
        # Nunca se enmascara en silencio una agrupación sin filiación --
        # mismo criterio que `campo_ideologico` en graficos.py.
        with pytest.raises(KeyError):
            _votos_por_filiacion(contenido, {"PARTIDO A": "peronistas"}, circuito_id=None)


class TestSeriePorAnioFiliacion:
    def test_arma_serie_con_filiaciones_y_categorias_no_ideologicas(self, tmp_path, agrupaciones_dir, contenido):
        destino = tmp_path / "2023" / "intendente" / "generales"
        destino.mkdir(parents=True)
        (destino / "circuito_intendente.json").write_text(json.dumps(contenido), encoding="utf-8")

        puntos, serie, totales = _serie_por_anio_filiacion(tmp_path, agrupaciones_dir, "municipal")

        assert puntos == [(2023, "intendente")]
        assert serie["peronistas"] == [90]
        assert serie["liberales"] == [35]
        assert "blanco_nulo" in serie and "ausentismo" in serie
        assert totales == [160]  # electores = 100 + 60

    def test_sin_datos_da_filenotfounderror(self, tmp_path, agrupaciones_dir):
        with pytest.raises(FileNotFoundError):
            _serie_por_anio_filiacion(tmp_path, agrupaciones_dir, "municipal")
