# Análisis Política y Economía — Resultados Electorales (La Plata)

Cliente y pipeline de datos para la API pública de Resultados Electorales del
Ministerio del Interior (`https://resultados.mininterior.gob.ar/api`), con foco
en La Plata (Provincia de Buenos Aires): los cargos ejecutivos —Presidente,
Gobernador, Intendente— entre 2011 y 2023, y los cargos legislativos —nacional
(Diputados/Senadores Nacionales), provincial (Diputados/Senadores
Provinciales), municipal (Concejales)— entre 2013 y 2025. También recopila una
capa socioeconómica (EPH Gran La Plata, IAELaP y su correspondencia espacial
con el Censo) para poder cruzar, más adelante, resultados electorales con
condiciones socioeconómicas del mismo territorio; el Índice de Confianza en
el Gobierno (ICG, UTDT) para comparar la confianza declarada de La Plata
contra el resto del país, 2011 en adelante; una capa macroeconómica
nacional (2011-2025, sin apertura espacial) que da contexto temporal a las
anteriores; y una capa de geolocalización (catálogo validado de las 36
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

```
src/electoral/         cliente HTTP + modelo de dominio + agrupación por localidad
src/analisis/           gráficos y series estáticas (PNG/Markdown) desde circuito_<nivel>.json
src/visualizacion/      generadores de HTML interactivo para docs/ (mapa, cuadrantes V-Party, trayectorias económicas)
src/socioeconomia/      EPH, correspondencia circuito↔radio censal, ICG (UTDT)
src/macroeconomia/      series macroeconómicas nacionales (sin apertura espacial)
src/geolocalizacion/    catálogo validado de localidades geolocalizadas
src/ml_models/          panel temporal de ventanas electorales (calendario, resultado por distrito, panel trimestral) para modelado
notebooks/               pipeline: 01-04 capa electoral, 05-06 capa socioeconómica
data/                    insumos crudos + datos derivados, un subdirectorio por dominio
graficos/                salidas estáticas (PNG/Markdown); casi todo derivado, no versionado
docs/                    documentación narrativa del repo + sitio de GitHub Pages
requirements.txt
```

Cada subcarpeta de `data/` y `graficos/` mezcla archivos versionados
(insumos hand-curated, catálogos de referencia, algunos gráficos puntuales)
con archivos derivados (no versionados, se regeneran corriendo el
script/notebook correspondiente) — el criterio general es: lo que no se
puede reconstruir automáticamente desde otra fuente queda versionado, lo
que sí, no. El detalle exacto de qué está versionado en cada subcarpeta
vive en [`docs/FUNCIONALIDADES.md`](docs/FUNCIONALIDADES.md) y en el
README/`.md` propio de esa subcarpeta (ver "Documentación" más abajo), no
acá.

Toda la documentación narrativa (`docs/`) está versionada — es
documentación, no datos.

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
9. (Opcional, capa ICG) colocar manualmente
   `Base_histórica_2001-presente-ICG.dta` en `data/socioeconomia/icg-icc/`
   (no se distribuye en el repo, hay que conseguirlo con la Escuela de
   Gobierno UTDT — ver `data/socioeconomia/icg-icc/README.md`) y correr
   `PYTHONPATH=src python -m socioeconomia.icg_exportar_csv` seguido de
   `PYTHONPATH=src python -m socioeconomia.icg_graficos` — tampoco
   depende de los notebooks anteriores; ver `data/socioeconomia/ICG.md`.

A partir de `circuito_<nivel>.json`, todos los scripts de `src/analisis/`
(gráficos, series temporales, totales, cuadros comparativos) se corren
independientemente unos de otros — comandos exactos de cada uno en
`docs/FUNCIONALIDADES.md`. De los dos scripts de `src/visualizacion/`,
`mapa_interactivo` es la excepción: necesita tanto `circuito_<nivel>.json`
(paso 5) como el catálogo de geolocalización (paso 8) ya generados.
`distribucion_ideologica_interactiva` no depende de ninguno de los dos —
lee directo de `data/tfi_data/elecciones/`, ver `docs/FUNCIONALIDADES.md`.

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
- Para el **panel temporal de ventanas electorales** (`src/ml_models/`,
  qué es cada fase, ventana corta vs. bloque largo), ver
  [`docs/especificacion_panel_temporal.md`](docs/especificacion_panel_temporal.md)
  y [`docs/decisiones_metodologicas.md`](docs/decisiones_metodologicas.md)
  para las decisiones de diseño puntuales (`D1`, `D2`, ...).
- Para **qué puntos de la auditoría metodológica están resueltos o
  siguen abiertos**, ver
  [`docs/AUDITORIA_ESTADO.md`](docs/AUDITORIA_ESTADO.md).
- Para el **gráfico de cuadrantes ideológicos V-Party** (qué indica cada
  eje/punto del scatter nacional), ver
  [`docs/vparty_cuadrantes.md`](docs/vparty_cuadrantes.md) — la
  metodología de qué fila de `clasificacion_ideologica_agrupaciones.csv`
  viene de V-Party real vs. estimación propia vive en
  `data/agrupaciones/v-party/README.md` (ver más abajo), no ahí.
- Para un **borrador de correcciones electorales fuera de git** (interno,
  no versionado), ver `docs/PLAN_CORRECCIONES_ELECTORALES.md` si existe
  en tu copia local.

Documentos que **no** están en `docs/` porque describen un dataset
puntual y viven al lado de él (ver `CLAUDE.md` para el detalle de cada
uno): `data/geolocalizacion/fuentes_extra/CIRCUITOS_LOCALIDADES.md` y
`AUDITORIA_DISCREPANCIAS.md` (crosswalk circuito↔localidad),
`data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` (cobertura de la
capa macro), `data/geolocalizacion/LOCALIDADES.md` (catálogo validado de
localidades geolocalizadas), `data/socioeconomia/EXTRACCION_REDATAM.md` y
`EXTRACCION_IAELAP.md`/`SISTEMATIZACION_VARIABLES.md` (capa
socioeconómica), `data/socioeconomia/ICG.md` (decisiones metodológicas
del pipeline ICG — cobertura real vs. codebook, por qué "país" incluye a
La Plata, asimetría de resolución mensual/anual, límites de la fuente),
`data/socioeconomia/icg-icc/README.md` (qué es el microdato ICG, cómo
conseguirlo — no se distribuye en el repo),
`data/agrupaciones/v-party/README.md` (procedencia del
dataset V-Party y de qué fuente viene cada `vparty_economico`/
`progresismo`/`populismo` de `clasificacion_ideologica_agrupaciones.csv`
— única fuente de esa distinción en todo el repo).

