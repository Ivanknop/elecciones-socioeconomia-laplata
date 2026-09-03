"""Cliente de descarga+caché de series de tiempo de datos.gob.ar, paginado
(límite 5000 filas/pedido); no transforma nada -- el parseo es
responsabilidad de `macroeconomia.series`."""
from __future__ import annotations

import json
from pathlib import Path

import requests

from constantes import MACRO_CACHE_DATOS_GOB_DIR

BASE_URL = "https://apis.datos.gob.ar/series/api/series/"
_LIMITE_MAXIMO = 5000


class DatosGobClient:
    def __init__(self, cache_dir: Path | str = MACRO_CACHE_DATOS_GOB_DIR, timeout: float = 30.0):
        self.cache_dir = Path(cache_dir)
        self.session = requests.Session()
        self.timeout = timeout

    def get_serie(self, serie_id: str, start_date: str = "2010-01-01", force_refresh: bool = False) -> dict:
        cache_path = self.cache_dir / f"{serie_id}.json"
        if cache_path.exists() and not force_refresh:
            return json.loads(cache_path.read_text(encoding="utf-8"))

        datos = []
        meta = None
        offset = 0
        while True:
            params = {
                "ids": serie_id,
                "format": "json",
                "start_date": start_date,
                "limit": _LIMITE_MAXIMO,
                "start": offset,
            }
            response = self.session.get(BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            if "errors" in payload:
                raise ValueError(f"error de la API para {serie_id}: {payload['errors']}")

            filas = payload["data"]
            meta = payload["meta"]
            datos.extend(filas)
            offset += len(filas)
            if len(filas) < _LIMITE_MAXIMO or offset >= payload["count"]:
                break

        resultado = {"data": datos, "meta": meta, "count": len(datos)}

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        return resultado
