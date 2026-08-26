"""Fixtures con JSON crudo representativo de la API, recortado del real
para que los tests sean legibles; incluye los mismos campos "extra" que
el modelo no mapea, para probar `extra` sin inventar un caso irreal."""
import pytest


@pytest.fixture
def raw_lista():
    return {"nombre": "LISTA 3 - UNIDAD", "votos": 1234, "numero": "3"}


@pytest.fixture
def raw_valor_agrupacion():
    return {
        "idAgrupacion": "0131",
        "nombreAgrupacion": "Alianza Frente para la Victoria                                   ",
        "votos": 160079,
        "votosPorcentaje": 45.44,
        "idAgrupacionTelegrama": "",
        "urlLogo": "",
    }


@pytest.fixture
def raw_estado_recuento():
    return {
        "mesasEsperadas": 0,
        "mesasTotalizadas": 1429,
        "mesasTotalizadasPorcentaje": 0,
        "cantidadElectores": 493225,
        "cantidadVotantes": 384273,
        "participacionPorcentaje": 77.91,
    }


@pytest.fixture
def raw_valores_otros():
    return {
        "votosNulos": 2941,
        "votosNulosPorcentaje": 0.77,
        "votosEnBlanco": 28864,
        "votosEnBlancoPorcentaje": 7.51,
        "votosRecurridosComandoImpugnados": 184,
        "votosRecurridosComandoImpugnadosPorcentaje": 0.05,
    }


@pytest.fixture
def raw_resultado_electoral(raw_estado_recuento, raw_valores_otros):
    return {
        "fechaTotalizacion": "2026-07-26T15:28:11.171Z",
        "estadoRecuento": raw_estado_recuento,
        "valoresTotalizadosPositivos": [
            {
                "idAgrupacion": "0131",
                "nombreAgrupacion": "Alianza Frente para la Victoria                    ",
                "votos": 160079,
                "votosPorcentaje": 45.44,
                "idAgrupacionTelegrama": "",
                "urlLogo": "",
            },
            {
                "idAgrupacion": "0047",
                "nombreAgrupacion": "Coalición Cívica ARI                               ",
                "votos": 13177,
                "votosPorcentaje": 3.74,
                "idAgrupacionTelegrama": "",
                "urlLogo": "",
            },
        ],
        "valoresTotalizadosOtros": raw_valores_otros,
    }
