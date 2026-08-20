"""Tests de `src/analisis/serie_temporal_por_localidad.py`: selección de
(año, cargo) con cuadro por localidad ya generado, y armado de la serie por
localidad a partir de esos cuadros.
"""
import json

import pandas as pd
import pytest

from analisis.graficos import IDEOLOGIAS
from analisis.serie_temporal_por_localidad import (
    _cargar_cuadro,
    _localidades_en_puntos,
    _puntos_con_cuadro,
    _ruta_cuadro,
    _serie_localidad,
)


def _escribir_circuito_json(data_dir, anio, nivel):
    path = data_dir / str(anio) / nivel / "generales"
    path.mkdir(parents=True)
    (path / f"circuito_{nivel}.json").write_text(json.dumps({"circuitos": {}}), encoding="utf-8")


def _escribir_cuadro(cuadros_dir, anio, cargo, filas):
    """`filas` mapea localidad -> {ideologia: votos}, solo para las ideologías
    que interesan en el test (las que no aparecen quedan en 0)."""
    cuadros_dir.mkdir(parents=True, exist_ok=True)
    columnas = ["localidad", *IDEOLOGIAS.values()]
    df = pd.DataFrame(
        [
            {"localidad": localidad, **{ideologia: valores.get(ideologia, 0) for ideologia in IDEOLOGIAS.values()}}
            for localidad, valores in filas.items()
        ],
        columns=columnas,
    )
    ruta = cuadros_dir / f"{anio}_{cargo}_generales_localidad.csv"
    with ruta.open("w", encoding="utf-8", newline="") as f:
        f.write("# comentario de cobertura, como en cuadros_por_localidad.py\n")
        df.to_csv(f, index=False)
    return ruta


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / "data"
    _escribir_circuito_json(d, 2019, "intendente")
    _escribir_circuito_json(d, 2021, "municipal")
    _escribir_circuito_json(d, 2023, "intendente")
    return d


@pytest.fixture
def cuadros_dir(tmp_path):
    c = tmp_path / "por_localidad"
    # 2021/municipal no tiene cuadro generado a propósito -- debe quedar afuera de _puntos_con_cuadro
    _escribir_cuadro(c, 2019, "intendente", {"BARRIO_A": {"izquierda": 10, "derecha": 40}})
    _escribir_cuadro(c, 2023, "intendente", {"BARRIO_A": {"izquierda": 30, "derecha": 20}, "BARRIO_B": {"centro": 5}})
    return c


class TestRutaCuadro:
    def test_sigue_la_convencion_de_nombre_anio_cargo(self, tmp_path):
        ruta = _ruta_cuadro(tmp_path, 2023, "intendente")
        assert ruta == tmp_path / "2023_intendente_generales_localidad.csv"


class TestCargarCuadro:
    def test_ignora_el_comentario_de_cobertura(self, cuadros_dir):
        df = _cargar_cuadro(cuadros_dir, 2019, "intendente")
        assert list(df["localidad"]) == ["BARRIO_A"]


class TestPuntosConCuadro:
    def test_solo_incluye_puntos_con_cuadro_generado(self, data_dir, cuadros_dir):
        puntos = _puntos_con_cuadro(data_dir, cuadros_dir, "municipal")
        assert puntos == [(2019, "intendente"), (2023, "intendente")]

    def test_excluye_el_punto_sin_cuadro_aunque_tenga_circuito_json(self, data_dir, cuadros_dir):
        puntos = _puntos_con_cuadro(data_dir, cuadros_dir, "municipal")
        assert (2021, "municipal") not in puntos


class TestLocalidadesEnPuntos:
    def test_devuelve_la_union_ordenada_de_localidades(self, data_dir, cuadros_dir):
        puntos = _puntos_con_cuadro(data_dir, cuadros_dir, "municipal")
        localidades = _localidades_en_puntos(cuadros_dir, puntos)
        assert localidades == ["BARRIO_A", "BARRIO_B"]


class TestSerieLocalidad:
    def test_devuelve_los_votos_por_ideologia_en_cada_punto(self, data_dir, cuadros_dir):
        puntos = _puntos_con_cuadro(data_dir, cuadros_dir, "municipal")
        serie, totales = _serie_localidad(cuadros_dir, puntos, "BARRIO_A")
        assert serie["izquierda"] == [10, 30]
        assert serie["derecha"] == [40, 20]

    def test_cuadro_sin_columnas_nuevas_cuenta_blanco_nulo_y_ausentismo_como_cero(self, data_dir, cuadros_dir):
        """Los cuadros de la fixture (`_escribir_cuadro`) solo tienen columnas
        de ideología"""
        puntos = _puntos_con_cuadro(data_dir, cuadros_dir, "municipal")
        serie, _ = _serie_localidad(cuadros_dir, puntos, "BARRIO_A")
        assert serie["blanco_nulo"] == [0, 0]
        assert serie["ausentismo"] == [0, 0]

    def test_devuelve_blanco_nulo_y_ausentismo_cuando_el_cuadro_los_trae(self, data_dir, tmp_path):
        cuadros_dir = tmp_path / "por_localidad_con_ausentismo"
        cuadros_dir.mkdir()
        df = pd.DataFrame([{
            "localidad": "BARRIO_A", "izquierda": 10, "derecha": 40,
            "blanco_nulo": 5, "otros": 1, "votos": 56, "ausentismo": 20,
        }])
        ruta = cuadros_dir / "2019_intendente_generales_localidad.csv"
        with ruta.open("w", encoding="utf-8", newline="") as f:
            f.write("# comentario de cobertura\n")
            df.to_csv(f, index=False)

        puntos = _puntos_con_cuadro(data_dir, cuadros_dir, "municipal")
        serie, totales = _serie_localidad(cuadros_dir, puntos, "BARRIO_A")
        assert serie["blanco_nulo"] == [5]
        assert serie["ausentismo"] == [20]
        assert totales == [10 + 40 + 5 + 20]  # ideologías + blanco_nulo + ausentismo, sin "otros"

    def test_localidad_ausente_en_un_punto_cuenta_como_cero(self, data_dir, cuadros_dir):
        puntos = _puntos_con_cuadro(data_dir, cuadros_dir, "municipal")
        serie, totales = _serie_localidad(cuadros_dir, puntos, "BARRIO_B")
        assert serie["centro"] == [0, 5]

    def test_totales_suman_todas_las_ideologias_del_punto(self, data_dir, cuadros_dir):
        puntos = _puntos_con_cuadro(data_dir, cuadros_dir, "municipal")
        _, totales = _serie_localidad(cuadros_dir, puntos, "BARRIO_A")
        assert totales == [50, 50]
