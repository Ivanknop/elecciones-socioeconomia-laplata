"""Tests de `src/analisis/graficos.py`: agregación pura por campo_ideologico
y blanco+nulo/ausentismo a partir de un `circuito_<nivel>.json` chico -- la
mitad de renderizado matplotlib (`graficar_barras`/`graficar_torta`) sigue sin
tests automatizados, se valida corriendo los scripts contra `data/` real (ver
CLAUDE.md).
"""
import json

import pytest

from analisis.graficos import (
    IDEOLOGIAS,
    _COLOR_IDEOLOGIA,
    _cargar_circuito,
    _cargar_escala_ideologica,
    _circuitos_seleccionados,
    _votos_no_ideologicos,
    _votos_por_ideologia,
    color_categoria,
)


def _circuito(positivos: dict[str, tuple[str, str, int]], electores: int, otros: dict[str, int]) -> dict:
    """`positivos` mapea id_agrupacion -> (nombre, campo_ideologico, votos)."""
    return {
        "electores": electores,
        "positivos": {
            id_agr: {"nombre": nombre, "campo_ideologico": campo, "votos": votos}
            for id_agr, (nombre, campo, votos) in positivos.items()
        },
        "otros": otros,
    }


@pytest.fixture
def contenido():
    return {
        "anio": 2023,
        "nivel": "intendente",
        "circuitos": {
            # positivos 80, otros 10 (blanco_nulo 7 + recurridos 3) -> ausentismo 10
            "100": _circuito(
                {"1": ("PARTIDO A", "3", 60), "2": ("PARTIDO B", "5", 20)},
                electores=100,
                otros={"EN BLANCO": 5, "NULO": 2, "RECURRIDOS": 3},
            ),
            # nombres "BLANCOS"/"NULOS" (variante 2021, no "EN BLANCO"/"NULO") --
            # positivos 45, otros 4 (todo blanco_nulo) -> ausentismo 11
            "101": _circuito(
                {"1": ("PARTIDO A", "3", 30), "2": ("PARTIDO B", "5", 15)},
                electores=60,
                otros={"BLANCOS": 3, "NULOS": 1},
            ),
        },
    }


class TestVotosPorIdeologia:
    def test_suma_por_campo_ideologico_todos_los_circuitos(self, contenido):
        assert _votos_por_ideologia(contenido, circuito_id=None) == {"centro": 90, "derecha": 35}

    def test_un_solo_circuito(self, contenido):
        assert _votos_por_ideologia(contenido, circuito_id="100") == {"centro": 60, "derecha": 20}

    def test_circuito_inexistente_da_keyerror(self, contenido):
        with pytest.raises(KeyError):
            _votos_por_ideologia(contenido, circuito_id="999")

    def test_campo_ideologico_no_reconocido_da_keyerror(self, contenido):
        # Nunca se enmascara en silencio una agrupación sin clasificación
        # válida -- mismo criterio que el join de notebook 04 (ver CLAUDE.md).
        contenido["circuitos"]["100"]["positivos"]["1"]["campo_ideologico"] = ""
        with pytest.raises(KeyError):
            _votos_por_ideologia(contenido, circuito_id=None)


class TestVotosNoIdeologicos:
    def test_blanco_nulo_reconoce_nombres_2011_y_2021(self, contenido):
        # circuito 100 usa "EN BLANCO"/"NULO", circuito 101 "BLANCOS"/"NULOS" -- ambas variantes suman
        assert _votos_no_ideologicos(contenido, circuito_id=None)["blanco_nulo"] == 7 + 4

    def test_blanco_nulo_no_incluye_categorias_procedimentales(self, contenido):
        # RECURRIDOS (circuito 100) resta en ausentismo pero no cuenta como blanco_nulo
        assert _votos_no_ideologicos(contenido, circuito_id="100")["blanco_nulo"] == 7

    def test_ausentismo_es_electores_menos_positivos_menos_otros(self, contenido):
        votos = _votos_no_ideologicos(contenido, circuito_id=None)
        assert votos["ausentismo"] == 10 + 11

    def test_un_solo_circuito(self, contenido):
        votos = _votos_no_ideologicos(contenido, circuito_id="101")
        assert votos == {"blanco_nulo": 4, "ausentismo": 11}


class TestCircuitosSeleccionados:
    def test_none_devuelve_todos(self, contenido):
        assert len(_circuitos_seleccionados(contenido, None)) == 2

    def test_id_puntual_devuelve_uno_solo(self, contenido):
        seleccion = _circuitos_seleccionados(contenido, "100")
        assert len(seleccion) == 1
        assert seleccion[0]["electores"] == 100

    def test_id_inexistente_da_keyerror(self, contenido):
        with pytest.raises(KeyError):
            _circuitos_seleccionados(contenido, "no-existe")


class TestColorCategoria:
    def test_categoria_ideologica(self):
        # el color real vive en data/agrupaciones/colorimetria_campo_ideologico.csv,
        # no se hardcodea acá un segundo literal que pueda quedar desactualizado
        assert color_categoria("centro") == _COLOR_IDEOLOGIA["centro"]

    def test_categoria_no_ideologica(self):
        assert color_categoria("blanco_nulo") == "#c9c9c9"

    def test_categoria_desconocida_da_keyerror(self):
        with pytest.raises(KeyError):
            color_categoria("no existe")


class TestCargarEscalaIdeologica:
    def test_lee_valor_a_ideologia_en_el_orden_del_csv(self, tmp_path):
        archivo = tmp_path / "campo_ideologico.csv"
        archivo.write_text("valor,ideologia\n1,izquierda\n2,centro\n3,derecha\n", encoding="utf-8")

        assert _cargar_escala_ideologica(archivo) == {"1": "izquierda", "2": "centro", "3": "derecha"}
        # el orden de inserción del dict importa -- lo usa list(IDEOLOGIAS.values()) en toda la capa de gráficos
        assert list(_cargar_escala_ideologica(archivo).values()) == ["izquierda", "centro", "derecha"]

    def test_ideologias_del_modulo_viene_del_csv_versionado(self):
        # Nunca hardcodeada de nuevo en el módulo -- `data/agrupaciones/campo_ideologico.csv`
        # es la única fuente (ver §2.1 de docs/PLAN_CORRECCIONES_ELECTORALES.md).
        assert IDEOLOGIAS == _cargar_escala_ideologica()


class TestCargarCircuito:
    def test_lee_generales_por_defecto(self, tmp_path, contenido):
        destino = tmp_path / "2023" / "intendente" / "generales"
        destino.mkdir(parents=True)
        (destino / "circuito_intendente.json").write_text(json.dumps(contenido), encoding="utf-8")

        leido = _cargar_circuito(tmp_path, 2023, "intendente")
        assert leido == contenido
