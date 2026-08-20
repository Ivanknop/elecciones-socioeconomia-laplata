"""Tests de `src/analisis/mapa_interactivo.py`: fórmulas de agregación
puras (blanco_nulo/ausentismo, top-N + residuo, índice de agrupaciones) --
sin red, sin Leaflet, sin generar HTML (misma línea divisoria que el resto
del repo entre lógica pura testeada y renderizado validado a mano)."""
from analisis.mapa_interactivo import (
    TOP_N,
    _construir_agrup_index,
    _construir_circuito,
    _construir_eleccion,
    _resolver_no_ideologicos,
    _votos_en_blanco,
    _votos_por_campo,
    _votos_por_familia,
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


class TestResolverNoIdeologicos:
    def test_formula_igual_a_graficos_votos_no_ideologicos(self):
        # positivos 80, otros 10 (blanco_nulo 7 + recurridos 3) -> ausentismo 10, mismo fixture que test_graficos.py
        c = _circuito(
            {"1": ("PARTIDO A", "3", 60), "2": ("PARTIDO B", "5", 20)},
            electores=100,
            otros={"EN BLANCO": 5, "NULO": 2, "RECURRIDOS": 3},
        )
        positivos, blanco_nulo, ausentismo = _resolver_no_ideologicos(c)
        assert (positivos, blanco_nulo, ausentismo) == (80, 7, 10)

    def test_ausentismo_negativo_no_se_recorta(self):
        # familia 504/505/508/509: más votos que electores registrados
        c = _circuito({"1": ("PARTIDO A", "3", 500)}, electores=100, otros={"EN BLANCO": 10})
        _, _, ausentismo = _resolver_no_ideologicos(c)
        assert ausentismo == 100 - 500 - 10 == -410

    def test_variante_blancos_nulos_plural(self):
        c = _circuito({"1": ("PARTIDO A", "3", 30)}, electores=60, otros={"BLANCOS": 3, "NULOS": 1})
        _, blanco_nulo, _ = _resolver_no_ideologicos(c)
        assert blanco_nulo == 4


class TestVotosEnBlanco:
    def test_solo_cuenta_blanco_no_nulo(self):
        c = _circuito({"1": ("PARTIDO A", "3", 30)}, electores=60, otros={"EN BLANCO": 5, "NULO": 2})
        assert _votos_en_blanco(c) == 5

    def test_variante_plural(self):
        c = _circuito({"1": ("PARTIDO A", "3", 30)}, electores=60, otros={"BLANCOS": 4, "NULOS": 1})
        assert _votos_en_blanco(c) == 4


class TestVotosPorCampoYFamilia:
    def test_suma_todas_las_agrupaciones_no_solo_el_top_n(self):
        positivos = {str(i): (f"PARTIDO {i}", "3", 1) for i in range(TOP_N + 3)}
        c = _circuito(positivos, electores=200, otros={})
        assert _votos_por_campo(c)["3"] == TOP_N + 3

    def test_agrupacion_sin_campo_va_a_clave_vacia_no_se_pierde(self):
        c = _circuito(
            {"1": ("PARTIDO A", "3", 10), "2": ("PARTIDO SIN CLASIFICAR", "", 5)},
            electores=60, otros={},
        )
        resultado = _votos_por_campo(c)
        assert resultado["3"] == 10
        assert resultado[""] == 5
        assert sum(resultado.values()) == 15  # nada se descarta

    def test_por_familia_usa_el_mapa_de_filiaciones(self):
        c = _circuito(
            {"1": ("PARTIDO A", "3", 10), "2": ("PARTIDO B", "5", 20)},
            electores=60, otros={},
        )
        filiaciones = {"PARTIDO A": "peronistas", "PARTIDO B": "liberales"}
        resultado = _votos_por_familia(c, filiaciones)
        assert resultado == {"peronistas": 10, "liberales": 20}

    def test_agrupacion_sin_filiacion_conocida_va_a_clave_vacia(self):
        c = _circuito({"1": ("PARTIDO NUEVO", "3", 7)}, electores=60, otros={})
        resultado = _votos_por_familia(c, filiaciones={})
        assert resultado == {"": 7}


class TestConstruirCircuito:
    def _circuito_y_filiaciones(self):
        c = _circuito(
            {
                "1": ("PARTIDO A", "3", 60),
                "2": ("PARTIDO B", "5", 20),
                "3": ("PARTIDO C", "1", 10),
            },
            electores=110,
            otros={"EN BLANCO": 5, "NULO": 2, "RECURRIDOS": 3},
        )
        filiaciones = {"PARTIDO A": "peronistas", "PARTIDO B": "liberales", "PARTIDO C": "marxistas"}
        agrup_index = {"PARTIDO A": 0, "PARTIDO B": 1, "PARTIDO C": 2}
        return c, filiaciones, agrup_index

    def test_total_incluye_blanco_nulo_y_ausentismo_no_solo_positivos(self):
        c, filiaciones, agrup_index = self._circuito_y_filiaciones()
        resultado = _construir_circuito(c, filiaciones, agrup_index)
        # positivos 90, blanco_nulo 7, ausentismo = 110-90-10=10 -> total 107
        assert resultado["pos"] == 90
        assert resultado["bn"][0] == 7
        assert resultado["aus"][0] == 10
        assert resultado["tot"] == 107

    def test_porcentajes_sobre_el_total_no_sobre_positivos(self):
        c, filiaciones, agrup_index = self._circuito_y_filiaciones()
        resultado = _construir_circuito(c, filiaciones, agrup_index)
        # PARTIDO A: 60 votos sobre total 107, no sobre positivos 90
        pct_partido_a = next(row[2] for row in resultado["r"] if row[0] == 0)
        assert abs(pct_partido_a - 60 / 107 * 100) < 0.01

    def test_ganador_es_el_de_mas_votos(self):
        c, filiaciones, agrup_index = self._circuito_y_filiaciones()
        resultado = _construir_circuito(c, filiaciones, agrup_index)
        assert resultado["g7"] == 0  # PARTIDO A
        assert resultado["cg"] == "3"
        assert resultado["fg"] == "peronistas"

    def test_sin_mas_de_top_n_agrupaciones_no_hay_residuo(self):
        c, filiaciones, agrup_index = self._circuito_y_filiaciones()
        resultado = _construir_circuito(c, filiaciones, agrup_index)
        assert resultado["otros_l"] is None

    def test_con_mas_de_top_n_agrupaciones_el_residuo_no_se_pierde(self):
        positivos = {str(i): (f"PARTIDO {i}", "3", 10 - i) for i in range(TOP_N + 3)}
        c = _circuito(positivos, electores=200, otros={"EN BLANCO": 1})
        filiaciones = {info[0]: "otros" for info in positivos.values()}
        agrup_index = {info[0]: i for i, info in enumerate(positivos.values())}
        resultado = _construir_circuito(c, filiaciones, agrup_index)
        assert len(resultado["r"]) == TOP_N
        assert resultado["otros_l"] is not None
        votos_top = sum(row[1] for row in resultado["r"])
        votos_totales_positivos = sum(v[2] for v in positivos.values())
        assert resultado["otros_l"][0] == votos_totales_positivos - votos_top

    def test_agrupacion_sin_campo_ideologico_queda_en_none_no_crashea(self):
        c = _circuito({"1": ("PARTIDO SIN CLASIFICAR", "", 50)}, electores=60, otros={})
        filiaciones = {"PARTIDO SIN CLASIFICAR": "otros"}
        agrup_index = {"PARTIDO SIN CLASIFICAR": 0}
        resultado = _construir_circuito(c, filiaciones, agrup_index)
        assert resultado["cg"] is None
        assert resultado["r"][0][3] is None

    def test_circuito_sin_positivos_no_crashea(self):
        c = _circuito({}, electores=10, otros={"EN BLANCO": 2})
        resultado = _construir_circuito(c, {}, {})
        assert resultado["pos"] == 0
        assert resultado["g7"] is None
        assert resultado["r"] == []

    def test_por_campo_y_por_familia_sobre_el_mismo_total_que_r(self):
        c, filiaciones, agrup_index = self._circuito_y_filiaciones()
        resultado = _construir_circuito(c, filiaciones, agrup_index)
        # PARTIDO A (campo "3", familia peronistas) es el único de ese campo/familia acá
        assert resultado["por_campo"]["3"] == [60, resultado["r"][0][2]]
        assert resultado["por_familia"]["peronistas"] == [60, resultado["r"][0][2]]


class TestConstruirEleccion:
    def test_acumulado_distrito_suma_los_circuitos(self):
        c1 = _circuito({"1": ("PARTIDO A", "3", 60)}, electores=100, otros={"EN BLANCO": 5})
        c2 = _circuito({"1": ("PARTIDO A", "3", 40)}, electores=80, otros={"NULO": 3})
        contenido = {"anio": 2023, "nivel": "intendente", "circuitos": {"0001": c1, "0002": c2}}
        filiaciones = {"PARTIDO A": "peronistas"}
        agrup_index = {"PARTIDO A": 0}
        resultado = _construir_eleccion(contenido, filiaciones, agrup_index)
        assert resultado["pos"] == 100
        assert resultado["bn"][0] == 8
        assert set(resultado["circuitos"]) == {"1", "2"}  # canonicalizado, sin ceros a la izquierda

    def test_no_pierde_votos_de_listas_chicas_fuera_del_top7_distrital(self):
        positivos = {str(i): (f"PARTIDO {i}", "3", 10 - i) for i in range(TOP_N + 2)}
        c = _circuito(positivos, electores=200, otros={})
        contenido = {"anio": 2023, "nivel": "intendente", "circuitos": {"0001": c}}
        filiaciones = {info[0]: "otros" for info in positivos.values()}
        agrup_index = {info[0]: i for i, info in enumerate(positivos.values())}
        resultado = _construir_eleccion(contenido, filiaciones, agrup_index)
        assert resultado["otros_l"] is not None
        assert resultado["otros_l"][0] > 0

    def test_por_campo_y_por_familia_acumulan_los_circuitos(self):
        c1 = _circuito({"1": ("PARTIDO A", "3", 60)}, electores=100, otros={"EN BLANCO": 5})
        c2 = _circuito({"1": ("PARTIDO A", "3", 40)}, electores=80, otros={"NULO": 3})
        contenido = {"anio": 2023, "nivel": "intendente", "circuitos": {"0001": c1, "0002": c2}}
        filiaciones = {"PARTIDO A": "peronistas"}
        agrup_index = {"PARTIDO A": 0}
        resultado = _construir_eleccion(contenido, filiaciones, agrup_index)
        assert resultado["por_campo"]["3"][0] == 100
        assert resultado["por_familia"]["peronistas"][0] == 100

    def test_resumen_ausentismo_relativo_al_padron_completo(self):
        # electores 100, positivos 60, blanco 5, nulo 2 (otros_total 7) -> ausentismo 33
        c = _circuito({"1": ("PARTIDO A", "3", 60)}, electores=100, otros={"EN BLANCO": 5, "NULO": 2})
        contenido = {"anio": 2023, "nivel": "intendente", "circuitos": {"0001": c}}
        resultado = _construir_eleccion(contenido, {"PARTIDO A": "peronistas"}, {"PARTIDO A": 0})
        assert resultado["resumen"]["ausentismo_pct"] == 33.0  # 33/100, no sobre "tot" (que excluye procedimentales)

    def test_resumen_blanco_relativo_a_votos_emitidos_no_a_positivos(self):
        # votos emitidos = electores - ausentismo = 100 - 33 = 67; blanco 5/67
        c = _circuito({"1": ("PARTIDO A", "3", 60)}, electores=100, otros={"EN BLANCO": 5, "NULO": 2})
        contenido = {"anio": 2023, "nivel": "intendente", "circuitos": {"0001": c}}
        resultado = _construir_eleccion(contenido, {"PARTIDO A": "peronistas"}, {"PARTIDO A": 0})
        assert resultado["resumen"]["blanco_votos"] == 5
        assert abs(resultado["resumen"]["blanco_pct"] - 5 / 67 * 100) < 0.01


class TestConstruirAgrupIndex:
    def test_orden_alfabetico_deterministico(self, tmp_path, monkeypatch):
        import json

        d = tmp_path / "2023" / "intendente" / "generales"
        d.mkdir(parents=True)
        contenido = {
            "anio": 2023, "nivel": "intendente",
            "circuitos": {
                "1": _circuito({"1": ("ZETA", "1", 5), "2": ("ALFA", "2", 3)}, electores=10, otros={}),
            },
        }
        (d / "circuito_intendente.json").write_text(json.dumps(contenido), encoding="utf-8")
        indice = _construir_agrup_index([(2023, "intendente", "generales")], tmp_path)
        assert indice == {"ALFA": 0, "ZETA": 1}
