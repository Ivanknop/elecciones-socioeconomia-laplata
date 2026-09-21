"""Tests de `ml_models.construir_elecciones_resumen`. Fixtures chicas en
memoria/`tmp_path`."""
import csv
import json

import pytest

from ml_models.construir_calendario import FilaCalendario
from ml_models.construir_elecciones_resumen import (
    PARTICIPACION_BENCHMARK_NACIONAL_PCT,
    UMBRAL_VIABLE,
    _dispersion_ponderada,
    _escribir_csv,
    _estructura_oferta,
    calcular_cobertura_minima,
    calcular_delta_dispersion,
    calcular_delta_participacion,
    calcular_delta_voto_exit_ausentismo,
    calcular_delta_voto_exit_blanco_nulo,
    calcular_participacion_voto_exit,
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

    def test_oficialismo_ganador_identidad_suma_100(self):
        of, op, otra = _v("OFICIALISMO", 600, 60.0), _v("OPOSICION", 300, 30.0), _v("OTRA", 100, 10.0)
        n, marginal, oposicion, otras = _estructura_oferta([of, op, otra], entrada_oficialismo=of)
        assert n == 3
        assert oposicion == 30.0
        assert otras == 10.0

        of2, op2, c2, d2 = _v("OF", 500, 50.0), _v("OP", 300, 30.0), _v("C", 180, 18.0), _v("marginal", 20, 2.0)
        _, marginal2, oposicion2, otras2 = _estructura_oferta([of2, op2, c2, d2], entrada_oficialismo=of2)
        assert marginal2 + oposicion2 + otras2 + 50.0 == pytest.approx(100.0)

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
        assert fila.dispersion_cobertura_share == 0.0

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
        # cobertura = (900+90)/1000 -- excluye a "chica" (marginal, aunque tenga score)
        assert fila.dispersion_cobertura_share == pytest.approx(99.0)

    def test_dispersion_cobertura_share_100_si_todas_las_viables_tienen_score(self):
        del_anio = [_v("A", 900, 90.0), _v("B", 100, 10.0)]
        vparty = {"A": (1.0, -1.0), "B": (-1.0, 1.0)}
        fila = construir_fila_eleccion(
            nivel="municipal", anio=2023, del_anio=del_anio,
            totales={"blanco": 0, "nulo": 0, "habilitados": 1000},
            vparty=vparty, of=None, fila_of_curada=None, alias_lista=None,
            resultado_disponible=False, ausentismo=None,
        )
        assert fila.dispersion_cobertura_share == pytest.approx(100.0)

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

    def test_votos_nulos_faltante_2025_like_calcula_ausentismo_tratando_nulo_como_cero(self, tmp_path):
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
        assert fila.ausentismo == 1200 - 1000 - 50 - 0
        assert fila.votos_blancos_y_nulos == 50
        assert fila.participacion_pct == pytest.approx((1000 + 50) / 1200 * 100)

    def test_ausentismo_2025_provincial_caso_real(self, tmp_path):
        # Valores reales de data/tfi_data/elecciones.csv (provincial, 2025):
        # habilitados=639839, positivos=393945, blanco=15186, nulo vacío.
        elecciones_dir = tmp_path / "elecciones"
        _escribir_eleccion_tfi(
            elecciones_dir, 2025, "provincial", [("0001", "PARTIDO A", 393945, "", "")],
            blanco=15186, nulo=None, habilitados=639839,
        )
        calendario = [FilaCalendario(anio=2025, nivel="provincial", fecha_eleccion="2025-09-07", tipo_eleccion="legislativa", desdoblada=True, cargos_en_juego="diputados provinciales")]

        filas = construir_elecciones(
            calendario, voto_partido=[_v("PARTIDO A", 393945, 100.0, anio=2025, nivel="provincial")],
            oficialismo_por_nivel={}, oficialismos_curados={},
            data_dir=tmp_path / "distrito", elecciones_dir=elecciones_dir,
        )
        fila = filas[0]
        assert fila.votos_nulos is None
        assert fila.ausentismo == 230708
        assert fila.votos_blancos_y_nulos == 15186
        assert fila.participacion_pct == pytest.approx((393945 + 15186) / 639839 * 100)

    def test_ausentismo_2025_municipal_caso_real(self, tmp_path):
        # Valores reales de data/tfi_data/elecciones.csv (municipal, 2025):
        # habilitados=639839, positivos=395040, blanco=14091, nulo vacío --
        # mismo ausentismo que provincial (230708) por coincidencia real
        # (positivos+blanco da 409131 en los dos niveles, mismo padrón), no
        # asumido: verificado con los valores propios de este nivel.
        elecciones_dir = tmp_path / "elecciones"
        _escribir_eleccion_tfi(
            elecciones_dir, 2025, "municipal", [("0001", "PARTIDO A", 395040, "", "")],
            blanco=14091, nulo=None, habilitados=639839,
        )
        calendario = [FilaCalendario(anio=2025, nivel="municipal", fecha_eleccion="2025-09-07", tipo_eleccion="legislativa", desdoblada=True, cargos_en_juego="concejales")]

        filas = construir_elecciones(
            calendario, voto_partido=[_v("PARTIDO A", 395040, 100.0, anio=2025, nivel="municipal")],
            oficialismo_por_nivel={}, oficialismos_curados={},
            data_dir=tmp_path / "distrito", elecciones_dir=elecciones_dir,
        )
        fila = filas[0]
        assert fila.votos_nulos is None
        assert fila.ausentismo == 230708
        assert fila.votos_blancos_y_nulos == 14091
        assert fila.participacion_pct == pytest.approx((395040 + 14091) / 639839 * 100)

    def test_ausentismo_2001_provincial_control_sin_bug(self, tmp_path):
        # Control de no regresión: nulo presente (no dispara el fallback
        # nulo=None), habilitados=410518, positivos=229230, blancos=28494,
        # nulos=57098, ausentismo=95696 -- valores reales de elecciones.csv.
        elecciones_dir = tmp_path / "elecciones"
        _escribir_eleccion_tfi(
            elecciones_dir, 2001, "provincial", [("0001", "PARTIDO A", 229230, "", "")],
            blanco=28494, nulo=57098, habilitados=410518,
        )
        calendario = [FilaCalendario(anio=2001, nivel="provincial", fecha_eleccion="2001-10-14", tipo_eleccion="legislativa", desdoblada=False, cargos_en_juego="diputados provinciales")]

        filas = construir_elecciones(
            calendario, voto_partido=[_v("PARTIDO A", 229230, 100.0, anio=2001, nivel="provincial")],
            oficialismo_por_nivel={}, oficialismos_curados={},
            data_dir=tmp_path / "distrito", elecciones_dir=elecciones_dir,
        )
        fila = filas[0]
        assert fila.ausentismo == 95696
        assert fila.votos_blancos_y_nulos == 85592
        assert fila.participacion_pct == pytest.approx((229230 + 85592) / 410518 * 100)

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


class TestDeltaDispersionYCoberturaMinima:
    def _fila(self, anio, mu_econ, votos_con_score) -> object:
        """`votos_con_score` (sobre un total de 1000, "A") controla
        `dispersion_cobertura_share` directamente -- el resto ("B") nunca
        tiene score."""
        del_anio = [_v("A", votos_con_score, votos_con_score / 10), _v("B", 1000 - votos_con_score, (1000 - votos_con_score) / 10)]
        vparty = {"A": (mu_econ, 0.0)} if mu_econ is not None else {}
        return construir_fila_eleccion(
            nivel="municipal", anio=anio, del_anio=del_anio,
            totales={"blanco": 0, "nulo": 0, "habilitados": 1000},
            vparty=vparty, of=None, fila_of_curada=None, alias_lista=None,
            resultado_disponible=False, ausentismo=None,
        )

    def test_delta_dispersion_resta_mu_del_eje_pedido(self):
        elecciones = {(2019, "municipal"): self._fila(2019, 1.0, 900), (2021, "municipal"): self._fila(2021, 3.0, 900)}
        delta = calcular_delta_dispersion(elecciones, "municipal", 2021, 2019, "economico")
        assert delta == pytest.approx(2.0)

    def test_delta_dispersion_none_si_falta_una_punta_mu_o_sigma2(self):
        elecciones = {(2021, "municipal"): self._fila(2021, 3.0, 900)}
        assert calcular_delta_dispersion(elecciones, "municipal", 2021, 2019, "economico") is None

        elecciones_dos_partidos = {(2021, "municipal"): self._fila_dos_partidos(2021, 2.0, -2.0)}
        assert (
            calcular_delta_dispersion(elecciones_dos_partidos, "municipal", 2021, 2019, "economico", estadistico="sigma2")
            is None
        )

    def test_delta_dispersion_none_si_mu_falta_en_una_punta(self):
        elecciones = {(2019, "municipal"): self._fila(2019, None, 0), (2021, "municipal"): self._fila(2021, 3.0, 900)}
        assert calcular_delta_dispersion(elecciones, "municipal", 2021, 2019, "economico") is None

    def test_cobertura_minima_toma_el_menor_de_las_dos_puntas(self):
        elecciones = {(2019, "municipal"): self._fila(2019, 1.0, 400), (2021, "municipal"): self._fila(2021, 3.0, 900)}
        assert calcular_cobertura_minima(elecciones, "municipal", 2021, 2019) == pytest.approx(40.0)

    def test_cobertura_minima_none_si_falta_una_punta(self):
        elecciones = {(2021, "municipal"): self._fila(2021, 3.0, 900)}
        assert calcular_cobertura_minima(elecciones, "municipal", 2021, 2019) is None

    def _fila_dos_partidos(self, anio, score_a, score_b) -> object:
        """Dos fuerzas viables de igual peso con scores `score_a`/`score_b`
        -- sigma2 = ((score_a - score_b) / 2) ** 2, controlable a diferencia
        de `_fila` (un solo partido con score, sigma2 siempre 0)."""
        del_anio = [_v("A", 500, 50.0), _v("B", 500, 50.0)]
        vparty = {"A": (score_a, 0.0), "B": (score_b, 0.0)}
        return construir_fila_eleccion(
            nivel="municipal", anio=anio, del_anio=del_anio,
            totales={"blanco": 0, "nulo": 0, "habilitados": 1000},
            vparty=vparty, of=None, fila_of_curada=None, alias_lista=None,
            resultado_disponible=False, ausentismo=None,
        )

    def test_delta_dispersion_resta_sigma2_del_eje_pedido(self):
        elecciones = {
            (2019, "municipal"): self._fila_dos_partidos(2019, 1.0, -1.0),  # sigma2 = 1.0
            (2021, "municipal"): self._fila_dos_partidos(2021, 2.0, -2.0),  # sigma2 = 4.0
        }
        delta = calcular_delta_dispersion(elecciones, "municipal", 2021, 2019, "economico", estadistico="sigma2")
        assert delta == pytest.approx(3.0)


def _fila_participacion(anio, nivel, habilitados, positivos, blanco, nulo, ausentismo) -> object:
    del_anio = [_v("A", positivos, 100.0, anio=anio, nivel=nivel)]
    return construir_fila_eleccion(
        nivel=nivel, anio=anio, del_anio=del_anio,
        totales={"blanco": blanco, "nulo": nulo, "habilitados": habilitados},
        vparty={}, of=None, fila_of_curada=None, alias_lista=None,
        resultado_disponible=False, ausentismo=ausentismo,
    )


class TestCalcularParticipacionVotoExit:
    def test_calcula_las_cuatro_magnitudes_con_participacion_no_relevante(self):
        # habilitados=1000, positivos=700, blanco=50, nulo=30, ausentismo=220
        # (suma 1000) -- participacion_pct = (700+80)/1000*100 = 78.0 < 79.0
        elecciones = {(2023, "municipal"): _fila_participacion(2023, "municipal", 1000, 700, 50, 30, 220)}
        resultado = calcular_participacion_voto_exit(elecciones, "municipal", 2023)
        assert resultado.participacion_pct == pytest.approx(78.0)
        assert resultado.voto_exit_blanco_nulo_pct == pytest.approx(8.0)
        assert resultado.voto_exit_ausentismo_pct == pytest.approx(22.0)
        assert resultado.voto_exit_total_pct == pytest.approx(30.0)
        assert resultado.participacion_relevante is False

    def test_participacion_relevante_true_por_encima_del_benchmark(self):
        # participacion_pct = (800+15)/1000*100 = 81.5 > 79.0
        elecciones = {(2023, "municipal"): _fila_participacion(2023, "municipal", 1000, 800, 10, 5, 185)}
        resultado = calcular_participacion_voto_exit(elecciones, "municipal", 2023)
        assert resultado.participacion_pct == pytest.approx(81.5)
        assert resultado.participacion_relevante is True
        assert PARTICIPACION_BENCHMARK_NACIONAL_PCT == 79.0

    def test_none_si_no_hay_fila_para_ese_anio_nivel(self):
        assert calcular_participacion_voto_exit({}, "municipal", 2023) is None

    def test_ausentismo_faltante_deja_solo_esas_dos_metricas_en_none(self):
        # mismo caso 2025 real: ausentismo falta pero habilitados/blanco/nulo
        # sí están -- participacion_pct/voto_exit_blanco_nulo_pct/
        # participacion_relevante quedan calculables igual, no todo-o-nada.
        elecciones = {(2025, "provincial"): _fila_participacion(2025, "provincial", 1000, 700, 80, None, None)}
        resultado = calcular_participacion_voto_exit(elecciones, "provincial", 2025)
        assert resultado.participacion_pct == pytest.approx(78.0)
        assert resultado.voto_exit_blanco_nulo_pct == pytest.approx(8.0)
        assert resultado.participacion_relevante is False
        assert resultado.voto_exit_ausentismo_pct is None
        assert resultado.voto_exit_total_pct is None

    def test_caso_real_2025_provincial_ausentismo_ya_no_es_none(self):
        # Con la corrección a D17 aplicada, ausentismo=230708 ya está
        # presente en la fila -- no depende de un fallback en el panel.
        elecciones = {
            (2025, "provincial"): _fila_participacion(2025, "provincial", 639839, 393945, 15186, None, 230708)
        }
        resultado = calcular_participacion_voto_exit(elecciones, "provincial", 2025)
        assert resultado.voto_exit_ausentismo_pct == pytest.approx(230708 / 639839 * 100)
        assert resultado.voto_exit_total_pct is not None


class TestDeltaParticipacionYVotoExit:
    def test_deltas_participacion_ausentismo_blanco_nulo_restan_t_menos_t_menos_1(self):
        elecciones = {
            # 2019: participacion 78.0, ausentismo 22.0, blanco_nulo 8.0
            (2019, "municipal"): _fila_participacion(2019, "municipal", 1000, 700, 50, 30, 220),
            # 2021: participacion 81.5, ausentismo 18.5, blanco_nulo 1.5
            (2021, "municipal"): _fila_participacion(2021, "municipal", 1000, 800, 10, 5, 185),
        }
        assert calcular_delta_participacion(elecciones, "municipal", 2021, 2019) == pytest.approx(3.5)
        assert calcular_delta_voto_exit_ausentismo(elecciones, "municipal", 2021, 2019) == pytest.approx(-3.5)
        assert calcular_delta_voto_exit_blanco_nulo(elecciones, "municipal", 2021, 2019) == pytest.approx(-6.5)

    def test_deltas_none_si_falta_una_punta(self):
        elecciones = {(2021, "municipal"): _fila_participacion(2021, "municipal", 1000, 800, 10, 5, 185)}
        assert calcular_delta_participacion(elecciones, "municipal", 2021, 2019) is None
        assert calcular_delta_voto_exit_ausentismo(elecciones, "municipal", 2021, 2019) is None
        assert calcular_delta_voto_exit_blanco_nulo(elecciones, "municipal", 2021, 2019) is None

    def test_delta_voto_exit_ausentismo_none_si_ausentismo_falta_en_una_punta(self):
        elecciones = {
            (2019, "municipal"): _fila_participacion(2019, "municipal", 1000, 700, 80, None, None),
            (2021, "municipal"): _fila_participacion(2021, "municipal", 1000, 800, 10, 5, 185),
        }
        assert calcular_delta_voto_exit_ausentismo(elecciones, "municipal", 2021, 2019) is None
