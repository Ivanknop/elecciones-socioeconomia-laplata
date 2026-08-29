"""Constantes centralizadas de `src/`: rutas de datos y constantes de
dominio compartidas entre módulos, antes duplicadas como string literal
en varios scripts."""
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
VPARTY_PATH = "data/agrupaciones/v-party/v_party_argentina_2001_2019_espaniol.csv"

# --- Geolocalización ---
LOCALIDADES_LA_PLATA_PATH = "data/geolocalizacion/localidades_la_plata.csv"
GEOLOCALIZACION_CACHE_DIR = "data/geolocalizacion/_cache"
CIRCUITOS_POR_LOCALIDAD_PATH = "data/geolocalizacion/circuitos_por_localidad.csv"
CIRCUITOS_POR_LOCALIDAD_DOC_PATH = "data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md"

# --- Fuentes extra / crosswalk (data/geolocalizacion/fuentes_extra/ -- insumos
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
ICG_RAW_PATH = "data/socioeconomia/icg/Base_histórica_2001-presente-ICG.dta"
ICG_HEADLINE_PATH = "data/socioeconomia/icg_mensual_la_plata_pais_2011_presente.csv"

# --- Panel (a completar a medida que se generen estos archivos) ---
# PANEL_DIR = "data/panel"
# VOTO_PARTIDO_PATH = "data/panel/voto_partido.csv"
# RESULTADO_ELECTORAL_PATH = "data/panel/resultado_electoral.csv"
# CLASIFICACION_FAMILIA_POLITICA_PATH = "data/agrupaciones/clasificacion_familia_politica.csv"

# --- Panel temporal de ventanas electorales
TFI_DATA_DIR = "data/tfi_data"
CALENDARIO_ELECTORAL_PATH = "data/tfi_data/calendario_electoral.csv"
OFICIALISMO_POR_NIVEL_PATH = "data/tfi_data/oficialismo_por_nivel.csv"
VENTANAS_PATH = "data/tfi_data/ventanas.csv"
RESULTADO_DISTRITO_PATH = "data/tfi_data/resultado_distrito.csv"
VOTO_PARTIDO_DISTRITO_PATH = "data/tfi_data/voto_partido_distrito.csv"
REGISTRO_VARIABLES_PATH = "data/tfi_data/registro_variables.csv"
SERIES_ECONOMICAS_MENSUALES_PATH = "data/tfi_data/series_economicas_mensuales.csv"
PANEL_VENTANAS_PATH = "data/tfi_data/panel_ventanas.csv"
ELECCIONES_DIR = "data/tfi_data/elecciones"


# --- Constantes de dominio compartidas ---

CARGO_LABEL = {
    "presidente": "Presidente",
    "nacional": "Diputados Nac.",
    "gobernador": "Gobernador",
    "provincial": "Diputados Prov.",
    "intendente": "Intendente",
    "municipal": "Concejales",
}
