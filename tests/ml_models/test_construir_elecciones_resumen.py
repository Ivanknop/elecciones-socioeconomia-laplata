"""Tests de `ml_models.construir_elecciones_resumen`. Fixtures chicas en
memoria/`tmp_path`, nunca datos reales de `data/` (mismo patrón que
`tests/ml_models/test_resultado_distrito.py`)."""
import csv
import json

import pytest

from ml_models.construir_calendario import FilaCalendario
from ml_models.construir_elecciones_resumen import (
    UMBRAL_VIABLE,
    _dispersion_ponderada,
    _escribir_csv,
    _estructura_oferta,
    cargar_elecciones,
    construir_elecciones,
    construir_fila_eleccion,
)
from ml_models.construir_resultado_distrito import FilaVotoPartido


def _v(agrupacion: str, votos: int, share: float, anio=2023, nivel="municipal", id_agrupacion="0001") -> FilaVotoPartido:
    return FilaVotoPartido(anio=anio, nivel=nivel, id_agrupacion=id_agrupacion, agrupacion=agrupacion, votos=votos, share=share)


class TestEstructuraOferta:
    def test_umbral_exacto_1_5_cuenta_como_viable(self):
        a, b, c = _v("A", 850, 85.0), _v("B", 135, 13.5), _v("C", 15, UMBRAL_VIABLE)
        n, marginal, oposicion, otras = _estructura_oferta([a, b, c], entrada_oficialismo=a)
        assert n == 3
        assert marginal == 0
        assert oposicion == 13.5
        assert otras == pytest.approx(1.5)

    def test_debajo_del_umbral_cae_en_marginal(self):
        a, b, c = _v("A", 850, 85.0), _v("B", 135, 13.5), _v("C", 14, 1.4)
        n, marginal, oposicion, otras = _estructura_oferta([a, b, c], entrada_oficialismo=a)
        assert n == 2
        assert marginal == pytest.approx(1.4)
        assert oposicion == 13.5
        assert otras == 0

    def test_oficialismo_tambien_ganador(self):
        of, op, otra = _v("OFICIALISMO", 600, 60.0), _v("OPOSICION", 300, 30.0), _v("OTRA", 100, 10.0)
        n, marginal, oposicion, otras = _estructura_oferta([of, op, otra], entrada_oficialismo=of)
        assert n == 3
        assert oposicion == 30.0
        assert otras == 10.0

    def test_oficialismo_no_viable_no_se_excluye_de_marginal_ni_se_cuenta_viable(self):
        of = _v("OFICIALISMO", 10, 1.0)
        op = _v("OPOSICION", 600, 60.0)
        otra = _v("OTRA", 390, 39.0)
        n, marginal, oposicion, otras = _estructura_oferta([of, op, otra], entrada_oficialismo=of)
        assert n == 2  # solo OPOSICION y OTRA -- el oficialismo (1%) no es viable
        assert marginal == pytest.approx(1.0)
        assert oposicion == 60.0
        assert otras == 39.0
        # identidad D17: al no ser viable el oficialismo, su share ya está
        # adentro de `marginal` -- no se vuelve a sumar aparte.
        assert marginal + oposicion + otras == pytest.approx(100.0)

    def test_identidad_con_oficialismo_viable_suma_100(self):
        of, op, c, d = _v("OF", 500, 50.0), _v("OP", 300, 30.0), _v("C", 180, 18.0), _v("marginal", 20, 2.0)
        n, marginal, oposicion, otras = _estructura_oferta([of, op, c, d], entrada_oficialismo=of)
        assert marginal + oposicion + otras + 50.0 == pytest.approx(100.0)

    def test_una_sola_fuerza_viable_sin_oposicion(self):
        of = _v("OF", 990, 99.0)
        marginal_fuerza = _v("chica", 10, 1.0)
        n, marginal, oposicion, otras = _estructura_oferta([of, marginal_fuerza], entrada_oficialismo=of)
        assert n == 1
        assert oposicion is None
        assert otras == 0


class TestDispersionPonderada:
    def test_una_sola_fuerza_sigma2_cero(self):
        mu, sigma2 = _dispersion_ponderada([(100, 2.0)])
        assert mu == 2.0
        assert sigma2 == 0.0

    def test_pondera_por_peso(self):
        mu, _ = _dispersion_ponderada([(90, 1.0), (10, -1.0)])
        assert mu == pytest.approx(0.8)


class TestConstruirFilaEleccion:
    def test_sin_ninguna_fuerza_con_score_dispersion_queda_vacia(self):
        del_anio = [_v("A", 900, 90.0), _v("B", 100, 10.0)]
        fila = construir_fila_eleccion(
            nivel="municipal", anio=2023, del_anio=del_anio,
            totales={"blanco": 10, "nulo": 5, "habilitados": 1200},
            vparty={}, of=None, fila_of_curada=None, alias_lista=None,
            resultado_disponible=False, ausentismo=None,
        )
        assert fila.dispersion_economico_mu is None
        assert fila.dispersion_progresismo_sigma2 is None

    def test_dispersion_solo_sobre_fuerzas_viables(self):
        # "chica" tiene score pero es marginal (1%) -- no debe entrar en mu/sigma2
        del_anio = [_v("A", 900, 90.0), _v("B", 90, 9.0), _v("chica", 10, 1.0)]
        vparty = {"A": (2.0, -1.0), "B": (-2.0, 1.0), "CHICA": (100.0, 100.0)}
        fila = construir_fila_eleccion(
            nivel="municipal", anio=2023, del_anio=del_anio,
            totales={"blanco": 0, "nulo": 0, "habilitados": 1000},
            vparty=vparty, of=None, fila_of_curada=None, alias_lista=None,
            resultado_disponible=False, ausentismo=None,
        )
        assert fila.dispersion_economico_mu is not None
        assert fila.dispersion_economico_mu < 100  # no arrastrada por "chica"

    def test_votos_nulos_faltante_no_calcula_ausentismo(self):
        del_anio = [_v("A", 900, 90.0), _v("B", 100, 10.0)]
        fila = construir_fila_eleccion(
            nivel="provincial", anio=2025, del_anio=del_anio,
            totales={"blanco": 10, "habilitados": 1200},  # sin "nulo"
            vparty={}, of=None, fila_of_curada=None, alias_lista=None,
            resultado_disponible=False, ausentismo=None,
        )
        assert fila.votos_nulos is None
        assert fila.ausentismo is None


def _escribir_eleccion_tfi(elecciones_dir, anio, nivel, filas_partido, blanco, nulo, habilitados):
    elecciones_dir.mkdir(parents=True, exist_ok=True)
    with (elecciones_dir / f"{anio}_{nivel}.csv").open("w", encoding="utf-8", newline="") as f:
        f.write(f"# Total de votos, elección general -- La Plata, {nivel} {anio}\n")
        writer = csv.writer(f)
        writer.writerow(["id_agrupacion", "agrupacion", "votos", "votos_porcentaje", "campo_ideologico", "filiacion_politica", "vparty_economico", "vparty_progresismo", "vparty_populismo"])
        for id_agr, nombre, votos, econ, prog in filas_partido:
            extra = ["", "", econ, prog, ""] if econ != "" else ["", "", "", "", ""]
            writer.writerow([id_agr, nombre, votos, "", *extra])
        writer.writerow(["BLANCO", "BLANCO", blanco, "", "", "", "", "", ""])
        if nulo is not None:
            writer.writerow(["NULO", "NULO", nulo, "", "", "", "", "", ""])
        writer.writerow(["VOTANTES_HABILITADOS", "VOTANTES_HABILITADOS", habilitados, "", "", "", "", "", ""])


class TestConstruirEleccionesIntegracion:
    def test_sin_circuito_json_usa_fallback_y_resta_ausentismo(self, tmp_path):
        elecciones_dir = tmp_path / "elecciones"
        _escribir_eleccion_tfi(
            elecciones_dir, 2023, "municipal",
            [("0001", "PARTIDO A", 900, "1.0", "-1.0"), ("0002", "PARTIDO B", 100, "-1.0", "1.0")],
            blanco=50, nulo=30, habilitados=1200,
        )
        calendario = [FilaCalendario(anio=2023, nivel="municipal", fecha_eleccion="2023-10-22", tipo_eleccion="legislativa", desdoblada=False, cargos_en_juego="concejales")]

        filas = construir_elecciones(
            calendario, voto_partido=[
                _v("PARTIDO A", 900, 90.0, anio=2023), _v("PARTIDO B", 100, 10.0, anio=2023),
            ],
            oficialismo_por_nivel={}, oficialismos_curados={},
            data_dir=tmp_path / "distrito", elecciones_dir=elecciones_dir,
        )
        assert len(filas) == 1
        fila = filas[0]
        assert fila.resultado_disponible is False
        assert fila.votos_nulos == 30
        assert fila.ausentismo == 1200 - 1000 - 50 - 30

    def test_votos_nulos_faltante_2025_like_no_calcula_ausentismo(self, tmp_path):
        elecciones_dir = tmp_path / "elecciones"
        _escribir_eleccion_tfi(
            elecciones_dir, 2025, "provincial",
            [("0001", "PARTIDO A", 900, "", ""), ("0002", "PARTIDO B", 100, "", "")],
            blanco=50, nulo=None, habilitados=1200,
        )
        calendario = [FilaCalendario(anio=2025, nivel="provincial", fecha_eleccion="2025-09-07", tipo_eleccion="legislativa", desdoblada=True, cargos_en_juego="diputados provinciales")]

        filas = construir_elecciones(
            calendario, voto_partido=[_v("PARTIDO A", 900, 90.0, anio=2025, nivel="provincial"), _v("PARTIDO B", 100, 10.0, anio=2025, nivel="provincial")],
            oficialismo_por_nivel={}, oficialismos_curados={},
            data_dir=tmp_path / "distrito", elecciones_dir=elecciones_dir,
        )
        fila = filas[0]
        assert fila.votos_nulos is None
        assert fila.ausentismo is None

    def test_calendario_sin_nacional_pre_2011_no_genera_esas_filas(self, tmp_path):
        # Mismo criterio que calendario_electoral.csv real: si nacional no
        # está en el calendario para un año, `construir_elecciones` no
        # fabrica una fila para ese (año, nivel).
        elecciones_dir = tmp_path / "elecciones"
        _escribir_eleccion_tfi(elecciones_dir, 2013, "nacional", [("0001", "A", 100, "", "")], blanco=1, nulo=1, habilitados=200)
        calendario = [FilaCalendario(anio=2013, nivel="nacional", fecha_eleccion="2013-10-27", tipo_eleccion="legislativa", desdoblada=False, cargos_en_juego="diputados nacionales")]
        filas = construir_elecciones(
            calendario, voto_partido=[_v("A", 100, 100.0, anio=2013, nivel="nacional")],
            oficialismo_por_nivel={}, oficialismos_curados={},
            data_dir=tmp_path / "distrito", elecciones_dir=elecciones_dir,
        )
        assert {(f.anio, f.nivel) for f in filas} == {(2013, "nacional")}

    def test_con_circuito_json_usa_formula_oficial_de_ausentismo(self, tmp_path):
        data_dir = tmp_path / "distrito"
        path = data_dir / "2023" / "municipal" / "generales"
        path.mkdir(parents=True)
        circuitos = {
            "1": {
                "electores": 1000,
                "positivos": {"0001": {"nombre": "PARTIDO A", "votos": 900}, "0002": {"nombre": "PARTIDO B", "votos": 50}},
                "otros": {"EN BLANCO": 20, "NULO": 10, "RECURRIDO": 5},
            }
        }
        (path / "circuito_municipal.json").write_text(json.dumps({"anio": 2023, "nivel": "municipal", "circuitos": circuitos}), encoding="utf-8")

        elecciones_dir = tmp_path / "elecciones"
        _escribir_eleccion_tfi(elecciones_dir, 2023, "municipal", [("0001", "PARTIDO A", 900, "", ""), ("0002", "PARTIDO B", 50, "", "")], blanco=20, nulo=10, habilitados=1000)
        calendario = [FilaCalendario(anio=2023, nivel="municipal", fecha_eleccion="2023-10-22", tipo_eleccion="legislativa", desdoblada=False, cargos_en_juego="concejales")]

        filas = construir_elecciones(
            calendario, voto_partido=[_v("PARTIDO A", 900, 94.7, anio=2023), _v("PARTIDO B", 50, 5.3, anio=2023)],
            oficialismo_por_nivel={}, oficialismos_curados={}, data_dir=data_dir, elecciones_dir=elecciones_dir,
        )
        fila = filas[0]
        assert fila.resultado_disponible is True
        # electores - positivos - otros_total = 1000 - 950 - 35 = 15
        # (RECURRIDO cuenta en otros_total pero no en votos_nulos: la
        # fórmula oficial lo trata como votante, no como ausente ni nulo)
        assert fila.ausentismo == 15


def test_cargar_elecciones_round_trip(tmp_path):
    del_anio = [_v("A", 900, 90.0), _v("B", 100, 10.0)]
    fila = construir_fila_eleccion(
        nivel="municipal", anio=2023, del_anio=del_anio,
        totales={"blanco": 10, "nulo": 5, "habilitados": 1200},
        vparty={"A": (1.0, -1.0)}, of={"agrupacion_oficialismo": "A"}, fila_of_curada=None, alias_lista=None,
        resultado_disponible=True, ausentismo=185,
    )
    destino = tmp_path / "elecciones.csv"
    _escribir_csv(destino, [fila])
    cargadas = cargar_elecciones(destino)
    assert cargadas[(2023, "municipal")] == fila
