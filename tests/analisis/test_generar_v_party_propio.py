"""Tests de `generar_v_party_propio.py`: parseo, validación, agregación y
calibración -- lógica pura, sin red. `main()` sin test, ver CLAUDE.md."""
import csv

import pytest

from analisis.generar_v_party_propio import (
    MAPEO_VPARTY,
    NO_MAPEAR_ADICIONALES,
    PARTIDOS,
    calibrar,
    cargar_encuesta,
    cargar_referencia,
    escribir_salida,
    estimar,
    mediana_por_partido,
    ols,
    rangos_vparty,
    targets_vparty,
    validar_expertos,
)

# ---------------------------------------------------------------------------
# Helpers para construir una encuesta anonimizada -- misma forma que
# encuesta_partidos_propia.csv: 1 columna de metadata (ID secuencial, sin
# datos personales), un bloque de 12 columnas (A1-D2) por cada uno de los
# 12 PARTIDOS reales del script (la validación de cantidad de columnas en
# cargar_encuesta está atada a ese largo fijo), y 1 columna final.
# ---------------------------------------------------------------------------

def _bloque(econ, prog, pop, d1=0, d2="Alta"):
    """A1-A4 → econ (invertida), B1-B4 → prog, C1-C2 → pop; D1/D2 no se
    usan en la agregación."""
    a = 4 - econ
    return [a, a, a, a, prog, prog, prog, prog, pop, pop, d1, d2]


def _fila(id_experto, valores_por_partido, comentario=""):
    fila = [str(id_experto)]
    for p in PARTIDOS:
        econ, prog, pop = valores_por_partido[p]
        fila.extend(_bloque(econ, prog, pop))
    fila.append(comentario)
    return fila


def _header():
    n_cols = 1 + 12 * len(PARTIDOS) + 1
    return [f"col{i}" for i in range(n_cols)]


def _escribir_csv(path, filas, header=None):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header if header is not None else _header())
        for fila in filas:
            w.writerow(fila)


# Valores "típicos" por partido, uniformes entre expertos, usados por varios
# tests para no repetir las 12 tuplas cada vez.
VALORES_BASE = {
    "Frente de Izquierda": (-2, 3, 0.5),
    "La Libertad Avanza": (3, -3, 0.2),
    "Proyecto Sur": (-1.5, 2, 0.6),
    "Coalicion Civica": (0.5, 0.3, 0.4),
    "Principios y Valores": (-0.5, -0.4, 0.5),
    "PRO": (1, -0.5, 0.2),
    "Union Civica Radical": (0.5, 0.4, 0.3),
    "Frente Renovador": (0.4, 0, 0.4),
    "Frente para la Victoria": (-1.7, 2, 0.9),
    "Patria Grande": (-1.4, 1.5, 0.8),
    "Partido Justicialista": (-0.1, 1, 0.5),
    "Encuentro Republicano Federal": (0.5, -0.4, 0.45),
}


# ---------------------------------------------------------------------------
# 1. cargar_encuesta
# ---------------------------------------------------------------------------

class TestCargarEncuesta:
    def test_calcula_econ_prog_pop_por_experto_y_partido(self, tmp_path):
        path = tmp_path / "encuesta.csv"
        otros = dict(VALORES_BASE, **{"Frente de Izquierda": (1, 1, 1)})
        _escribir_csv(path, [_fila("1", VALORES_BASE), _fila("2", otros)])

        survey, expertos = cargar_encuesta(str(path))

        assert expertos == ["1", "2"]
        for p, (econ, prog, pop) in VALORES_BASE.items():
            assert survey[("1", p)] == pytest.approx({"econ": econ, "prog": prog, "pop": pop})
        assert survey[("2", "Frente de Izquierda")] == pytest.approx({"econ": 1, "prog": 1, "pop": 1})

    def test_polaridad_economica_invertida(self, tmp_path):
        # A1-A4 = 0 (mínimo posible en la escala 0-4, "más estado") debe dar
        # econ = 4 - 0 = 4 (máximo de mercado/derecha), no 0 -- es la
        # inversión de polaridad documentada en el docstring del script.
        # Se arma la fila a mano (no vía _bloque, que ya aplica la
        # inversión al revés para construir el caso de prueba) para
        # controlar las respuestas crudas A1-A4 directamente.
        path = tmp_path / "encuesta.csv"
        fila = _fila("1", VALORES_BASE)
        pro_idx = 1 + PARTIDOS.index("PRO") * 12
        fila[pro_idx:pro_idx + 4] = [0, 0, 0, 0]  # A1-A4 crudas = 0
        _escribir_csv(path, [fila])

        survey, _ = cargar_encuesta(str(path))

        assert survey[("1", "PRO")]["econ"] == 4

    def test_ignora_filas_completamente_vacias(self, tmp_path):
        path = tmp_path / "encuesta.csv"
        n_cols = 1 + 12 * len(PARTIDOS) + 1
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(_header())
            w.writerow(_fila("1", VALORES_BASE))
            w.writerow([""] * n_cols)

        survey, expertos = cargar_encuesta(str(path))

        assert expertos == ["1"]

    def test_mismo_id_repetido_no_duplica_el_orden_de_expertos(self, tmp_path):
        path = tmp_path / "encuesta.csv"
        otros = dict(VALORES_BASE, **{"PRO": (2, 2, 2)})
        _escribir_csv(path, [_fila("1", VALORES_BASE), _fila("1", otros)])

        survey, expertos = cargar_encuesta(str(path))

        assert expertos == ["1"]
        # la segunda fila con el mismo ID pisa los valores de la primera
        assert survey[("1", "PRO")]["econ"] == 2

    def test_error_si_la_cantidad_de_columnas_no_coincide(self, tmp_path):
        path = tmp_path / "encuesta.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(_header()[:-1])  # header le falta una columna

        with pytest.raises(SystemExit):
            cargar_encuesta(str(path))

    def test_error_si_una_respuesta_no_es_numerica(self, tmp_path):
        path = tmp_path / "encuesta.csv"
        fila = _fila("1", VALORES_BASE)
        fila[1] = "texto"  # primer A1 del primer partido
        _escribir_csv(path, [fila])

        with pytest.raises(SystemExit):
            cargar_encuesta(str(path))


# ---------------------------------------------------------------------------
# 2. cargar_referencia / targets_vparty / rangos_vparty
# ---------------------------------------------------------------------------

REF_ROWS = [
    {"agrupacion": "COALICION CIVICA ARI", "vparty_economico": "2.0", "vparty_progresismo": "0.2", "vparty_populismo": "1.1"},
    {"agrupacion": "JUNTOS", "vparty_economico": "3.0", "vparty_progresismo": "1.0", "vparty_populismo": "0.5"},
    {"agrupacion": "FRENTE RENOVADOR", "vparty_economico": "1.8", "vparty_progresismo": "0.5", "vparty_populismo": "1.1"},
    {"agrupacion": "FRENTE PARA LA VICTORIA", "vparty_economico": "-2.4", "vparty_progresismo": "-1.5", "vparty_populismo": "2.6"},
    {"agrupacion": "FRENTE JUSTICIALISTA", "vparty_economico": "0.8", "vparty_progresismo": "-0.5", "vparty_populismo": "1.4"},
    {"agrupacion": "OTRO PARTIDO CUALQUIERA", "vparty_economico": "-3.0", "vparty_progresismo": "3.0", "vparty_populismo": "0.0"},
]


class TestCargarReferencia:
    def test_descarta_filas_sin_vparty_economico(self, tmp_path):
        path = tmp_path / "referencia.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["agrupacion", "vparty_economico", "vparty_progresismo", "vparty_populismo"])
            w.writeheader()
            w.writerow({"agrupacion": "CON DATO", "vparty_economico": "1.0", "vparty_progresismo": "1.0", "vparty_populismo": "1.0"})
            w.writerow({"agrupacion": "SIN DATO", "vparty_economico": "", "vparty_progresismo": "", "vparty_populismo": ""})

        rows = cargar_referencia(str(path))

        assert [r["agrupacion"] for r in rows] == ["CON DATO"]

    def test_error_si_no_hay_ninguna_fila_con_vparty(self, tmp_path):
        path = tmp_path / "referencia.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["agrupacion", "vparty_economico"])
            w.writeheader()
            w.writerow({"agrupacion": "SIN DATO", "vparty_economico": ""})

        with pytest.raises(SystemExit):
            cargar_referencia(str(path))


class TestTargetsVparty:
    def test_promedia_las_filas_que_matchean_mapeo_vparty(self):
        targets = targets_vparty(REF_ROWS)

        assert set(targets) == set(MAPEO_VPARTY)
        assert targets["Coalicion Civica"] == pytest.approx({"econ": 2.0, "prog": 0.2, "pop": 1.1, "n_filas": 1})
        assert targets["Frente para la Victoria"] == pytest.approx({"econ": -2.4, "prog": -1.5, "pop": 2.6, "n_filas": 1})

    def test_avisa_y_excluye_partido_sin_fila_de_referencia(self, capsys):
        ref_rows_incompleto = [r for r in REF_ROWS if r["agrupacion"] != "JUNTOS"]  # sin match para PRO

        targets = targets_vparty(ref_rows_incompleto)

        assert "PRO" not in targets
        assert "AVISO" in capsys.readouterr().out


class TestRangosVparty:
    def test_calcula_min_y_max_por_dimension(self):
        rangos = rangos_vparty(REF_ROWS)

        assert rangos == {
            "econ": pytest.approx((-3.0, 3.0)),
            "prog": pytest.approx((-1.5, 3.0)),
            "pop": pytest.approx((0.0, 2.6)),
        }


# ---------------------------------------------------------------------------
# 3. validar_expertos
# ---------------------------------------------------------------------------

class TestValidarExpertos:
    def test_sin_targets_no_valida_y_lo_deja_asentado_en_el_log(self):
        survey = {(e, p): {"econ": 0, "prog": 0, "pop": 0} for e in ["E1"] for p in PARTIDOS}
        log = []

        distancias = validar_expertos(survey, ["E1"], {}, REF_ROWS, log)

        assert distancias == {}
        assert any("no se puede validar" in linea for linea in log)

    def test_detecta_como_outlier_al_experto_que_mas_se_aleja_del_valor_real(self):
        targets = targets_vparty(REF_ROWS)
        # E1, E2 y E3 responden igual (valores "típicos"); E4 responde de
        # forma extrema para los 5 partidos con match real -- debería
        # quedar con una distancia muy superior al resto y marcarse como
        # posible outlier.
        survey = {}
        for e in ["E1", "E2", "E3"]:
            for p, (econ, prog, pop) in VALORES_BASE.items():
                survey[(e, p)] = {"econ": econ, "prog": prog, "pop": pop}
        for p, (econ, prog, pop) in VALORES_BASE.items():
            if p in targets:
                survey[("E4", p)] = {"econ": -econ * 50, "prog": -prog * 50, "pop": -pop * 50}
            else:
                survey[("E4", p)] = {"econ": econ, "prog": prog, "pop": pop}
        log = []

        distancias = validar_expertos(survey, ["E1", "E2", "E3", "E4"], targets, REF_ROWS, log)

        assert set(distancias) == {"E1", "E2", "E3", "E4"}
        assert distancias["E1"] == pytest.approx(distancias["E2"]) == pytest.approx(distancias["E3"])
        assert distancias["E4"] > distancias["E1"]
        assert any("Posibles outliers" in linea and "E4" in linea for linea in log)


# ---------------------------------------------------------------------------
# 4. mediana_por_partido / ols / calibrar / estimar
# ---------------------------------------------------------------------------

class TestMedianaPorPartido:
    def test_mediana_de_tres_expertos_con_un_disidente(self):
        survey = {}
        for e in ["E1", "E2", "E3"]:
            for p, (econ, prog, pop) in VALORES_BASE.items():
                survey[(e, p)] = {"econ": econ, "prog": prog, "pop": pop}
        # PRO: los tres expertos difieren -- la mediana debe ser el valor
        # del medio, no el promedio.
        for e, (econ, prog, pop) in zip(["E1", "E2", "E3"], [(1, 1, 1), (2, 2, 2), (9, 9, 9)]):
            survey[(e, "PRO")] = {"econ": econ, "prog": prog, "pop": pop}

        medianas = mediana_por_partido(survey, ["E1", "E2", "E3"])

        assert medianas["PRO"] == pytest.approx({"econ": 2, "prog": 2, "pop": 2})
        assert medianas["Frente de Izquierda"] == pytest.approx(
            {"econ": -2, "prog": 3, "pop": 0.5}
        )


class TestOls:
    def test_ajuste_perfecto_da_r2_uno(self):
        xs = [0, 1, 2, 3]
        ys = [1, 3, 5, 7]  # y = 1 + 2x

        a, b, r2 = ols(xs, ys)

        assert (a, b, r2) == pytest.approx((1.0, 2.0, 1.0))

    def test_x_constante_devuelve_la_media_de_y_con_pendiente_cero(self):
        a, b, r2 = ols([5, 5, 5], [1, 2, 3])

        assert (a, b) == pytest.approx((2.0, 0.0))
        assert r2 != r2  # nan


class TestCalibrarYEstimar:
    def test_calibracion_lineal_perfecta_y_estimacion_consistente(self):
        targets = targets_vparty(REF_ROWS)
        survey = {}
        for e in ["E1", "E2", "E3"]:
            for p, (econ, prog, pop) in VALORES_BASE.items():
                survey[(e, p)] = {"econ": econ, "prog": prog, "pop": pop}
        medianas = mediana_por_partido(survey, ["E1", "E2", "E3"])
        log = []

        calib, rangos = calibrar(medianas, targets, REF_ROWS, log)

        # Los 5 partidos con match real fueron construidos para caer
        # exactamente sobre una recta por dimensión (ver REF_ROWS): la
        # calibración debe recuperar esa recta con R²=1.
        assert calib["econ"] == pytest.approx((1.0, 2.0))
        assert calib["prog"] == pytest.approx((0.5, -1.0))
        assert calib["pop"] == pytest.approx((-0.1, 3.0))
        assert all("1.000" in linea for linea in log if linea.startswith("| econ") or linea.startswith("| prog") or linea.startswith("| pop"))

        estimaciones = estimar(medianas, calib)

        assert estimaciones["Frente de Izquierda"] == pytest.approx({"econ": -3.0, "prog": -2.5, "pop": 1.4})
        assert estimaciones["La Libertad Avanza"] == pytest.approx({"econ": 7.0, "prog": 3.5, "pop": 0.5})

    def test_avisa_si_hay_menos_de_tres_partidos_con_match_real(self):
        targets_pocos = {"Frente Renovador": {"econ": 1.8, "prog": 0.5, "pop": 1.1, "n_filas": 1}}
        medianas = {p: {"econ": 0, "prog": 0, "pop": 0} for p in PARTIDOS}
        medianas["Frente Renovador"] = {"econ": 0.4, "prog": 0, "pop": 0.4}
        log = []

        calibrar(medianas, targets_pocos, REF_ROWS, log)

        assert any("AVISO" in linea and "menos de 3" in linea for linea in log)


# ---------------------------------------------------------------------------
# 5. escribir_salida
# ---------------------------------------------------------------------------

class TestEscribirSalida:
    def test_pipeline_completo_reproduce_valores_y_marcado_con_numeral(self, tmp_path):
        """Extremo a extremo: partidos con match real llevan fuente="real"
        y prefijo "#"; valores lineales, comprobables con precisión."""
        targets = targets_vparty(REF_ROWS)
        survey = {}
        for e in ["E1", "E2", "E3"]:
            for p, (econ, prog, pop) in VALORES_BASE.items():
                survey[(e, p)] = {"econ": econ, "prog": prog, "pop": pop}
        medianas = mediana_por_partido(survey, ["E1", "E2", "E3"])
        log = []
        calib, rangos = calibrar(medianas, targets, REF_ROWS, log)
        estimaciones = estimar(medianas, calib)

        salida = tmp_path / "v_party_propio.csv"
        escribir_salida(str(salida), targets, estimaciones, rangos, log)

        with open(salida, encoding="utf-8", newline="") as f:
            filas = list(csv.reader(f))

        assert filas[0] == ["partido", "vparty_economico", "vparty_progresismo", "vparty_populismo"]
        por_partido = {fila[0].lstrip("#"): fila for fila in filas[1:]}

        assert set(MAPEO_VPARTY) <= set(NO_MAPEAR_ADICIONALES | set(MAPEO_VPARTY))  # sanity de las constantes usadas abajo
        for p in MAPEO_VPARTY:
            assert por_partido[p][0].startswith("#"), f"{p} debería salir marcado con # (fuente real)"
        for p in NO_MAPEAR_ADICIONALES:
            assert por_partido[p][0].startswith("#"), f"{p} debería salir marcado con # (NO_MAPEAR_ADICIONALES)"
        for p in set(PARTIDOS) - set(MAPEO_VPARTY) - NO_MAPEAR_ADICIONALES:
            assert not por_partido[p][0].startswith("#"), f"{p} no debería salir marcado con #"

        assert por_partido["Coalicion Civica"][1:] == [f"{v:.3f}" for v in (2.0, 0.2, 1.1)]
        assert por_partido["Frente para la Victoria"][1:] == [f"{v:.3f}" for v in (-2.4, -1.5, 2.6)]
        assert por_partido["Frente de Izquierda"][1:] == [f"{v:.3f}" for v in (-3.0, -2.5, 1.4)]
        assert por_partido["Union Civica Radical"][1:] == [f"{v:.3f}" for v in (2.0, 0.1, 0.8)]

    def test_usa_terminador_de_linea_unix(self, tmp_path):
        targets = {}
        estimaciones = {p: {"econ": 0.0, "prog": 0.0, "pop": 0.0} for p in PARTIDOS}
        rangos = {"econ": (-1.0, 1.0), "prog": (-1.0, 1.0), "pop": (-1.0, 1.0)}
        salida = tmp_path / "salida.csv"

        escribir_salida(str(salida), targets, estimaciones, rangos, [])

        contenido = salida.read_bytes()
        assert b"\r" not in contenido

    def test_marca_extrapolacion_fuera_del_rango_de_referencia(self, tmp_path):
        targets = {}
        estimaciones = {p: {"econ": 0.0, "prog": 0.0, "pop": 0.0} for p in PARTIDOS}
        estimaciones["La Libertad Avanza"] = {"econ": 99.0, "prog": 0.0, "pop": 0.0}
        rangos = {"econ": (-1.0, 1.0), "prog": (-1.0, 1.0), "pop": (-1.0, 1.0)}
        log = []
        salida = tmp_path / "salida.csv"

        escribir_salida(str(salida), targets, estimaciones, rangos, log)

        linea_lla = next(linea for linea in log if linea.startswith("| La Libertad Avanza"))
        assert "econ" in linea_lla.rsplit("|", 2)[-2]
