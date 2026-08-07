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


def _escribir_circuito(tmp_path, anio, nivel, etapa, circuitos):
    contenido = {"anio": anio, "nivel": nivel, "circuitos": circuitos}
    path = tmp_path / str(anio) / nivel / etapa
    path.mkdir(parents=True)
    (path / f"circuito_{nivel}.json").write_text(json.dumps(contenido), encoding="utf-8")


@pytest.fixture
def data_dir(tmp_path):
    _escribir_circuito(
        tmp_path,
        2023,
        "intendente",
        "generales",
        {
            "100": _circuito({"1": ("PARTIDO A", 60), "2": ("PARTIDO B", 20)}),
            "101": _circuito({"1": ("PARTIDO A", 30), "2": ("PARTIDO B", 15)}),
        },
    )
    return tmp_path


@pytest.fixture
def data_dir_con_paso_y_balotaje(data_dir):
    _escribir_circuito(
        data_dir, 2023, "intendente", "paso", {"100": _circuito({"1": ("PARTIDO A", 40), "3": ("PARTIDO C", 10)})}
    )
    _escribir_circuito(
        data_dir, 2023, "presidente", "balotaje", {"200": _circuito({"1": ("PARTIDO A", 90), "2": ("PARTIDO B", 80)})}
    )
    return data_dir


class TestCombosDisponibles:
    def test_encuentra_los_combos_con_circuito_json(self, data_dir):
        assert _combos_disponibles(data_dir) == [(2023, "intendente", "generales")]

    def test_vacio_si_no_hay_nada(self, tmp_path):
        assert _combos_disponibles(tmp_path) == []

    def test_incluye_paso_y_balotaje_cuando_existen(self, data_dir_con_paso_y_balotaje):
        combos = _combos_disponibles(data_dir_con_paso_y_balotaje)
        assert set(combos) == {
            (2023, "intendente", "generales"),
            (2023, "intendente", "paso"),
            (2023, "presidente", "balotaje"),
        }


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

    def test_etapa_paso_lee_su_propio_circuito_json(self, data_dir_con_paso_y_balotaje):
        totales = resultado_total_por_agrupacion(data_dir_con_paso_y_balotaje, 2023, "intendente", etapa="paso")
        por_id = {v.id_agrupacion: v.votos for v in totales}
        assert por_id == {"1": 40, "3": 10}

    def test_etapa_balotaje_lee_su_propio_circuito_json(self, data_dir_con_paso_y_balotaje):
        totales = resultado_total_por_agrupacion(data_dir_con_paso_y_balotaje, 2023, "presidente", etapa="balotaje")
        por_id = {v.id_agrupacion: v.votos for v in totales}
        assert por_id == {"1": 90, "2": 80}

    def test_default_etapa_es_generales_no_se_mezcla_con_paso(self, data_dir_con_paso_y_balotaje):
        totales = resultado_total_por_agrupacion(data_dir_con_paso_y_balotaje, 2023, "intendente")
        por_id = {v.id_agrupacion: v.votos for v in totales}
        assert por_id == {"1": 90, "2": 35}  # sigue siendo el de generales, no el de paso


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

    def test_paso_se_guarda_en_subcarpeta_propia_sin_pisar_generales(self, data_dir_con_paso_y_balotaje, tmp_path):
        destino_generales = generar_csv_totales(data_dir_con_paso_y_balotaje, tmp_path / "totales", 2023, "intendente")
        destino_paso = generar_csv_totales(
            data_dir_con_paso_y_balotaje, tmp_path / "totales", 2023, "intendente", etapa="paso"
        )
        assert destino_paso == tmp_path / "totales" / "intendente" / "2023" / "paso" / "resultado_total.csv"
        assert destino_paso != destino_generales
        assert destino_generales.exists() and destino_paso.exists()

    def test_balotaje_se_guarda_en_subcarpeta_propia(self, data_dir_con_paso_y_balotaje, tmp_path):
        destino = generar_csv_totales(
            data_dir_con_paso_y_balotaje, tmp_path / "totales", 2023, "presidente", etapa="balotaje"
        )
        assert destino == tmp_path / "totales" / "presidente" / "2023" / "balotaje" / "resultado_total.csv"
