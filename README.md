# Análisis Política y Economía — Resultados Electorales (La Plata)

Cliente y pipeline de datos para la API pública de Resultados Electorales del
Ministerio del Interior (`https://resultados.mininterior.gob.ar/api`), con foco
en La Plata (Provincia de Buenos Aires): los cargos ejecutivos —Presidente,
Gobernador, Intendente— entre 2011 y 2023, y los cargos legislativos —nacional
(Diputados/Senadores Nacionales), provincial (Diputados/Senadores
Provinciales), municipal (Concejales)— entre 2013 y 2025. También recopila una
capa socioeconómica (EPH Gran La Plata, IAELaP y su correspondencia espacial
con el Censo) para poder cruzar, más adelante, resultados electorales con
condiciones socioeconómicas del mismo territorio; una capa macroeconómica
nacional (2011-2025, sin apertura espacial) que da contexto temporal a las
dos anteriores; y una capa de geolocalización (catálogo validado de las 36
localidades del partido, Georef-AR cruzado contra el Ministerio de Obras
Públicas) pensada para, más adelante, cruzar circuitos y series censales
por localidad.

Este archivo es la puerta de entrada: qué es el repo, cómo se instala, cómo
se reproduce desde cero, y qué está versionado. El detalle operativo de cada
script/módulo/anomalía conocida vive en
**[`docs/FUNCIONALIDADES.md`](docs/FUNCIONALIDADES.md)**, y el resto de la
documentación narrativa del proyecto (metodología, specs, estado de
auditoría) vive en `docs/` — ver la sección "Documentación" más abajo.

## Estructura del repositorio

Código, siempre versionado:

```
src/electoral/       client.py, models.py, localidades.py, totales.py
src/analisis/         graficos.py, generar_graficos.py, serie_temporal.py,
                       serie_temporal_filiacion.py, cuadros_anualizados.py,
                       cuadros_por_localidad.py, serie_temporal_por_localidad.py,
                       totales_por_lista.py, comparativo_nivel.py,
                       mapa_interactivo.py
src/socioeconomia/    geo.py, eph_client.py, graficos_eph_iaelap.py
src/macroeconomia/    datos_gob_client.py, series.py, graficos.py, auditoria_estadisticasbcra.py
src/geolocalizacion/  georef_client.py, catalogo.py, mapa.py
notebooks/             01_explorar_resultados.ipynb
                       02_la_plata_cargos_ejecutivos.ipynb
                       03_la_plata_legislativas.ipynb
                       04_totales_por_circuito.ipynb
                       05_capa_socioeconomica.ipynb
                       06_graficos_eph_iaelap.ipynb
docs/                  toda la documentación narrativa suelta del repo
                       (ver sección "Documentación" más abajo)
requirements.txt
```

Datos y gráficos, mezcla de versionado (curaduría manual) y derivado
(se regenera desde el código de arriba — nunca hace falta pedir permiso
para borrarlo y correrlo de nuevo):

| Ruta | Contenido | ¿Versionado en git? |
|---|---|---|
| `data/distrito/<año>/<nivel>/<etapa>/` | JSON+CSV crudo bajado de la API | No — se descarga con los notebooks |
| `data/distrito/<año>/<nivel>/<etapa>/circuito_<nivel>.json` | agregado por circuito  | No — derivado (notebook 04) |
| `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` | clasificación ideológica manual| **Sí** |
| `data/agrupaciones/tabla_referencia_filiacion_politica.csv` | fuente/confianza de `filiacion_politica` | **Sí** |
| `data/agrupaciones/campo_ideologico.csv` | escala 1-6  | **Sí** |
| `data/agrupaciones/colorimetria_campo_ideologico.csv` | color por `campo_ideologico`, única fuente en todo el repo | **Sí** |
| `data/agrupaciones/colorimetria_familia_politica.csv` | color por `filiacion_politica`, única fuente en todo el repo | **Sí** |
| `data/agrupaciones/circuito_id_correspondencias.csv` | normalización de `circuito_id` entre años | **Sí** |
| `data/socioeconomia/` | EPH, correspondencia circuito↔radio censal | **Sí**, salvo `eph_cache/` (gitignored) |
| `data/macroeconomia/catalogo_series.csv` | catálogo de series mensuales/diarias/trimestrales | **Sí** |
| `data/macroeconomia/series_macro_2011_2025.csv` | CSV mensual generado | No — derivado, se regenera desde `_cache/` |
| `data/macroeconomia/catalogo_series_anuales.csv` | catálogo de series de frecuencia anual | **Sí** |
| `data/macroeconomia/series_macro_anuales_2011_2025.csv` | CSV anual generado | No — derivado, se regenera desde `_cache/` |
| `data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` | doc de cobertura/auditoría | **Sí** |
| `data/geolocalizacion/localidades_la_plata.csv` | catálogo validado de localidades (Georef-AR × Ministerio de Obras Públicas) | **Sí** |
| `data/geolocalizacion/LOCALIDADES.md` | doc de metodología/hallazgos de ese catálogo | **Sí** |
| `data/por_localidad/` | cuadros por localidad | No — derivado (`cuadros_por_localidad.py`) |
| `data/totales/<nivel>/<año>/[<etapa>/]` | total de votos por agrupación (`<etapa>` solo para paso/balotaje) | No — derivado (`electoral.totales`) |
| `graficos/distrito/<año>/<nivel>/` | barras/torta circuito por circuito | No — se regenera on demand |
| `graficos/distrito/serie_temporal/` | series temporales por ideología/filiación | **Sí** |
| `graficos/distrito/totales_por_lista/` | barras de total + comparativos Municipio/Provincia/Nación | **Sí** |
| `graficos/socioeconomia/eph/` | gráficos de la EPH | **Sí** |
| `graficos/socioeconomia/` (resto) | IAELaP y contraste EPH/IAELaP | No |
| `graficos/por_localidad/` | series temporales por localidad | No — derivado |
| `docs/index.html`, `docs/mapa_electoral_la_plata.html` | sitio de GitHub Pages: landing + mapa interactivo (Leaflet), 68 circuitos × 22 elecciones generales | **Sí** |

Toda la documentación narrativa (`docs/`) también está versionada — es
documentación, no datos. Detalle de cada archivo en "Documentación" más
abajo.

## Instalación

```bash
pip install -r requirements.txt
```

No hace falta API key: los endpoints usados (Resultados Electorales,
datos.gob.ar) son públicos. Sí hace falta acceso de red saliente a
`resultados.mininterior.gob.ar` y, para las capas macro y de
geolocalización, a `apis.datos.gob.ar` (esta última incluye
`apis.datos.gob.ar/georef`).

## Cómo reproducir

1. `pip install -r requirements.txt`
2. Abrir y correr `notebooks/01_explorar_resultados.ipynb` para ver cómo se usa
   el cliente (`ResultadosClient`) y el modelo de dominio (`ResultadoElectoral`)
   sobre un solo caso (La Plata, Presidente, 2011).
3. Abrir y correr `notebooks/02_la_plata_cargos_ejecutivos.ipynb`. Este es el
   notebook que efectivamente genera/actualiza `data/`: trae el CSV oficial y
   el agregado JSON de cada combinación (año × cargo), y valida/actualiza
   `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` contra lo
   que trae la API (detalle del merge en `docs/FUNCIONALIDADES.md`, "Libro
   de códigos ideológico").
4. Abrir y correr `notebooks/03_la_plata_legislativas.ipynb`: mismo patrón
   pero para los cargos legislativos (nacional/provincial/municipal,
   2013-2025), sobre el mismo
   `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`.
5. Abrir y correr `notebooks/04_totales_por_circuito.ipynb`: normaliza
   `circuito_id`, agrega por ese id los totales de cada agrupación y de los
   "otros" (blanco, nulo, recurrido, impugnado...) para cada (año, nivel) ya
   descargado, cruza contra el libro de códigos ideológico, y escribe
   `data/distrito/<año>/<nivel>/generales/circuito_<nivel>.json` y
   `data/agrupaciones/circuito_id_correspondencias.csv` -- después hace lo
   mismo para PASO y balotaje, en los (año, nivel) donde existieron (ver
   `docs/FUNCIONALIDADES.md`, "PASO y balotaje").
6. Si ya existe la caché en `data/`, los notebooks corren instantáneo (leen
   de disco, no vuelven a pedirle nada a la API). Para forzar una
   actualización real, pasar `force_refresh=True` a los métodos del cliente.
7. (Opcional, capa macro) `PYTHONPATH=src python -m macroeconomia.series` —
   no depende de los notebooks anteriores, es un dominio separado por fecha,
   no por circuito (ver `docs/FUNCIONALIDADES.md`, "Capa macroeconómica").
8. (Opcional, capa de geolocalización) `PYTHONPATH=src python -m geolocalizacion.catalogo`
   seguido de `PYTHONPATH=src python -m geolocalizacion.mapa` — tampoco
   depende de los notebooks anteriores; ver
   `data/geolocalizacion/LOCALIDADES.md`.

A partir de `circuito_<nivel>.json`, todos los scripts de `src/analisis/`
(gráficos, series temporales, totales, cuadros comparativos) se corren
independientemente unos de otros — comandos exactos de cada uno en
`docs/FUNCIONALIDADES.md`. `analisis.mapa_interactivo` es la excepción:
necesita tanto `circuito_<nivel>.json` (paso 5) como el catálogo de
geolocalización (paso 8) ya generados.

## Tests

```bash
pytest
```

`pytest.ini` fija `pythonpath = src` y `testpaths = tests`. Qué está cubierto
por test y qué se valida corriendo los notebooks/scripts directamente está
detallado en `CLAUDE.md`.

## Documentación

- Para el **detalle operativo de cada script, comando y anomalía
  conocida**, ver [`docs/FUNCIONALIDADES.md`](docs/FUNCIONALIDADES.md).
- Para una **especificación no técnica del proyecto** (qué pregunta
  intenta responder, qué falta, para quién no sabe de código), ver
  [`docs/ESPECIFICACION_NO_TECNICA.md`](docs/ESPECIFICACION_NO_TECNICA.md).
- Para una **especificación técnica de la capa electoral** (uso, datos
  obtenidos, visualizaciones), ver
  [`docs/ESPECIFICACION_CAPA_ELECTORAL.md`](docs/ESPECIFICACION_CAPA_ELECTORAL.md).
- Para **fuentes evaluadas y catálogo de la capa macroeconómica**, ver
  [`docs/plan_macroeconomia.md`](docs/plan_macroeconomia.md) (y
  `data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` para la
  cobertura real obtenida).
- Para el **diseño de investigación completo** (hipótesis, alcance válido
  de las inferencias, la falacia ecológica a evitar), ver
  [`docs/nota_metodologica.md`](docs/nota_metodologica.md).
- Para **qué puntos de la auditoría metodológica están resueltos o
  siguen abiertos**, ver
  [`docs/AUDITORIA_ESTADO.md`](docs/AUDITORIA_ESTADO.md).
- Para un **borrador de correcciones electorales fuera de git** (interno,
  no versionado), ver `docs/PLAN_CORRECCIONES_ELECTORALES.md` si existe
  en tu copia local.

Documentos que **no** están en `docs/` porque describen un dataset
puntual y viven al lado de él (ver `CLAUDE.md` para el detalle de cada
uno): `data/fuentes_extra/CIRCUITOS_LOCALIDADES.md` y
`AUDITORIA_DISCREPANCIAS.md` (crosswalk circuito↔localidad),
`data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` (cobertura de la
capa macro), `data/geolocalizacion/LOCALIDADES.md` (catálogo validado de
localidades geolocalizadas), `data/socioeconomia/EXTRACCION_REDATAM.md` y
`EXTRACCION_IAELAP.md`/`SISTEMATIZACION_VARIABLES.md` (capa
socioeconómica).

Para **comandos, arquitectura y convenciones para trabajar en el repo**
(orientado a agentes/devs), ver `CLAUDE.md` (raíz, no se movió — es el
archivo que usa Claude Code para orientarse en el proyecto).

