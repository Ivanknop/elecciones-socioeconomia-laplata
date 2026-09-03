#!/usr/bin/env python3
"""
Descarga V-Party (V-Dem Institute), filtra Argentina 2001-2019 y arma
`v_party_argentina_2001_2019.csv`/`_espaniol.csv`. Procedencia y semántica
completas en `data/agrupaciones/v-party/README.md`.

Uso:
  PYTHONPATH=src python -m analisis.generar_v_party_argentina [--forzar-descarga]
"""

import argparse
from pathlib import Path

import pandas as pd
import requests

URL_VPARTY = "https://raw.githubusercontent.com/vdeminstitute/vdemdata/master/data/vparty.RData"
CACHE_RDATA = Path("data/agrupaciones/v-party/cache/vparty.RData")
SALIDA_EN = Path("data/agrupaciones/v-party/v_party_argentina_2001_2019.csv")
SALIDA_ES = Path("data/agrupaciones/v-party/v_party_argentina_2001_2019_espaniol.csv")

ANIO_MIN, ANIO_MAX = 2001, 2019

# Identificación + posicionamiento (V-Dem), mismo set/orden que traía el
# CSV previo 2011-2019 -- ver README de la carpeta para el detalle de cada
# variable.
COLUMNAS = [
    "v2paenname", "v2paorname", "v2pashname", "year", "historical_date", "v2pavote",
    "v2pariglef", "v2pariglef_codelow", "v2pariglef_codehigh",
    "v2pariglef_osp", "v2pariglef_osp_codelow", "v2pariglef_osp_codehigh",
    "v2pawelf", "v2pawelf_codelow", "v2pawelf_codehigh",
    "v2pawelf_osp", "v2pawelf_osp_codelow", "v2pawelf_osp_codehigh",
    "v2pawomlab", "v2pawomlab_codelow", "v2pawomlab_codehigh",
    "v2pawomlab_osp", "v2pawomlab_osp_codelow", "v2pawomlab_osp_codehigh",
    "v2palgbt", "v2palgbt_codelow", "v2palgbt_codehigh",
    "v2palgbt_osp", "v2palgbt_osp_codelow", "v2palgbt_osp_codehigh",
    "v2paimmig", "v2paimmig_codelow", "v2paimmig_codehigh",
    "v2paimmig_osp", "v2paimmig_osp_codelow", "v2paimmig_osp_codehigh",
    "v2parelig", "v2parelig_codelow", "v2parelig_codehigh",
    "v2parelig_osp", "v2parelig_osp_codelow", "v2parelig_osp_codehigh",
    "v2paanteli", "v2paanteli_codelow", "v2paanteli_codehigh",
    "v2paanteli_osp", "v2paanteli_osp_codelow", "v2paanteli_osp_codehigh",
    "v2papeople", "v2papeople_codelow", "v2papeople_codehigh",
    "v2papeople_osp", "v2papeople_osp_codelow", "v2papeople_osp_codehigh",
    "v2paclient", "v2paclient_codelow", "v2paclient_codehigh",
    "v2paclient_osp", "v2paclient_osp_codelow", "v2paclient_osp_codehigh",
    "v2xpa_popul", "v2xpa_popul_codelow", "v2xpa_popul_codehigh",
]

# Traducción de v2paenname (nombre del partido en inglés, tal como lo
# codifica V-Party) al español -- join estricto, ver `traducir()`. Incluye
# los 18 partidos ya traducidos en el archivo 2011-2019 más los 5 nuevos
# que sólo aparecen en las olas 2001-2009.
TRADUCCIONES = {
    "1País": "1País",
    "Aliance for Work, Justice, and Education": "Alianza para el Trabajo, la Justicia y la Educación",
    "Citizen's Unity": "Unidad Ciudadana",
    "Civic Coalition ARI": "Coalición Cívica ARI",
    "Concertation Party": "Partido de la Concertación",
    "Federal Consensus": "Consenso Federal",
    "Federal Peronism / Dissident Peronism": "Peronismo Federal / Peronismo Disidente",
    "Frente Justicialista-Justicialist [Peronist] Party": "Frente Justicialista - Partido Justicialista (Peronista)",
    "Front for Victory": "Frente para la Victoria",
    "Front for a Country in Solidarity": "Frente País Solidario",
    "Generation for a National Encounter": "Generación para un Encuentro Nacional",
    "Justicialist [Peronist] Party": "Partido Justicialista (Peronista)",
    "Let's change": "Cambiemos",
    "Let’s change": "Cambiemos",
    "Popular Union": "Unión Popular",
    "Progressive, Civic and Social Front": "Frente Progresista, Cívico y Social",
    "Radical Civic Union": "Unión Cívica Radical",
    "Renewal Front": "Frente Renovador",
    "Republican Proposal": "Propuesta Republicana",
    "Socialist Party": "Partido Socialista",
    "Support for an Egalitarian Republic": "Afirmación para una República Igualitaria",
    "alliance: Frente Amplio Progresista": "alianza: Frente Amplio Progresista",
    "alliance: Frente de Todos": "alianza: Frente de Todos",
    "alliance: United for a New Alternative": "alianza: Unidos por una Nueva Alternativa",
}


def descargar_rdata(cache_path: Path = CACHE_RDATA, url: str = URL_VPARTY, forzar: bool = False) -> Path:
    if cache_path.exists() and not forzar:
        return cache_path
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    respuesta = requests.get(url, timeout=60)
    respuesta.raise_for_status()
    cache_path.write_bytes(respuesta.content)
    return cache_path


def _filtrar_argentina(df: pd.DataFrame, anio_min: int = ANIO_MIN, anio_max: int = ANIO_MAX) -> pd.DataFrame:
    filtro = (df["country_name"] == "Argentina") & (df["year"] >= anio_min) & (df["year"] <= anio_max)
    return df.loc[filtro, COLUMNAS].sort_values(["year", "v2paenname"]).reset_index(drop=True)


def cargar_argentina(rdata_path: Path, anio_min: int = ANIO_MIN, anio_max: int = ANIO_MAX) -> pd.DataFrame:
    import pyreadr

    tablas = pyreadr.read_r(str(rdata_path))
    return _filtrar_argentina(tablas["vparty"], anio_min, anio_max)


def traducir(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega `v2paenname_espaniol`; falla si algún partido no está en
    `TRADUCCIONES` (mismo criterio de join estricto que `campo_ideologico`)."""
    faltantes = sorted(set(df["v2paenname"]) - set(TRADUCCIONES))
    if faltantes:
        raise KeyError(f"Sin traducción en TRADUCCIONES para: {faltantes}")
    salida = df.copy()
    salida.insert(1, "v2paenname_espaniol", salida["v2paenname"].map(TRADUCCIONES))
    return salida


def escribir(df_en: pd.DataFrame, df_es: pd.DataFrame, salida_en: Path = SALIDA_EN, salida_es: Path = SALIDA_ES) -> None:
    df_en.to_csv(salida_en, index=False)
    df_es.to_csv(salida_es, index=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anio-min", type=int, default=ANIO_MIN)
    ap.add_argument("--anio-max", type=int, default=ANIO_MAX)
    ap.add_argument("--forzar-descarga", action="store_true")
    args = ap.parse_args()

    rdata_path = descargar_rdata(forzar=args.forzar_descarga)
    df_en = cargar_argentina(rdata_path, args.anio_min, args.anio_max)
    df_es = traducir(df_en)
    escribir(df_en, df_es)

    print(f"OK: {len(df_en)} filas partido-elección {args.anio_min}-{args.anio_max} -> {SALIDA_ES}")


if __name__ == "__main__":
    main()
