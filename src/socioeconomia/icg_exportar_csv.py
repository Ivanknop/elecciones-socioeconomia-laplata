"""Escribe los 7 CSV livianos del pipeline ICG a `data/socioeconomia/`:
headline + seis cortes demográficos. Detalle en `data/socioeconomia/ICG.md`.

Uso:
    PYTHONPATH=src python -m socioeconomia.icg_exportar_csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

from constantes import ICG_HEADLINE_PATH, ICG_RAW_PATH
from socioeconomia.icg_cargar import CIUDAD_LA_PLATA, cargar_microdatos
from socioeconomia.icg_construir_series import construir_serie_headline, construir_series_demograficas

CORTES = ("sexo", "edad", "edu")


def _ruta_corte(directorio: Path, grano: str, resolucion: str, corte: str) -> Path:
    return directorio / f"icg_{grano}_{resolucion}_por_{corte}_2011_presente.csv"


def exportar_todo(
    raw_path: Path | str = ICG_RAW_PATH,
    salida_headline: Path | str = ICG_HEADLINE_PATH,
) -> list[Path]:
    df = cargar_microdatos(raw_path)
    directorio = Path(salida_headline).parent
    directorio.mkdir(parents=True, exist_ok=True)

    destinos = []

    destino_headline = Path(salida_headline)
    construir_serie_headline(df).to_csv(destino_headline, index=False)
    destinos.append(destino_headline)

    df_pais = df
    df_la_plata = df[df["Ciudad"] == CIUDAD_LA_PLATA]

    for corte in CORTES:
        destino = _ruta_corte(directorio, "pais", "mensual", corte)
        construir_series_demograficas(df_pais, corte=corte, resolucion="mensual").to_csv(destino, index=False)
        destinos.append(destino)

        destino = _ruta_corte(directorio, "la_plata", "anual", corte)
        construir_series_demograficas(df_la_plata, corte=corte, resolucion="anual").to_csv(destino, index=False)
        destinos.append(destino)

    return destinos


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-path", default=ICG_RAW_PATH)
    parser.add_argument("--salida-headline", default=ICG_HEADLINE_PATH)
    args = parser.parse_args()

    for destino in exportar_todo(args.raw_path, args.salida_headline):
        print(f"{destino} generado")


if __name__ == "__main__":
    main()
