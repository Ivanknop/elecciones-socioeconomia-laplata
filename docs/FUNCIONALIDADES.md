# Funcionalidades — Análisis Política y Economía (La Plata)

Referencia detallada de cada módulo, script y decisión de diseño del
repositorio. `README.md` (raíz) es la puerta de entrada — estructura,
instalación, orden de reproducción; este documento es donde vive el
detalle operativo de cada pieza, para que el README no tenga que crecer
sin límite.

## Índice

1. [El cliente (`src/electoral/client.py`)](#el-cliente-srcelectoralclientpy)
2. [El modelo de dominio (`src/electoral/models.py`)](#el-modelo-de-dominio-srcelectoralmodelspy)
3. [Alcance de los datos ya descargados](#alcance-de-los-datos-ya-descargados)
4. [Totales por circuito](#totales-por-circuito)
5. [Resultado total por agrupación (`src/electoral/totales.py`)](#resultado-total-por-agrupación-srcelectoraltotalespy)
6. [Gráficos (`src/analisis/`, salida en `graficos/`)](#gráficos-srcanalisis-salida-en-graficos)
7. [PASO y balotaje](#paso-y-balotaje)
8. [Libro de códigos ideológico — estado actual](#libro-de-códigos-ideológico--estado-actual)
9. [Distribución ideológica interactiva (`src/visualizacion/distribucion_ideologica_interactiva.py`)](#distribución-ideológica-interactiva-srcvisualizaciondistribucion_ideologica_interactivapy)
10. [Trayectorias económicas trimestrales (`src/visualizacion/trayectorias_economicas.py`)](#trayectorias-económicas-trimestrales-srcvisualizaciontrayectorias_economicaspy)
11. [Trayectorias económicas bielección trimestrales (`src/visualizacion/trayectorias_economicas_bieleccion.py`)](#trayectorias-económicas-bielección-trimestrales-srcvisualizaciontrayectorias_economicas_bieleccionpy)
12. [Capa socioeconómica (EPH + Censo) — estado actual](#capa-socioeconómica-eph--censo--estado-actual)
13. [Agrupación de resultados por localidad — estado actual](#agrupación-de-resultados-por-localidad--estado-actual)
14. [Capa macroeconómica nacional — estado actual](#capa-macroeconómica-nacional--estado-actual)
15. [Extender a otro distrito, sección o cargo](#extender-a-otro-distrito-sección-o-cargo)

---

## El cliente (`src/electoral/client.py`)

`ResultadosClient` envuelve dos endpoints distintos de la misma API:

- **`get_resultados(...)`** → `GET /api/resultados/getResultados`. Devuelve el
  JSON crudo totalizado (agregado o de una mesa puntual, según los parámetros).
  Parámetros: `anio_eleccion`, `tipo_eleccion` (1=PASO, 2=Generales,
  3=Segunda vuelta), `categoria_id`, y opcionalmente
  `distrito_id`/`seccion_provincial_id`/`seccion_id`/`circuito_id`/`mesa_id`.
- **`get_resultados_csv(...)`** → `GET /api/resultado/totalizadocsv`. Es el
  mismo mecanismo que arma el CSV descargable desde el sitio: trae **todas las
  mesas de la categoría pedida en un solo request**, ya con columna `mesa_id`.
  Este endpoint **no está en la documentación pública** de la API; se descubrió
  leyendo el bundle JS del sitio (`app.js`). Usa nombres de parámetro
  distintos al endpoint JSON (`año`, `recuento="Provisorio"`, `idEleccion`,
  `idCargo`, `idDistrito`, `idSeccionProvincial`, `idSeccion`).
- **`iter_mesas(...)`** → itera un rango de `mesaId` llamando a
  `get_resultados` una vez por mesa. Sirve para exploración/validación
  puntual, pero **no es el camino recomendado para traer datos**: el CSV ya
  trae todas las mesas en un pedido, es más rápido y no genera cientos de
  archivos de caché.

## El modelo de dominio (`src/electoral/models.py`)

`ResultadoElectoral.from_json(raw, consulta=...)` parsea el JSON crudo a
dataclasses tipadas: `EstadoRecuento`, `ValorAgrupacion` (con `listas:
list[Lista]`), `ValoresOtros`. Cada nivel tiene un campo `extra: dict` que
junta cualquier key del JSON que no esté modelada explícitamente — así, si la
API agrega un campo nuevo, aparece ahí en vez de romper el parseo o perderse
en silencio.

## Alcance de los datos ya descargados

`data/distrito/<2011|2015|2019|2023>/<presidente|gobernador|intendente>/generales/`,
cada una con 2 archivos: el agregado de la sección (`.json`) y el CSV oficial
(`.csv`) — más `paso/` y, para Presidente, `balotaje/` (ver "PASO y balotaje"
más abajo). Todo scopeado a **La Plata**:

- `distritoId=2` → Buenos Aires
- `seccionProvincialId=8` → Sección Capital
- `seccionId=63` → La Plata
- `tipoEleccion=2` → Generales

Y el mapeo de categoría, **estable en los cuatro años para esta sección**:

| categoriaId (`idCargo`) | cargo       |
|---|---|
| 1 | PRESIDENTE |
| 4 | GOBERNADOR |
| 7 | INTENDENTE |

### Legislativas (2013-2025)

`data/distrito/<2013|2017|2021|2025>/<nacional|provincial|municipal>/generales/`. Mismo
distrito/sección que arriba. `idCargo` estable en los cuatro años para La
Plata:

| idCargo (`categoriaId`) | cargo | nivel |
|---|---|---|
| 2 | Senador Nacional | nacional |
| 3 | Diputado(s) Nacional(es) | nacional |
| 5 | Senadores Provinciales | provincial |
| 6 | Diputado(s) Provincial(es) | provincial |
| 10 | Concejales | municipal |

El notebook 03 agrega, al mismo
`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` que genera
el notebook 02, filas con `nivel` en `nacional`/`provincial`/`municipal`
(`anio`, `agrupacion`, `nivel`; el archivo en disco tiene además
`campo_ideologico`, agregado a mano — ver "Libro de códigos ideológico" más
abajo). Cuando un nivel tuvo dos cargos el mismo año, sus agrupaciones se
juntan bajo ese `nivel` y se deduplican.

## Totales por circuito

`data/distrito/<año>/<nivel>/<etapa>/circuito_<nivel>.json` — agrega, por
`circuito_id`, los positivos por agrupación y los "otros"
(blanco/nulo/recurrido/impugnado/comando, lo que exista ese año). Sale del
CSV oficial. `etapa` es `generales`, `paso` o `balotaje` — las tres se
construyen con la misma lógica (notebook 04, secciones 1-5 para Generales,
6-7 para PASO/balotaje), pero PASO y balotaje solo existen para los (año,
nivel) donde efectivamente hubo esa instancia (ver "PASO y balotaje" más
abajo) — la disponibilidad se detecta chequeando si el CSV crudo de esa
etapa ya está cacheado en disco, no una lista fija a mano.

**`circuito_id`**: el mismo circuito se identifica con distinto
ancho/relleno de ceros según el año (`"0460"` en 2011/2015, `"000460"` en
2019, `"00460"` en 2023). El notebook 04 normaliza a una forma canónica (sin
ceros a la izquierda, conservando cualquier sufijo de letra por subdivisión,
ej. `"0496F"` → `"496F"`) **antes** de agregar, y usa esa forma como clave en
`circuitos`. La correspondencia entre el id crudo de cada año y el canónico
queda versionada en `data/agrupaciones/circuito_id_correspondencias.csv`. De
los circuitos de La Plata, un subconjunto no es común a todos los años
procesados (`493`, `496F`, `504C` en esta ejecución).

`2017/nacional` tuvo dos cargos ese año (Senador Nacional idCargo=2, solo
2017; Diputados Nacionales idCargo=3, todos los años) compartiendo la misma
carpeta. `circuito_nacional.json` usa Diputados Nacionales, por ser el
consistente en los 4 años legislativos — Senador Nacional 2017 queda afuera
de este archivo.

Cada agrupación dentro de `positivos` suma el campo `campo_ideologico`,
copiado tal cual de `clasificacion_ideologica_agrupaciones.csv`
(join exacto por año/nivel/nombre; `"gobernador"` se mapea a
`"gobernacion"`). Si una agrupación no aparece en el CSV de clasificación,
el notebook falla con `KeyError` en vez de guardar el circuito sin el
campo.

Cada circuito también trae `mesas_sin_votos_positivos`: cuántas de sus mesas
no tienen ningún voto positivo (37 en Presidente 2023, 47 en Gobernador e
Intendente 2023, en 26 circuitos). Es una señal a revisar (puede ser padrón
sin categoría —p. ej. electores extranjeros en cargos nacionales— o una mesa
todavía no escrutada al momento de la consulta), **no** una clasificación
automática: no se decide la causa por código, se deja el número para
revisión manual.

Cada archivo trae además tres campos de procedencia/cobertura, a nivel de
todo el (año, nivel):

- `fuente`: siempre `"csv"` — el pipeline usa el CSV oficial, no el JSON
  agregado, para construir `circuito_<nivel>.json` (ver anomalía 2019 abajo).
- `coincide_con_agregado_json` / `advertencia_fuente`: si la suma por
  circuito no coincide exactamente con el JSON agregado de la misma
  consulta, `advertencia_fuente` explica por qué (hoy, el único caso es
  Presidente 2019 — ver más abajo).
- `cobertura`: los campos de `estadoRecuento` que ya expone la API
  (`EstadoRecuento`, `src/electoral/models.py`) para todo el (año, nivel):
  `mesas_totalizadas`, `cantidad_electores`, `cantidad_votantes`,
  `participacion_porcentaje`. **`mesas_esperadas` y
  `mesas_totalizadas_porcentaje` están siempre en `0`** en los datos ya
  descargados: la API no los completa para elecciones cerradas/históricas
  (solo tendrían valor en una consulta en vivo), así que no sirven hoy para
  calcular un % de cobertura real — quedan igual en el archivo, sin
  recalcularlos, para no inventar un dato que la fuente no da.

### Anomalía conocida: JSON agregado de Presidente 2019

El JSON agregado crudo cacheado para Presidente 2019
(`data/distrito/2019/presidente/generales/tipoEleccion-2_categoriaId-1_..._.json`) reporta 96
mesas totalizadas y 27.567 votos positivos; el CSV oficial de la misma
consulta tiene 1.517 mesas y 418.164 votos positivos (~16x más). El dato
analítico (`circuito_presidente.json`) ya está bien porque sale del CSV, no
del JSON agregado — pero ese JSON agregado sigue en el repo tal cual se
cacheó, sin corregir, porque es el crudo devuelto por la API en su momento.
`circuito_presidente.json` de 2019 documenta esto mismo con
`"coincide_con_agregado_json": false` y una `"advertencia_fuente"` explícita.
Ningún paso del pipeline debería tomar los totales de ese JSON agregado.

### Anomalía conocida: circuito 508G (2013) con más votos que electores

Al calcular `ausentismo` (`electores` del circuito menos sus votos válidos —
ver sección "Gráficos" más abajo) surgió un caso puntual: el circuito
`508G`, en los tres cargos legislativos de 2013 (`municipal`, `nacional`,
`provincial`, que comparten mesas), tiene más votos emitidos que `electores`
registrados (ej. `municipal`: 619 votos vs. 429 electores, `ausentismo` =
-190). `508G` es parte de la familia de circuitos subdivididos 504/505/508/509
sin resolución equivalente a la 1990/2007 (ver skill `laplata-elecciones`,
"Gaps conocidos"), consistente con un problema de asignación de `mesa_electores`
entre subdivisiones más que con un error de conteo de votos. No se corrigió
el dato: `graficar_torta` detecta cualquier categoría negativa y muestra un
aviso en vez de graficar la torta para ese circuito puntual (una torta no
puede representar un gajo negativo); `graficar_barras` sí puede, y el bar
label muestra el valor y % negativos tal cual.

### Anomalía conocida: PASO 2013 legislativas, mesas/electores por debajo del agregado

`circuito_nacional.json`/`circuito_provincial.json`/`circuito_municipal.json`
de PASO 2013 quedan con `coincide_con_agregado_json: false`, pero **no por
los votos**: `positivos` y `otros` suman exactamente lo mismo que el JSON
agregado (nacional 2013: 354.290 positivos y 29.149 "otros" en ambas
fuentes). La diferencia está en `mesas`/`electores`: sumando el `cobertura`
de todos los circuitos da 1.524 mesas y 524.733 electores, contra 2.550
mesas y 878.293 electores que informa el agregado — como si al CSV oficial
le faltaran filas de mesas enteras (sin ningún voto, ni siquiera en blanco)
para esta categoría puntual. Es un tipo de discrepancia distinto al de
Presidente 2019 (ahí el agregado subestimaba los votos; acá los votos están
bien, falta cobertura de mesas/electores). No se investigó la causa raíz
todavía — no usar la `cobertura` de estos tres archivos de PASO 2013 para
calcular `ausentismo` sin tener esto presente; los tres quedan igual con
`advertencia_fuente` explícita.

## Resultado total por agrupación (`src/electoral/totales.py`)

`data/totales/<nivel>/<año>/resultado_total.csv` — una fila por agrupación
con el total de votos de todo (año, nivel) en La Plata para **Generales**,
sumando los circuitos de `circuito_<nivel>.json` (no el JSON agregado
crudo, por la misma razón que "Totales por circuito" más arriba: ese
agregado subestima Presidente 2019). Columnas: `id_agrupacion`,
`agrupacion`, `votos`, `votos_porcentaje` (recalculado sobre el total de
esa consulta, no heredado de otra).

**PASO y balotaje** usan el mismo formato, en
`data/totales/<nivel>/<año>/<etapa>/resultado_total.csv` (subcarpeta
hermana de la ruta de Generales, que no cambia) — solo para los (año,
nivel) donde esa etapa existió (ver "PASO y balotaje" más abajo);
`_combos_disponibles` los descubre igual que a Generales, buscando
cualquier `circuito_<nivel>.json` bajo `data/distrito/`, no una lista fija.

La suma se hace con `electoral.models.totalizar_agrupaciones`, una función
de propósito general: combina cualquier lista de
`ValorAgrupacion` por `id_agrupacion` -- sirve igual para totalizar mesas,
circuitos, o cualquier otro nivel de detalle que use ese mismo dataclass.

```bash
PYTHONPATH=src python -m electoral.totales --anio 2023 --nivel intendente                # solo Generales de ese (año, nivel)
PYTHONPATH=src python -m electoral.totales --anio 2023 --nivel intendente --etapa paso    # solo PASO de ese (año, nivel)
PYTHONPATH=src python -m electoral.totales                    # todo lo disponible -- generales + paso + balotaje
```

## Gráficos (`src/analisis/`, salida en `graficos/`)

Barras y torta por **campo ideológico** (izquierda → derecha radical, con
una paleta divergente azul↔rojo — es un dato de polaridad, no de identidad),
a partir de `circuito_<nivel>.json`.

**Todo gráfico de `src/analisis/` que desglosa por campo ideológico o
filiación política suma siempre dos muestras más, en gris para no competir
con la paleta de ideología**: `blanco_nulo` (votos en blanco + nulos — fue a
votar, no eligió agrupación) y `ausentismo` (`electores` del circuito/nivel
menos sus votos válidos — no fue a votar). `ausentismo` resta también los
procedimentales del año (recurridos/impugnados/comando), aunque esos no se
grafican como categoría propia (`graficos._votos_no_ideologicos`). Como
ahora el total de cada gráfico incluye ausentismo, el % que muestra cada
categoría pasa a ser aproximadamente "% del padrón" en vez de "% de los
positivos".

**Solo `graficos/distrito/serie_temporal/` y `graficos/distrito/comparativos_nivel/`
están versionados en git.** El resto de `graficos/distrito/<año>/<nivel>/`
(circuito por circuito, más el cuadro anual de todos los cargos de ese año)
está en `.gitignore` — se genera on demand con los scripts de abajo y no
hace falta subirlo (son miles de archivos, se regeneran en segundos desde
`data/`). Para la capa socioeconómica, `notebooks/06_graficos_eph_iaelap.ipynb`/
`src/socioeconomia/graficos_eph_iaelap.py` generan tanto los PNG de la EPH
(`graficos/socioeconomia/eph/`) como los de IAELaP y el de contraste
EPH/IAELaP (`graficos/socioeconomia/`) — ninguno de esos PNG está
versionado. Lo que sí está versionado son los JSON de IAELaP que el mismo
notebook escribe junto a sus PNG (`iaelap_general.json`/
`iaelap_sectorial_*.json`, el contrato de datos para reconstruir esos
gráficos, excepción explícita en `.gitignore`).

- **`graficos.py`**: `graficar_barras(data_dir, anio, nivel, circuito_id=None)`
  y `graficar_torta(...)` — devuelven una figura de matplotlib.
  `circuito_id=None` (default) agrega todos los circuitos del (año, nivel);
  pasando un `circuito_id` puntual, grafica solo ese circuito. Son funciones
  para usar sueltas (ej. desde un notebook), no generan archivos por su
  cuenta.
- **`generar_graficos.py`**: script que, dado un `--anio` y un `--nivel`,
  genera **circuito por circuito** (barras + torta) más **un acumulado**
  con el total del (año, nivel) — todo por campo ideológico. Escribe en
  `graficos/distrito/<año>/<nivel>/` — carpeta al mismo nivel que `data/` y
  `src/`, **no** adentro de `data/`: `<circuito_id>_barras.png` /
  `<circuito_id>_torta.png` por cada circuito, y `total_barras.png` /
  `total_torta.png` para el acumulado.

  ```bash
  PYTHONPATH=src python -m analisis.generar_graficos --anio 2011 --nivel intendente
  ```

- **`serie_temporal.py`**: **un gráfico por nivel de gobierno** (nacional /
  provincial / municipal, no por cargo puntual), con una línea por campo
  ideológico cubriendo 2011-2025. Cada nivel combina su cargo
  ejecutivo y su cargo legislativo en una sola serie continua.

  | nivel | ejecutivo | legislativo | puntos | rango |
  |---|---|---|---|---|
  | nacional | Presidente | Diputados Nacionales | 8 | 2011-2025 completo |
  | provincial | Gobernador | Diputados Provinciales | 7 | 2011-2023 (sin 2025 ) |
  | municipal | Intendente | Concejales | 7 | 2011-2023 (sin 2025) |

- **`serie_temporal_filiacion.py`**: mismo formato que `serie_temporal.py`
  (un gráfico por nivel, mismos puntos/rango de la tabla de arriba), pero
  con una línea por `filiacion_politica` (familia/identidad partidaria —
  peronistas, progresistas, liberales, marxistas, nacionalistas, etc., ver
  "Libro de códigos ideológico" más abajo) en vez de `campo_ideologico`
  (posición ideológico-programática por elección). Solo genera la variante
  en porcentaje (`<nivel>_filiacion_porcentaje.png`), no hay versión en
  votos crudos. No modifica `circuito_<nivel>.json` ni el notebook 04: la
  filiación se une en el momento de graficar contra
  `clasificacion_ideologica_agrupaciones.csv`, por nombre de agrupación.

  ```bash
  PYTHONPATH=src python -m analisis.serie_temporal_filiacion
  ```

- **`cuadros_anualizados.py`**: **un gráfico por año** (2011-2025), con todos
  los cargos que se disputaron ese año lado a lado — a diferencia de
  `serie_temporal.py`, acá el eje temporal no existe: es una foto de un año
  puntual, comparando sus propios cargos entre sí. **No suma los cargos entre
  sí** (mismo motivo que el punto anterior: sumar Presidente + Gobernador +
  Intendente sugeriría más comparabilidad de la que hay) — cada cargo es su
  propia serie de barras, con el nombre del cargo en la leyenda. Escribe en
  `graficos/distrito/<año>/<año>_votos.png` y `<año>_porcentaje.png` —
  junto al resto de los gráficos de ese año (`<nivel>/`, circuito por
  circuito), no en una carpeta aparte.

  ```bash
  PYTHONPATH=src python -m analisis.cuadros_anualizados --anio 2023
  ```

- **`totales_por_lista.py`**: ya no genera gráfico propio ni tiene CLI —
  el bar chart por (año, nivel) que antes escribía en
  `graficos/distrito/totales_por_lista/` se retiró por no aportar al nuevo
  enfoque temporal. Sobrevive como capa de datos compartida:
  `resultado_total_con_blanco_nulo(data_dir, anio, nivel)` parte de
  `electoral.totales.resultado_total_por_agrupacion` — la función que
  también arma `data/totales/` — y le agrega una entrada `BLANCO + NULO`,
  **recalculando `votos_porcentaje` sobre el nuevo total** con
  `electoral.models.totalizar_agrupaciones` (no relee `data/totales/`, que
  es agnóstico de blanco/nulo a propósito). La consumen
  `vparty_cuadrantes_local.py`, `comparativo_nivel.py`,
  `distribucion_ideologica_interactiva.py` y
  `ml_models/construir_calendario.py`/`construir_elecciones.py`.

- **`comparativo_nivel.py`**: **un cuadro Markdown por año**, compara el % de cada agrupación (+ `blanco_nulo`) en los tres
  cargos disputados ese año (Municipio/Provincia/Nación, ej. 2019:
  Intendente/Gobernador/Presidente) más las tres diferencias entre pares,
  en puntos porcentuales (pp). El cruce entre categorías es por nombre
  exacto de agrupación — dentro de un mismo año la misma alianza corre bajo
  el mismo nombre en los tres cargos (verificado contra los datos, no
  asumido). Una agrupación que no compitió en alguna categoría queda con
  `—` en esa columna y en sus diferencias, en vez de tratarse como 0%. Las
  filas de partidos se ordenan por % en Nación, de mayor a menor;
  `BLANCO + NULO` queda siempre última. Reutiliza
  `totales_por_lista.resultado_total_con_blanco_nulo` (mismos porcentajes
  que ese cálculo, no uno aparte). Años con un solo cargo
  disputado (2025: solo nacional) no tienen comparación posible y se
  omiten. Escribe en
  `graficos/distrito/comparativos_nivel/<año>.md` —
  versionado (excepción explícita en `.gitignore`, mismo criterio que
  `serie_temporal/`).

  ```bash
  PYTHONPATH=src python -m analisis.comparativo_nivel --anio 2019
  PYTHONPATH=src python -m analisis.comparativo_nivel               # todos los años disponibles
  ```

- **`vparty_distribucion_tfi.py`**: **un PNG por (año, nivel)** con los
  cuadrantes ideológicos V-Party (económico × progresismo, tamaño = % de
  votos, color = familia política) leídos directo de
  `data/tfi_data/elecciones/<año>_<nivel>.csv` — a diferencia del resto de
  esta sección (que arranca de `circuito_<nivel>.json`), cubre **2001-2025**
  porque esos CSV no dependen de tener geometría de circuito. Reemplaza en
  los hechos al generador deprecado
  `analisis.vparty_cuadrantes_local.generar_distrito` (ver CLAUDE.md), pero
  sin extender ese módulo: solo reusa `_color_por_partido`/`_sombras` de
  ahí (aún activas) y define su propio `graficar_cuadrantes_eleccion`.
  Límites de eje fijos y simétricos respecto de 0
  (`limites_globales`, sobre toda la cobertura cargada), calculados una
  sola vez para que los 34 PNG sean comparables entre sí. Escribe en
  `graficos/tfi/v-party/<año>_<nivel>.png` — `.gitignore`d como el resto de
  `graficos/`, no es una de las excepciones versionadas.

  ```bash
  PYTHONPATH=src python -m analisis.vparty_distribucion_tfi
  PYTHONPATH=src python -m analisis.vparty_distribucion_tfi --anio 2023 --nivel municipal
  ```

## PASO y balotaje

Además de Generales (`tipo_eleccion=2`, en `data/distrito/<año>/<cargo>/generales/`),
el pipeline también trae **PASO** (`tipo_eleccion=1`) y
**balotaje/segunda vuelta** (`tipo_eleccion=3`) — con dos excepciones reales
confirmadas contra la API (no asumidas): **2011/intendente** no tuvo PASO
(la interna de esa categoría no estuvo disputada ese año) y **2025** no tuvo
PASO en ningún nivel (Ley 27.781, que las suspendió a nivel nacional).
Balotaje solo existe para Presidente, y solo en los años en que efectivamente
hubo segunda vuelta — 2015 y 2023 (2011 y 2019 se definieron en primera
vuelta); Gobernador/Intendente no tienen segunda vuelta en la Provincia de
Buenos Aires (se definen por pluralidad simple).

**`circuito_<nivel>.json` y `resultado_total.csv` también existen para PASO
y balotaje** (notebook 04 §6-7; `electoral.totales`), no solo para
Generales — ver "Totales por circuito" y "Resultado total por agrupación"
más arriba. La disponibilidad real de cada (año, nivel, etapa) se detecta
comprobando si el CSV crudo ya está cacheado en disco, no una lista fija:
así el pipeline no necesita mantener la lista de excepciones (2011/intendente,
2025) en dos lugares distintos.

## Libro de códigos ideológico — estado actual

**`clasificacion_ideologica_agrupaciones.csv` nunca se regenera ni se
pisa.** Es un único archivo, compartido por los notebooks 02 (cargos
ejecutivos) y 03 (cargos legislativos), con una 4ª columna,
`campo_ideologico`, clasificada a mano; el último paso de cada notebook:

1. arma la tabla de agrupaciones a partir de lo que devuelve la API para ese
   run (`anio`, `agrupacion`, `nivel`);
2. la compara contra el archivo ya existente en disco por clave exacta
   (`anio`, `nivel`, `agrupacion`);
3. si **no hay agrupaciones nuevas**, no toca el archivo (solo lo informa);
4. si **hay alguna nueva**, la imprime explícitamente (aviso, no error
   silencioso) y la agrega al final con `campo_ideologico` vacío — las filas
   existentes, con su clasificación, nunca se sobreescriben, incluidas las
   filas que agregó el otro notebook (ejecutivo/legislativo no comparten
   valores de `nivel`, así que no hay colisión de claves entre ambos).

**Cobertura 2001-2025, no solo 2011-2025**: los notebooks 02/03 solo
pueden aportar agrupaciones de años con `circuito_<cargo>.json`
(2011-2025). Las 2001-2009 se agregaron aparte, vía
`src/analisis/completar_clasificacion_historica.py`, que lee
`campo_ideologico`/`filiacion_politica`/`vparty_*` ya resueltos en
`data/tfi_data/elecciones/<año>_<nivel>.csv` (completados a mano ahí,
nunca en este CSV, durante el backfill de esos años — ver
`docs/adquisicion_datos_especializacion.md` §1.a) y los agrega con el
mismo criterio append-only de los notebooks (nunca pisa una fila
existente). Comando en `CLAUDE.md`; correrlo de nuevo después de
incorporado no duplica nada (idempotente).

**Nombre de agrupación, normalizado a mayúsculas**: `agrupacion` en el CSV
está en mayúsculas — es la convención que ya traía la API en la mayoría de
los años; solo Generales 2011 (ejecutivos) venía en minúscula/capitalizado.
`agregar_por_circuito` (notebook 04) sube a mayúsculas el `agrupacion_nombre`
del CSV oficial antes de armar `positivos`, así que el `nombre` dentro de
`circuito_<nivel>.json` también queda en mayúsculas — coincide con la clave
usada en el join contra `clasificacion_ideologica_agrupaciones.csv`. Al
incorporar PASO se agregaron ~179 filas nuevas (agrupaciones que compitieron
en la interna y no llegaron a Generales).

`campo_ideologico` (columna en `clasificacion_ideologica_agrupaciones.csv`,
escala 1-6) es hoy una clasificación cargada a mano. La unidad de
clasificación (alianza vs. candidatura vs. programa) y el criterio de
asignación todavía no están fijados de forma sistemática.

**`data/agrupaciones/campo_ideologico.csv` está sin usar por el código
actual** — `src/analisis/graficos.py` define su propio diccionario
`IDEOLOGIAS` hardcodeado en vez de leer este CSV (ítem 9,
`docs/AUDITORIA_ESTADO.md`, abierto desde antes del release v4.0.0). No se
corrigió porque cambiar `graficos.py` para que lea de un CSV externo es un
cambio de comportamiento que necesita su propia verificación, no un ajuste
de documentación — queda como pendiente explícito, no hay que asumir que
este archivo está en uso solo porque existe en `data/`.

`filiacion_politica` (misma tabla) es un segundo campo, ortogonal a
`campo_ideologico`: familia o identidad partidaria (peronistas,
progresistas, liberales, marxistas, nacionalistas, conservadores,
peronismo provincial, otros), no posición ideológico-programática
por elección. No varía por `anio`/`nivel` (una agrupación tiene una única
`filiacion_politica` en todo el período, a diferencia de `campo_ideologico`,
que sí puede cambiar elección a elección). Atiende el señalamiento de la
nota metodológica (§5.2): antes, una alianza como FPV/Unidad
Ciudadana/Frente de Todos/Unión por la Patria quedaba siempre con
`campo_ideologico=3` (centro) 2011-2025, lo que aplanaba una genealogía
peronista continua a una sola posición ideológica. Con `filiacion_politica`
separada, esas cinco denominaciones comparten `filiacion_politica=peronistas`
mientras su `campo_ideologico` puede (o no) variar por elección sin que eso
se lea como inconsistencia del dataset.

Se fusionó desde `data/agrupaciones/tabla_referencia_filiacion_politica.csv`
(121 agrupaciones), que sigue existiendo como fuente de referencia — trae
además `confianza_clasificacion` (alta/media/baja) y `nota_clasificacion`
(fuente o justificación de la clasificación), deliberadamente **no**
fusionadas al CSV principal para mantenerlo liviano; consultar ese
archivo directamente para auditar el porqué de un valor de
`filiacion_politica` puntual. **Ya no es cobertura 1:1** — desde que
`clasificacion_ideologica_agrupaciones.csv` incorporó 2001-2009 (ver
arriba), tiene 237 agrupaciones únicas, de las cuales 193 tienen
`filiacion_politica` poblada; las 121 de `tabla_referencia_filiacion_politica.csv`
no se volvieron a ampliar para cubrir las agrupaciones nuevas — brecha
pendiente, no investigada fila por fila (mismo tipo de deuda que la de
V-Party, ver `docs/AUDITORIA_ESTADO.md`).

El mismo CSV trae además tres columnas opcionales —
`vparty_economico`/`vparty_progresismo`/`vparty_populismo`, posición
programática en el espacio de V-Party (V-Dem Institute), ortogonal tanto a
`campo_ideologico` como a `filiacion_politica` — pobladas para una parte de
las filas (V-Party real más una estimación propia calibrada a su misma
escala). De qué fuente viene cada fila puntual está documentado en un único
lugar, `data/agrupaciones/v-party/README.md`, no acá.

## Distribución ideológica interactiva (`src/visualizacion/distribucion_ideologica_interactiva.py`)

Pestaña del sitio de GitHub Pages (`docs/distribucion_ideologica_la_plata.html`,
enlazada desde `docs/index.html`), mismo patrón de interacción temporal que
`visualizacion.mapa_interactivo` (selector + autoplay) — ambos generadores
de HTML interactivo viven en `src/visualizacion/`, separado de
`src/analisis/` (que solo bulk-escribe PNG/Markdown estáticos), ver
CLAUDE.md. Acá el selector es solo **Nivel + Año**
(nacional/provincial/municipal, sin el toggle Cargo/Nivel del mapa) — los
cuadros V-Party de este repo solo existen por nivel unificado.

**Fuente de datos: `data/tfi_data/elecciones/<año>_<nivel>.csv` directo**,
vía `analisis.vparty_distribucion_tfi.cargar_eleccion`/`combos_disponibles`
(no `circuito_<cargo>.json` ni `clasificacion_ideologica_agrupaciones.csv`
por join propio) — por eso cubre **2001-2025**, no solo 2011-2025: esos
CSV ya traen `campo_ideologico`/`filiacion_politica`/`vparty_*` resueltos
para cada agrupación de cada elección, incluidos los años sin
`circuito_<cargo>.json` (2001-2009). **No tiene mapa ni desglose por
localidad** — se sacó deliberadamente (pedido explícito, ver historial de
la conversación que lo generó) porque esos años no tienen geometría de
circuito para mapear; hasta que se defina un criterio para tratar
2001-2009 en ese nivel, la pestaña es un único bubble chart a nivel
distrito. **🔒 Bloqueado además por cambio de alcance**: el proyecto pasó
a trabajar a nivel municipal, no circuito/localidad — no reintroducir
sin volver a preguntar (ver `docs/AUDITORIA_ESTADO.md`).

El panel único es un bubble chart SVG: eje X económico, eje Y progresismo,
tamaño = % de votos del partido en esa elección (sobre el total de la
elección: agrupaciones + BLANCO + NULO, aunque BLANCO/NULO no se grafican
por no tener V-Party), color = familia política (`filiacion_politica`,
sombreada por partido dentro de la familia, mismas
`_color_por_partido`/`_sombras` de `vparty_cuadrantes_local`, aún activas
para esto). **Todos los puntos se muestran de la misma forma, sin
distinguir V-Party real de estimación propia** — de qué fuente viene cada
valor está documentado en un único lugar,
`data/agrupaciones/v-party/README.md`, y no se refleja en ningún elemento
visual ni interactivo de esta pestaña (ni color, ni trazo, ni filtro): la
estimación propia calibrada (incluida la variante ad hoc de
`estimar_partido_cobertura_parcial`, ver ese README) se trata como igual
de válida.

El eje usa una **escala fija y simétrica respecto de 0** —
`analisis.vparty_distribucion_tfi.limites_globales`, calculados sobre toda
la cobertura V-Party cargada de los 39 archivos de `data/tfi_data/elecciones/` —
enviada una sola vez en el payload (`eje_limites`) y nunca recalculada por
render: el (0,0) siempre cae en el centro visual del gráfico, y el rango
no cambia al pasar de año o nivel, así el autoplay no reescala el chart.

No modifica `vparty_cuadrantes_local.py` — solo reusa
`_color_por_partido`/`_sombras`, que siguen activas; el resto de ese
módulo (`tabla_distrito`, `tabla_localidades`, `cargar_posiciones_propias`,
`cargar_filiaciones`, `_limites_globales`) quedó sin llamador desde que
esta pestaña dejó de usarlo, ver CLAUDE.md. El equivalente en PNG estático
por (año, nivel) es `analisis.vparty_distribucion_tfi` (sección "Gráficos"
más abajo) — mismo dato, mismo criterio de color, salida a
`graficos/tfi/v-party/` en vez de un payload JSON.

```bash
PYTHONPATH=src python -m visualizacion.distribucion_ideologica_interactiva
```

## Trayectorias económicas trimestrales (`src/visualizacion/trayectorias_economicas.py`)

Pestaña del sitio (`docs/trayectorias_economicas_la_plata.html`,
enlazada desde `docs/index.html`, mismo patrón payload+template que las
otras, ver skill `laplata-visualizacion`).

**Fuente de datos: `data/tfi_data/panel/t-1/panel_trimestral_<nivel>.csv`**
(Fase 5 del panel temporal de ventanas electorales, ver
`docs/decisiones_metodologicas.md` D13), no `panel_ventanas.csv` ni
`series_economicas_mensuales.csv` directo — ese CSV ya trae, por
ventana electoral, una fila frontera con el resultado de la elección
`t-1`, una fila por trimestre real dentro de la ventana y una fila
frontera con el resultado de la elección `t`. La subcarpeta `t-1/` (junto
con `t-2/`, ver más abajo) distingue el bloque corto del bloque largo
dentro de `data/tfi_data/panel/` -- `PANEL_TRIMESTRAL_DIR`/
`PANEL_BIELECCION_TRIMESTRAL_DIR` en `constantes.py`.

Selector **Nivel + Elección + Variable**: Nivel fijo (municipal/
provincial/nacional); Elección se puebla con las ventanas de ese nivel
(el `label` `"2001→2003"` de cada `id_transicion`, más reciente por
defecto); Variable se puebla **dinámicamente desde las columnas
económicas reales del CSV** (`_variables_de`, D9) — nunca una lista
hardcodeada, así que si se completa la adquisición de alguna de las 4
variables hoy `exploratoria` (`pobreza`/`gini`/`brecha_cambiaria`/
`empleo_registrado_pba`, ver `cargar_series_economicas.py`), aparece
sola sin tocar este módulo.

**Un gráfico por ventana, nunca las 31 superpuestas**: elegidos nivel +
elección + variable, se muestra la trayectoria trimestral de esa única
ventana, alineada por **posición relativa dentro de la ventana**
(trimestre 1..N desde la elección anterior), no por fecha calendario —
las ventanas tienen largo real distinto (6 a 10 trimestres, D13/corrección
a D4). Un solo color fijo (`var(--accent)`) para la línea, sin distinguir
continuidad/ruptura del oficialismo -- se probó ese color-coding y se sacó
(pedido explícito, no reintroducir sin volver a preguntar): para una
ventana de ~2 años esa clasificación binaria agrega ruido, no valor,
tiene sentido para agregados de ventanas más largas, no acá. `side-sub`
solo muestra `agrupacion_inicio → agrupacion_t` (quién gobernaba al
principio y al final de la ventana), sin la etiqueta ruptura/continuidad.
Claves genéricas a propósito (`anio_inicio_ventana`/`agrupacion_inicio`,
no `anio_t_menos_1`/`agrupacion_t_menos_1`): el mismo template se reusa
sin cambios para la pestaña bielección de más abajo, donde ese límite
inicial es la elección `t-2`, no `t-1`.
Huecos reales dentro de la serie (ej. el hueco de `ipc` 2014-01/2016-11,
ver `cargar_series_economicas.py`) cortan la línea en tramos, nunca se
interpolan; cada punto real es hoverable individualmente (valor exacto de
ese trimestre).

Eje X escalado al largo real de la ventana seleccionada (1..N, recalculado
por render — sin sentido fijarlo a un máximo global si solo se muestra una
ventana a la vez); eje Y recalculado por render sobre los valores de esa
ventana/variable (los rangos difieren demasiado entre variables como para
compartir una escala fija).

**Referencia de unidades** (`_UNIDADES`, panel fijo "Referencia — unidad
de cada variable" bajo el gráfico, resalta la variable seleccionada):
compacta en una etiqueta lo que `registro_variables.csv` ya documenta en
prosa (`nota_metodologica`) -- no una fuente nueva del dato. Aclara en
particular que `ipc` en este panel es la **variación % acumulada del
trimestre** (`es_flujo=true`, ver
`construir_panel_trimestral._variacion_flujo_trimestre`), no un nivel de
índice como `emae`/`icc`/`icg`. `desocupacion` llega de
`series_economicas_mensuales.csv` en fracción 0-1 (ver
`cargar_series_economicas.py` y la nota de `tasa_desocupacion` en
`catalogo_series.csv`), pero `_serie_variable` la multiplica por 100 solo
para este payload -- mostrar `0.074` en el eje se leía como
"prácticamente cero"; el CSV de origen no se toca, la unidad mostrada
(`_UNIDADES["desocupacion"] = "%"`) ya refleja el valor multiplicado.

**`salario_real` se reexpresa en dólar oficial** (`salario_real_usd`,
`_salario_real_usd_mensual`): la columna `salario_real` de
`panel_trimestral_<nivel>.csv` ya viene deflactada por IPC (índice, no
pesos) -- dividirla directo por `tc_oficial` no tiene unidad económica
coherente (probado empíricamente: da un orden de magnitud equivocado,
~15-20 en vez de ~1000-1500 USD/mes). Se revierte la deflación
(`nominal = salario_real * ipc / 100`, usando el **índice mensual crudo**
de `series_economicas_mensuales.csv`, no la variación % trimestral de
`panel_trimestral`) para recuperar el RIPTE nominal en pesos de ese mes,
y recién ahí se divide por `tc_oficial` mensual — el resultado mensual se
agrega a trimestre con la misma partición de meses y el mismo promedio
simple que usó Fase 5 (`_meses_en_ventana`/`_promedio_trimestre`,
reusados, no reimplementados). Reemplaza a `salario_real` en
`payload["variables"]`, no coexisten las dos.

```bash
PYTHONPATH=src python -m visualizacion.trayectorias_economicas
```

`_variables_de`/`_serie_variable`/`_label_ventana`/`_salario_real_usd_mensual`
(lógica nueva de extracción del payload, no reusada de otro módulo ya
testeado) están cubiertas por
`tests/visualizacion/test_trayectorias_economicas.py`;
`construir_payload`/`generar_trayectorias_economicas` y el template no
tienen test automatizado, mismo criterio que el resto de
`src/visualizacion/*` (validado corriendo el script contra `data/` real
más una pasada headless).

## Trayectorias económicas bielección trimestrales (`src/visualizacion/trayectorias_economicas_bieleccion.py`)

Pestaña paralela a la anterior, sobre el **bloque largo** (`_vl` de
`features_ventana.py`: elección `t-2` a elección `t`, 4 años/dos
elecciones, saltea la elección `t-1` intermedia) en vez del bloque corto
(`_vc`, `t-1` a `t`). Mismo patrón payload+template, misma UI -- reusa
`trayectorias_economicas_template.html` sin cambios porque el payload
usa el mismo esquema genérico de claves (`anio_inicio_ventana`/
`agrupacion_inicio`, ver arriba); acá esas dos claves representan la
elección `t-2`, no `t-1`.

**Fuente de datos: `data/tfi_data/panel/t-2/panel_bieleccion_trimestral_<nivel>.csv`**
(`ml_models.construir_panel_bieleccion_trimestral`, artefacto nuevo y
paralelo a `construir_panel_trimestral.py` -- no lo reemplaza ni lo
modifica, mismas fuentes: `ventanas.csv`/`series_economicas_mensuales.csv`/
`resultado_distrito.csv`/`oficialismo_por_nivel.csv`). Estructura de fila
idéntica a la del bloque corto (frontera + trimestre), salvo que la
columna `anio_t_menos_1` se reemplaza por `anio_t_menos_2` y la frontera
inicial es `tipo_fila="eleccion_t_menos_2"` en vez de
`"eleccion_t_menos_1"`. **Ventanas sin `fecha_inicio_vl` (la primera
transición de cada nivel, sin bloque largo posible -- D3) se saltean**,
no generan fila: de las 31 ventanas `_vc` totales (12 municipal + 12
provincial + 7 nacional) quedan **28 ventanas bielección** (11 + 11 + 6).
`id_transicion` propio, `<nivel>_<anio_t_menos_2>_<anio_t>` (ej.
`municipal_2001_2005`), distinto del `id_transicion` del bloque corto
para la misma agrupación de años.

```bash
PYTHONPATH=src python -m ml_models.construir_panel_bieleccion_trimestral
PYTHONPATH=src python -m visualizacion.trayectorias_economicas_bieleccion
```

`construir_panel_bieleccion_trimestral`/`generar_csvs` están cubiertas
por `tests/ml_models/test_panel_bieleccion_trimestral.py`;
`construir_payload` de `trayectorias_economicas_bieleccion.py` por
`tests/visualizacion/test_trayectorias_economicas_bieleccion.py` -- mismo
criterio de cobertura que los módulos análogos del bloque corto.

## Capa socioeconómica (EPH + Censo) — estado actual

**Correspondencia circuito electoral ↔ radio censal**
(`data/socioeconomia/circuito_radio_correspondencia.csv`, construida por
`src/socioeconomia/geo.py`): circuitos electorales y radios censales son
geografías de instituciones distintas sin id compartido, así que la
correspondencia es un join espacial (`geopandas`), no un lookup por id como
`circuito_id_correspondencias.csv`. Cada radio censal (2010 y 2022, cargados
desde la cartografía armonizada de CONICET) se reparte entre los circuitos
que intersecta, ponderado por área — `match_limpio=True` si cayó entero en
un único circuito, o varias filas con `peso_area` sumando 1.0 si cruza un
límite. **Bastante más de un tercio de los radios de La Plata están
prorrateados** (2010: 395/849 = 46.5%; 2022: 464/1.049 = 44.2% — no es un
caso raro, es la norma en los bordes de circuito): cualquier cifra censal
por circuito construida a partir de esas filas es una estimación por área,
no un conteo censal, y debe presentarse como tal. De los circuitos ya
señalados como límite incierto en la sección "Totales por circuito" de más
arriba, `493` y `496F` sí están en la capa de circuitos electorales
descargada; **`504C` no está** — el circuito electoral en sí no tiene
polígono en la fuente usada (`mapa2.electoral.gob.ar` / catálogo de datos
abiertos de la Provincia de Buenos Aires), no es un problema de la
correspondencia con radios.

**EPH Gran La Plata** (`src/socioeconomia/eph_client.py`, tres CSV en
`data/socioeconomia/`): serie trimestral **2011T1-2025T4 (57 de 60
trimestres)**, para `AGLOMERADO=2` — confirmado empíricamente: en el 1er
trimestre de 2018 concentra 870.693 personas ponderadas, en línea con la
población conocida de Gran La Plata (La Plata + Berisso + Ensenada). **Es un
dato de aglomerado, nunca de circuito** — no tiene apertura geográfica más
fina, y no se pretende forzarla.

- `eph_gran_la_plata.csv`: una fila por trimestre, ~25 indicadores —
  núcleo laboral (tasa de actividad, empleo, desocupación, informalidad,
  ingreso de la ocupación principal), composición ocupacional (`CAT_OCUP`),
  calidad del empleo asalariado (obra social/aguinaldo/vacaciones pagas —
  `PP07G1/G2/G4`), cobertura de salud (`CH08`), educación (secundario
  completo, alfabetización, asistencia escolar), hacinamiento y tenencia de
  vivienda (`II1`/`IX_TOT`, `IV7`, `II7`), estrategias de subsistencia del
  hogar en los últimos 3 meses (ayuda social del gobierno, préstamo
  bancario, venta de pertenencias — `V5`/`V15`/`V17`), e ingreso total
  individual e IPCF. Se descartó explícitamente un indicador de
  subocupación horaria (`INTENSI`): dio ~71% sobre datos reales, muy por
  encima de la tasa oficial de INDEC (~10%) — no se pudo confirmar la causa
  a tiempo, mejor no publicarlo que publicar un número probablemente mal
  (ver comentario en el código).
- `eph_gran_la_plata_por_sexo.csv` / `_por_edad.csv`: el núcleo laboral
  (actividad/empleo/desocupación/informalidad/ingreso) abierto por sexo
  (`CH04`) y por tramo etario (`CH06`: 10-24, 25-39, 40-59, 60+) — para
  brecha de género y desocupación juvenil, entre otros.

Desde 2023T4 INDEC dividió la pregunta `V5` (ayuda social del gobierno) en
`V5_01`/`V5_02`/`V5_03` — el cliente reconstruye una `V5` equivalente (1 si
cualquiera de las tres es "Sí") para no perder continuidad de la serie.

2011-2015 salió de una fuente distinta a 2016 en adelante: INDEC dejó de
servir esos trimestres en su propio sitio (el dominio que los alojaba,
`www.indec.gov.ar`) — se recuperaron desde el archivo de
Internet (`web.archive.org`), en formato DBF (no txt/csv), con un esquema de
nombres previo (`t<trimestre><año>_dbf.<zip|rar>`).

Quedan exactamente **3 trimestres sin dato**: INDEC no publicó la encuesta en 2015T3, 2015T4 y 2016T1
("emergencia estadística").

**Censo 2010 y 2022 por radio censal** (país de nacimiento, nivel
educativo, condición de actividad, vivienda/hacinamiento): **falta
todavía**. A diferencia de lo anterior, REDATAM no tiene un endpoint
masivo tipo CSV — la extracción es manual, tabla por tabla, en la
herramienta web. Los pasos y parámetros geográficos exactos (partido de La
Plata = `PROV 06`, `DEPTO 441`; formato del id de radio) están en
`data/socioeconomia/EXTRACCION_REDATAM.md`. El notebook 05 ya tiene el paso
de unión listo (`unir_censo_a_circuitos`, prorratea cada variable por
`peso_area` antes de sumar por circuito) — corre automáticamente apenas
`censo_2010_radio.csv` / `censo_2022_radio.csv` existan en
`data/socioeconomia/`.

**No hay un índice NBI único que INDEC recalcule igual en 2010 y 2022**

## Agrupación de resultados por localidad — estado actual

**🔒 Bloqueado por cambio de alcance**: el proyecto pasó a trabajar a
nivel municipal, no circuito/localidad — esta sección documenta lo ya
construido (código y datos se conservan), pero no hay trabajo previsto
acá hasta que ese alcance cambie (ver `docs/AUDITORIA_ESTADO.md`).

Además de la correspondencia circuito↔radio censal de la sección anterior
(para cruzar con el Censo), existe una **segunda correspondencia
territorial, independiente y con otro propósito**: agrupar los resultados
electorales por localidad/barrio de La Plata (Villa Elvira, Los Hornos, San
Lorenzo, Melchor Romero, etc.) con nombres legibles, no censales.

- **Crosswalk por defecto** (`data/geolocalizacion/circuitos_por_localidad.csv`,
  **derivado**, no hand-curated — se regenera en segundos con
  `PYTHONPATH=src python -m geolocalizacion.circuitos_por_localidad`):
  mapea `circuito` → `localidad` + `distancia_metros` por nearest-neighbor
  contra el catálogo geolocalizado (36 localidades, Ministerio de Obras
  Públicas + Georef-AR, ver skill `laplata-geolocalizacion`). Cubre los 68
  circuitos de `circuitos_electorales_la_plata.geojson` con una fila cada
  uno, sin niveles de cobertura que resolver. Metodología completa,
  distancia media/máxima del match y localidades sin ningún circuito
  asignado en `data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md`.
- **Crosswalk histórico** (`data/geolocalizacion/fuentes_extra/circuito_localidad.csv`,
  hand-curated como `clasificacion_ideologica_agrupaciones.csv` — no se
  regenera desde ningún notebook, y ya no es el default): mapea
  `circuito_id` → `localidad`/barrio con tres niveles de cobertura que
  nunca se mezclan sin pedirlo explícitamente — `oficial_confirmada`
  (Resolución 1990/2007 del Ministerio del Interior, 16/68 circuitos),
  `revision_web` (relevamiento "barrio por barrio" de El Día, octubre
  2025, con la etiqueta recontrastada contra fuentes adicionales en la
  web, 6/68 circuitos) y `periodistico_no_oficial` (el mismo relevamiento
  de El Día sin esa revisión adicional, 59/68 circuitos). Sigue disponible
  para quien específicamente quiera nombre de barrio o reproducir
  resultados previos a la reconstrucción sobre geolocalización. El
  detalle completo del armado, la cobertura circuito a circuito y qué
  falta está en `data/geolocalizacion/fuentes_extra/CIRCUITOS_LOCALIDADES.md`; la
  auditoría de qué tan bien coincide cada localidad `oficial_confirmada`
  contra el texto completo de la resolución (no solo el título de la
  subsección) está en `data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`.
- **`src/electoral/localidades.py`**: la lógica de agrupamiento pura
  (`agrupar_resultados_por_localidad`), sin tocar `data/` ni la API —
  agnóstica de qué crosswalk armó el mapa `circuito_id -> localidad` que
  recibe (`cargar_circuito_localidad_geo` para el crosswalk geolocalizado,
  o `cargar_crosswalk` + `mapa_localidad_por_circuito` para el histórico,
  donde `oficial_confirmada` prevalece siempre sobre `revision_web`, y
  `revision_web` sobre `periodistico_no_oficial`). Ningún voto se pierde
  nunca en ninguno de los dos casos — lo que no tiene localidad asignada
  (con el crosswalk geolocalizado, solo `circuito_id` de años anteriores
  al recorte geojson vigente, ej. `504C`) queda en la fila
  `SIN_DETERMINAR`, siempre presente en el resultado.
- **`src/analisis/cuadros_por_localidad.py`**: script que combina el
  crosswalk geolocalizado (default) con los `circuito_<nivel>.json` ya
  generados por el notebook 04 (no vuelve a tocar la API ni el CSV
  oficial) y escribe un CSV por (año, nivel, etapa) en
  `data/por_localidad/` — es un CSV derivado (data, no imagen), pero no
  se versiona: se regenera en segundos, igual criterio que `graficos/`.
  Cada cuadro trae, además de las 6 columnas de campo ideológico, una
  columna `blanco_nulo` (votos en blanco + nulos — no es una ideología,
  pero tampoco se mezcla en un "otros" genérico), una columna `otros` con
  el resto (impugnado/recurrido/comando, procedimental) y una columna
  `ausentismo` (`electores` del circuito menos sus votos válidos), más la
  cobertura de circuitos/votos lograda como comentario `#` en el
  encabezado.

  ```bash
  PYTHONPATH=src python -m analisis.cuadros_por_localidad --anio 2023 --nivel intendente
  PYTHONPATH=src python -m analisis.cuadros_por_localidad                    # todo lo disponible
  ```

- **`src/analisis/serie_temporal_por_localidad.py`** (eliminado en
  `fb35b41`, "elimina salidas obsoletas"): generaba, a partir de esos
  cuadros, un gráfico de serie temporal por campo ideológico +
  `blanco_nulo` + `ausentismo` por localidad y nivel de gobierno
  (2011-2025). Ya no existe en el código ni sus ~132 PNG — no hay hoy una
  serie temporal por localidad activa (ver `docs/AUDITORIA_ESTADO.md`).

## Capa macroeconómica nacional — estado actual

Un dominio analítico separado del electoral y del socioeconómico:
**grano exclusivamente nacional** (sin circuito, sin localidad, sin
apertura regional), se relaciona con el resto del repositorio por fecha,
nunca por unidad espacial ni por join territorial. El detalle completo de
fuentes evaluadas, decisiones de diseño y catálogo variable por variable
está en `docs/plan_macroeconomia.md`; la cobertura real
obtenida, las salvedades encontradas al implementar y el resultado de la
auditoría externa están en
`data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md`.

- **`src/macroeconomia/datos_gob_client.py`**: cliente de descarga+caché
  para la API pública de Series de Tiempo de `datos.gob.ar` (sin
  autenticación), mismo contrato que `electoral/client.py` — nunca
  transforma, solo pagina y cachea en disco (`data/macroeconomia/_cache/`,
  no versionado).
- **`src/macroeconomia/series.py`**: lee
  `data/macroeconomia/catalogo_series.csv` (20 conceptos de frecuencia
  diaria/mensual/trimestral — monetario/cambiario, precios, actividad,
  empleo, ingresos, sector externo — hand-curated y append-only, mismo
  criterio que `clasificacion_ideologica_agrupaciones.csv`) y arma
  `data/macroeconomia/series_macro_2011_2025.csv`: una fila por **mes**
  (2011-01 a 2025-12), una columna por concepto, más `observaciones`. No
  versionado (se regenera en segundos desde la caché, igual criterio que
  `data/totales/`).
- **`src/macroeconomia/series_anuales.py`**: mismo patrón, pero para los
  conceptos de frecuencia **anual** (finanzas públicas:
  `gasto_deuda_publica_nivel`/`_pib`), separados en su propio catálogo
  `data/macroeconomia/catalogo_series_anuales.csv` y su propio CSV
  `data/macroeconomia/series_macro_anuales_2011_2025.csv` — **una fila por
  año** (2011-2025), no por mes. Se separaron del catálogo mensual porque
  forzar una serie anual dentro de una tabla fila-por-mes la dejaba con
  ~93% de celdas vacías (solo 1 de cada 12 filas puede tener dato, y sin
  forward-fill ninguna de las otras 11 lo tiene nunca) — a grano anual,
  esas mismas dos columnas quedan con 13/15 años reales (86,7%), sin ese
  ruido. Reusa `ConceptoCatalogo`/`cargar_catalogo`/`_parsear_puntos` de
  `series.py` en vez de duplicarlos.
- **Ninguna celda repite ni rellena un valor anterior, en ninguno de los
  dos catálogos**: solo tiene dato el mes/año en que la fuente publicó
  exactamente para ese período. Una serie trimestral, entonces, solo llena
  su mes de origen (ej. enero/abril/julio/octubre) — los demás meses
  quedan vacíos (`""`), nunca con el dato del período anterior. Series
  diarias (tipo de cambio, BADLAR, base monetaria) se agregan a mensual
  tomando el último valor hábil del mes, sin promediar. Cada celda vacía queda explicada en `observaciones`.
- **Auditoría externa** (`src/macroeconomia/auditoria_estadisticasbcra.py`):
  script manual, no integrado al pipeline regular, que compara cada
  concepto marcado `auditable_estadisticasbcra` en el catálogo contra
  `estadisticasbcra.com` (requiere token propio de
  `estadisticasbcra.com/api/registracion`, nunca guardado en el
  repositorio). La corrida de 2026-08 corrigió un mapeo del catálogo
  (`tipo_cambio_oficial` apuntaba al dólar informal/blue, no al oficial) y
  encontró que esa fuente externa está atrasada entre 1,5 y 2 años según
  el endpoint — solo sirve para auditar tramos históricos ya cerrados, no
  los meses más recientes del CSV. Resultado completo en
  `SISTEMATIZACION_VARIABLES_MACRO.md` §3.

  ```bash
  PYTHONPATH=src python -m macroeconomia.series                    # arma/actualiza el CSV mensual, usa caché si existe
  PYTHONPATH=src python -m macroeconomia.series_anuales             # ídem, catálogo/CSV anual
  ESTADISTICASBCRA_TOKEN=<tu_token> PYTHONPATH=src python -m macroeconomia.auditoria_estadisticasbcra  # auditoría manual puntual
  ```

## Extender a otro distrito, sección o cargo

1. Encontrar `distritoId`/`seccionProvincialId`/`seccionId` (no hay endpoint
   para listarlos; en este proyecto se resolvieron con un CSV oficial de
   referencia y, para los códigos de distrito, con el GeoJSON embebido en el
   bundle del sitio).
2. **No asumir** el mapeo de `categoriaId` de la tabla de arriba — es local a
   distrito/año. Resolverlo pidiendo `get_resultados_csv` con distintos
   `categoria_id` y leyendo el campo `cargo_nombre` de la respuesta (ver
   sección 1 de `02_la_plata_cargos_ejecutivos.ipynb`).
3. Usar `get_resultados_csv` para traer los datos, y a partir de ahí seguir
   el mismo camino que los notebooks de este repo:
   - Agregar por `circuito_id` (normalizado a su forma canónica, sin ceros a
     la izquierda) con la misma lógica de `notebooks/04_totales_por_circuito.ipynb`
     (`agregar_por_circuito`), validando contra el JSON agregado de
     `get_resultados` antes de confiar en el resultado.
   - Armar (o extender) el libro de códigos ideológico para las agrupaciones
     nuevas del distrito, con la unidad y el criterio de clasificación
     explicitados (ver "Libro de códigos ideológico" más arriba) — el join
     falla ruidosamente (`KeyError`) si una agrupación queda sin clasificar,
     a propósito.
   - Recién con eso escribir el equivalente a `circuito_<nivel>.json` y, si
     hace falta, graficar con `src/analisis/graficos.py` /
     `generar_graficos.py`.
