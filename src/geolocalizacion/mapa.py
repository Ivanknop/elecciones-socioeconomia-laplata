"""Un PNG con las 36 localidades del catálogo sobre el contorno del
partido -- referencia visual, no un mapa de precisión (ver
`data/geolocalizacion/LOCALIDADES.md`).

Uso:
    PYTHONPATH=src python -m geolocalizacion.mapa
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import shape

from constantes import GEOLOCALIZACION_CACHE_DIR, LOCALIDADES_LA_PLATA_PATH
from geolocalizacion.georef_client import GeorefClient

DEPARTAMENTO_ID = "06441"

COLOR_CONFIRMADA = "#256abf"
COLOR_SOLO_GEOREF = "#d9822b"
COLOR_PARTIDO = "#889"


def _leer_catalogo(path: Path | str) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _geoserie_partido(feature: dict) -> gpd.GeoSeries:
    return gpd.GeoSeries([shape(feature["geometry"])], crs="EPSG:4326")


def graficar_mapa(catalogo: list[dict], feature_partido: dict, ax=None):
    """Pura (sin red): `catalogo` ya viene leído del CSV,
    `feature_partido` ya viene de `GeorefClient.get_departamento_geometria`."""
    if ax is None:
        _, ax = plt.subplots(figsize=(11, 9))

    partido = _geoserie_partido(feature_partido)
    partido.boundary.plot(ax=ax, color=COLOR_PARTIDO, linewidth=1.2)
    partido.plot(ax=ax, color=COLOR_PARTIDO, alpha=0.06)

    for loc in catalogo:
        confirmada = loc["fuentes"] == "georef+ministerio"
        color = COLOR_CONFIRMADA if confirmada else COLOR_SOLO_GEOREF
        marker = "o" if confirmada else "^"
        lon, lat = float(loc["lon"]), float(loc["lat"])
        ax.scatter(lon, lat, s=26, color=color, marker=marker, zorder=3, edgecolor="white", linewidth=0.6)
        ax.annotate(
            loc["nombre"], (lon, lat), fontsize=6.5, color="#2b2b28",
            xytext=(4, 3), textcoords="offset points", zorder=4,
        )

    lats_continente = [float(loc["lat"]) for loc in catalogo if loc["nombre"] != "Martín García"]
    lons_continente = [float(loc["lon"]) for loc in catalogo if loc["nombre"] != "Martín García"]
    pad_lat = (max(lats_continente) - min(lats_continente)) * 0.08
    pad_lon = (max(lons_continente) - min(lons_continente)) * 0.08
    ax.set_xlim(min(lons_continente) - pad_lon, max(lons_continente) + pad_lon)
    ax.set_ylim(min(lats_continente) - pad_lat, max(lats_continente) + pad_lat)

    lat0 = sum(lats_continente) / len(lats_continente)
    ax.set_aspect(1 / math.cos(math.radians(lat0)))

    ax.set_xlabel("longitud")
    ax.set_ylabel("latitud")
    ax.set_title(
        "Localidades geolocalizadas — Partido de La Plata",
        fontsize=10,
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    return ax.figure


def generar_mapa(
    catalogo_path: Path | str = LOCALIDADES_LA_PLATA_PATH,
    destino: Path | str = "graficos/geolocalizacion/mapa_localidades.png",
    cache_dir: Path | str = GEOLOCALIZACION_CACHE_DIR,
    departamento_id: str = DEPARTAMENTO_ID,
    force_refresh: bool = False,
) -> Path:
    if not Path(catalogo_path).exists():
        raise FileNotFoundError(f"{catalogo_path} no existe -- correr antes `python -m geolocalizacion.catalogo`")

    catalogo = _leer_catalogo(catalogo_path)
    client = GeorefClient(cache_dir=cache_dir)
    feature_partido = client.get_departamento_geometria(departamento_id, force_refresh=force_refresh)

    fig = graficar_mapa(catalogo, feature_partido)
    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino_path, dpi=140)
    plt.close(fig)
    return destino_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalogo", default=LOCALIDADES_LA_PLATA_PATH)
    parser.add_argument("--destino", default="graficos/geolocalizacion/mapa_localidades.png")
    parser.add_argument("--cache-dir", default=GEOLOCALIZACION_CACHE_DIR)
    parser.add_argument("--departamento-id", default=DEPARTAMENTO_ID)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    destino = generar_mapa(
        catalogo_path=args.catalogo,
        destino=args.destino,
        cache_dir=args.cache_dir,
        departamento_id=args.departamento_id,
        force_refresh=args.force_refresh,
    )
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
