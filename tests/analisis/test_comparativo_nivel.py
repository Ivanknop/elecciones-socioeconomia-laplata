"""Tests de `src/analisis/comparativo_nivel.py`: cuadro Markdown Municipio /
Provincia / Nación por agrupación -- salida determinística (texto), sin
matplotlib de por medio.
"""
import json

import pytest

from analisis.comparativo_nivel import _fmt_dif, _fmt_pct, _porcentajes_por_categoria, tabla_comparativa


def _circuito(positivos: dict[str, tuple[str, str, int]], electores: int, otros: dict[str, int]) -> dict:
    return {
        "electores": electores,
        "positivos": {
            id_agr: {"nombre": nombre, "campo_ideologico": campo, "votos": votos}
            for id_agr, (nombre, campo, votos) in positivos.items()
        },
        "otros": otros,
    }


def _escribir_circuito(data_dir, anio, nivel, circuitos):
    contenido = {"anio": anio, "nivel": nivel, "circuitos": circuitos}
    destino = data_dir / str(anio) / nivel / "generales"
    destino.mkdir(parents=True)
    (destino / f"circuito_{nivel}.json").write_text(json.dumps(contenido), encoding="utf-8")


class TestFmtPct:
    def test_formatea_con_un_decimal(self):
        assert _fmt_pct(45.678) == "45.7%"

    def test_none_da_rayita(self):
        assert _fmt_pct(None) == "—"


class TestFmtDif:
    def test_diferencia_con_signo(self):
        assert _fmt_dif(45.0, 40.0) == "+5.0 pp"
        assert _fmt_dif(40.0, 45.0) == "-5.0 pp"

    def test_none_en_cualquier_lado_da_rayita(self):
        assert _fmt_dif(None, 40.0) == "—"
        assert _fmt_dif(40.0, None) == "—"


class TestPorcentajesPorCategoria:
    def test_agrupa_por_categoria_municipio_provincia_nacion(self, tmp_path):
        # 2019 tiene los tres cargos ejecutivos: presidente/gobernador/intendente
        _escribir_circuito(
            tmp_path, 2019, "presidente",
            {"1": _circuito({"1": ("PARTIDO A", "3", 80)}, electores=100, otros={"EN BLANCO": 20, "NULO": 0})},
        )
        _escribir_circuito(
            tmp_path, 2019, "gobernador",
            {"1": _circuito({"1": ("PARTIDO A", "3", 60)}, electores=100, otros={"EN BLANCO": 40, "NULO": 0})},
        )
        _escribir_circuito(
            tmp_path, 2019, "intendente",
            {"1": _circuito({"1": ("PARTIDO A", "3", 50)}, electores=100, otros={"EN BLANCO": 50, "NULO": 0})},
        )

        por_categoria = _porcentajes_por_categoria(tmp_path, 2019, ["presidente", "gobernador", "intendente"])

        assert por_categoria["Nación"]["PARTIDO A"] == 80.0
        assert por_categoria["Provincia"]["PARTIDO A"] == 60.0
        assert por_categoria["Municipio"]["PARTIDO A"] == 50.0


class TestTablaComparativa:
    @pytest.fixture
    def data_dir_2019_completo(self, tmp_path):
        _escribir_circuito(
            tmp_path, 2019, "presidente",
            {"1": _circuito({"1": ("PARTIDO A", "3", 80)}, electores=100, otros={"EN BLANCO": 20, "NULO": 0})},
        )
        _escribir_circuito(
            tmp_path, 2019, "gobernador",
            {"1": _circuito({"1": ("PARTIDO A", "3", 60)}, electores=100, otros={"EN BLANCO": 40, "NULO": 0})},
        )
        _escribir_circuito(
            tmp_path, 2019, "intendente",
            {"1": _circuito({"1": ("PARTIDO A", "3", 50)}, electores=100, otros={"EN BLANCO": 50, "NULO": 0})},
        )
        return tmp_path

    def test_none_si_falta_alguna_de_las_tres_categorias(self, tmp_path):
        # 2025 sólo tiene "nacional" en NIVELES_POR_ANIO -- un único cargo, nada que comparar
        _escribir_circuito(tmp_path, 2025, "nacional", {"1": _circuito({}, electores=10, otros={})})
        assert tabla_comparativa(tmp_path, 2025) is None

    def test_incluye_las_tres_columnas_y_la_agrupacion(self, data_dir_2019_completo):
        tabla = tabla_comparativa(data_dir_2019_completo, 2019)
        assert tabla is not None
        assert "| Agrupación | Municipio | Provincia | Nación |" in tabla
        assert "PARTIDO A" in tabla
        assert "80.0%" in tabla and "60.0%" in tabla and "50.0%" in tabla

    def test_blanco_nulo_va_siempre_al_final(self, data_dir_2019_completo):
        tabla = tabla_comparativa(data_dir_2019_completo, 2019)
        lineas = [l for l in tabla.splitlines() if l.startswith("|") and "---" not in l and "Agrupación" not in l]
        assert lineas[-1].split("|")[1].strip() == "BLANCO + NULO"

    def test_diferencias_en_puntos_porcentuales(self, data_dir_2019_completo):
        tabla = tabla_comparativa(data_dir_2019_completo, 2019)
        # PARTIDO A: Municipio 50%, Provincia 60%, Nación 80% -> Mun-Prov=-10, Mun-Nac=-30, Prov-Nac=-20
        fila = next(l for l in tabla.splitlines() if l.startswith("| PARTIDO A"))
        assert "-10.0 pp" in fila and "-30.0 pp" in fila and "-20.0 pp" in fila
