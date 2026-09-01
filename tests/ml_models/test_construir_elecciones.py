"""Tests de `ml_models.construir_elecciones`: total de votos por
agrupación + BLANCO/NULO desde `circuito_<cargo>.json` chicos en
`tmp_path` -- puro, sin red. `main()` sin test, ver CLAUDE.md."""
import json

import pytest

from ml_models.construir_calendario import FilaCalendario
from ml_models.construir_elecciones import (
    _blanco_nulo,
    _clasificacion_de_agrupacion,
    _combos_disponibles,
    construir_eleccion,
)


def _circuito(positivos: dict[str, tuple[str, int]], otros: dict[str, int]) -> dict:
    return {
        "mesas": 1,
        "electores": 1000,
        "positivos": {
            id_agr: {"nombre": nombre, "votos": votos, "campo_ideologico": "3"}
            for id_agr, (nombre, votos) in positivos.items()
        },
        "otros": otros,
    }


def _escribir_circuito(tmp_path, anio, cargo, circuitos):
    contenido = {"anio": anio, "nivel": cargo, "circuitos": circuitos}
    path = tmp_path / str(anio) / cargo / "generales"
    path.mkdir(parents=True)
    (path / f"circuito_{cargo}.json").write_text(json.dumps(contenido), encoding="utf-8")
    return tmp_path


@pytest.fixture
def data_dir(tmp_path):
    _escribir_circuito(
        tmp_path,
        2023,
        "intendente",
        {
            "100": _circuito(
                {"1": ("PARTIDO A", 60), "2": ("PARTIDO B", 20)},
                {"EN BLANCO": 5, "NULO": 2, "COMANDO": 0, "IMPUGNADO": 1},
            ),
            "101": _circuito(
                {"1": ("PARTIDO A", 30), "2": ("PARTIDO B", 10)},
                {"BLANCOS": 3, "NULOS": 1, "RECURRIDO": 0},
            ),
        },
    )
    return tmp_path


class TestBlancoNulo:
    def test_suma_blanco_y_nulo_singular_y_plural_por_separado(self, data_dir):
        blanco, nulo = _blanco_nulo(data_dir, 2023, "intendente")
        assert blanco == 8  # 5 (EN BLANCO) + 3 (BLANCOS)
        assert nulo == 3  # 2 (NULO) + 1 (NULOS)

    def test_no_cuenta_categorias_procedimentales(self, tmp_path):
        _escribir_circuito(
            tmp_path,
            2023,
            "intendente",
            {"100": _circuito({}, {"EN BLANCO": 5, "NULO": 2, "COMANDO": 9, "IMPUGNADO": 9, "RECURRIDO": 9})},
        )
        blanco, nulo = _blanco_nulo(tmp_path, 2023, "intendente")
        assert (blanco, nulo) == (5, 2)  # COMANDO/IMPUGNADO/RECURRIDO no entran


class TestConstruirEleccion:
    def test_incluye_agrupaciones_blanco_nulo_y_votantes_habilitados(self, data_dir):
        filas = construir_eleccion(data_dir, 2023, "intendente")
        nombres = {f.agrupacion for f in filas}
        assert nombres == {"PARTIDO A", "PARTIDO B", "BLANCO", "NULO", "VOTANTES_HABILITADOS"}

    def test_votos_porcentaje_suma_100_sobre_agrupaciones_mas_blanco_nulo(self, data_dir):
        filas = construir_eleccion(data_dir, 2023, "intendente")
        sin_votantes = [f for f in filas if f.agrupacion != "VOTANTES_HABILITADOS"]
        assert round(sum(f.votos_porcentaje for f in sin_votantes), 6) == 100.0

    def test_votantes_habilitados_es_el_padron_con_100_por_ciento(self, data_dir):
        filas = construir_eleccion(data_dir, 2023, "intendente")
        por_nombre = {f.agrupacion: f for f in filas}
        assert por_nombre["VOTANTES_HABILITADOS"].votos == 2000  # 1000 electores x 2 circuitos
        assert por_nombre["VOTANTES_HABILITADOS"].votos_porcentaje == 100.0

    def test_votos_agregados_correctamente(self, data_dir):
        filas = construir_eleccion(data_dir, 2023, "intendente")
        por_nombre = {f.agrupacion: f.votos for f in filas}
        assert por_nombre["PARTIDO A"] == 90
        assert por_nombre["PARTIDO B"] == 30
        assert por_nombre["BLANCO"] == 8
        assert por_nombre["NULO"] == 3

    def test_sin_votos_no_rompe_por_division_cero(self, tmp_path):
        _escribir_circuito(tmp_path, 2023, "intendente", {"100": _circuito({}, {})})
        filas = construir_eleccion(tmp_path, 2023, "intendente")
        sin_votantes = [f for f in filas if f.agrupacion != "VOTANTES_HABILITADOS"]
        assert all(f.votos_porcentaje == 0.0 for f in sin_votantes)

    def test_completa_clasificacion_de_agrupaciones_conocidas(self, data_dir):
        clasificacion = {
            ("2023", "PARTIDO A", "intendente"): {
                "campo_ideologico": "3",
                "filiacion_politica": "peronistas",
                "vparty_economico": "-0.465",
                "vparty_progresismo": "1.069",
                "vparty_populismo": "0.642",
            }
        }
        filas = construir_eleccion(data_dir, 2023, "intendente", clasificacion)
        por_nombre = {f.agrupacion: f for f in filas}
        assert por_nombre["PARTIDO A"].campo_ideologico == "3"
        assert por_nombre["PARTIDO A"].filiacion_politica == "peronistas"
        assert por_nombre["PARTIDO A"].vparty_economico == "-0.465"
        assert por_nombre["PARTIDO B"].campo_ideologico == ""  # sin fila -- no inventado

    def test_blanco_nulo_y_votantes_habilitados_nunca_tienen_clasificacion(self, data_dir):
        clasificacion = {
            ("2023", "BLANCO", "intendente"): {"campo_ideologico": "9", "filiacion_politica": "x"},
            ("2023", "NULO", "intendente"): {"campo_ideologico": "9", "filiacion_politica": "x"},
            ("2023", "VOTANTES_HABILITADOS", "intendente"): {"campo_ideologico": "9", "filiacion_politica": "x"},
        }
        filas = construir_eleccion(data_dir, 2023, "intendente", clasificacion)
        por_nombre = {f.agrupacion: f for f in filas}
        assert por_nombre["BLANCO"].campo_ideologico == ""
        assert por_nombre["NULO"].campo_ideologico == ""
        assert por_nombre["VOTANTES_HABILITADOS"].campo_ideologico == ""


class TestClasificacionDeAgrupacion:
    def test_sin_fila_devuelve_todo_vacio(self):
        assert _clasificacion_de_agrupacion({}, 2023, "PARTIDO X", "intendente") == ("", "", "", "", "")

    def test_normaliza_mayusculas_y_espacios_para_matchear(self):
        clasificacion = {
            ("2023", "PARTIDO A", "intendente"): {
                "campo_ideologico": "3", "filiacion_politica": "peronistas",
                "vparty_economico": "-0.5", "vparty_progresismo": "1.0", "vparty_populismo": "0.6",
            }
        }
        assert _clasificacion_de_agrupacion(clasificacion, 2023, "  partido a  ", "intendente") == (
            "3", "peronistas", "-0.5", "1.0", "0.6",
        )

    def test_mapea_gobernador_a_gobernacion(self):
        clasificacion = {("2011", "PARTIDO A", "gobernacion"): {"campo_ideologico": "3", "filiacion_politica": "peronistas"}}
        campo, filiacion, *_ = _clasificacion_de_agrupacion(clasificacion, 2011, "PARTIDO A", "gobernador")
        assert (campo, filiacion) == ("3", "peronistas")


class TestCombosDisponibles:
    def test_solo_incluye_combos_con_circuito_cacheado(self, data_dir):
        calendario = [
            FilaCalendario(2023, "municipal", "2023-10-22", "ejecutiva", False, "intendente"),
            FilaCalendario(2025, "municipal", "2025-09-07", "legislativa", True, "concejales"),
        ]
        combos = _combos_disponibles(calendario, data_dir)
        assert combos == [(2023, "municipal", "intendente")]
