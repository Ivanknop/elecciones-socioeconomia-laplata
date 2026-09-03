"""Cliente de descarga+caché de la API pública Georef-AR para las
localidades y el polígono del Partido de La Plata. No transforma nada --
eso es responsabilidad de `geolocalizacion.catalogo`."""
from __future__ import annotations

import json
from pathlib import Path

import requests

from constantes import GEOLOCALIZACION_CACHE_DIR

BASE_URL = "https://apis.datos.gob.ar/georef/api"
BULK_DEPARTAMENTOS_URL = "https://apis.datos.gob.ar/georef/api/v2.0/departamentos.geojson"


class GeorefClient:
    def __init__(self, cache_dir: Path | str = GEOLOCALIZACION_CACHE_DIR, timeout: float = 60.0):
        self.cache_dir = Path(cache_dir)
        self.session = requests.Session()
        self.timeout = timeout

    def get_asentamientos(self, municipio_id: str, force_refresh: bool = False) -> list[dict]:
        """Lista de {id, nombre, lat, lon} de los asentamientos del
        municipio pedido."""
        cache_path = self.cache_dir / f"asentamientos_{municipio_id}.json"
        if cache_path.exists() and not force_refresh:
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response = self.session.get(
            f"{BASE_URL}/asentamientos",
            params={"municipio": municipio_id, "max": 100, "campos": "id,nombre,centroide"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()

        asentamientos = [
            {"id": a["id"], "nombre": a["nombre"], "lat": a["centroide"]["lat"], "lon": a["centroide"]["lon"]}
            for a in payload["asentamientos"]
        ]

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(asentamientos, ensure_ascii=False, indent=2), encoding="utf-8")
        return asentamientos

    def get_departamento_geometria(self, departamento_id: str, force_refresh: bool = False) -> dict:
        cache_path = self.cache_dir / f"departamento_{departamento_id}.geojson"
        if cache_path.exists() and not force_refresh:
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response = self.session.get(BULK_DEPARTAMENTOS_URL, timeout=self.timeout)
        response.raise_for_status()
        coleccion = response.json()

        feature = next(
            (f for f in coleccion["features"] if f["properties"].get("id") == departamento_id),
            None,
        )
        if feature is None:
            raise ValueError(f"departamento {departamento_id!r} no encontrado en departamentos.geojson")

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(feature, ensure_ascii=False), encoding="utf-8")
        return feature
