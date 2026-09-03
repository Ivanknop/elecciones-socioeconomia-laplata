---
name: laplata-general
description: Mapa de arranque del repositorio elecciones-socioeconomia-laplata -- estructura de alto nivel, convenciones de código, y la regla de versionado SemVer. Usar SIEMPRE como primer skill al trabajar en este repositorio, antes de tocar cualquier dominio puntual -- después, según el tema de la tarea, invocar además el skill de dominio correspondiente (laplata-elecciones, laplata-economia, laplata-geolocalizacion, o laplata-visualizacion). Evita releer CLAUDE.md/git log desde cero en cada sesión para las convenciones que aplican a todo el repo por igual.
---

# analisis-politica-economia — mapa general

Repositorio de investigación con tres dominios analíticos, cada uno con
su propio skill de detalle:

1. **Electoral + socioeconómico** (`src/electoral/`, `src/analisis/`,
   `src/socioeconomia/`) — resultados electorales de La Plata 2011-2025
   cruzados con indicadores socioeconómicos (EPH, IAELaP, Censo), unidad
   de análisis `circuito_id`. Skill: **`laplata-elecciones`**.
2. **Macroeconómico** (`src/macroeconomia/`) — series nacionales
   2011-2025 (IPC, tipo de cambio, deuda, PBI, mercado laboral), grano
   exclusivamente nacional, sin `circuito_id` ni localidad. Skill:
   **`laplata-economia`**.
3. **Geolocalización** (`src/geolocalizacion/`) — catálogo validado de
   las 36 localidades del Partido de La Plata (nombre + lat/lon),
   cruzado entre Georef-AR y el Ministerio de Obras Públicas, y ya
   cruzado con `circuito_id` (`data/geolocalizacion/circuitos_por_localidad.csv`,
   nearest-neighbor, es el crosswalk que usa por defecto la agrupación
   por localidad del dominio 1). Todavía no cruzado con el Censo. Skill:
   **`laplata-geolocalizacion`**.
4. **Panel temporal de ventanas electorales** (`src/ml_models/`) — una
   fila por transición electoral (año×nivel), cruzando resultado
   electoral del dominio 1 con las series nacionales del dominio 2, para
   modelado futuro. Cinco fases (calendario, resultado por distrito,
   features intra/interventana, panel de ventanas, panel trimestral
   largo) documentadas en `docs/especificacion_panel_temporal.md` y
   `docs/decisiones_metodologicas.md` — sin skill propio todavía, ver
   `CLAUDE.md` sección "`src/ml_models/`".

No es un quinto dominio de datos, pero tiene su propio skill por ser una
capa transversal con reglas propias: **Visualización interactiva**
(`src/visualizacion/`) — los cuatro generadores de HTML completo para el
sitio de GitHub Pages (mapa electoral Leaflet, cuadrantes ideológicos
V-Party, trayectorias económicas trimestrales/bielección), sobre datos
del dominio 1 (dominio 3 para localidades, dominio 4 para las dos
pestañas de trayectorias económicas). Skill: **`laplata-visualizacion`**.

Este archivo alcanza para trabajo puramente estructural (convenciones de
código, versionado, layout general). Para cualquier tarea sobre datos
concretos de un dominio, invocá además el skill de ese dominio — ahí
está el detalle que este archivo no repite.

**Este archivo puede desactualizarse** si el repo se reorganiza (pasó
con la migración a `data/distrito/` en v3.0.0). Ante cualquier ruta que
no coincida con lo que ves en el filesystem o en `CLAUDE.md`, confiá en
el filesystem/`CLAUDE.md` — que documenta la estructura vigente con más
detalle — y avisá para que esto se corrija.

## Estructura de alto nivel

```
src/electoral/, src/analisis/, src/socioeconomia/   # dominio 1 -- ver laplata-elecciones
src/visualizacion/                                    # generadores de HTML interactivo para docs/ (capa de presentación sobre los dominios 1/3/4, separada de src/analisis/ porque no bulk-escribe PNG/Markdown) -- ver laplata-visualizacion
src/macroeconomia/                                    # dominio 2 -- ver laplata-economia
src/geolocalizacion/                                  # dominio 3 -- ver laplata-geolocalizacion
src/ml_models/                                        # dominio 4, panel temporal de ventanas electorales -- ver CLAUDE.md ("src/ml_models/") y docs/especificacion_panel_temporal.md
notebooks/               # 01-06, pipeline del dominio 1 (ver CLAUDE.md)
data/agrupaciones/, data/distrito/, data/socioeconomia/   # dominio 1
data/macroeconomia/                                                            # dominio 2
data/geolocalizacion/                                                          # dominio 3, EXCEPTO el subdirectorio de abajo
data/tfi_data/                                                                 # dominio 4 (calendario/ventanas/panel), ver docs/especificacion_panel_temporal.md
data/geolocalizacion/fuentes_extra/                                            # excepción: contenido del dominio 1 (crosswalk histórico circuito->barrio + su documentación), vive anidado acá porque es "información adicional" -- no confundir con el resto de data/geolocalizacion/, que sí es dominio 3
docs/                     # documentación narrativa del repo entero
tests/
CLAUDE.md                 # comandos + arquitectura autoritativa -- manda si algo difiere de los skills
```

## Convenciones de código, para los tres dominios por igual

- Docstrings, comentarios y mensajes de error en **español**.
- **El código tiene que ser autodescriptivo; comentarios y docstrings
  son la excepción, no la norma.** Se agregan solo para dejar constancia
  de una decisión puntual que no se entiende leyendo el código: una
  trampa del dato (la fuente dice una unidad, el valor real es otra), el
  origen de un número mágico, un invariante entre archivos, una anomalía
  conocida, o una referencia a una decisión `D` de
  `docs/decisiones_metodologicas.md`. Nunca un docstring/comentario que
  repite la firma de la función, parafrasea las líneas de abajo, o
  explica un "por qué" que cualquiera infiere del código de alrededor --
  eso se borra, no se acorta. Si una decisión necesita más contexto que
  una línea, apuntar a `CLAUDE.md`/`docs/FUNCIONALIDADES.md`/el README o
  `.md` propio del dominio en vez de inlinearlo -- un hecho, un solo
  lugar, nunca duplicado entre archivos.
- Reportes de resultados como `@dataclass` con propiedades calculadas
  (ver `ReporteCobertura` en `src/electoral/localidades.py`,
  `ReporteValidacion` en `src/geolocalizacion/catalogo.py`) en vez de
  tuplas sueltas o dicts sin tipo.
- Tests con `pytest`, fixtures chicas, un `assert` por comportamiento,
  nombres de test descriptivos en español
  (`test_circuito_no_agrupable_cae_en_sin_determinar`, no `test_case_3`).
  Mismo patrón en los tres dominios: la lógica pura (parsing, merge,
  normalización) tiene tests; el fetch de red y el renderizado
  matplotlib no — se valida corriendo el script contra datos reales (ver
  "qué está cubierto por test" en `CLAUDE.md`).
- Trabajo espacial con `geopandas`. Instalación de dependencias con
  `pip install -r requirements.txt` — no asumas un flag distinto sin
  confirmarlo contra `CLAUDE.md`.
- Cuando se agregue una fuente nueva (una resolución, un relevamiento
  periodístico, un dataset oficial, un endpoint de API), documentarla
  con: nombre de fuente, fecha, URL, y qué porción del universo cubre —
  siguiendo el formato ya usado en
  `data/geolocalizacion/fuentes_extra/CIRCUITOS_LOCALIDADES.md` o
  `data/geolocalizacion/LOCALIDADES.md`.
- **No tocar datos para que un número dé mejor.** Si un accuracy,
  cobertura o test da bajo, el resultado es que da bajo — se documenta,
  no se ajusta el dato de origen para maquillarlo. Regla sin excepciones
  en los tres dominios.
- **Los CSV/PNG derivados no se versionan**, salvo excepciones puntuales
  documentadas en `.gitignore` y `CLAUDE.md` (ej.
  `graficos/distrito/serie_temporal/` sí; `graficos/distrito/<año>/`
  no). Se regeneran en segundos corriendo el script correspondiente —
  nunca hace falta pedir permiso para borrarlos y correr de nuevo.

## Versionado (SemVer real, no solo la convención previa del repo)

- **MINOR** (x.Y.0): agregado compatible hacia atrás sobre un dominio de
  datos que ya existe — nuevo crosswalk, nueva agregación, nueva
  columna opcional. Nada existente cambia de esquema, de ruta, ni deja
  de andar con los defaults previos.
- **MAJOR** (X.0.0): nuevo dominio analítico que no existía (ej. el
  salto v1→v2 fue agregar toda la capa socioeconómica desde cero; sumar
  `src/geolocalizacion/` fue MAJOR por el mismo criterio), o cualquier
  cambio que rompe algo que ya se usaba — incluye mover o renombrar
  rutas de `data/`/`graficos/` que otro script o notebook pudiera
  asumir, no solo cambios de esquema de datos (ej. v3.0.0, la
  reorganización a `data/distrito/`).
- Antes de tagear, confirmar en cuál de las dos categorías cae el
  cambio — no asumir MAJOR solo porque "se siente grande", pero
  tampoco asumir MINOR solo porque no cambiaron los datos si cambiaron
  las rutas o los defaults de CLI que algo externo pudiera usar.

## Qué skill invocar según la tarea

| Tarea | Skill |
|---|---|
| Resultados electorales, `circuito_id`, crosswalk circuito↔localidad, clasificación ideológica, EPH/IAELaP, correspondencia circuito↔radio censal | `laplata-elecciones` |
| Series macroeconómicas nacionales (IPC, tipo de cambio, deuda, PBI, datos.gob.ar, BCRA) | `laplata-economia` |
| Localidades geolocalizadas, Georef-AR, Ministerio de Obras Públicas, mapa de localidades, lat/lon | `laplata-geolocalizacion` |
| `src/visualizacion/` (mapa Leaflet, cuadrantes V-Party interactivos, cualquier HTML nuevo para `docs/`) | `laplata-visualizacion` |
| `src/ml_models/`, panel temporal de ventanas electorales, `data/tfi_data/panel/` | sin skill propio -- ver `CLAUDE.md` ("src/ml_models/") y `docs/especificacion_panel_temporal.md` |
