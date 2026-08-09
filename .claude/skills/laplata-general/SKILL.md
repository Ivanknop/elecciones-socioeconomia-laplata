---
name: laplata-general
description: Mapa de arranque del repositorio elecciones-socioeconomia-laplata -- estructura de alto nivel, convenciones de código, y la regla de versionado SemVer. Usar SIEMPRE como primer skill al trabajar en este repositorio, antes de tocar cualquier dominio puntual -- después, según el tema de la tarea, invocar además el skill de dominio correspondiente (laplata-elecciones, laplata-economia, o laplata-geolocalizacion). Evita releer CLAUDE.md/git log desde cero en cada sesión para las convenciones que aplican a todo el repo por igual.
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
   cruzado entre Georef-AR y el Ministerio de Obras Públicas. Todavía no
   cruzado con `circuito_id` ni con el Censo. Skill:
   **`laplata-geolocalizacion`**.

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
src/macroeconomia/                                    # dominio 2 -- ver laplata-economia
src/geolocalizacion/                                  # dominio 3 -- ver laplata-geolocalizacion
notebooks/               # 01-06, pipeline del dominio 1 (ver CLAUDE.md)
data/agrupaciones/, data/fuentes_extra/, data/distrito/, data/socioeconomia/   # dominio 1
data/macroeconomia/                                                            # dominio 2
data/geolocalizacion/                                                          # dominio 3
docs/                     # documentación narrativa del repo entero
tests/
CLAUDE.md                 # comandos + arquitectura autoritativa -- manda si algo difiere de los skills
```

## Convenciones de código, para los tres dominios por igual

- Docstrings, comentarios y mensajes de error en **español**.
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
  `data/fuentes_extra/CIRCUITOS_LOCALIDADES.md` o
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
