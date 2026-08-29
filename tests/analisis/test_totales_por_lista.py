"""Tests de `src/analisis/totales_por_lista.py`: combinador puro que agrega
BLANCO + NULO al resultado total por agrupación -- capa de datos compartida
por otros módulos, sin gráficos propios (ver CLAUDE.md).
"""
import json

from analisis.totales_por_lista import _ID_BLANCO_NULO, _NOMBRE_BLANCO_NULO, resultado_total_con_blanco_nulo


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


class TestResultadoTotalConBlancoNulo:
    def test_agrega_blanco_nulo_a_los_totales_por_agrupacion(self, tmp_path):
        _escribir_circuito(
            tmp_path, 2023, "intendente",
            {
                "100": _circuito(
                    {"1": ("PARTIDO A", "3", 60), "2": ("PARTIDO B", "5", 20)},
                    electores=100, otros={"EN BLANCO": 5, "NULO": 3},
                ),
            },
        )

        totales = resultado_total_con_blanco_nulo(tmp_path, 2023, "intendente")
        por_id = {v.id_agrupacion: v.votos for v in totales}

        assert por_id == {"1": 60, "2": 20, _ID_BLANCO_NULO: 8}

    def test_blanco_nulo_tiene_el_nombre_esperado(self, tmp_path):
        _escribir_circuito(
            tmp_path, 2023, "intendente",
            {"100": _circuito({"1": ("PARTIDO A", "3", 60)}, electores=100, otros={"EN BLANCO": 5, "NULO": 3})},
        )

        totales = resultado_total_con_blanco_nulo(tmp_path, 2023, "intendente")
        blanco_nulo = next(v for v in totales if v.id_agrupacion == _ID_BLANCO_NULO)

        assert blanco_nulo.nombre_agrupacion == _NOMBRE_BLANCO_NULO

    def test_porcentaje_se_recalcula_sobre_el_nuevo_total(self, tmp_path):
        _escribir_circuito(
            tmp_path, 2023, "intendente",
            {"100": _circuito({"1": ("PARTIDO A", "3", 75)}, electores=100, otros={"EN BLANCO": 25, "NULO": 0})},
        )

        totales = resultado_total_con_blanco_nulo(tmp_path, 2023, "intendente")
        por_id = {v.id_agrupacion: v.votos_porcentaje for v in totales}

        # 75 + 25 = 100 total -> 75% / 25%, no el % sobre positivos únicamente (que daría 100%)
        assert por_id["1"] == 75.0
        assert por_id[_ID_BLANCO_NULO] == 25.0

    def test_sin_blanco_ni_nulo_agrega_entrada_en_cero(self, tmp_path):
        _escribir_circuito(
            tmp_path, 2023, "intendente",
            {"100": _circuito({"1": ("PARTIDO A", "3", 100)}, electores=100, otros={"EN BLANCO": 0, "NULO": 0})},
        )

        totales = resultado_total_con_blanco_nulo(tmp_path, 2023, "intendente")
        por_id = {v.id_agrupacion: v.votos for v in totales}

        assert por_id[_ID_BLANCO_NULO] == 0
