# Plan: pestaña interactiva "Distribución ideológica (V-Party)"

> Documento de trabajo interno (no versionado, ver `.gitignore` — mismo
> criterio que `docs/especificaciones/PLAN_CORRECCIONES_ELECTORALES.md`). Plan acordado
> antes de escribir código; retomar desde acá.

## Pedido original

Nueva pestaña en el sitio de GitHub Pages, mismo patrón de interacción
temporal que `docs/mapa_electoral_la_plata.html` (selectores
Cargo/Nivel/Año), mostrando:

- Panel principal: mapa de circuitos de La Plata (geojson + layer ya
  usado en `mapa_interactivo.py`), sin colorear por ideología — solo
  referencia geográfica + click.
- Columna derecha: el cuadro V-Party distrital para el año/nivel
  seleccionado (hoy PNG estático, migrar a payload JSON reactivo).
- Click en un circuito del mapa → resuelve la localidad → estado
  "Distribución ideológica de {localidad} — próximamente" (no hay datos
  a nivel localidad todavía; no simular, no mostrar el cuadro distrital
  como si fuera de esa localidad).

Restricción dura: **no tocar la ruta que genera el PNG**. Todo esto es
aditivo.

## Investigación (hecha antes de programar)

### 1. Script que genera los PNG distritales: `src/analisis/vparty_cuadrantes_local.py`

- **Qué calcula**: dispersión de agrupaciones en un plano por elección
  puntual (no serie temporal). `tabla_distrito(nivel, posiciones, data_dir)`
  → una fila por `(agrupación, año)` con `economico`, `progresismo`,
  `populismo`, `votos`, `votos_porcentaje`. `generar_distrito()` la
  parte por año y llama a `graficar_cuadrantes_partido()`: **X=económico,
  Y=progresismo, tamaño=% de votos** (no votos absolutos), **color=familia
  política** (`filiacion_politica`, con una sombra de luminosidad por
  partido dentro de la familia — no por populismo). Populismo queda
  **fuera del encoding visual** hoy, aunque sigue en el DataFrame.
- **Fuente de datos**: `clasificacion_ideologica_agrupaciones.csv` (los 3
  ejes V-Party) unida contra votos reales vía
  `electoral.totales.resultado_total_por_agrupacion` (lee
  `circuito_<nivel>.json`) — mismo dato que usa `mapa_interactivo.py`. No
  existen `voto_partido.csv` ni `tabla_export_ml.csv` en este repo.
- **¿Marca procedencia (V-Party real vs. propia)? No.** Ni
  `cargar_posiciones_propias()` ni el CSV guardan de qué fuente viene
  cada valor — esa distinción vive solo en prosa, en
  `data/agrupaciones/v-party/README.md` (tablas "Fuente 1/2/3" +
  "Fuente adicional"). La sub-distinción "especialista/no especialista"
  **no existe en absoluto**: `encuesta_partidos_propia.csv` (anonimizada)
  nunca retuvo un campo de perfil/expertise.

### 2. Columnas reales de `clasificacion_ideologica_agrupaciones.csv`

```
anio,agrupacion,nivel,campo_ideologico,filiacion_politica,vparty_economico,vparty_progresismo,vparty_populismo
```

3 ejes V-Party, **sin columna de procedencia/confianza**.
`tabla_referencia_filiacion_politica.csv` tiene `confianza_clasificacion`,
pero es para `filiacion_politica`, no para los ejes V-Party.

### 3. Función pura previa al ploteo: ya existe, se reusa tal cual

`tabla_distrito()` y `_color_por_partido()` ya están separadas de
matplotlib — **no hace falta refactor ni extracción**. Llamando
`tabla_distrito()` una vez por cada uno de los 3 niveles unificados
(nacional/provincial/municipal) y concatenando se cubren los 6 cargos
crudos sin tocar el código existente.

## Decisiones tomadas (con el usuario, antes de programar)

- **Procedencia**: 2 categorías — `real` / `estimado` (no 3; "especialista
  vs. no especialista" es irreconstruible con los datos actuales, se
  perdió al anonimizar la encuesta). Se deriva por matching numérico
  (con tolerancia, no igualdad estricta de floats) del triplete
  `(económico, progresismo, populismo)` de cada fila contra dos
  conjuntos de referencia: `v_party_argentina_2011_2019_espaniol.csv`
  (real) y las filas sin `#` de `v_party_propio.csv` (estimado). Lo que
  no matchee ninguno de los dos queda `sin_clasificar` (no se adivina) —
  puede pasar en los ~10 casos de "mapeos por similitud" con origen no
  documentado (ver README de v-party).
- **Cargo vs. Nivel**: solo Nivel + Año (sin el toggle Cargo/Nivel del
  mapa) — los PNG V-Party solo existen por nivel unificado, nunca por
  cargo suelto, y no hay necesidad de introducir cálculo sin contraparte
  validada.

## Diseño acordado

### Archivos nuevos

- `src/analisis/distribucion_ideologica_interactiva.py` (mismo patrón
  que `mapa_interactivo.py`: `construir_payload()` →
  `generar_distribucion_interactiva()` → `main()`)
- `src/analisis/distribucion_ideologica_template.html` (mismo esqueleto
  visual/CSS que `mapa_interactivo_template.html`)
- Salida: `docs/distribucion_ideologica_la_plata.html`

### Funciones reusadas tal cual (cero cambios)

- De `vparty_cuadrantes_local.py`: `tabla_distrito()`,
  `cargar_posiciones_propias()`, `cargar_filiaciones()`,
  `_color_por_partido()`.
- De `mapa_interactivo.py`: `_cargar_geojson_circuitos()`,
  `_redondear_coords()`, `_cargar_localidades()`.
- De `electoral.localidades`: `cargar_circuito_localidad_geo()`.
- De `analisis.graficos`: `_COLOR_FILIACION`.
- De `constantes`: `CARGO_LABEL`.

### Función nueva (única lógica nueva, pura, testeable)

`derivar_procedencia_vparty(clasificacion_path, vparty_real_path, vparty_propio_path, tolerancia=5e-4) -> dict[(anio,nivel,agrupacion) -> "real"|"estimado"|"sin_clasificar"]`
— vive en `vparty_cuadrantes_local.py`, junto a las otras funciones `cargar_*`.

### Payload (`docs/distribucion_ideologica_la_plata.html`, `/*__RAW_DATA__*/`)

```json
{
  "geojson": {"...": "..."},
  "circuito_localidad": {"496A": "Villa Elvira"},
  "localidades": [{"nombre": "...", "lat": 0.0, "lon": 0.0}],
  "fam_colors": {"peronistas": "#B2FFFF"},
  "nivel_labels": {"nacional": "Nacional (Presidente / Diputados Nac.)"},
  "distrito": {
    "2023_municipal": {
      "anio": 2023,
      "nivel": "municipal",
      "cargo": "intendente",
      "cargo_label": "Intendente",
      "puntos": [
        {
          "agrupacion": "...",
          "votos": 12345,
          "votos_pct": 34.5,
          "economico": -1.4,
          "progresismo": 1.6,
          "populismo": 0.8,
          "filiacion": "peronistas",
          "color": "#7fd9d9",
          "procedencia": "real"
        }
      ]
    }
  }
}
```

### Template

- Selectores Nivel (3 botones) + Año (`<select>`, poblado dinámicamente
  por nivel) + autoplay — mismo widget que el mapa.
- Mapa: mismo `L.geoJSON` de circuitos, estilo fijo neutro (sin
  choropleth), click → resuelve `circuito_localidad[cid]`.
- Columna derecha: un único `renderColumnaDerecha()` — bubble chart SVG
  (X=económico, Y=progresismo, tamaño=% votos, color=familia
  política+sombra, trazo sólido/punteado según procedencia) cuando no
  hay localidad seleccionada, o el placeholder "Distribución ideológica
  de *{localidad}* — próximamente" cuando sí la hay. Checkbox "excluir
  estimación propia" filtra `puntos` client-side. Tooltip con
  agrupación/votos/%/3 ejes/procedencia. Leyenda de familia política +
  procedencia.

### Integración y validación

- `docs/index.html`: nuevo `viz-card` en sección 01.
- `docs/FUNCIONALIDADES.md`: nueva subsección, aclarando explícitamente
  que nivel-localidad está pendiente y que `procedencia` es derivada (no
  es una columna del CSV).
- Tests nuevos para `derivar_procedencia_vparty()` (pura, sin red/HTML),
  mismo criterio que `test_mapa_interactivo.py`.
- Validación manual: 2-3 combinaciones año/nivel, comparando `puntos`
  del payload contra las filas que produce `tabla_distrito()` para ese
  mismo (año, nivel) — mismo dato, así que la única diferencia posible
  sería un bug en el join de color/procedencia, no en los números base.

## Estado

**Implementado, con dos ajustes post-entrega pedidos por Ivan:**

1. **Reubicación**: ambos generadores de HTML interactivo del sitio
   (`mapa_interactivo.py` + su template, y
   `distribucion_ideologica_interactiva.py` + su template) se movieron a
   un módulo nuevo `src/visualizacion/`, separado de `src/analisis/`
   (que queda solo para los scripts que bulk-escriben PNG/Markdown a
   `graficos/`). Tests de `mapa_interactivo` se movieron con él a
   `tests/visualizacion/`. `CLAUDE.md`, `README.md`, `docs/FUNCIONALIDADES.md`
   y los skills `laplata-general`/`laplata-elecciones`/`laplata-geolocalizacion`
   quedaron actualizados con el path nuevo.
2. **Se revirtió por completo la distinción real/estimado en esta
   pestaña**: el checkbox "excluir estimación propia", el trazo
   sólido/punteado por procedencia y las filas de leyenda
   correspondientes se eliminaron del template. `derivar_procedencia_vparty()`
   (la función que se había agregado a `vparty_cuadrantes_local.py` para
   esto) y sus tests también se eliminaron por completo -- quedó sin
   ningún consumidor tras sacar el filtro, y el pedido explícito fue que
   esa separación **no aparezca en ningún lado de la app**, solo en
   `data/agrupaciones/v-party/README.md` (donde ya vivía, en prosa,
   desde antes de este plan). Todos los puntos del bubble chart se ven
   igual ahora, sin importar la fuente del valor V-Party.

Validado: `pytest` completo (322 tests), payload cruzado a mano contra
`tabla_distrito()`, y una pasada headless con Playwright (sin errores de
consola, los tres niveles renderizan, el click en circuito resuelve
localidad y muestra el placeholder, autoplay funciona, no queda rastro
del checkbox ni de "procedencia"/"estimación" en la leyenda).
