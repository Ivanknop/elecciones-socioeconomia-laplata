"""Tests de `src/analisis/vparty_cuadrantes_local.py`: carga de posiciones
V-Party propias y filiaciones, las dos tablas de agregación
(distrito/localidad), y el armado de colores por partido (sombras dentro de
una familia política) -- toda lógica pura de join/agregación/color, sin
matplotlib ni red. El graficado en sí (`generar_distrito`/`generar_localidad`,
`graficar_cuadrantes_partido`) sigue sin test automatizado, mismo criterio
que el resto de `src/analisis/*` -- se valida corriendo el script contra
`data/` real (ver CLAUDE.md).
"""
import csv
import json

import pytest

from analisis.vparty_cuadrantes_local import (
    _color_por_partido,
    _sombras,
    _votos_por_circuito_agrupacion,
    cargar_filiaciones,
    cargar_posiciones_propias,
    tabla_distrito,
    tabla_localidades,
)


def _fila_clasificacion(anio, agrupacion, nivel, econ="", prog="", pop="", filiacion="otros"):
    return {
        "anio": str(anio), "agrupacion": agrupacion, "nivel": nivel,
        "campo_ideologico": "3", "filiacion_politica": filiacion,
        "vparty_economico": econ, "vparty_progresismo": prog, "vparty_populismo": pop,
    }


CAMPOS = [
    "anio", "agrupacion", "nivel", "campo_ideologico", "filiacion_politica",
    "vparty_economico", "vparty_progresismo", "vparty_populismo",
]


def _escribir_clasificacion(path, filas):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)


@pytest.fixture
def clasificacion_path(tmp_path):
    path = tmp_path / "clasificacion.csv"
    _escribir_clasificacion(path, [
        _fila_clasificacion(2023, "PARTIDO A", "intendente", "-1.0", "1.0", "0.5"),
        _fila_clasificacion(2023, "PARTIDO B", "intendente", "1.0", "-1.0", "0.2"),
        _fila_clasificacion(2023, "PARTIDO C", "intendente"),  # sin cobertura V-Party
        _fila_clasificacion(2011, "PARTIDO D", "gobernacion", "0.5", "0.5", "0.1"),  # nivel distinto en el CSV
    ])
    return path


def _circuito(positivos: dict[str, tuple[str, int]], electores: int = 100) -> dict:
    return {
        "electores": electores,
        "positivos": {
            id_agr: {"nombre": nombre, "votos": votos}
            for id_agr, (nombre, votos) in positivos.items()
        },
        "otros": {},
    }


@pytest.fixture
def data_dir(tmp_path):
    contenido_intendente = {
        "circuitos": {
            # dos circuitos de la misma localidad oficial
            "100": _circuito({"1": ("PARTIDO A", 60), "2": ("PARTIDO B", 20), "3": ("PARTIDO C", 10)}),
            "101": _circuito({"1": ("PARTIDO A", 30)}),
            # sin localidad asignada en el crosswalk de prueba
            "999": _circuito({"2": ("PARTIDO B", 15)}),
        },
    }
    path = tmp_path / "2023" / "intendente" / "generales"
    path.mkdir(parents=True)
    (path / "circuito_intendente.json").write_text(json.dumps(contenido_intendente), encoding="utf-8")

    contenido_gobernador = {
        "circuitos": {
            "200": _circuito({"4": ("PARTIDO D", 40)}),
        },
    }
    path = tmp_path / "2011" / "gobernador" / "generales"
    path.mkdir(parents=True)
    (path / "circuito_gobernador.json").write_text(json.dumps(contenido_gobernador), encoding="utf-8")

    return tmp_path


@pytest.fixture
def crosswalk_path(tmp_path):
    path = tmp_path / "circuitos_por_localidad.csv"
    path.write_text(
        "circuito;localidad;distancia_metros\n"
        "100;BARRIO_A;100.0\n"
        "101;BARRIO_A;150.0\n",
        encoding="utf-8",
    )
    return path


class TestCargarPosicionesPropias:
    def test_solo_incluye_filas_con_vparty_economico_poblado(self, clasificacion_path):
        posiciones = cargar_posiciones_propias(clasificacion_path)

        assert ("2023", "intendente", "PARTIDO A") in posiciones
        assert ("2023", "intendente", "PARTIDO B") in posiciones
        assert ("2023", "intendente", "PARTIDO C") not in posiciones

    def test_devuelve_la_tupla_econ_prog_pop_como_float(self, clasificacion_path):
        posiciones = cargar_posiciones_propias(clasificacion_path)

        assert posiciones[("2023", "intendente", "PARTIDO A")] == (-1.0, 1.0, 0.5)

    def test_conserva_el_nombre_de_nivel_tal_cual_esta_en_el_csv(self, clasificacion_path):
        posiciones = cargar_posiciones_propias(clasificacion_path)

        assert ("2011", "gobernacion", "PARTIDO D") in posiciones


class TestTablaDistrito:
    def test_suma_votos_de_todos_los_circuitos_para_agrupaciones_con_cobertura(self, data_dir, clasificacion_path):
        posiciones = cargar_posiciones_propias(clasificacion_path)

        df = tabla_distrito("municipal", posiciones, data_dir)

        fila_a = df.set_index("agrupacion").loc["PARTIDO A"]
        assert fila_a["votos"] == 60 + 30
        assert (fila_a["economico"], fila_a["progresismo"], fila_a["populismo"]) == (-1.0, 1.0, 0.5)

    def test_excluye_agrupaciones_sin_cobertura_vparty(self, data_dir, clasificacion_path):
        posiciones = cargar_posiciones_propias(clasificacion_path)

        df = tabla_distrito("municipal", posiciones, data_dir)

        assert "PARTIDO C" not in df["agrupacion"].values

    def test_usa_nivel_a_nivel_csv_para_el_join_de_gobernador(self, data_dir, clasificacion_path):
        posiciones = cargar_posiciones_propias(clasificacion_path)

        df = tabla_distrito("provincial", posiciones, data_dir)

        assert list(df["agrupacion"]) == ["PARTIDO D"]
        assert df.iloc[0]["votos"] == 40

    def test_devuelve_dataframe_vacio_si_no_hay_ninguna_agrupacion_con_cobertura(self, data_dir):
        df = tabla_distrito("municipal", {}, data_dir)

        assert df.empty


class TestVotosPorCircuitoAgrupacion:
    def test_mapea_nombre_de_agrupacion_a_votos_por_circuito(self):
        contenido = {
            "circuitos": {
                "100": _circuito({"1": ("PARTIDO A", 60), "2": ("PARTIDO B", 20)}),
            },
        }

        resultado = _votos_por_circuito_agrupacion(contenido)

        assert resultado == {"100": {"PARTIDO A": 60, "PARTIDO B": 20}}


class TestTablaLocalidades:
    def test_suma_votos_de_los_circuitos_de_la_misma_localidad(self, data_dir, clasificacion_path, crosswalk_path):
        posiciones = cargar_posiciones_propias(clasificacion_path)

        df = tabla_localidades("municipal", posiciones, data_dir, crosswalk_path)

        fila_a = df[(df["localidad"] == "BARRIO_A") & (df["agrupacion"] == "PARTIDO A")].iloc[0]
        assert fila_a["votos"] == 60 + 30  # circuitos 100 + 101

    def test_circuito_sin_crosswalk_cae_en_sin_determinar(self, data_dir, clasificacion_path, crosswalk_path):
        from electoral.localidades import SIN_DETERMINAR

        posiciones = cargar_posiciones_propias(clasificacion_path)

        df = tabla_localidades("municipal", posiciones, data_dir, crosswalk_path)

        fila_b = df[(df["localidad"] == SIN_DETERMINAR) & (df["agrupacion"] == "PARTIDO B")].iloc[0]
        assert fila_b["votos"] == 15  # circuito 999

    def test_excluye_agrupaciones_sin_cobertura_vparty(self, data_dir, clasificacion_path, crosswalk_path):
        posiciones = cargar_posiciones_propias(clasificacion_path)

        df = tabla_localidades("municipal", posiciones, data_dir, crosswalk_path)

        assert "PARTIDO C" not in df["agrupacion"].values

    def test_no_incluye_filas_de_votos_cero(self, tmp_path, clasificacion_path, crosswalk_path):
        contenido = {
            "circuitos": {
                # PARTIDO A con 0 votos en este circuito (ej. no se presentó ahí)
                "100": _circuito({"1": ("PARTIDO A", 0), "2": ("PARTIDO B", 20)}),
            },
        }
        path = tmp_path / "2023" / "intendente" / "generales"
        path.mkdir(parents=True)
        (path / "circuito_intendente.json").write_text(json.dumps(contenido), encoding="utf-8")

        posiciones = cargar_posiciones_propias(clasificacion_path)
        df = tabla_localidades("municipal", posiciones, tmp_path, crosswalk_path)

        assert df[(df["localidad"] == "BARRIO_A") & (df["agrupacion"] == "PARTIDO A")].empty
        assert not df[(df["localidad"] == "BARRIO_A") & (df["agrupacion"] == "PARTIDO B")].empty


class TestCargarFiliaciones:
    def test_devuelve_filiacion_por_agrupacion(self, clasificacion_path):
        filiaciones = cargar_filiaciones(clasificacion_path)

        assert filiaciones[("2023", "intendente", "PARTIDO A")] == "otros"

    def test_incluye_agrupaciones_sin_cobertura_vparty(self, clasificacion_path):
        """A diferencia de `cargar_posiciones_propias`, no filtra por
        `vparty_economico` -- PARTIDO C no tiene V-Party pero sí filiación."""
        filiaciones = cargar_filiaciones(clasificacion_path)

        assert ("2023", "intendente", "PARTIDO C") in filiaciones

    def test_omite_filas_sin_filiacion_politica(self, tmp_path):
        path = tmp_path / "clasificacion.csv"
        _escribir_clasificacion(path, [_fila_clasificacion(2023, "PARTIDO X", "intendente", filiacion="")])

        filiaciones = cargar_filiaciones(path)

        assert ("2023", "intendente", "PARTIDO X") not in filiaciones


class TestSombras:
    def test_devuelve_n_colores_distintos(self):
        colores = _sombras("#FF0000", 3)

        assert len(colores) == 3
        assert len(set(colores)) == 3

    def test_n_uno_devuelve_un_solo_color(self):
        colores = _sombras("#0000FF", 1)

        assert len(colores) == 1

    def test_mantiene_el_matiz_y_la_saturacion_del_color_base(self):
        import colorsys

        base = "#FF0000"
        h_base, l_base, s_base = colorsys.rgb_to_hls(1.0, 0.0, 0.0)

        for color in _sombras(base, 4):
            r, g, b = (int(color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            assert h == pytest.approx(h_base, abs=1e-6)
            assert s == pytest.approx(s_base, abs=1e-6)


class TestColorPorPartido:
    def test_partidos_de_distinta_familia_no_comparten_color(self):
        filiacion_de = {"PARTIDO A": "peronistas", "PARTIDO B": "liberales"}

        colores = _color_por_partido(["PARTIDO A", "PARTIDO B"], filiacion_de)

        assert colores["PARTIDO A"] != colores["PARTIDO B"]

    def test_partidos_de_la_misma_familia_reciben_sombras_distintas(self):
        filiacion_de = {"PARTIDO A": "peronistas", "PARTIDO B": "peronistas"}

        colores = _color_por_partido(["PARTIDO A", "PARTIDO B"], filiacion_de)

        assert colores["PARTIDO A"] != colores["PARTIDO B"]

    def test_partido_sin_filiacion_conocida_va_a_gris_sin_clasificar(self):
        from analisis.totales_por_lista import _COLOR_SIN_CLASIFICAR

        colores = _color_por_partido(["PARTIDO A"], {})

        assert colores["PARTIDO A"] == _COLOR_SIN_CLASIFICAR

    def test_familia_sin_color_definido_en_la_colorimetria_va_a_gris_sin_clasificar(self):
        from analisis.totales_por_lista import _COLOR_SIN_CLASIFICAR

        colores = _color_por_partido(["PARTIDO A"], {"PARTIDO A": "familia_inexistente"})

        assert colores["PARTIDO A"] == _COLOR_SIN_CLASIFICAR

    def test_partido_unico_en_su_familia_usa_el_color_base_de_la_colorimetria(self):
        from analisis.graficos import _COLOR_FILIACION

        colores = _color_por_partido(["PARTIDO A"], {"PARTIDO A": "marxistas"})

        assert colores["PARTIDO A"].lower() == _COLOR_FILIACION["marxistas"].lower()
