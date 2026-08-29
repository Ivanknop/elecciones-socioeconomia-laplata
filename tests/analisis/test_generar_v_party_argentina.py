"""Tests de `generar_v_party_argentina.py`: filtrado por país/año y
traducción -- lógica pura, sin red ni pyreadr. Descarga/main sin test,
ver CLAUDE.md."""
import pandas as pd
import pytest

from analisis.generar_v_party_argentina import COLUMNAS, TRADUCCIONES, _filtrar_argentina, traducir


def _df_crudo():
    filas = [
        {"country_name": "Argentina", "v2paenname": "Radical Civic Union", "year": 2001.0},
        {"country_name": "Argentina", "v2paenname": "Front for Victory", "year": 2011.0},
        {"country_name": "Argentina", "v2paenname": "Radical Civic Union", "year": 2023.0},
        {"country_name": "Brazil", "v2paenname": "PT", "year": 2011.0},
    ]
    df = pd.DataFrame(filas)
    for col in COLUMNAS:
        if col not in df.columns:
            df[col] = None
    return df


def test_filtrar_argentina_excluye_otros_paises():
    filtrado = _filtrar_argentina(_df_crudo(), anio_min=2001, anio_max=2019)
    assert set(filtrado["v2paenname"]) == {"Radical Civic Union", "Front for Victory"}


def test_filtrar_argentina_respeta_rango_de_anios():
    filtrado = _filtrar_argentina(_df_crudo(), anio_min=2001, anio_max=2019)
    assert set(filtrado["year"]) == {2001.0, 2011.0}


def test_filtrar_argentina_columnas_y_orden():
    filtrado = _filtrar_argentina(_df_crudo(), anio_min=2001, anio_max=2019)
    assert list(filtrado.columns) == COLUMNAS
    assert list(filtrado["year"]) == [2001.0, 2011.0]


def test_traducir_agrega_columna_espaniol_en_segunda_posicion():
    df = pd.DataFrame({"v2paenname": ["Front for Victory", "Radical Civic Union"], "otro": [1, 2]})
    traducido = traducir(df)
    assert list(traducido.columns)[:2] == ["v2paenname", "v2paenname_espaniol"]
    assert list(traducido["v2paenname_espaniol"]) == ["Frente para la Victoria", "Unión Cívica Radical"]


def test_traducir_falla_ante_partido_sin_traduccion():
    df = pd.DataFrame({"v2paenname": ["Partido Inventado"]})
    with pytest.raises(KeyError):
        traducir(df)


def test_traducciones_no_tienen_valores_vacios():
    assert all(v.strip() for v in TRADUCCIONES.values())
