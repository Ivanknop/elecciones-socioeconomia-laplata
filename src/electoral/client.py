"""Cliente HTTP para la API de Resultados Electorales del Ministerio del Interior.

Devuelve siempre los datos crudos tal como los entrega la API (JSON o CSV),
sin transformarlos. El parseo a objetos de dominio es responsabilidad de
`electoral.models`.

El caché en disco se organiza como `data/<anioEleccion>/<categoria_nombre>/...`.
`categoria_nombre` es una etiqueta que decide quien llama (ej. "presidente",
"gobernador"), no un dato que devuelva la API: `categoriaId` está indexado
localmente por distrito/año, no hay forma de derivar el nombre de la
categoría de manera confiable a partir del id solo (ver notebooks).
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

BASE_URL = "https://resultados.mininterior.gob.ar/api/resultados/getResultados"
CSV_URL = "https://resultados.mininterior.gob.ar/api/resultado/totalizadocsv"


_MARCA_NO_DISPONIBLE = b"mensaje\nResultados no disponibles."


class ResultadosNoDisponibles(Exception):
    """La API respondió que no hay resultados para esta consulta """

# Único valor documentado por la API para tipoRecuento (endpoint JSON).
TIPO_RECUENTO_PROVISORIO = 1

RECUENTO_PROVISORIO = "Provisorio"

_ORDEN_CACHE = (
    "tipoEleccion",
    "categoriaId",
    "distritoId",
    "seccionProvincialId",
    "seccionId",
    "circuitoId",
    "mesaId",
)


class ResultadosClient:
    def __init__(self, cache_dir: Path | str = "data", timeout: float = 30.0):
        self.cache_dir = Path(cache_dir)
        self.session = requests.Session()
        self.timeout = timeout

    def get_resultados(
        self,
        anio_eleccion: int,
        categoria_nombre: str,
        tipo_eleccion: int,
        categoria_id: int,
        distrito_id: int | None = None,
        seccion_provincial_id: int | None = None,
        seccion_id: int | None = None,
        circuito_id: int | None = None,
        mesa_id: int | None = None,
        force_refresh: bool = False,
    ) -> dict:
        """Trae el JSON crudo de resultados totalizados, usando caché en disco.

        `categoria_nombre` (ej. "presidente") solo se usa para organizar el
        caché en `data/<anio_eleccion>/<categoria_nombre>/`; no se envía a la API.
        """
        params = {
            "anioEleccion": anio_eleccion,
            "tipoRecuento": TIPO_RECUENTO_PROVISORIO,
            "tipoEleccion": tipo_eleccion,
            "categoriaId": categoria_id,
            "distritoId": distrito_id,
            "seccionProvincialId": seccion_provincial_id,
            "seccionId": seccion_id,
            "circuitoId": circuito_id,
            "mesaId": mesa_id,
        }
        params = {k: v for k, v in params.items() if v is not None}

        cache_path = self._cache_path(anio_eleccion, categoria_nombre, params, ext="json")
        if cache_path.exists() and not force_refresh:
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response = self.session.get(BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return data

    def get_resultados_csv(
        self,
        anio_eleccion: int,
        categoria_nombre: str,
        tipo_eleccion: int,
        categoria_id: int,
        distrito_id: int,
        seccion_provincial_id: int | None = None,
        seccion_id: int | None = None,
        force_refresh: bool = False,
    ) -> bytes:
        """Trae el CSV oficial. Trae todas las mesas del alcance pedido en un
        solo pedido.
        """
        params = {
            "año": anio_eleccion,
            "recuento": RECUENTO_PROVISORIO,
            "idEleccion": tipo_eleccion,
            "idCargo": categoria_id,
            "idDistrito": distrito_id,
        }
        if seccion_provincial_id is not None:
            params["idSeccionProvincial"] = seccion_provincial_id
        if seccion_id is not None:
            params["idSeccion"] = seccion_id

        params_cache = {
            "tipoEleccion": tipo_eleccion,
            "categoriaId": categoria_id,
            "distritoId": distrito_id,
            "seccionProvincialId": seccion_provincial_id,
            "seccionId": seccion_id,
        }
        params_cache = {k: v for k, v in params_cache.items() if v is not None}
        cache_path = self._cache_path(anio_eleccion, categoria_nombre, params_cache, ext="csv")

        if cache_path.exists() and not force_refresh:
            return cache_path.read_bytes()

        response = self.session.get(CSV_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        if response.content.strip() == _MARCA_NO_DISPONIBLE:
            raise ResultadosNoDisponibles(
                f"Sin resultados: anio={anio_eleccion} categoria_id={categoria_id} "
                f"distrito_id={distrito_id} seccion_id={seccion_id}"
            )

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(response.content)
        return response.content

    def iter_mesas(
        self,
        mesa_ids,
        anio_eleccion: int,
        categoria_nombre: str,
        tipo_eleccion: int,
        categoria_id: int,
        distrito_id: int,
        seccion_provincial_id: int | None = None,
        seccion_id: int | None = None,
        circuito_id: str | None = None,
        force_refresh: bool = False,
    ):
        """Itera `mesa_ids` y devuelve `(mesa_id, raw)` solo para las mesas que
        existen (`mesasTotalizadas > 0`).
        """
        for mesa_id in mesa_ids:
            raw = self.get_resultados(
                anio_eleccion=anio_eleccion,
                categoria_nombre=categoria_nombre,
                tipo_eleccion=tipo_eleccion,
                categoria_id=categoria_id,
                distrito_id=distrito_id,
                seccion_provincial_id=seccion_provincial_id,
                seccion_id=seccion_id,
                circuito_id=circuito_id,
                mesa_id=mesa_id,
                force_refresh=force_refresh,
            )
            if raw["estadoRecuento"]["mesasTotalizadas"] > 0:
                yield mesa_id, raw

    def _cache_path(
        self, anio_eleccion: int, categoria_nombre: str, params: dict, ext: str
    ) -> Path:
        subdir = self.cache_dir / str(anio_eleccion) / categoria_nombre
        partes = [f"{clave}-{params[clave]}" for clave in _ORDEN_CACHE if clave in params]
        nombre = "_".join(partes) if partes else "consulta"
        return subdir / f"{nombre}.{ext}"
