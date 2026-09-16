"""Escribe los 7 CSV livianos del pipeline ICG a `data/socioeconomia/icg/`:
headline + seis cortes demográficos. `icg_pais`/`_pais_*` arrancan en 2001,
`icg_la_plata`/`_la_plata_*` en 2008 (piso real, ver ANIO_DESDE_* más abajo
y "Piso real" en `data/socioeconomia/ICG.md`) -- el headline mezcla ambos
pisos en el mismo archivo, con `icg_la_plata`/`n_la_plata` vacíos antes de
2008. Detalle en `data/socioeconomia/ICG.md`.

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

# "país" arranca en 2001 (piso real del `.dta`); "La Plata" en 2008, cuando
# la ciudad entra al panel UTDT -- no es el mismo piso para las dos series,
# ver "Piso real" en data/socioeconomia/ICG.md.
ANIO_DESDE_PAIS = 2001
ANIO_DESDE_LA_PLATA = 2008

_PERIODO_POR_GRANO = {"pais": "2001_presente", "la_plata": "2008_presente"}


def _ruta_corte(directorio: Path, grano: str, resolucion: str, corte: str) -> Path:
    return directorio / f"icg_{grano}_{resolucion}_por_{corte}_{_PERIODO_POR_GRANO[grano]}.csv"


def exportar_todo(
    raw_path: Path | str = ICG_RAW_PATH,
    salida_headline: Path | str = ICG_HEADLINE_PATH,
) -> list[Path]:
    df = cargar_microdatos(raw_path)
    directorio = Path(salida_headline).parent
    directorio.mkdir(parents=True, exist_ok=True)

    destinos = []

    # anio_desde=ANIO_DESDE_PAIS: icg_pais cubre 2001 en adelante; icg_la_plata
    # queda NaN antes de 2008 (Ciudad==7 no existe en el panel todavía) --
    # mismo mecanismo que ya deja NaN los meses de ene-feb/2008 sin La Plata.
    destino_headline = Path(salida_headline)
    construir_serie_headline(df, anio_desde=ANIO_DESDE_PAIS).to_csv(destino_headline, index=False)
    destinos.append(destino_headline)

    df_pais = df
    df_la_plata = df[df["Ciudad"] == CIUDAD_LA_PLATA]

    for corte in CORTES:
        destino = _ruta_corte(directorio, "pais", "mensual", corte)
        construir_series_demograficas(
            df_pais, corte=corte, resolucion="mensual", anio_desde=ANIO_DESDE_PAIS
        ).to_csv(destino, index=False)
        destinos.append(destino)

        destino = _ruta_corte(directorio, "la_plata", "anual", corte)
        construir_series_demograficas(
            df_la_plata, corte=corte, resolucion="anual", anio_desde=ANIO_DESDE_LA_PLATA
        ).to_csv(destino, index=False)
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
