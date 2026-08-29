# Gráfico de cuadrantes V-Party: qué indica cada punto

Documenta `src/analisis/vparty_cuadrantes.py`, que genera
`graficos/agrupaciones/vparty_cuadrantes_economico_progresismo_populismo.png`
a partir de `data/agrupaciones/v-party/v_party_argentina_2001_2019_espaniol.csv`
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

## Cobertura: 46 de 56 filas partido-elección

De las 56 filas partido-elección del CSV fuente (2001-2019), 10 quedan
fuera del gráfico por no tener ninguna de las variables de posicionamiento:

- **3 partidos 2011** (`Generation for a National Encounter`, `Popular
  Union`, `Socialist Party`) no llegaron al umbral de cobertura de
  expertos de V-Party (tampoco tienen `v2pavote`).
- **7 alianzas** (`Aliance for Work, Justice, and Education` en 2001,
  `Let's change`/Cambiemos en 2015/2017/2019, `alliance: United for a New
  Alternative` en 2015 y `alliance: Frente de Todos` en 2019, más la
  restante sin columna propia) no tienen valor directo: V-Party codifica
  la identidad de los partidos que integran cada alianza por separado
  (`Radical Civic Union`/UCR y `Justicialist [Peronist] Party`/PJ dentro
  de la Alianza 2001; `Republican Proposal`/PRO y `Radical Civic
  Union`/UCR dentro de Cambiemos; `Front for Victory`/FPV-PJ y `Frente
  Justicialista`/PJ dentro de Frente de Todos), no la alianza como
  entidad.

## Fusión de puntos cercanos del mismo partido

Un mismo partido aparece hasta 9 veces (una por elección 2001–2019), y en
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
  fusionados, p. ej. **"FPV-PJ 2005-2007-2009-2011-2013-2015"** o **"PRO
  2009-2011-2013-2015-2017-2019"** (el caso extremo: seis elecciones de
  PRO son mutuamente cercanas entre sí).
- Un partido puede tener a la vez un punto fusionado y uno o más puntos
  sueltos, o incluso dos grupos fusionados separados, si alguna elección
  (o tramo de elecciones) se aleja del resto — p. ej. **UCR
  2001-2003-2005-2007-2009-2011** fusionado por un lado y **UCR
  2015-2017-2019** fusionado por otro (dos épocas distintas del partido);
  o **RF 2013-2015-2017** fusionado, con **RF '19** aparte porque ese año
  se desplazó lo suficiente en el eje de progresismo.
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
`vparty_populismo`) también viven en
`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` (151 de 313
filas), combinando V-Party real con una estimación propia por encuesta de
expertos calibrada para caer en la misma escala — mismo modelo, así que
los consumidores de esa columna (`vparty_cuadrantes_local.py`, etc.) no
necesitan distinguir el origen. El detalle de qué fila viene de qué
fuente y bajo qué criterio vive **solo** en
`data/agrupaciones/v-party/README.md` — no se repite acá.
