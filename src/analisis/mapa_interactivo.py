"""Mapa interactivo (Leaflet) de resultados electorales de La Plata por
circuito, 2011-2025, **generales únicamente** (no incluye PASO ni
balotaje). Construye un único HTML autocontenido salvo Leaflet y las
teselas del mapa base, que se cargan por CDN (sin eso no hay conexión a
internet que lo evite: es un mapa, no un artefacto aislable). Escribe a
`docs/mapa_electoral_la_plata.html` -- no `graficos/`, porque este
archivo (junto con `docs/index.html`) es el sitio que sirve GitHub
Pages desde la carpeta `docs/` del repo, y ese es uno de los dos únicos
directorios que GitHub permite elegir como raíz de Pages sin un
workflow de Actions aparte.

## Fuentes (todas ya versionadas, ninguna se recalcula acá)

- `data/socioeconomia/circuitos_electorales_la_plata.geojson` -- polígonos
  oficiales CNE/PBA de los 68 circuitos (`socioeconomia.geo.canonicalizar_circuito_id`
  para los ids).
- `data/geolocalizacion/localidades_la_plata.csv` -- las 36 localidades
  geolocalizadas (`geolocalizacion.catalogo`).
- `data/fuentes_extra/circuito_localidad.csv` -- crosswalk circuito→localidad,
  vía `electoral.localidades.mapa_localidad_por_circuito` con ambos niveles
  de cobertura (oficial gana sobre periodístico, igual que en el resto del
  repo); los circuitos sin ninguna fuente (hoy solo el 521) quedan en `null`,
  nunca se inventan.
- `data/distrito/<año>/<nivel>/generales/circuito_<nivel>.json` -- resultados,
  descubiertos con `electoral.totales._combos_disponibles` filtrado a
  `etapa == "generales"` (mismo criterio que `totales_por_lista.py`).
- `data/agrupaciones/campo_ideologico.csv` (vía `analisis.graficos.IDEOLOGIAS`)
  y `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` (vía
  `analisis.serie_temporal_filiacion._cargar_filiaciones`) -- campo
  ideológico y filiación política por agrupación.

## Qué cambió respecto de la versión anterior (sin script, hecha a mano)

Esa versión solo mostraba "% de los positivos" -- viola la regla del
resto del repo de que ningún gráfico se queda solo con eso (ver skill
`laplata-elecciones`, "Reglas que no se negocian"). Acá cada circuito y
cada elección traen además `blanco_nulo` y `ausentismo`, con la misma
fórmula exacta que usa `graficos._votos_no_ideologicos`
(`ausentismo = electores - positivos - otros_total`, que puede dar
negativo en la familia de circuitos 504/505/508/509 -- se preserva
así, no se recorta a cero, y el mapa lo marca aparte en vez de
mezclarlo en la escala de color). El top-7 por circuito ahora trae un
renglón "otros" con el residuo (`positivos - suma del top7`) en vez de
dejar que las barras visibles no sumen 100% sin explicación.

Uso:
    PYTHONPATH=src python -m analisis.mapa_interactivo
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from analisis.graficos import (
    _CLAVES_BLANCO_NULO,
    _COLOR_FILIACION,
    _COLOR_IDEOLOGIA,
    _COLOR_NO_IDEOLOGICA,
    IDEOLOGIAS,
    _cargar_circuito,
)
from analisis.serie_temporal import CARGO_LABEL
from analisis.serie_temporal_filiacion import _cargar_filiaciones
from electoral.localidades import NIVEL_OFICIAL, NIVEL_PERIODISTICO, cargar_crosswalk, mapa_localidad_por_circuito
from electoral.totales import _combos_disponibles
from socioeconomia.geo import canonicalizar_circuito_id

TOP_N = 7

# Ni campo ideológico ni familia política ni blanco_nulo/ausentismo se
# hardcodean acá -- `_COLOR_IDEOLOGIA`/`_COLOR_FILIACION`/`_COLOR_NO_IDEOLOGICA`
# (import de arriba) son la misma fuente que usa el resto de `src/analisis/`,
# cargada en `graficos.py` desde `data/agrupaciones/colorimetria_campo_ideologico.csv`
# y `colorimetria_familia_politica.csv`. Acá solo se reindexa
# `_COLOR_IDEOLOGIA` (por nombre de campo) al código '1'-'6' que trae
# `campo_ideologico` en `circuito_<nivel>.json`.
_CAMPO_COLOR = {codigo: _COLOR_IDEOLOGIA[nombre] for codigo, nombre in IDEOLOGIAS.items()}
_COLOR_BLANCO_NULO = _COLOR_NO_IDEOLOGICA["blanco_nulo"]
_COLOR_AUSENTISMO = _COLOR_NO_IDEOLOGICA["ausentismo"]
_SIN_DATO = "#2a323c"  # "sin datos para esta elección" en el mapa -- no es una categoría de graficos.py, es propio de este visor


def _resolver_no_ideologicos(circuito: dict) -> tuple[int, int, int]:
    """`(positivos_total, blanco_nulo, ausentismo)` -- misma fórmula que
    `analisis.graficos._votos_no_ideologicos`, adaptada a un único
    circuito en vez de un `circuito_id` opcional sobre todo el archivo.
    `ausentismo` puede dar negativo (familia 504/505/508/509, ver
    `docs/FUNCIONALIDADES.md` "Anomalía conocida: circuito 508G") -- nunca
    se recorta a cero."""
    positivos_total = sum(info["votos"] for info in circuito["positivos"].values())
    blanco_nulo = sum(v for k, v in circuito["otros"].items() if k.upper() in _CLAVES_BLANCO_NULO)
    otros_total = sum(circuito["otros"].values())
    ausentismo = circuito["electores"] - positivos_total - otros_total
    return positivos_total, blanco_nulo, ausentismo


def _construir_circuito(circuito: dict, filiaciones: dict[str, str], agrup_index: dict[str, int]) -> dict:
    """Pura. `circuito` es `contenido['circuitos'][cid]` de un
    `circuito_<nivel>.json`; `filiaciones` viene de
    `serie_temporal_filiacion._cargar_filiaciones`; `agrup_index` mapea
    nombre de agrupación -> índice en la lista global `agrup_names`.

    El total que se usa como denominador de **todos** los porcentajes
    (listas + blanco_nulo + ausentismo) es `positivos + blanco_nulo +
    ausentismo` -- el mismo total implícito de `graficos._preparar`, no
    "positivos" solo. Con esto un mismo circuito con mucha abstención no
    puede mostrar un ganador con "38%" que en realidad es 38% de la
    mitad del padrón que efectivamente votó por una lista.
    """
    positivos_total, blanco_nulo, ausentismo = _resolver_no_ideologicos(circuito)
    total = positivos_total + blanco_nulo + ausentismo

    def pct(v: float) -> float:
        return round(v / total * 100, 2) if total else 0.0

    ranked = sorted(circuito["positivos"].items(), key=lambda kv: -kv[1]["votos"])
    top = ranked[:TOP_N]
    resto = ranked[TOP_N:]
    otros_listas_votos = sum(info["votos"] for _, info in resto)

    r = []
    for _, info in top:
        campo = info["campo_ideologico"] or None
        fam = filiaciones.get(info["nombre"])
        r.append([agrup_index[info["nombre"]], info["votos"], pct(info["votos"]), campo, fam])

    ganador_nombre, ganador_info = ranked[0] if ranked else (None, None)

    return {
        "pos": positivos_total,
        "bn": [blanco_nulo, pct(blanco_nulo)],
        "aus": [ausentismo, pct(ausentismo)],
        "elec": circuito["electores"],
        "tot": total,
        "r": r,
        "otros_l": [otros_listas_votos, pct(otros_listas_votos)] if resto else None,
        "g7": agrup_index[ganador_info["nombre"]] if ganador_info else None,
        "cg": (ganador_info["campo_ideologico"] or None) if ganador_info else None,
        "fg": filiaciones.get(ganador_info["nombre"]) if ganador_info else None,
    }


def _construir_eleccion(contenido: dict, filiaciones: dict[str, str], agrup_index: dict[str, int]) -> dict:
    """Pura. `contenido` es el `circuito_<nivel>.json` completo de un
    (año, nivel) puntual. Agrega también el acumulado a nivel distrito con
    la misma fórmula/total que cada circuito -- no solo la suma de los top7
    de cada uno, que subestimaría a las listas chicas."""
    circuitos_out = {}
    positivos_d = blanco_nulo_d = ausentismo_d = electores_d = 0
    votos_por_agrup: dict[str, int] = {}
    campo_por_agrup: dict[str, str | None] = {}

    for cid_crudo, circuito in contenido["circuitos"].items():
        cid = canonicalizar_circuito_id(cid_crudo)
        circuitos_out[cid] = _construir_circuito(circuito, filiaciones, agrup_index)

        positivos, blanco_nulo, ausentismo = _resolver_no_ideologicos(circuito)
        positivos_d += positivos
        blanco_nulo_d += blanco_nulo
        ausentismo_d += ausentismo
        electores_d += circuito["electores"]
        for info in circuito["positivos"].values():
            votos_por_agrup[info["nombre"]] = votos_por_agrup.get(info["nombre"], 0) + info["votos"]
            campo_por_agrup[info["nombre"]] = info["campo_ideologico"] or None

    total_d = positivos_d + blanco_nulo_d + ausentismo_d

    def pct_d(v: float) -> float:
        return round(v / total_d * 100, 2) if total_d else 0.0

    ranked_d = sorted(votos_por_agrup.items(), key=lambda kv: -kv[1])
    top_d = ranked_d[:TOP_N]
    top7 = [
        [agrup_index[nombre], votos, pct_d(votos), campo_por_agrup[nombre], filiaciones.get(nombre)]
        for nombre, votos in top_d
    ]
    otros_d_votos = sum(v for _, v in ranked_d[TOP_N:])

    return {
        "anio": contenido["anio"],
        "cargo": contenido["nivel"],
        "cargo_label": CARGO_LABEL[contenido["nivel"]],
        "pos": positivos_d,
        "bn": [blanco_nulo_d, pct_d(blanco_nulo_d)],
        "aus": [ausentismo_d, pct_d(ausentismo_d)],
        "elec": electores_d,
        "tot": total_d,
        "top7": top7,
        "otros_l": [otros_d_votos, pct_d(otros_d_votos)] if len(ranked_d) > TOP_N else None,
        "circuitos": circuitos_out,
    }


def _construir_agrup_index(combos: list[tuple[int, str, str]], data_dir: Path | str) -> dict[str, int]:
    """Todas las agrupaciones que aparecen en algún `circuito_<nivel>.json`
    de los combos pedidos, en orden alfabético (determinístico -- a
    diferencia de "orden de aparición", no depende del orden de iteración
    de un dict)."""
    nombres = set()
    for anio, nivel, etapa in combos:
        contenido = _cargar_circuito(data_dir, anio, nivel) if etapa == "generales" else None
        if contenido is None:
            continue
        for circuito in contenido["circuitos"].values():
            nombres.update(info["nombre"] for info in circuito["positivos"].values())
    ordenados = sorted(nombres)
    return {nombre: i for i, nombre in enumerate(ordenados)}


def _cargar_geojson_circuitos(path: Path | str) -> dict:
    crudo = json.loads(Path(path).read_text(encoding="utf-8"))
    features = []
    for feature in crudo["features"]:
        cid = canonicalizar_circuito_id(feature["properties"]["circuito"])
        coords = _redondear_coords(feature["geometry"]["coordinates"], feature["geometry"]["type"])
        features.append({
            "type": "Feature",
            "properties": {"circuito_id": cid},
            "geometry": {"type": feature["geometry"]["type"], "coordinates": coords},
        })
    return {"type": "FeatureCollection", "features": features}


def _redondear_coords(coords, tipo: str, decimales: int = 5):
    """Redondea longitud/latitud a `decimales` (5 ~= 1.1 m de precisión,
    de sobra para un mapa de referencia, no para un join espacial) --
    reduce bastante el tamaño del HTML sin perder nada visible."""
    if isinstance(coords[0], (int, float)):
        return [round(v, decimales) for v in coords]
    return [_redondear_coords(c, tipo, decimales) for c in coords]


def _cargar_localidades(path: Path | str) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return [
            {"nombre": fila["nombre"], "lat": round(float(fila["lat"]), 5), "lon": round(float(fila["lon"]), 5)}
            for fila in csv.DictReader(f)
        ]


def construir_payload(
    data_dir: Path | str = "data/distrito",
    geojson_path: Path | str = "data/socioeconomia/circuitos_electorales_la_plata.geojson",
    localidades_path: Path | str = "data/geolocalizacion/localidades_la_plata.csv",
    crosswalk_path: Path | str = "data/fuentes_extra/circuito_localidad.csv",
    clasificacion_path: Path | str = "data/agrupaciones",
) -> dict:
    combos = [c for c in _combos_disponibles(data_dir) if c[2] == "generales"]
    filiaciones = _cargar_filiaciones(clasificacion_path)
    agrup_index = _construir_agrup_index(combos, data_dir)
    agrup_names = sorted(agrup_index, key=agrup_index.get)

    fam_names = sorted({f for f in filiaciones.values()})

    elecciones = {}
    for anio, nivel, _etapa in combos:
        contenido = _cargar_circuito(data_dir, anio, nivel)
        elecciones[f"{anio}_{nivel}"] = _construir_eleccion(contenido, filiaciones, agrup_index)

    crosswalk = cargar_crosswalk(crosswalk_path)
    circuito_localidad_raw = mapa_localidad_por_circuito(crosswalk, (NIVEL_PERIODISTICO, NIVEL_OFICIAL))
    # nombre legible (Title Case, espacios) en vez del UPPER_SNAKE_CASE interno
    circuito_localidad = {
        cid: localidad.replace("_", " ").title() for cid, localidad in circuito_localidad_raw.items()
    }
    todos_los_circuitos = {f["properties"]["circuito"] for f in json.loads(Path(geojson_path).read_text(encoding="utf-8"))["features"]}
    for cid_crudo in todos_los_circuitos:
        cid = canonicalizar_circuito_id(cid_crudo)
        circuito_localidad.setdefault(cid, None)

    return {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "geojson": _cargar_geojson_circuitos(geojson_path),
        "circuito_localidad": circuito_localidad,
        "localidades": _cargar_localidades(localidades_path),
        "campo_labels": IDEOLOGIAS,
        "campo_colors": _CAMPO_COLOR,
        "agrup_names": agrup_names,
        "fam_names": fam_names,
        "fam_colors": {k: v for k, v in _COLOR_FILIACION.items() if k in fam_names},
        "color_blanco_nulo": _COLOR_BLANCO_NULO,
        "color_ausentismo": _COLOR_AUSENTISMO,
        "elecciones": elecciones,
    }


_HTML_TEMPLATE = None  # cargado de mapa_interactivo_template.html, ver generar_mapa_interactivo


def generar_mapa_interactivo(
    destino: Path | str = "docs/mapa_electoral_la_plata.html",
    data_dir: Path | str = "data/distrito",
) -> Path:
    payload = construir_payload(data_dir=data_dir)

    plantilla_path = Path(__file__).parent / "mapa_interactivo_template.html"
    plantilla = plantilla_path.read_text(encoding="utf-8")
    html = plantilla.replace(
        "/*__RAW_DATA__*/",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )

    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    destino_path.write_text(html, encoding="utf-8")
    return destino_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--destino", default="docs/mapa_electoral_la_plata.html")
    parser.add_argument("--data-dir", default="data/distrito")
    args = parser.parse_args()

    destino = generar_mapa_interactivo(destino=args.destino, data_dir=args.data_dir)
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
