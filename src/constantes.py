"""Constantes centralizadas para toda la capa de `src/`: rutas de datos que
antes estaban repetidas como string literal (default de `argparse` o de
parámetro de función) en varios scripts, y constantes de dominio
compartidas entre módulos (ej. `CARGO_LABEL`, antes duplicado literal en
`analisis/serie_temporal.py` y `analisis/cuadros_anualizados.py`).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Electoral / distrito ---
DATA_DISTRITO_DIR = "data/distrito"
DATA_TOTALES_DIR = "data/totales"
DATA_POR_LOCALIDAD_DIR = "data/por_localidad"

# --- Agrupaciones / clasificación ---
AGRUPACIONES_DIR = "data/agrupaciones"
CAMPO_IDEOLOGICO_PATH = "data/agrupaciones/campo_ideologico.csv"
CLASIFICACION_IDEOLOGICA_PATH = "data/agrupaciones/clasificacion_ideologica_agrupaciones.csv"
COLORIMETRIA_CAMPO_IDEOLOGICO_PATH = "data/agrupaciones/colorimetria_campo_ideologico.csv"
COLORIMETRIA_FAMILIA_POLITICA_PATH = "data/agrupaciones/colorimetria_familia_politica.csv"
OFICIALISMOS_PATH = "data/agrupaciones/oficialismos.csv"
CIRCUITO_ID_CORRESPONDENCIAS_PATH = "data/agrupaciones/circuito_id_correspondencias.csv"
VPARTY_PATH = "data/agrupaciones/v-party/v_party_argentina_2011_2019_espaniol.csv"

# --- Geolocalización ---
LOCALIDADES_LA_PLATA_PATH = "data/geolocalizacion/localidades_la_plata.csv"
GEOLOCALIZACION_CACHE_DIR = "data/geolocalizacion/_cache"
CIRCUITOS_POR_LOCALIDAD_PATH = "data/geolocalizacion/circuitos_por_localidad.csv"
CIRCUITOS_POR_LOCALIDAD_DOC_PATH = "data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md"

# --- Fuentes extra / crosswalk (data/geolocalizacion/fuentes_extra/ -- insumos
# hand-curated adicionales, no derivados del catálogo de geolocalización en sí) ---
FUENTES_EXTRA_DIR = "data/geolocalizacion/fuentes_extra"
CROSSWALK_CIRCUITO_LOCALIDAD_PATH = "data/geolocalizacion/fuentes_extra/circuito_localidad.csv"
LOCALIDADES_MINISTERIO_PATH = "data/geolocalizacion/fuentes_extra/localidades.csv"
AUDITORIA_DISCREPANCIAS_PATH = "data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md"

# --- Macroeconomía ---
MACRO_CATALOGO_SERIES_PATH = "data/macroeconomia/catalogo_series.csv"
MACRO_CATALOGO_SERIES_ANUALES_PATH = "data/macroeconomia/catalogo_series_anuales.csv"
MACRO_SERIES_MENSUAL_PATH = "data/macroeconomia/series_macro_2011_2025.csv"
MACRO_SERIES_ANUAL_PATH = "data/macroeconomia/series_macro_anuales_2011_2025.csv"
MACRO_CACHE_DATOS_GOB_DIR = "data/macroeconomia/_cache/datos_gob"

# --- Socioeconomía ---
EPH_CACHE_DIR = "data/socioeconomia/eph_cache"
CIRCUITOS_GEOJSON_PATH = "data/socioeconomia/circuitos_electorales_la_plata.geojson"

# --- Panel (a completar a medida que se generen estos archivos) ---
# PANEL_DIR = "data/panel"
# VOTO_PARTIDO_PATH = "data/panel/voto_partido.csv"
# RESULTADO_ELECTORAL_PATH = "data/panel/resultado_electoral.csv"
# CLASIFICACION_FAMILIA_POLITICA_PATH = "data/agrupaciones/clasificacion_familia_politica.csv"


# --- Constantes de dominio compartidas ---

CARGO_LABEL = {
    "presidente": "Presidente",
    "nacional": "Diputados Nac.",
    "gobernador": "Gobernador",
    "provincial": "Diputados Prov.",
    "intendente": "Intendente",
    "municipal": "Concejales",
}
