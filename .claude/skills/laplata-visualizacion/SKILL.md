---
name: laplata-visualizacion
description: Estructura y convenciones de src/visualizacion/, el módulo que genera los HTML interactivos del sitio de GitHub Pages del repositorio elecciones-socioeconomia-laplata (mapa electoral Leaflet, cuadrantes ideológicos V-Party) -- patrón payload+template, qué va en docs/ vs. graficos/, y la regla de no distinguir V-Party real de estimación propia en la UI. Usar al tocar mapa_interactivo.py, distribucion_ideologica_interactiva.py, sus *_template.html, o al agregar una pestaña interactiva nueva al sitio. Para convenciones generales del repo ver primero el skill laplata-general; para el dato que estos scripts consumen (circuito_id, clasificación ideológica, crosswalk circuito↔localidad) ver laplata-elecciones.
---

# Visualización interactiva (`src/visualizacion/`)

`src/visualizacion/` es donde viven los generadores de **HTML interactivo
completo** para `docs/` (el sitio de GitHub Pages) -- a diferencia de
`src/analisis/`, que bulk-escribe PNGs/Markdown estáticos a `graficos/`
a partir de los mismos `circuito_<nivel>.json`. No es un dominio de datos
nuevo: es una capa de presentación sobre datos que ya existen en
`src/electoral/`, `src/analisis/` y `data/agrupaciones/` (dominio 1, ver
`laplata-elecciones`) y, para el catálogo de localidades, `src/geolocalizacion/`
(dominio 3, ver `laplata-geolocalizacion`).

Este módulo se separó de `src/analisis/` porque mezclar "genera 1 de N
PNGs por año/nivel" con "genera el único HTML interactivo del sitio,
consumido por Pages" bajo la misma carpeta hacía perder de vista qué
scripts alimentan `graficos/` (regenerable en segundos, casi todo
`.gitignore`d) y cuáles alimentan `docs/` (2 archivos, ambos
git-tracked, ambos parte del deploy). Antes de v-siguiente (ver
`CLAUDE.md` para el número de versión vigente) ambos vivían en
`src/analisis/`.

## Antes de tocar este módulo

1. `CLAUDE.md`, sección "Architecture" -- bullet `src/visualizacion/` y
   el bullet de `src/electoral/totales.py` (que documenta
   `mapa_interactivo.py` en detalle, junto a `totales_por_lista.py`/
   `comparativo_nivel.py` por compartir la misma cadena de
   `circuito_<nivel>.json`). Es la fuente autoritativa si algo de este
   skill queda desactualizado.
2. `docs/FUNCIONALIDADES.md`, sección "Distribución ideológica
   interactiva" -- detalle de esa pestaña puntual.
3. Este archivo, para el patrón compartido entre los dos scripts y las
   decisiones de diseño que no son obvias leyendo el código.

## Patrón compartido: payload + template

Los dos scripts del módulo siguen la misma forma:

```
construir_payload(...) -> dict          # toda la lógica de datos, pura, testeable
generar_<algo>(destino, ...) -> Path      # lee <script>_template.html, reemplaza
                                           # "/*__RAW_DATA__*/" por json.dumps(payload),
                                           # escribe a docs/
main()                                    # argparse + orquestación, sin lógica propia
```

`construir_payload()` en sí (la función completa, no sus piezas) no
tiene test dedicado -- mismo criterio que el resto de `src/analisis/*`:
la lógica de agregación/join que reusa (`_construir_circuito`,
`_construir_eleccion`, `tabla_distrito`, etc.) ya está testeada en su
módulo de origen, y el ensamblado final se valida corriendo el script
contra `data/` real más una pasada headless del HTML resultante.

El template (`<script>_template.html`) es HTML+CSS+JS autocontenido
salvo Leaflet y las teselas del mapa base, que cargan por CDN -- **el
HTML no funciona completamente offline**, necesita internet para
renderizar el mapa. `/*__RAW_DATA__*/` es un placeholder literal dentro
de un `<script>`, reemplazado por un string JSON en una sola pasada de
`str.replace` (no un templating engine) -- si se necesita escapar algo
raro en un valor (comillas, `</script>` literal dentro de un string),
resolverlo en `json.dumps` o en el dato de origen, no agregando lógica
de escape en el replace.

## Qué vive en `docs/` y por qué

Ambos HTML generados (`docs/mapa_electoral_la_plata.html`,
`docs/distribucion_ideologica_la_plata.html`) están en `docs/`, no en
`graficos/`, y **sí están git-tracked** -- `docs/` (junto con la raíz
del repo) es uno de los dos únicos directorios que GitHub Pages puede
servir sin un workflow de Actions aparte, y `docs/index.html` ya vivía
ahí. Cada uno se enlaza desde `docs/index.html` con una `viz-card` en la
sección 01 ("Visualización"). Si se agrega una pestaña nueva: mismo
patrón (script + template acá, salida a `docs/<nombre>.html`, card
nueva en `index.html`, subsección nueva en `docs/FUNCIONALIDADES.md`).

## `mapa_interactivo.py`

Documentado en detalle en `CLAUDE.md` (junto a `totales_por_lista.py`/
`comparativo_nivel.py`, mismo linaje de `circuito_<nivel>.json`) -- no
se repite acá. Puntos clave para no perder si se edita:

- Único script que hace join de geometría de circuito
  (`circuitos_electorales_la_plata.geojson`) + resultados electorales +
  catálogo de localidades, los tres a la vez.
- El total de cada porcentaje (por circuito y distrito) es siempre
  `positivos + blanco_nulo + ausentismo`, nunca solo `positivos` -- misma
  regla no negociable que el resto de `laplata-elecciones`.
- `ausentismo` nunca se recorta a cero (familia de circuitos
  504/505/508/509 con ausentismo negativo, ver `laplata-elecciones`) --
  se marca aparte en vez de mezclarse en la escala de color.
- Colores de campo ideológico/familia política vienen de
  `analisis.graficos._COLOR_IDEOLOGIA`/`_COLOR_FILIACION` (cargados de
  los CSV de colorimetría) -- nunca una paleta propia.
- Lógica de agregación pura en `_construir_circuito`/`_construir_eleccion`/
  `_construir_agrup_index` (testeada, `tests/visualizacion/test_mapa_interactivo.py`).

## `distribucion_ideologica_interactiva.py`

Documentado en detalle en `docs/FUNCIONALIDADES.md`, sección
"Distribución ideológica interactiva" -- no se repite acá. Puntos clave
para no perder si se edita:

**Sin mapa ni panel de localidad, por ahora -- pedido explícito de Ivan,
no reintroducir sin volver a preguntar.** La versión anterior tenía un mapa
Leaflet + un panel por localidad (mismo patrón que `mapa_interactivo.py`);
se sacó al migrar la fuente de datos a `data/tfi_data/elecciones/` (ver
abajo), que no tiene geometría de circuito para 2001-2009 -- hasta que se
defina un criterio para ese desglose, la pestaña es un único bubble chart
a nivel distrito.

- **Fuente de datos: `data/tfi_data/elecciones/<año>_<nivel>.csv`**, vía
  `analisis.vparty_distribucion_tfi.cargar_eleccion`/`combos_disponibles` --
  no `circuito_<cargo>.json` ni el join propio de
  `vparty_cuadrantes_local` contra `clasificacion_ideologica_agrupaciones.csv`.
  Por eso cubre **2001-2025**, no solo 2011-2025.
- Selector **Nivel + Año únicamente**, sin el toggle Cargo/Nivel del
  mapa -- los cuadros V-Party solo existen por nivel unificado.
- Escala de ejes fija y simétrica respecto de 0
  (`analisis.vparty_distribucion_tfi.limites_globales`, mismo criterio que
  los PNG estáticos), enviada una sola vez en el payload -- nunca
  recalculada por render.
- De `vparty_cuadrantes_local` solo reusa `_color_por_partido`/`_sombras`
  -- `tabla_distrito`/`tabla_localidades`/`cargar_posiciones_propias`/
  `cargar_filiaciones`/`_limites_globales` quedaron sin llamador acá (ver
  CLAUDE.md).

**Regla de diseño explícita, pedida por Ivan -- no reintroducir sin
volver a preguntar**: esta pestaña **no distingue visualmente V-Party
real de estimación propia calibrada** (se sacó deliberadamente un
intento anterior con checkbox/trazo distinto/leyenda de procedencia). Esa
distinción sigue existiendo, pero **solo en prosa, en un único lugar**:
`data/agrupaciones/v-party/README.md`.

## `vparty_distribucion_tfi.py` (`src/analisis/`, no `src/visualizacion/`)

Vive en `src/analisis/`, no acá -- es el generador de **PNG estático** (uno
por año/nivel a `graficos/tfi/v-party/`), no HTML interactivo, así que
sigue el criterio de esa carpeta (bulk output, `.gitignore`d), no el
patrón payload+template de este skill. Se documenta acá igual porque
`distribucion_ideologica_interactiva.py` reusa sus mismas
`cargar_eleccion`/`combos_disponibles`/`limites_globales` como fuente de
datos -- mismo número, dos salidas (HTML interactivo vs. PNG). Detalle
completo en `docs/FUNCIONALIDADES.md` sección "Gráficos" y en `CLAUDE.md`
(nota sobre el reemplazo de `vparty_cuadrantes_local.generar_distrito`,
deprecado).

## Testing

Mismo criterio que el resto de `src/analisis/*` (ver `laplata-general`):
lógica pura testeada, renderizado sin test automatizado. Concretamente:

- Lo que reusan de otros módulos (`analisis.graficos`,
  `analisis.serie_temporal_filiacion`, `analisis.vparty_cuadrantes_local`,
  `analisis.vparty_distribucion_tfi`, `electoral.localidades`,
  `electoral.totales`) ya está cubierto en los tests de esos módulos -- no
  se duplica acá (`vparty_distribucion_tfi`: `tests/analisis/test_vparty_distribucion_tfi.py`).
- `_construir_circuito`/`_construir_eleccion`/`_construir_agrup_index`/
  `_resolver_no_ideologicos`/`_votos_en_blanco`/`_votos_por_campo`/
  `_votos_por_familia` (todo de `mapa_interactivo.py`) están cubiertos en
  `tests/visualizacion/test_mapa_interactivo.py`, sin red ni HTML.
- `construir_payload`, `generar_mapa_interactivo`/
  `generar_distribucion_interactiva`, y ambos templates no tienen test
  automatizado -- se validan corriendo el script contra `data/` real y
  una pasada headless (Playwright/Chromium): la página carga sin errores
  de consola, y el selector puebla y renderiza (Cargo/Nivel + click de
  circuito para `mapa_interactivo`; Nivel/Año para
  `distribucion_ideologica_interactiva`, que ya no tiene circuitos que
  clickear), y el autoplay avanza en ambos.
