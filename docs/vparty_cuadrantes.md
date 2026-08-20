# Gráfico de cuadrantes V-Party: qué indica cada punto

Documenta `src/analisis/vparty_cuadrantes.py`, que genera
`graficos/agrupaciones/vparty_cuadrantes_economico_progresismo_populismo.png`
a partir de `data/agrupaciones/v-party/v_party_argentina_2011_2019.csv`
(ver el README de esa carpeta para la procedencia del dataset V-Party). No
es parte del pipeline de notebooks 01→04 

Comando para regenerarlo:

```bash
PYTHONPATH=src python -m analisis.vparty_cuadrantes
```

## Qué es cada punto

La unidad de análisis de V-Party es **partido-elección** (un partido, en
una elección puntual). Antes de graficar, el
script calcula tres valores por partido-elección:

| Eje/tamaño | Columna V-Party | Rango | Qué significa |
|---|---|---|---|
| **Eje X** (`economico`) | `v2pariglef` tal cual | continuo, centrado en 0 | Negativo = izquierda/estatismo económico (más regulación, impuestos, gasto social). Positivo = derecha/mercado (privatización, menos impuestos, menos regulación). Es un único índice V-Dem que fusiona regulación económica **y** política fiscal — el codebook no las separa, así que este gráfico tampoco. |
| **Eje Y** (`progresismo`) | promedio de `v2pawomlab` + `v2palgbt` + `v2paimmig` + `v2parelig` | continuo, centrado en 0 (cada componente ya lo está) | Positivo = progresista (mujeres en el mercado laboral, derechos LGBT, inmigración, no confesional). Negativo = conservador. **No es una columna nativa de V-Party** — es un promedio simple construido para este gráfico; V-Party no publica un índice social único. |
| **Tamaño del punto** (`populismo`) | `v2xpa_popul` tal cual | índice derivado, acotado 0–1 por construcción | Más grande = discurso más antagonista pueblo-vs-élite. No es un tercer eje espacial a propósito: dos ejes cruzados + tamaño evita el error de graficar tres ejes espaciales al mismo tiempo. |

Las líneas de cuadrante están en `x=0` (centro por construcción del índice
económico) y en `y=0` (centro por construcción del promedio de las cuatro
variables sociales, cada una ya centrada en 0 individualmente) — no son
cortes estadísticos arbitrarios sobre la muestra, son los centros teóricos
de cada escala.

`obtener_tuplas()` expone el diccionario completo
`{(sigla, año): (economico, progresismo, populismo)}` por si se necesita
graficar otro par de ejes sin recalcular.

## Cobertura: 26 de 35 filas partido-elección

De las 35 filas partido-elección del CSV fuente, 9 quedan fuera del gráfico por no tener ninguna de las
variables de posicionamiento:

- **3 partidos 2011** (`Generation for a National Encounter`, `Popular
  Union`, `Socialist Party`) no llegaron al umbral de cobertura de
  expertos de V-Party (tampoco tienen `v2pavote`).
- **6 alianzas** (`Let's change`/Cambiemos en 2015/2017/2019 y
  `alliance: Frente de Todos` en 2019, más las otras dos alianzas sin
  columna propia) no tienen valor directo: V-Party codifica la identidad
  de los partidos que integran cada alianza por separado (`Republican
  Proposal`/PRO y `Radical Civic Union`/UCR dentro de Cambiemos; `Front
  for Victory`/FPV-PJ y `Frente Justicialista`/PJ dentro de Frente de
  Todos), no la alianza como entidad.

## Fusión de puntos cercanos del mismo partido

Un mismo partido aparece hasta 5 veces (una por elección 2011–2019), y en
varios casos su posición prácticamente no se mueve de una elección a la
otra — graficar cada año por separado sólo agrega puntos superpuestos sin
información nueva. `_fusionar_por_cercania()` colapsa esos casos en un
solo punto:

- Agrupa por partido (`v2pashname`) y arma componentes conexas: dos
  elecciones del mismo partido quedan en el mismo grupo si su distancia
  normalizada (fracción del rango de cada eje) es menor a
  `UMBRAL_FUSION = 0.05` en **ambos** ejes a la vez.
- La unión es transitiva (si A está cerca de B y B cerca de C, las tres
  quedan juntas aunque A y C no lo estén directamente) — así una fuerza
  que se desplaza gradualmente de elección en elección no queda partida
  en dos grupos por un corte arbitrario.
- El punto resultante **promedia** posición (`economico`, `progresismo`)
  y populismo de las elecciones fusionadas, y la etiqueta lista los años
  fusionados, p. ej. **"FPV-PJ 2011-2013-2015"** o **"PRO
  2011-2013-2015-2017-2019"** (el caso extremo: los cinco años de PRO son
  mutuamente cercanos entre sí).
- Un partido puede tener a la vez un punto fusionado y uno o más puntos
  sueltos si alguna elección se aleja del resto — p. ej. **RF
  2013-2015-2017** fusionado, con **RF '19** aparte porque ese año se
  desplazó lo suficiente en el eje de progresismo.
- Los puntos fusionados se pintan en **gris neutro** (`COLOR_FUSIONADO =
  "#4d4d4d"`, leyenda "2+ elecciones (posición promedio)"), a diferencia
  de los puntos de una sola elección, que mantienen el color por año
  (`COLOR_POR_ANIO`). Esto es intencional: un punto fusionado ya no
  representa una elección puntual, así que no tiene sentido pintarlo del
  color de ninguna de ellas.

El mismo criterio de cercanía normalizada (`_asignar_offsets`, con su
propio umbral independiente) reparte las etiquetas de texto entre
posiciones candidatas alternando lado izquierda/derecha para que dos
puntos cercanos no terminen con las etiquetas apiladas una sobre otra.

## Integración con `clasificacion_ideologica_agrupaciones.csv`

Las mismas tres variables (`vparty_economico`, `vparty_progresismo`,
`vparty_populismo`) se agregaron como columnas nuevas a
`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` — el archivo
hand-curated que ya trae `campo_ideologico`/`filiacion_politica` por
agrupación/año/nivel (ver `CLAUDE.md`, sección `data/agrupaciones/`: ese
archivo **nunca se regenera desde cero**, se edita a mano). Esta carga es
puntual (no hay un script que la repita automáticamente ni la mantenga
sincronizada — si se agregan filas nuevas a `clasificacion_ideologica_agrupaciones.csv`
o se corrige `oficialismos.csv`, hay que reaplicar el criterio de abajo a
mano), igual que la edición manual de `campo_ideologico`/`filiacion_politica`
en ese mismo archivo. **62 de 313 filas tienen las tres variables
pobladas**, por tres fuentes (1 y 2 no se mezclan, una prevalece sobre la
otra cuando ambas aplicarían; 3 es una extensión explícita de 1 para casos
sin superposición de año; ver cada una abajo) más un puñado de filas
cargadas a mano fuera de cualquiera de las tres:

**1 — Cruce directo con V-Party** (`v_party_argentina_2011_2019_espaniol.csv`),
por nombre exacto de agrupación normalizado (mayúsculas, sin acentos, sin
puntuación) en el mismo año — 8 partidos:

| Año | `agrupacion` en este repo | Partido V-Party |
|---|---|---|
| 2011 | ALIANZA FRENTE AMPLIO PROGRESISTA | alianza: Frente Amplio Progresista (el prefijo `alianza:` de V-Party ≡ la convención local `ALIANZA <NOMBRE>`) |
| 2013 | FRENTE PARA LA VICTORIA | Front for Victory (FPV-PJ) |
| 2013 | FRENTE PROGRESISTA CIVICO Y SOCIAL | Progressive, Civic and Social Front (FPCyS) |
| 2013 | FRENTE RENOVADOR | Renewal Front (RF) |
| 2015 | FRENTE PARA LA VICTORIA | Front for Victory (FPV-PJ) — fila distinta de "ALIANZA FRENTE PARA LA VICTORIA" (también 2015, sin match propio, ver abajo) |
| 2017 | FRENTE JUSTICIALISTA | Frente Justicialista-Justicialist [Peronist] Party (FP-PJ) |
| 2017 | UNIDAD CIUDADANA | Citizen's Unity (CU) |
| 2019 | CONSENSO FEDERAL | Consensus Federal (CF) |

**2 — Proxy de la ola V-Party más cercana, cuando no hay superposición de
año.** Caso: **COALICIÓN CÍVICA ARI / COALICIÓN CÍVICA - AFIRMACIÓN PARA
UNA REPÚBLICA IGUALITARIA ARI / COALICIÓN CÍVICA - A.R.I.** — mismo
partido, tres grafías del nombre en distintos años de este repo (2011:
gobernación/intendente/presidente; 2025: nacional), en años donde
V-Party **no** tiene ola propia (V-Party sólo cubre 2015/2017/2019 para
este partido). Se usó la ola más cercana disponible en cada dirección:
2011 toma el valor de **2015** (la primera ola, hacia atrás en el
tiempo — no hay ola anterior para "prestar"), 2025 toma el valor de
**2019** (la última ola, hacia adelante — mismo criterio de arrastre que
ya usa `oficialismos.csv` para 2021+, fuente 2 arriba). El eje económico
de este partido no se mueve entre 2015/2017/2019 (`v2pariglef = 0.452`
las tres olas), lo que da algo más de confianza al proxy hacia atrás que
si hubiera tendencia marcada; el eje de progresismo sí varía año a año
(0.299 en 2015, usado para 2011; 0.288 en 2019, usado para 2025) — es una
aproximación, no un dato medido para esos años puntuales, a diferencia de
las fuentes 1 y 2.

**Casos con fila propia en `clasificacion_ideologica_agrupaciones.csv`
pero deliberadamente sin completar** (ninguna de las tres fuentes
aplica y no se cargaron a mano):

- **UCR (Unión Cívica Radical) y PRO (Propuesta Republicana)**: V-Party
  los cubre 2011-2019, pero en `clasificacion_ideologica_agrupaciones.csv`
  nunca corren como línea propia — siempre están fusionados dentro de una
  alianza más grande (CAMBIEMOS BUENOS AIRES, JUNTOS POR EL CAMBIO,
  JUNTOS) que sí tiene fila, cubierta por la fuente 2 usando PRO como
  proxy (ver arriba). No hay ninguna fila "UNION CIVICA RADICAL" ni
  "PROPUESTA REPUBLICANA"/"PRO" sueltas contra las cuales adjuntar el
  valor de V-Party directamente.
- **ALIANZA FRENTE PARA LA VICTORIA (2015)**: fila hermana de `FRENTE
  PARA LA VICTORIA` 2015 (completada vía fuente 1), pero con un nombre
  distinto en el que V-Party no tiene una fila propia exacta que la
  respalde.
- **Peronismo Federal/Peronismo Disidente**: V-Party lo cubre 2011, pero
  no hay ninguna fila con ese nombre (ni una traducción razonable de él)
  en `clasificacion_ideologica_agrupaciones.csv` ningún año.

No se generaron filas nuevas para llenar estos huecos ni se aproximó
ningún valor por fuera de las fuentes 1 y 2.

### Advertencia metodológica adicional

V-Party codifica la posición de cada partido a escala **nacional**