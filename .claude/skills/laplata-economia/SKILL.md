---
name: laplata-economia
description: Estructura de datos y decisiones de diseño de la capa macroeconómica nacional del repositorio elecciones-socioeconomia-laplata (series 2011-2025 -- IPC, tipo de cambio, deuda pública, PBI, mercado laboral -- sin apertura espacial). Usar al trabajar con datos.gob.ar, BCRA, series de tiempo nacionales, o los catálogos catalogo_series*.csv. Para convenciones generales del repo (versionado, estilo de código) ver primero el skill laplata-general.
---

# Capa macroeconómica

`src/macroeconomia/` es un dominio separado de electoral/socioeconómico:
grano **nacional exclusivamente** (sin `circuito_id`, sin localidad),
relacionado con el resto del repo por fecha, nunca por join espacial.

Para convenciones que aplican a todo el repo (versionado, estilo de
código), ver el skill `laplata-general` primero.

## Antes de escribir código

- `docs/plan_macroeconomia.md` -- evaluación completa de fuentes y
  diseño por variable, incluyendo el "Rediseño posterior" que abandonó
  un primer diseño con forward-fill.
- `data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` -- qué se
  terminó bajando, su cobertura real, y los hallazgos de la última
  auditoría manual contra estadisticasbcra.com -- incluye un bug de
  catálogo real que encontró esa auditoría (`tipo_cambio_oficial`
  apuntaba al endpoint informal/blue, no al oficial; ya corregido) que
  sirve de precedente para no confiar en un mapeo de catálogo sin
  auditar.

## Estructura de datos

```
data/macroeconomia/catalogo_series.csv               # 20 conceptos mensuales/diarios/trimestrales -- hand-curated, append-only, git-tracked
data/macroeconomia/catalogo_series_anuales.csv        # conceptos de frecuencia anual (gasto/deuda pública, PBI) -- catálogo separado, git-tracked
data/macroeconomia/series_macro_2011_2025.csv         # generado, NO versionado -- una fila por mes
data/macroeconomia/series_macro_anuales_2011_2025.csv # generado, NO versionado -- una fila por año
data/macroeconomia/_cache/                             # respuestas crudas de datos.gob.ar, NO versionado
data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md  # cobertura + auditoría, git-tracked
src/macroeconomia/datos_gob_client.py   # fetch+cache de datos.gob.ar (pagina por sobre el límite de 5000 filas/pedido)
src/macroeconomia/series.py             # arma el CSV mensual desde el catálogo + caché
src/macroeconomia/series_anuales.py     # arma el CSV anual, reusa ConceptoCatalogo/cargar_catalogo/_parsear_puntos de series.py
src/macroeconomia/graficos.py           # un PNG por concepto (mensual + anual, 22 en total) -> graficos/macroeconomia/, NO versionado
src/macroeconomia/auditoria_estadisticasbcra.py  # cruce manual puntual contra estadisticasbcra.com -- no forma parte del pipeline regular, necesita ESTADISTICASBCRA_TOKEN (nunca commiteado)
```

## Reglas que no se negocian

- **Nunca se rellena ni se repite un valor (no forward-fill).** Una
  celda solo tiene dato si la fuente publicó exactamente para ese mes
  (o, en series diarias, para algún día hábil de ese mes); si no, queda
  vacía y `observaciones` lo declara. Un forward-fill le daría
  apariencia de granularidad mensual real a una serie trimestral/anual
  -- ver `docs/plan_macroeconomia.md`, "Rediseño posterior", para el
  diseño anterior que se abandonó por esto.
- **Frecuencia mensual y anual van en catálogos y CSV separados**, no
  en una sola grilla mensual -- una serie anual en grilla mensual queda
  ~93% vacía (1 de cada 12 filas puede tener dato alguna vez); al grano
  correcto (anual) esas mismas columnas quedan ~87% reales.
- **El caché (`_cache/`) y los CSV generados no se versionan** -- los
  catálogos (`catalogo_series*.csv`) sí, son hand-curated, mismo
  criterio que `data/totales/` vs. `clasificacion_ideologica_agrupaciones.csv`
  en la capa electoral.
- `auditoria_estadisticasbcra.py` solo audita tramos históricos
  cerrados -- el endpoint de estadisticasbcra.com está desactualizado
  (~1.5-2 años según la serie), nunca contrastar ahí los meses más
  recientes del CSV generado.

## Referencias

- `docs/plan_macroeconomia.md` -- evaluación de fuentes y diseño por
  variable.
- `data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` -- cobertura
  real y auditoría.
- `CLAUDE.md` -- comandos exactos y arquitectura autoritativa.
