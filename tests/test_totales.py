"""Tests de `src/electoral/totales.py`: resultado total por agrupación a
partir de un `circuito_<nivel>.json` chico, en `tmp_path`.
"""
import json

import pytest

from electoral.totales import _combos_disponibles, generar_csv_totales, resultado_total_por_agrupacion


def _circuito(positivos: dict[str, tuple[str, int]]) -> dict:
    """`positivos` mapea id_agrupacion -> (nombre, votos)."""
    return {
        "mesas": 1,
        "electores": 100,
        "positivos": {
            id_agr: {"nombre": nombre, "votos": votos, "campo_ideologico": "3"}
            for id_agr, (nombre, votos) in positivos.items()
        },
        "otros": {"EN BLANCO": 1, "NULO": 0},
    }


@pytest.fixture
def data_dir(tmp_path):
    contenido = {
        "anio": 2023,
        "nivel": "intendente",
        "circuitos": {
            "100": _circuito({"1": ("PARTIDO A", 60), "2": ("PARTIDO B", 20)}),
            "101": _circuito({"1": ("PARTIDO A", 30), "2": ("PARTIDO B", 15)}),
        },
    }
    path = tmp_path / "2023" / "intendente" / "generales"
    path.mkdir(parents=True)
    (path / "circuito_intendente.json").write_text(json.dumps(contenido), encoding="utf-8")
    return tmp_path


class TestCombosDisponibles:
    def test_encuentra_los_combos_con_circuito_json(self, data_dir):
        assert _combos_disponibles(data_dir) == [(2023, "intendente")]

    def test_vacio_si_no_hay_nada(self, tmp_path):
        assert _combos_disponibles(tmp_path) == []


class TestResultadoTotalPorAgrupacion:
    def test_suma_los_circuitos_por_agrupacion(self, data_dir):
        totales = resultado_total_por_agrupacion(data_dir, 2023, "intendente")
        por_id = {v.id_agrupacion: v.votos for v in totales}
        assert por_id == {"1": 90, "2": 35}  # PARTIDO A: 60+30, PARTIDO B: 20+15

    def test_ordenado_de_mayor_a_menor(self, data_dir):
        totales = resultado_total_por_agrupacion(data_dir, 2023, "intendente")
        assert [v.id_agrupacion for v in totales] == ["1", "2"]

    def test_no_incluye_blanco_nulo_ni_otros(self, data_dir):
        totales = resultado_total_por_agrupacion(data_dir, 2023, "intendente")
        assert sum(v.votos for v in totales) == 90 + 35  # ni el EN BLANCO/NULO de _circuito()


class TestGenerarCsvTotales:
    def test_guarda_en_data_totales_nivel_anio(self, data_dir, tmp_path):
        destino = generar_csv_totales(data_dir, tmp_path / "totales", 2023, "intendente")
        assert destino == tmp_path / "totales" / "intendente" / "2023" / "resultado_total.csv"
        assert destino.exists()

    def test_csv_trae_encabezado_de_procedencia_como_comentario(self, data_dir, tmp_path):
        destino = generar_csv_totales(data_dir, tmp_path / "totales", 2023, "intendente")
        primera_linea = destino.read_text(encoding="utf-8").splitlines()[0]
        assert primera_linea.startswith("#")

    def test_csv_tiene_una_fila_por_agrupacion_con_las_columnas_esperadas(self, data_dir, tmp_path):
        import pandas as pd

        destino = generar_csv_totales(data_dir, tmp_path / "totales", 2023, "intendente")
        df = pd.read_csv(destino, comment="#")
        assert list(df.columns) == ["id_agrupacion", "agrupacion", "votos", "votos_porcentaje"]
        assert len(df) == 2
        fila = df.set_index("id_agrupacion").loc[1]
        assert fila["votos"] == 90
        assert fila["agrupacion"] == "PARTIDO A"
