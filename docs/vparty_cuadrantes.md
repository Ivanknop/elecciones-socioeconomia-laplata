# Gráfico de cuadrantes V-Party: qué indica cada punto

Documenta `src/analisis/vparty_cuadrantes.py`, que genera
`graficos/agrupaciones/vparty_cuadrantes_economico_progresismo_populismo.png`
a partir de `data/agrupaciones/v-party/v_party_argentina_2011_2019.csv`
(ver el README de esa carpeta para la procedencia del dataset V-Party). No
es parte del pipeline de notebooks 01→04 (esa capa es exclusivamente
electoral/circuito); es un análisis aparte sobre el posicionamiento
programático de los partidos, a escala nacional.

Comando para regenerarlo:

```bash
PYTHONPATH=src python -m analisis.vparty_cuadrantes
```

## Qué es cada punto

La unidad de análisis de V-Party es **partido-elección** (un partido, en
una elección a Diputados Nacionales puntual). Antes de graficar, el
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

De las 35 filas partido-elección del CSV fuente (Diputados 2011, 2013,
2015, 2017, 2019), 9 quedan fuera del gráfico por no tener ninguna de las
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
archivo **nunca se regenera desde cero**, se edita a mano). Esta carga fue
puntual (no hay un script que la repita automáticamente), igual que la
edición manual de `campo_ideologico`/`filiacion_politica` en ese mismo
archivo.

**El cruce sólo pudo poblar 6 de las 26 filas partido-elección con datos
de V-Party**, uniendo por `(año, nivel="nacional", agrupacion)` contra el
nombre exacto del partido en V-Party:

| Año | `agrupacion` en este repo | Partido V-Party |
|---|---|---|
| 2013 | FRENTE PARA LA VICTORIA | Front for Victory (FPV-PJ) |
| 2013 | FRENTE PROGRESISTA CIVICO Y SOCIAL | Progressive, Civic and Social Front (FPCyS) |
| 2013 | FRENTE RENOVADOR | Renewal Front (RF) |
| 2017 | UNIDAD CIUDADANA | Citizen's Unity (CU) |
| 2017 | FRENTE JUSTICIALISTA | Frente Justicialista-Justicialist [Peronist] Party (FP-PJ) |
| 2017 | 1PAIS | Renewal Front (RF) — la alianza de Sergio Massa en 2017 |

Las otras 20 filas de V-Party quedan sin fila para adjuntar, por dos
motivos estructurales de este repo (no del dataset V-Party):

1. **`clasificacion_ideologica_agrupaciones.csv` no tiene ninguna fila
   con `nivel="nacional"` para 2011, 2015 ni 2019** — por diseño, este
   repo sólo releva la categoría legislativa nacional (Diputados) en los
   años sin elección ejecutiva concurrente (2013, 2017, 2021, 2025; ver
   `CLAUDE.md`: "legislative offices ... 2013-2025"). V-Party sí cubre
   Diputados en años de elección presidencial (2011, 2015, 2019), pero
   este repo no releva esa categoría esos años — no es un dato faltante
   por error, es el alcance declarado del repo.
2. **En 2017, PRO/UCR/Coalición Cívica compitieron en una sola línea
   fusionada** ("CAMBIEMOS BUENOS AIRES" en este repo), mientras que
   V-Party codifica cada partido de la alianza por separado — el mismo
   patrón, ya documentado, que excluye a Cambiemos y Frente de Todos del
   propio gráfico (ver sección anterior). No hay una fila de "PRO",
   "UCR" o "Coalición Cívica" sueltas en 2017 contra la cual adjuntar el
   valor de V-Party.

No se generaron filas nuevas para llenar estos huecos ni se aproximó el
valor con otro `nivel` (p. ej. `gobernacion`): las tres variables de
V-Party están calculadas específicamente para la elección a Diputados
Nacionales, y adjuntarlas a la fila de otro cargo del mismo año
implicaría atribuirle a esa categoría un valor que no le corresponde.

### Advertencia metodológica adicional

V-Party codifica la posición de cada partido a escala **nacional**
(típicamente a partir de su distrito más relevante para el partido, no
necesariamente Provincia de Buenos Aires). El resto de este repo trabaja
a escala de **circuito electoral de La Plata**. Aun en las 6 filas donde
el nombre de la lista coincide exactamente, el valor de V-Party describe
la identidad programática nacional del partido, no una medición
específica de su desempeño o discurso en La Plata — tratarlo como
equivalente a `campo_ideologico` (que sí es una clasificación pensada
para este dataset electoral) sería forzar una equivalencia que no está
garantizada. Se deja como referencia cruzada, no como reemplazo.
