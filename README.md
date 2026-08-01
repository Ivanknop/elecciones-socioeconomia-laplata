# Análisis Política y Economía — Resultados Electorales (La Plata)

Cliente y pipeline de datos para la API pública de Resultados Electorales del
Ministerio del Interior (`https://resultados.mininterior.gob.ar/api`), con foco
en La Plata (Provincia de Buenos Aires): los cargos ejecutivos —Presidente,
Gobernador, Intendente— entre 2011 y 2023, y los cargos legislativos —nacional
(Diputados/Senadores Nacionales), provincial (Diputados/Senadores
Provinciales), municipal (Concejales)— entre 2013 y 2025. También recopila una
capa socioeconómica (EPH Gran La Plata, IAELaP y su correspondencia espacial
con el Censo) para poder cruzar, más adelante, resultados electorales con
condiciones socioeconómicas del mismo territorio.

## Estructura del repositorio

```
src/electoral/
  client.py
  models.py
  localidades.py
src/analisis/
  graficos.py
  generar_graficos.py
  serie_temporal.py
  cuadros_anualizados.py
  cuadros_por_localidad.py
  serie_temporal_por_localidad.py
src/socioeconomia/
  geo.py
  eph_client.py
  graficos_eph_iaelap.py
notebooks/
  01_explorar_resultados.ipynb
  02_la_plata_cargos_ejecutivos.ipynb
  03_la_plata_legislativas.ipynb
  04_totales_por_circuito.ipynb
  05_capa_socioeconomica.ipynb
  06_graficos_eph_iaelap.ipynb
data/distrito/<año>/<categoría o nivel>/<etapa>/
data/por_localidad/
data/agrupaciones/agrupaciones.csv
data/agrupaciones/agrupaciones_legislativas.csv
data/agrupaciones/campo_ideologico.csv
data/agrupaciones/circuito_id_correspondencias.csv
data/fuentes_extra/
data/socioeconomia/
graficos/distrito/<año>/<nivel>/
graficos/distrito/serie_temporal/
graficos/socioeconomia/
graficos/por_localidad/
requirements.txt
```

## Instalación

```bash
pip install -r requirements.txt
```

No hace falta API key: es un endpoint público. Sí hace falta acceso de red
saliente a `resultados.mininterior.gob.ar`.

## Cómo reproducir

1. `pip install -r requirements.txt`
2. Abrir y correr `notebooks/01_explorar_resultados.ipynb` para ver cómo se usa
   el cliente (`ResultadosClient`) y el modelo de dominio (`ResultadoElectoral`)
   sobre un solo caso (La Plata, Presidente, 2011).
3. Abrir y correr `notebooks/02_la_plata_cargos_ejecutivos.ipynb`. Este es el
   notebook que efectivamente genera/actualiza `data/`: trae el CSV oficial y
   el agregado JSON de cada combinación (año × cargo), hace un ejemplo de análisis mesa por mesa, confirma que el caché en
   disco quedó limpio y valida
   `data/agrupaciones/agrupaciones.csv` contra lo que trae la API — si hay
   agrupaciones nuevas las agrega.
4. Abrir y correr `notebooks/03_la_plata_legislativas.ipynb`: mismo patrón
   pero para los cargos legislativos (nacional/provincial/municipal,
   2013-2025), sobre `data/agrupaciones/agrupaciones_legislativas.csv`.
5. Abrir y correr `notebooks/04_totales_por_circuito.ipynb`: normaliza
   `circuito_id`, agrega por ese id los totales de cada agrupación y de los "otros"
   (blanco, nulo, recurrido, impugnado...) para cada (año, nivel) ya
   descargado, cruza contra el libro de códigos ideológico, agrega un
   indicador de cobertura, y escribe `data/distrito/<año>/<nivel>/generales/circuito_<nivel>.json`
   y `data/agrupaciones/circuito_id_correspondencias.csv`.
6. Si ya existe la caché en `data/`, los notebooks corren instantáneo (leen
   de disco, no vuelven a pedirle nada a la API). Para forzar una actualización
   real, pasar `force_refresh=True` a los métodos del cliente.

**`agrupaciones.csv`/`agrupaciones_legislativas.csv` nunca se regeneran ni se
pisan.** Ambos archivos tienen una 4ª columna, `campo_ideologico`, clasificada
a mano; el último paso de cada notebook:

1. arma la tabla de agrupaciones a partir de lo que devuelve la API para ese
   run (`anio`, `agrupacion`, `nivel`);
2. la compara contra el archivo ya existente en disco por clave exacta
   (`anio`, `nivel`, `agrupacion`);
3. si **no hay agrupaciones nuevas**, no toca el archivo (solo lo informa);
4. si **hay alguna nueva**, la imprime explícitamente (aviso, no error
   silencioso) y la agrega al final con `campo_ideologico` vacío — las filas
   existentes, con su clasificación, nunca se sobreescriben.

**Nombre de agrupación, normalizado a mayúsculas**: `agrupacion` en ambos CSV
está en mayúsculas — es la convención que ya traía la API en la mayoría de
los años; solo Generales 2011 (ejecutivos) venía en minúscula/capitalizado.
`agregar_por_circuito` (notebook 04) sube a mayúsculas el `agrupacion_nombre`
del CSV oficial antes de armar `positivos`, así que el `nombre` dentro de
`circuito_<nivel>.json` también queda en mayúsculas — coincide con la clave
usada en el join contra `agrupaciones.csv`/`agrupaciones_legislativas.csv`. Al
incorporar PASO se agregaron ~179 filas nuevas (agrupaciones que compitieron
en la interna y no llegaron a Generales). 

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

`data/<2011|2015|2019|2023>/<presidente|gobernador|intendente>/generales/`,
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

`data/<2013|2017|2021|2025>/<nacional|provincial|municipal>/generales/`. Mismo
distrito/sección que arriba. `idCargo` estable en los cuatro años para La
Plata:

| idCargo (`categoriaId`) | cargo | nivel |
|---|---|---|
| 2 | Senador Nacional | nacional |
| 3 | Diputado(s) Nacional(es) | nacional |
| 5 | Senadores Provinciales | provincial |
| 6 | Diputado(s) Provincial(es) | provincial |
| 10 | Concejales | municipal |


`data/agrupaciones/agrupaciones_legislativas.csv`, misma estructura que
genera el notebook 03 para `agrupaciones.csv` (`anio`, `agrupacion`,
`nivel`; el archivo en disco tiene además `campo_ideologico`, agregado a
mano — ver advertencia arriba). Cuando un nivel tuvo dos cargos el mismo año,
sus agrupaciones se juntan bajo ese `nivel` y se deduplican.

### Totales por circuito

`data/distrito/<año>/<nivel>/generales/circuito_<nivel>.json` — agrega, por
`circuito_id`, los positivos por agrupación y los "otros"
(blanco/nulo/recurrido/impugnado/comando, lo que exista ese año). Sale del
CSV oficial.

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
copiado tal cual de `agrupaciones.csv` / `agrupaciones_legislativas.csv`
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

## Gráficos (`src/analisis/`, salida en `graficos/`)

Barras y torta por **campo ideológico** (izquierda → derecha radical, con
una paleta divergente azul↔rojo — es un dato de polaridad, no de identidad),
a partir de `circuito_<nivel>.json`.

**Solo `graficos/distrito/serie_temporal/` está versionado en git.** El resto
de `graficos/distrito/<año>/<nivel>/` (circuito por circuito, más el cuadro
anual de todos los cargos de ese año) está en `.gitignore` — se genera on
demand con los scripts de abajo y no hace falta subirlo (son miles de
archivos, se regeneran en segundos desde `data/`).

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

## PASO y balotaje

Además de Generales (`tipo_eleccion=2`, en `data/distrito/<año>/<cargo>/generales/`),
el pipeline también trae **PASO** (`tipo_eleccion=1`) para todas las
combinaciones (año, cargo) ya cubiertas, y **balotaje/segunda vuelta**
(`tipo_eleccion=3`) para Presidente en los años en que efectivamente hubo —
2015 y 2023 (2011 y 2019 se definieron en primera vuelta). 

## Libro de códigos ideológico — estado actual

`campo_ideologico` (columna en `agrupaciones.csv` /
`agrupaciones_legislativas.csv`, escala 1-6 en `campo_ideologico.csv`) es
hoy una clasificación cargada a mano. La unidad de clasificación (alianza vs.
candidatura vs. programa) y el criterio de asignación todavía no están
fijados de forma sistemática.

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

Además de la correspondencia circuito↔radio censal de la sección anterior
(para cruzar con el Censo), existe una **segunda correspondencia
territorial, independiente y con otro propósito**: agrupar los resultados
electorales por localidad/barrio de La Plata (Villa Elvira, Los Hornos, San
Lorenzo, Melchor Romero, etc.) con nombres legibles, no censales.

- **Crosswalk** (`data/fuentes_extra/circuito_localidad.csv`,
  hand-curated como `agrupaciones.csv` — no se regenera desde ningún
  notebook): mapea `circuito_id` → `localidad` con dos niveles de cobertura
  que nunca se mezclan sin pedirlo explícitamente —
  `oficial_confirmada` (Resolución 1990/2007 del Ministerio del Interior,
  16/68 circuitos) y `periodistico_no_oficial` (relevamiento "barrio por
  barrio" de El Día, octubre 2025, 65/68 circuitos). El detalle completo
  del armado, la cobertura circuito a circuito y qué falta está en
  `data/fuentes_extra/LOCALIDADES_README.md`; la auditoría de qué tan
  bien coincide cada localidad `oficial_confirmada` contra el texto
  completo de la resolución (no solo el título de la subsección) está en
  `data/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`.
- **`src/electoral/localidades.py`**: la lógica de agrupamiento pura
  (`agrupar_resultados_por_localidad`), sin tocar `data/` ni la API.
  `oficial_confirmada` prevalece siempre sobre `periodistico_no_oficial`
  cuando ambas existen para un circuito; ningún voto se pierde nunca — lo
  que no tiene localidad asignada queda en la fila `SIN_DETERMINAR`,
  siempre presente en el resultado.
- **`src/analisis/cuadros_por_localidad.py`**: script que combina ese
  crosswalk con los `circuito_<nivel>.json` ya generados por el notebook
  04 (no vuelve a tocar la API ni el CSV oficial) y escribe un CSV por
  (año, nivel, etapa) en `data/por_localidad/` — es un CSV derivado (data,
  no imagen), pero no se versiona: se regenera en segundos, igual criterio
  que `graficos/`. Cada cuadro trae, además de las 6 columnas de campo
  ideológico, una columna `blanco_nulo` (votos en blanco + nulos — no es
  una ideología, pero tampoco se mezcla en un "otros" genérico) y una
  columna `otros` con el resto (impugnado/recurrido/comando,
  procedimental), más la cobertura de circuitos/votos lograda como
  comentario `#` en el encabezado.

  ```bash
  PYTHONPATH=src python -m analisis.cuadros_por_localidad --anio 2023 --nivel intendente
  PYTHONPATH=src python -m analisis.cuadros_por_localidad                    # todo lo disponible
  ```

- **`src/analisis/serie_temporal_por_localidad.py`**: a partir de esos
  cuadros (no relee `circuito_<nivel>.json` ni el crosswalk), un gráfico
  de serie temporal por campo ideológico por localidad y nivel de
  gobierno (2011-2025), reusando la fusión ejecutivo+legislativo de
  `serie_temporal.py`. Escribe en `graficos/por_localidad/`.
  `SIN_DETERMINAR` se grafica siempre como una serie más, nunca se oculta.

  ```bash
  PYTHONPATH=src python -m analisis.serie_temporal_por_localidad                # todas las localidades, los 3 niveles
  PYTHONPATH=src python -m analisis.serie_temporal_por_localidad --nivel municipal
  ```

Falta subir de nivel a `oficial_confirmada` las familias de circuitos 504,
505, 508 y 509 (hoy solo tienen la etiqueta de El Día) — ver "Qué falta" en
`LOCALIDADES_README.md` para el resto del plan (pedido de acceso a la
información a la Junta Electoral, contraste contra las 24 localidades
oficiales usadas por la cobertura de 0221.com.ar).

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
     explicitados (ver sección anterior) — el join falla ruidosamente
     (`KeyError`) si una agrupación queda sin clasificar, a propósito.
   - Recién con eso escribir el equivalente a `circuito_<nivel>.json` y, si
     hace falta, graficar con `src/analisis/graficos.py` /
     `generar_graficos.py`.
