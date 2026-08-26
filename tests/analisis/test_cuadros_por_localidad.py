"""Tests de `src/analisis/cuadros_por_localidad.py`: genera el cuadro a partir
de un `circuito_<nivel>.json` y un crosswalk chicos, ambos en `tmp_path`.
"""
import json

import pandas as pd
import pytest

from analisis.cuadros_por_localidad import _clasificar_no_positivo, generar_cuadro_localidad
from electoral.localidades import SIN_DETERMINAR


def _circuito(positivos: dict[str, tuple[str, int, str]], otros: dict[str, int]) -> dict:
    """`positivos` mapea id_agrupacion -> (nombre, votos, campo_ideologico)."""
    return {
        "mesas": 1,
        "electores": 100,
        "mesas_sin_votos_positivos": 0,
        "positivos": {
            id_agr: {"nombre": nombre, "votos": votos, "campo_ideologico": campo}
            for id_agr, (nombre, votos, campo) in positivos.items()
        },
        "otros": otros,
    }


@pytest.fixture
def circuito_json_path(tmp_path):
    contenido = {
        "anio": 2023,
        "nivel": "intendente",
        "categoria_id": 7,
        "fuente": "csv",
        "coincide_con_agregado_json": True,
        "advertencia_fuente": None,
        "cobertura": {},
        "circuitos": {
            # dos circuitos de la misma localidad oficial
            "100": _circuito(
                {"1": ("PARTIDO A", 60, "3"), "2": ("PARTIDO B", 20, "1")},
                {"EN BLANCO": 5, "NULO": 1, "IMPUGNADO": 0, "RECURRIDO": 0, "COMANDO": 0},
            ),
            "101": _circuito(
                {"1": ("PARTIDO A", 30, "3")},
                {"EN BLANCO": 2, "NULO": 0, "IMPUGNADO": 0, "RECURRIDO": 0, "COMANDO": 0},
            ),
            # sin localidad asignada en el crosswalk de prueba
            "999": _circuito(
                {"2": ("PARTIDO B", 15, "1")},
                {"EN BLANCO": 0, "NULO": 0, "IMPUGNADO": 0, "RECURRIDO": 0, "COMANDO": 0},
            ),
        },
    }
    path = tmp_path / "2023" / "intendente" / "generales"
    path.mkdir(parents=True)
    archivo = path / "circuito_intendente.json"
    archivo.write_text(json.dumps(contenido), encoding="utf-8")
    return tmp_path


@pytest.fixture
def crosswalk_path(tmp_path):
    archivo = tmp_path / "circuitos_por_localidad.csv"
    archivo.write_text(
        "circuito;localidad;distancia_metros\n"
        "100;BARRIO_A;100.0\n"
        "101;BARRIO_A;150.0\n",
        encoding="utf-8",
    )
    return archivo


def _leer_cuadro(path):
    return pd.read_csv(path, comment="#")


class TestClasificarNoPositivo:
    @pytest.mark.parametrize("nombre", ["EN BLANCO", "BLANCOS", "BLANCO"])
    def test_blanco_va_a_blanco_nulo(self, nombre):
        assert _clasificar_no_positivo(nombre) == "blanco_nulo"

    @pytest.mark.parametrize("nombre", ["NULO", "NULOS"])
    def test_nulo_va_a_blanco_nulo(self, nombre):
        assert _clasificar_no_positivo(nombre) == "blanco_nulo"

    @pytest.mark.parametrize("nombre", ["IMPUGNADO", "IMPUGNADOS", "RECURRIDO", "RECURRIDOS", "COMANDO"])
    def test_procedimentales_van_a_otros(self, nombre):
        assert _clasificar_no_positivo(nombre) == "otros"

    def test_categoria_no_vista_antes_va_a_otros_sin_perder_el_voto(self):
        assert _clasificar_no_positivo("UNA_CATEGORIA_NUEVA") == "otros"


class TestGenerarCuadroLocalidad:
    def test_devuelve_none_si_no_existe_el_circuito_json(self, tmp_path, crosswalk_path):
        salida = generar_cuadro_localidad(
            tmp_path, tmp_path / "por_localidad", 2023, "intendente", "paso", crosswalk_path,
        )
        assert salida is None

    def test_nombre_de_archivo_sigue_la_convencion_anio_nivel_etapa(self, circuito_json_path, crosswalk_path, tmp_path):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        assert salida.name == "2023_intendente_generales_localidad.csv"

    def test_archivo_se_guarda_directamente_en_salida_dir(self, circuito_json_path, crosswalk_path, tmp_path):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        assert salida.parent == tmp_path / "por_localidad"

    def test_ningun_voto_se_pierde(self, circuito_json_path, crosswalk_path, tmp_path):
        contenido = json.loads(
            (circuito_json_path / "2023" / "intendente" / "generales" / "circuito_intendente.json").read_text()
        )
        total_origen = sum(
            sum(p["votos"] for p in c["positivos"].values()) + sum(c["otros"].values())
            for c in contenido["circuitos"].values()
        )
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        cuadro = _leer_cuadro(salida)
        assert cuadro["votos"].sum() == total_origen

    def test_barrio_a_suma_los_dos_circuitos_agrupados(self, circuito_json_path, crosswalk_path, tmp_path):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        cuadro = _leer_cuadro(salida)
        fila = cuadro.set_index("localidad").loc["BARRIO_A"]
        assert fila["votos"] == (60 + 20 + 5 + 1) + (30 + 2)  # circuitos 100 + 101

    def test_circuito_sin_crosswalk_cae_en_sin_determinar(self, circuito_json_path, crosswalk_path, tmp_path):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        cuadro = _leer_cuadro(salida)
        fila = cuadro.set_index("localidad").loc[SIN_DETERMINAR]
        assert fila["votos"] == 15  # circuito 999

    def test_encabezado_incluye_porcentaje_de_cobertura(self, circuito_json_path, crosswalk_path, tmp_path):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        encabezado = salida.read_text(encoding="utf-8")
        assert "Cobertura votos:" in encabezado

    def test_encabezado_referencia_la_documentacion_del_crosswalk_geolocalizado(
        self, circuito_json_path, crosswalk_path, tmp_path,
    ):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        encabezado = salida.read_text(encoding="utf-8")
        assert "CIRCUITOS_POR_LOCALIDAD.md" in encabezado

    def test_columna_izquierda_refleja_campo_ideologico_1(self, circuito_json_path, crosswalk_path, tmp_path):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        cuadro = _leer_cuadro(salida)
        fila = cuadro.set_index("localidad").loc["BARRIO_A"]
        assert fila["izquierda"] == 20  # PARTIDO B, circuito 100

    def test_columna_blanco_nulo_suma_en_blanco_mas_nulo_separado_de_otros(
        self, circuito_json_path, crosswalk_path, tmp_path,
    ):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        cuadro = _leer_cuadro(salida)
        fila = cuadro.set_index("localidad").loc["BARRIO_A"]
        # circuito 100: EN BLANCO=5, NULO=1; circuito 101: EN BLANCO=2, NULO=0
        assert fila["blanco_nulo"] == 8
        assert fila["otros"] == 0  # IMPUGNADO/RECURRIDO/COMANDO están en cero en la fixture

    def test_no_pierde_votos_de_otros_con_nombres_de_categoria_distintos(self, tmp_path, crosswalk_path):
        """Nombres de categoría no vistos antes no deben perder votos;
        blanco/nulo se separa igual de lo procedimental."""
        contenido = {
            "circuitos": {
                "100": _circuito({}, {"BLANCOS": 3, "NULOS": 2, "IMPUGNADOS": 0, "RECURRIDOS": 0, "COMANDO": 0}),
            },
        }
        path = tmp_path / "2021" / "nacional" / "generales"
        path.mkdir(parents=True)
        (path / "circuito_nacional.json").write_text(json.dumps(contenido), encoding="utf-8")

        salida = generar_cuadro_localidad(tmp_path, tmp_path / "por_localidad", 2021, "nacional", "generales", crosswalk_path)
        cuadro = _leer_cuadro(salida)
        assert cuadro["votos"].sum() == 5
        assert cuadro["blanco_nulo"].sum() == 5
        assert cuadro["otros"].sum() == 0

    def test_columna_ausentismo_es_padron_menos_votos_validos(self, circuito_json_path, crosswalk_path, tmp_path):
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        cuadro = _leer_cuadro(salida)
        fila = cuadro.set_index("localidad").loc["BARRIO_A"]
        # circuito 100: electores=100, votos=60+20+5+1=86 -> ausentismo=14
        # circuito 101: electores=100, votos=30+2=32 -> ausentismo=68
        assert fila["ausentismo"] == 14 + 68

    def test_ausentismo_no_pierde_electores_de_ningun_circuito(self, circuito_json_path, crosswalk_path, tmp_path):
        contenido = json.loads(
            (circuito_json_path / "2023" / "intendente" / "generales" / "circuito_intendente.json").read_text()
        )
        electores_totales = sum(c["electores"] for c in contenido["circuitos"].values())
        salida = generar_cuadro_localidad(
            circuito_json_path, tmp_path / "por_localidad", 2023, "intendente", "generales", crosswalk_path,
        )
        cuadro = _leer_cuadro(salida)
        assert cuadro["ausentismo"].sum() == electores_totales - cuadro["votos"].sum()
