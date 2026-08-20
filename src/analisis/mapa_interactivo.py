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
- `data/geolocalizacion/circuitos_por_localidad.csv` -- crosswalk
  circuito→localidad geolocalizada, vía
  `electoral.localidades.cargar_circuito_localidad_geo` (nearest-neighbor
  contra el catálogo de arriba, ver skill `laplata-geolocalizacion` y
  `data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md`) -- mismo crosswalk que
  usa por defecto `analisis.cuadros_por_localidad` desde la reconstrucción
  del flujo por localidad. Cubre los 68 circuitos con una fila cada uno (a
  diferencia del crosswalk histórico por nombre de barrio que usaba antes
  esta vista, no quedan circuitos en `null` salvo que falten del propio
  geojson).
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
from constantes import (
    AGRUPACIONES_DIR,
    CIRCUITOS_GEOJSON_PATH,
    CIRCUITOS_POR_LOCALIDAD_PATH,
    DATA_DISTRITO_DIR,
    LOCALIDADES_LA_PLATA_PATH,
)
from electoral.localidades import cargar_circuito_localidad_geo
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


_CLAVES_BLANCO = {"EN BLANCO", "BLANCOS"}


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


def _votos_en_blanco(circuito: dict) -> int:
    """Solo "EN BLANCO"/"BLANCOS" -- a diferencia de `blanco_nulo` (que ya
    se usa en el resto del mapa para la leyenda/panel de circuito), acá se
    aísla del voto nulo porque el resumen del distrito (`resumen_distrito`)
    pide específicamente el voto en blanco solo."""
    return sum(v for k, v in circuito["otros"].items() if k.upper() in _CLAVES_BLANCO)


def _votos_por_campo(circuito: dict) -> dict[str, int]:
    """`{codigo_campo_ideologico: votos}` sumado sobre **todas** las
    agrupaciones del circuito (no solo el top-N) -- `""` agrupa las
    agrupaciones sin `campo_ideologico` clasificado todavía (ver
    `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`), nunca
    se descartan esos votos."""
    votos: dict[str, int] = {}
    for info in circuito["positivos"].values():
        clave = info["campo_ideologico"] or ""
        votos[clave] = votos.get(clave, 0) + info["votos"]
    return votos


def _votos_por_familia(circuito: dict, filiaciones: dict[str, str]) -> dict[str, int]:
    """Igual que `_votos_por_campo` pero por `filiacion_politica`."""
    votos: dict[str, int] = {}
    for info in circuito["positivos"].values():
        clave = filiaciones.get(info["nombre"]) or ""
        votos[clave] = votos.get(clave, 0) + info["votos"]
    return votos


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

    por_campo = {k: [v, pct(v)] for k, v in _votos_por_campo(circuito).items()}
    por_familia = {k: [v, pct(v)] for k, v in _votos_por_familia(circuito, filiaciones).items()}

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
        "por_campo": por_campo,
        "por_familia": por_familia,
    }


def _construir_eleccion(contenido: dict, filiaciones: dict[str, str], agrup_index: dict[str, int]) -> dict:
    """Pura. `contenido` es el `circuito_<nivel>.json` completo de un
    (año, nivel) puntual. Agrega también el acumulado a nivel distrito con
    la misma fórmula/total que cada circuito -- no solo la suma de los top7
    de cada uno, que subestimaría a las listas chicas."""
    circuitos_out = {}
    positivos_d = blanco_nulo_d = ausentismo_d = electores_d = blanco_d = 0
    votos_por_agrup: dict[str, int] = {}
    campo_por_agrup: dict[str, str | None] = {}
    votos_por_campo_d: dict[str, int] = {}
    votos_por_familia_d: dict[str, int] = {}

    for cid_crudo, circuito in contenido["circuitos"].items():
        cid = canonicalizar_circuito_id(cid_crudo)
        circuitos_out[cid] = _construir_circuito(circuito, filiaciones, agrup_index)

        positivos, blanco_nulo, ausentismo = _resolver_no_ideologicos(circuito)
        positivos_d += positivos
        blanco_nulo_d += blanco_nulo
        ausentismo_d += ausentismo
        electores_d += circuito["electores"]
        blanco_d += _votos_en_blanco(circuito)
        for info in circuito["positivos"].values():
            votos_por_agrup[info["nombre"]] = votos_por_agrup.get(info["nombre"], 0) + info["votos"]
            campo_por_agrup[info["nombre"]] = info["campo_ideologico"] or None
        for clave, votos in _votos_por_campo(circuito).items():
            votos_por_campo_d[clave] = votos_por_campo_d.get(clave, 0) + votos
        for clave, votos in _votos_por_familia(circuito, filiaciones).items():
            votos_por_familia_d[clave] = votos_por_familia_d.get(clave, 0) + votos

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

    # Resumen para la franja fija bajo los controles (no el desglose de
    # arriba): denominadores distintos a propósito, sobre pedido explícito
    # -- ausentismo relativo al padrón completo (`electores_d`, no `total_d`,
    # que ya excluye los votos procedimentales) y blanco relativo a los
    # votos efectivamente emitidos (`electores_d - ausentismo_d`, es decir
    # positivos + todo "otros" -- válidos, blancos, nulos o procedimentales).
    votos_emitidos_d = electores_d - ausentismo_d
    resumen = {
        "ausentismo_pct": round(ausentismo_d / electores_d * 100, 2) if electores_d else 0.0,
        "blanco_pct": round(blanco_d / votos_emitidos_d * 100, 2) if votos_emitidos_d else 0.0,
        "blanco_votos": blanco_d,
    }

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
        "por_campo": {k: [v, pct_d(v)] for k, v in votos_por_campo_d.items()},
        "por_familia": {k: [v, pct_d(v)] for k, v in votos_por_familia_d.items()},
        "resumen": resumen,
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
    data_dir: Path | str = DATA_DISTRITO_DIR,
    geojson_path: Path | str = CIRCUITOS_GEOJSON_PATH,
    localidades_path: Path | str = LOCALIDADES_LA_PLATA_PATH,
    crosswalk_path: Path | str = CIRCUITOS_POR_LOCALIDAD_PATH,
    clasificacion_path: Path | str = AGRUPACIONES_DIR,
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

    # `circuito_localidad_geo.csv` ya trae el nombre legible tal cual figura
    # en `localidades_la_plata.csv` (el mismo que usan los marcadores de
    # `localidades` más abajo) -- a diferencia del crosswalk histórico que
    # usaba esta vista antes, no hace falta reformatear UPPER_SNAKE_CASE.
    circuito_localidad = cargar_circuito_localidad_geo(crosswalk_path)
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
    data_dir: Path | str = DATA_DISTRITO_DIR,
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
    parser.add_argument("--data-dir", default=DATA_DISTRITO_DIR)
    args = parser.parse_args()

    destino = generar_mapa_interactivo(destino=args.destino, data_dir=args.data_dir)
    print(f"{destino} generado")


if __name__ == "__main__":
    main()
