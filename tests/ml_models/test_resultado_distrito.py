"""Tests de `ml_models.construir_resultado_distrito`. Usa `tmp_path` con
`circuito_<cargo>.json` chicos (mismo patrón que `tests/electoral/test_totales.py`),
nunca la caché real."""
import json

import pytest

from ml_models.construir_calendario import FilaCalendario
from ml_models.construir_resultado_distrito import (
    FilaVotoPartido,
    calcular_delta_posicion_ideologica,
    calcular_delta_v,
    calcular_distancia_oficialismo_alternativa,
    construir_resultado_distrito,
    construir_voto_partido_distrito,
)


def _circuito(positivos: dict[str, tuple[str, int]], electores: int = 100) -> dict:
    return {
        "electores": electores,
        "positivos": {
            id_agr: {"nombre": nombre, "votos": votos, "campo_ideologico": "3"}
            for id_agr, (nombre, votos) in positivos.items()
        },
        "otros": {"EN BLANCO": 2, "NULO": 1},
    }


def _escribir_circuito(tmp_path, anio, cargo, circuitos):
    path = tmp_path / str(anio) / cargo / "generales"
    path.mkdir(parents=True)
    (path / f"circuito_{cargo}.json").write_text(
        json.dumps({"anio": anio, "nivel": cargo, "circuitos": circuitos}), encoding="utf-8"
    )


@pytest.fixture
def data_dir(tmp_path):
    _escribir_circuito(
        tmp_path,
        2011,
        "intendente",
        {"100": _circuito({"1": ("ALIANZA FRENTE PARA LA VICTORIA", 60), "2": ("PARTIDO B", 40)})},
    )
    _escribir_circuito(
        tmp_path,
        2015,
        "intendente",
        {"100": _circuito({"1": ("ALIANZA FRENTE PARA LA VICTORIA", 30), "2": ("CAMBIEMOS BUENOS AIRES", 70)})},
    )
    return tmp_path


def _fc(anio, nivel, tipo_eleccion="ejecutiva"):
    return FilaCalendario(anio, nivel, f"{anio}-01-01", tipo_eleccion, False, "")


class TestConstruirVotoPartidoDistrito:
    def test_una_fila_por_agrupacion_del_anio_disponible(self, data_dir):
        calendario = [_fc(2011, "municipal")]
        filas = construir_voto_partido_distrito(calendario, data_dir)
        assert len(filas) == 2
        assert {f.agrupacion for f in filas} == {"ALIANZA FRENTE PARA LA VICTORIA", "PARTIDO B"}

    def test_sin_filas_si_no_hay_circuito_cacheado(self, data_dir):
        calendario = [_fc(2001, "municipal")]
        filas = construir_voto_partido_distrito(calendario, data_dir)
        assert filas == []

    def test_share_suma_100(self, data_dir):
        calendario = [_fc(2011, "municipal")]
        filas = construir_voto_partido_distrito(calendario, data_dir)
        assert sum(f.share for f in filas) == pytest.approx(100.0)


class TestConstruirResultadoDistrito:
    def test_anio_sin_circuito_queda_marcado_no_disponible(self, data_dir):
        calendario = [_fc(2001, "municipal")]
        filas = construir_resultado_distrito(calendario, [], {}, {}, data_dir)
        assert filas[0].resultado_disponible is False
        assert filas[0].votos_validos is None
        assert filas[0].nota != ""

    def test_gana_oficialismo_viene_de_era_oficialismo_no_de_matchear_nombres(self, data_dir):
        calendario = [_fc(2011, "municipal")]
        voto_partido = construir_voto_partido_distrito(calendario, data_dir)
        oficialismo_por_nivel = {
            (2011, "municipal"): {"agrupacion_oficialismo": "PARTIDO PROGRESO SOCIAL"}  # etiqueta vieja, no compite en 2011
        }
        oficialismos_curados = {(2011, "municipal"): {"agrupacion_ganadora": "ALIANZA FRENTE PARA LA VICTORIA", "era_oficialismo": "true"}}
        filas = construir_resultado_distrito(calendario, voto_partido, oficialismo_por_nivel, oficialismos_curados, data_dir)
        assert filas[0].gana_oficialismo is True  # a pesar de que "PARTIDO PROGRESO SOCIAL" no matchea ningún competidor

    def test_share_oficialismo_es_el_del_ganador_cuando_gana(self, data_dir):
        calendario = [_fc(2011, "municipal")]
        voto_partido = construir_voto_partido_distrito(calendario, data_dir)
        oficialismo_por_nivel = {(2011, "municipal"): {"agrupacion_oficialismo": "PARTIDO PROGRESO SOCIAL"}}
        oficialismos_curados = {(2011, "municipal"): {"agrupacion_ganadora": "ALIANZA FRENTE PARA LA VICTORIA", "era_oficialismo": "true"}}
        filas = construir_resultado_distrito(calendario, voto_partido, oficialismo_por_nivel, oficialismos_curados, data_dir)
        assert filas[0].share_oficialismo == pytest.approx(60.0)  # 60/(60+40)

    def test_share_oficialismo_none_con_nota_si_pierde_y_no_matchea(self, data_dir):
        calendario = [_fc(2015, "municipal")]
        voto_partido = construir_voto_partido_distrito(calendario, data_dir)
        oficialismo_por_nivel = {(2015, "municipal"): {"agrupacion_oficialismo": "ALIANZA FRENTE PARA LA VICTORIA_ETIQUETA_VIEJA"}}
        oficialismos_curados = {(2015, "municipal"): {"agrupacion_ganadora": "CAMBIEMOS BUENOS AIRES", "era_oficialismo": "false"}}
        filas = construir_resultado_distrito(calendario, voto_partido, oficialismo_por_nivel, oficialismos_curados, data_dir)
        assert filas[0].gana_oficialismo is False
        assert filas[0].share_oficialismo is None
        assert "etiqueta" in filas[0].nota.lower()

    def test_share_oficialismo_matchea_por_nombre_si_pierde_pero_compite_con_el_mismo_nombre(self, data_dir):
        calendario = [_fc(2015, "municipal")]
        voto_partido = construir_voto_partido_distrito(calendario, data_dir)
        oficialismo_por_nivel = {(2015, "municipal"): {"agrupacion_oficialismo": "ALIANZA FRENTE PARA LA VICTORIA"}}
        oficialismos_curados = {(2015, "municipal"): {"agrupacion_ganadora": "CAMBIEMOS BUENOS AIRES", "era_oficialismo": "false"}}
        filas = construir_resultado_distrito(calendario, voto_partido, oficialismo_por_nivel, oficialismos_curados, data_dir)
        assert filas[0].gana_oficialismo is False
        assert filas[0].share_oficialismo == pytest.approx(30.0)  # 30/(30+70)

    def test_votos_blanco_y_participacion(self, data_dir):
        calendario = [_fc(2011, "municipal")]
        voto_partido = construir_voto_partido_distrito(calendario, data_dir)
        filas = construir_resultado_distrito(calendario, voto_partido, {}, {}, data_dir)
        assert filas[0].votos_validos == 100  # 60+40
        assert filas[0].votos_blanco == 3  # EN BLANCO (2) + NULO (1), ambos cuentan como blanco_nulo
        # participación = (positivos+otros)/electores = (100+3)/100
        assert filas[0].participacion == pytest.approx(103.0)


class TestCalcularDeltaV:
    def test_diferencia_de_shares(self):
        from ml_models.construir_resultado_distrito import FilaResultadoDistrito

        resultado = {
            (2015, "municipal"): FilaResultadoDistrito(2015, "municipal", 100, 2, 90.0, False, 30.0, True, ""),
            (2011, "municipal"): FilaResultadoDistrito(2011, "municipal", 100, 2, 90.0, True, 60.0, True, ""),
        }
        assert calcular_delta_v(resultado, "municipal", 2015, 2011) == pytest.approx(-30.0)

    def test_none_si_falta_algun_lado(self):
        assert calcular_delta_v({}, "municipal", 2015, 2011) is None


class TestCalcularDeltaPosicionIdeologica:
    def test_promedio_ponderado_por_share_solo_con_score_conocido(self):
        voto_partido = {
            2011: [
                FilaVotoPartido(2011, "municipal", "1", "PARTIDO A", 60, 60.0),
                FilaVotoPartido(2011, "municipal", "2", "PARTIDO B", 40, 40.0),
            ],
            2015: [
                FilaVotoPartido(2015, "municipal", "1", "PARTIDO A", 30, 30.0),
                FilaVotoPartido(2015, "municipal", "3", "PARTIDO SIN SCORE", 70, 70.0),
            ],
        }
        posiciones = {
            (2011, "municipal", "PARTIDO A"): -1.0,
            (2011, "municipal", "PARTIDO B"): 1.0,
            (2015, "municipal", "PARTIDO A"): -1.0,
            # PARTIDO SIN SCORE deliberadamente ausente
        }
        voto_partido_por_anio_nivel = {(2011, "municipal"): voto_partido[2011], (2015, "municipal"): voto_partido[2015]}
        resultado = calcular_delta_posicion_ideologica(voto_partido_por_anio_nivel, posiciones, "municipal", 2015, 2011)
        # 2011: (60*-1 + 40*1)/100 = -0.2 ; 2015: solo PARTIDO A con score => -1.0
        assert resultado == pytest.approx(-1.0 - (-0.2))

    def test_none_si_ninguna_agrupacion_tiene_score_ese_anio(self):
        voto_partido_por_anio_nivel = {(2015, "municipal"): [FilaVotoPartido(2015, "municipal", "1", "X", 10, 100.0)]}
        assert calcular_delta_posicion_ideologica(voto_partido_por_anio_nivel, {}, "municipal", 2015, 2011) is None


class TestCalcularDistanciaOficialismoAlternativa:
    def test_distancia_contra_la_principal_oposicion(self):
        voto_partido = [
            FilaVotoPartido(2011, "municipal", "1", "OFICIALISMO", 60, 60.0),
            FilaVotoPartido(2011, "municipal", "2", "OPOSICION CHICA", 10, 10.0),
            FilaVotoPartido(2011, "municipal", "3", "OPOSICION PRINCIPAL", 30, 30.0),
        ]
        posiciones = {"OFICIALISMO": -1.0, "OPOSICION CHICA": 2.0, "OPOSICION PRINCIPAL": 1.5}
        resultado = calcular_distancia_oficialismo_alternativa(voto_partido, posiciones, "OFICIALISMO")
        assert resultado == pytest.approx(2.5)  # |-1.0 - 1.5|, contra la de MÁS votos, no la más lejana

    def test_none_si_oficialismo_sin_score(self):
        voto_partido = [FilaVotoPartido(2011, "municipal", "1", "OFICIALISMO", 60, 60.0)]
        assert calcular_distancia_oficialismo_alternativa(voto_partido, {}, "OFICIALISMO") is None
