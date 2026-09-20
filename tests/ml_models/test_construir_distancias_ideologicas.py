"""Tests de `ml_models.construir_distancias_ideologicas`."""
import pandas as pd
import pytest

from constantes import (
    CALENDARIO_ELECTORAL_PATH,
    DATA_DISTRITO_DIR,
    DISTANCIAS_IDEOLOGICAS_PATH,
    ELECCIONES_DIR,
    OFICIALISMOS_PATH,
    OFICIALISMO_POR_NIVEL_PATH,
)
from ml_models.construir_calendario import _cargar_oficialismos
from ml_models.construir_distancias_ideologicas import (
    construir_distancias,
    construir_distancias_eleccion,
    generar_csv,
)
from ml_models.construir_elecciones_resumen import _cargar_calendario
from ml_models.construir_resultado_distrito import (
    FilaVotoPartido,
    _cargar_oficialismo_por_nivel,
    construir_voto_partido_distrito,
)


def _v(agrupacion: str, votos: int, share: float, anio=2023, nivel="municipal", id_agrupacion="0001") -> FilaVotoPartido:
    return FilaVotoPartido(anio=anio, nivel=nivel, id_agrupacion=id_agrupacion, agrupacion=agrupacion, votos=votos, share=share)


class TestConstruirDistanciasEleccion:
    def test_una_fila_por_fuerza_viable_excluye_marginales(self):
        del_anio = [_v("OF", 800, 80.0), _v("OP", 150, 15.0), _v("chica", 30, 3.0), _v("marginal", 20, 2.0)]
        # UMBRAL_VIABLE=1.5 -- las 4 son viables acá (todas >=1.5); forzamos una sub-umbral
        del_anio = [_v("OF", 850, 85.0), _v("OP", 140, 14.0), _v("marginal", 10, 1.0)]
        vparty = {"OF": (1.0, -1.0), "OP": (2.0, 0.0)}
        of = {"agrupacion_oficialismo": "OF"}
        filas = construir_distancias_eleccion(del_anio, vparty, of, None, None)
        assert {f.agrupacion for f in filas} == {"OF", "OP"}

    def test_fila_oficialismo_distancia_cero_y_flag(self):
        del_anio = [_v("OF", 800, 80.0), _v("OP", 200, 20.0)]
        vparty = {"OF": (1.0, -1.0), "OP": (2.0, 0.5)}
        of = {"agrupacion_oficialismo": "OF"}
        filas = construir_distancias_eleccion(del_anio, vparty, of, None, None)
        fila_of = next(f for f in filas if f.agrupacion == "OF")
        assert fila_of.es_oficialismo is True
        assert fila_of.distancia_economico_al_oficialismo == 0.0
        assert fila_of.distancia_progresismo_al_oficialismo == 0.0
        assert fila_of.distancia_euclidea_al_oficialismo == 0.0

    def test_distancia_con_signo_y_euclidea(self):
        del_anio = [_v("OF", 800, 80.0), _v("OP", 200, 20.0)]
        vparty = {"OF": (1.0, -1.0), "OP": (2.0, 0.5)}
        of = {"agrupacion_oficialismo": "OF"}
        filas = construir_distancias_eleccion(del_anio, vparty, of, None, None)
        fila_op = next(f for f in filas if f.agrupacion == "OP")
        assert fila_op.distancia_economico_al_oficialismo == pytest.approx(1.0)  # 2.0 - 1.0
        assert fila_op.distancia_progresismo_al_oficialismo == pytest.approx(1.5)  # 0.5 - (-1.0)
        assert fila_op.distancia_euclidea_al_oficialismo == pytest.approx((1.0**2 + 1.5**2) ** 0.5)

    def test_fuerza_viable_sin_score_queda_con_distancia_vacia(self):
        del_anio = [_v("OF", 800, 80.0), _v("SIN_SCORE", 200, 20.0)]
        vparty = {"OF": (1.0, -1.0)}
        of = {"agrupacion_oficialismo": "OF"}
        filas = construir_distancias_eleccion(del_anio, vparty, of, None, None)
        fila = next(f for f in filas if f.agrupacion == "SIN_SCORE")
        assert fila.vparty_economico is None
        assert fila.distancia_euclidea_al_oficialismo is None

    def test_oficialismo_sin_score_ninguna_distancia_se_calcula(self):
        del_anio = [_v("OF", 800, 80.0), _v("OP", 200, 20.0)]
        vparty = {"OP": (2.0, 0.5)}  # OF no tiene score
        of = {"agrupacion_oficialismo": "OF"}
        filas = construir_distancias_eleccion(del_anio, vparty, of, None, None)
        fila_of = next(f for f in filas if f.agrupacion == "OF")
        fila_op = next(f for f in filas if f.agrupacion == "OP")
        assert fila_of.distancia_euclidea_al_oficialismo == 0.0  # identidad, no depende del score
        assert fila_of.vparty_economico is None  # pero no se conoce su score real
        assert fila_op.distancia_euclidea_al_oficialismo is None  # sin referencia, no se puede calcular

    def test_oficialismo_no_viable_no_aparece_pero_no_rompe(self):
        # oficialismo con 1% -- por debajo del piso de viabilidad
        # (id_agrupacion distintos: _entrada_oficialismo compara por id
        # cuando no hay match de nombre curado, un id repetido falsearía
        # la comparación "es el mismo partido que ganó")
        del_anio = [
            _v("OF", 10, 1.0, id_agrupacion="0001"),
            _v("A", 600, 60.0, id_agrupacion="0002"),
            _v("B", 390, 39.0, id_agrupacion="0003"),
        ]
        vparty = {"OF": (1.0, -1.0), "A": (2.0, 0.0), "B": (-2.0, 0.0)}
        of = {"agrupacion_oficialismo": "OF"}
        filas = construir_distancias_eleccion(del_anio, vparty, of, None, None)
        assert {f.agrupacion for f in filas} == {"A", "B"}
        assert all(not f.es_oficialismo for f in filas)


@pytest.fixture(scope="module")
def distancias_reales():
    calendario = _cargar_calendario(CALENDARIO_ELECTORAL_PATH)
    voto_partido = construir_voto_partido_distrito(calendario, DATA_DISTRITO_DIR, ELECCIONES_DIR)
    oficialismo_por_nivel = _cargar_oficialismo_por_nivel(OFICIALISMO_POR_NIVEL_PATH)
    oficialismos_curados = _cargar_oficialismos(OFICIALISMOS_PATH)
    filas = construir_distancias(calendario, voto_partido, oficialismo_por_nivel, oficialismos_curados, ELECCIONES_DIR)
    return pd.DataFrame([vars(f) for f in filas])


class TestCasoRealAuditoria2023:
    """D18: `distancia_oficialismo_alternativa` queda vacía para
    (2023, nacional)/(2023, provincial) porque `oficialismo_por_nivel.csv`
    dice 'FRENTE DE TODOS' y la boleta real dice 'UNION POR LA PATRIA'.
    Este módulo resuelve el mismo caso por identidad de objeto vía
    `_entrada_oficialismo`, no por nombre -- sobre datos reales, sin red."""

    @pytest.mark.parametrize("nivel", ["nacional", "provincial"])
    def test_2023_resuelve_union_por_la_patria_no_frente_de_todos(self, distancias_reales, nivel):
        del_2023 = distancias_reales[(distancias_reales["nivel"] == nivel) & (distancias_reales["anio"] == 2023)]
        oficialismo = del_2023[del_2023["es_oficialismo"]]
        assert len(oficialismo) == 1
        assert oficialismo.iloc[0]["agrupacion"] == "UNION POR LA PATRIA"

    # (nacional, 2003): la Alianza (titular entrante a esa elección, ver
    # _EJECUTIVA_PRE_2011["nacional"] en construir_calendario.py) no tiene
    # ninguna lista en la boleta de 2003 -- colapsó en dic-2001 y no
    # compitió. No es un hueco de adquisición ni una regresión: el
    # oficialismo de esa fila directamente no es identificable en los
    # datos reales.
    _SIN_OFICIALISMO_VIABLE_DOCUMENTADO = {("nacional", 2003)}

    def test_exactamente_un_oficialismo_por_nivel_anio_con_oficialismo_resuelto(self, distancias_reales):
        """Pedido explícito: nunca 0 ni >1 fila `es_oficialismo=True` por
        (nivel, año) -- salvo los casos documentados en
        _SIN_OFICIALISMO_VIABLE_DOCUMENTADO, donde el oficialismo real no
        tiene lista en la boleta."""
        conteo = distancias_reales[distancias_reales["es_oficialismo"]].groupby(["nivel", "anio"]).size()
        assert (conteo == 1).all(), conteo[conteo != 1]

        # todo (nivel, anio) que aparece en la tabla tiene que tener su
        # oficialismo resuelto -- si no lo tuviera, quedaría sin ninguna
        # fila es_oficialismo=True y el assert de arriba no lo vería
        # (paginaría el grupo entero), así que lo comparamos aparte contra
        # el universo real de (nivel, anio) de la tabla.
        universo = set(map(tuple, distancias_reales[["nivel", "anio"]].drop_duplicates().values.tolist()))
        con_oficialismo = set(conteo.index)
        sin_oficialismo_resuelto = universo - con_oficialismo - self._SIN_OFICIALISMO_VIABLE_DOCUMENTADO
        assert sin_oficialismo_resuelto == set(), (
            f"(nivel, anio) sin ninguna fila es_oficialismo=True: {sin_oficialismo_resuelto} "
            "-- si es por oficialismo no viable, documentarlo; si no, es una regresión"
        )


def test_generar_csv_escribe_columnas_esperadas(tmp_path):
    destino = generar_csv(destino=tmp_path / "distancias_ideologicas.csv")
    df = pd.read_csv(destino)
    assert list(df.columns) == [
        "nivel", "anio", "agrupacion", "votos", "share", "es_oficialismo",
        "vparty_economico", "vparty_progresismo",
        "distancia_economico_al_oficialismo", "distancia_progresismo_al_oficialismo",
        "distancia_euclidea_al_oficialismo",
    ]
    assert len(df) > 0
