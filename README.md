# Análisis Política y Economía — Resultados Electorales (La Plata)

Cliente y pipeline de datos para la API pública de Resultados Electorales del
Ministerio del Interior (`https://resultados.mininterior.gob.ar/api`), con foco
en La Plata (Provincia de Buenos Aires): los cargos ejecutivos —Presidente,
Gobernador, Intendente— entre 2011 y 2023, y los cargos legislativos —nacional
(Diputados/Senadores Nacionales), provincial (Diputados/Senadores
Provinciales), municipal (Concejales)— entre 2013 y 2025.


## Estructura del repositorio

```
src/electoral/
  client.py     
  models.py     
src/analisis/
  graficos.py               # graficar_barras / graficar_torta (por campo ideológico) a partir de circuito_<nivel>.json
  generar_graficos.py       # script: para un (año, nivel), genera todos los PNG (circuito por circuito + acumulado)
  serie_temporal.py         # script: por nivel de gobierno (nacional/provincial/municipal), línea por ideología 2011-2025
  cuadros_anualizados.py    # script: un gráfico por año, con todos sus cargos lado a lado
notebooks/
  01_explorar_resultados.ipynb           # cómo usar el cliente + el modelo de dominio
  02_la_plata_cargos_ejecutivos.ipynb    # pipeline: cargos ejecutivos, 2011-2023
  03_la_plata_legislativas.ipynb         # pipeline: cargos legislativos, 2013-2025
  04_totales_por_circuito.ipynb         
data/<año>/<categoría o nivel>/<etapa>/  # etapa: generales (.json + .csv + circuito_<nivel>.json) | paso | balotaje
data/agrupaciones/agrupaciones.csv                 # año/agrupación/nivel/campo_ideologico — cargos ejecutivos
data/agrupaciones/agrupaciones_legislativas.csv    # año/agrupación/nivel/campo_ideologico — cargos legislativos
data/agrupaciones/campo_ideologico.csv             # escala 1-6 izquierda→derecha radical (provisto)
data/agrupaciones/circuito_id_correspondencias.csv # circuito_id crudo (por año) -> circuito_id canónico
graficos/serie_temporal/                 # el único subdirectorio de graficos/ versionado en git
graficos/<año>/<nivel>/, graficos/cuadros_anualizados/   # generados on demand, no versionados (ver .gitignore)
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
   el agregado JSON de cada combinación (año × cargo), valida uno contra el
   otro, hace un ejemplo de análisis mesa por mesa, confirma que el caché en
   disco quedó limpio (2 archivos por carpeta), y valida
   `data/agrupaciones/agrupaciones.csv` contra lo que trae la API — si hay
   agrupaciones nuevas las agrega (avisando), si no, no toca el archivo (ver
   advertencia abajo).
4. Abrir y correr `notebooks/03_la_plata_legislativas.ipynb`: mismo patrón
   pero para los cargos legislativos (nacional/provincial/municipal,
   2013-2025), sobre `data/agrupaciones/agrupaciones_legislativas.csv`.
5. Abrir y correr `notebooks/04_totales_por_circuito.ipynb`: normaliza
   `circuito_id` a su forma canónica (sin ceros a la izquierda — ver más
   abajo), agrega por ese id los totales de cada agrupación y de los "otros"
   (blanco, nulo, recurrido, impugnado...) para cada (año, nivel) ya
   descargado, cruza contra el libro de códigos ideológico, agrega un
   indicador de cobertura, y escribe `data/<año>/<nivel>/generales/circuito_<nivel>.json`
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

Esto hace seguro correr 02→03→04 desde cero en cualquier momento: en el caso
normal (sin agrupaciones nuevas) el archivo queda bit a bit idéntico.

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

Todas las respuestas se cachean en disco en
`data/<anio_eleccion>/<categoria_nombre>/`. `categoria_nombre` (ej.
`"presidente"`) es una etiqueta que decide quien llama, **no** un dato que
devuelva la API — no hay forma confiable de derivar el nombre de una
categoría a partir de su id (ver más abajo). El nombre de archivo dentro de
cada carpeta codifica los demás parámetros de la consulta
(`tipoEleccion-2_categoriaId-1_...json`).

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

`data/<año>/<nivel>/generales/circuito_<nivel>.json` — agrega, por
`circuito_id`, los positivos por agrupación y los "otros"
(blanco/nulo/recurrido/impugnado/comando, lo que exista ese año). Sale del
CSV oficial.

**`circuito_id` canónico**: el mismo circuito se identifica con distinto
ancho/relleno de ceros según el año (`"0460"` en 2011/2015, `"000460"` en
2019, `"00460"` en 2023). El notebook 04 normaliza a una forma canónica (sin
ceros a la izquierda, conservando cualquier sufijo de letra por subdivisión,
ej. `"0496F"` → `"496F"`) **antes** de agregar, y usa esa forma como clave en
`circuitos`. La correspondencia entre el id crudo de cada año y el canónico
queda versionada en `data/agrupaciones/circuito_id_correspondencias.csv`. De
los circuitos de La Plata, un subconjunto no es común a todos los años
procesados (`493`, `496F`, `504C` en esta ejecución) — no es un problema de
formato sino de altas/bajas/subdivisiones reales de circuito, y requiere
revisión manual de límites, no normalización adicional.

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
(`data/2019/presidente/generales/tipoEleccion-2_categoriaId-1_..._.json`) reporta 96
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

**Solo `graficos/serie_temporal/` está versionado en git.** `graficos/<año>/<nivel>/`
(circuito por circuito) y `graficos/cuadros_anualizados/` están en
`.gitignore` — se generan on demand con los scripts de abajo y no hace falta
subirlos (son miles de archivos, se regeneran en segundos desde `data/`).

- **`graficos.py`**: `graficar_barras(data_dir, anio, nivel, circuito_id=None)`
  y `graficar_torta(...)` — devuelven una figura de matplotlib.
  `circuito_id=None` (default) agrega todos los circuitos del (año, nivel);
  pasando un `circuito_id` puntual, grafica solo ese circuito. Son funciones
  para usar sueltas (ej. desde un notebook), no generan archivos por su
  cuenta.
- **`generar_graficos.py`**: script que, dado un `--anio` y un `--nivel`,
  genera **circuito por circuito** (barras + torta) más **un acumulado**
  con el total del (año, nivel) — todo por campo ideológico. Escribe en
  `graficos/<año>/<nivel>/` — carpeta al mismo nivel que `data/` y `src/`,
  **no** adentro de `data/`: `<circuito_id>_barras.png` /
  `<circuito_id>_torta.png` por cada circuito, y `total_barras.png` /
  `total_torta.png` para el acumulado.

  ```bash
  PYTHONPATH=src python -m analisis.generar_graficos --anio 2011 --nivel intendente
  ```

- **`serie_temporal.py`**: **un gráfico por nivel de gobierno** (nacional /
  provincial / municipal, no por cargo puntual), con una línea por campo
  ideológico (las 6) cubriendo 2011-2025. Cada nivel combina su cargo
  ejecutivo y su cargo legislativo en una sola serie continua. **Todos los
  años del proyecto son impares** (ejecutivos 2011/2015/2019/2023,
  legislativos 2013/2017/2021/2025 — no hay ningún año par en el dataset):
  lo que alterna es el *tipo* de elección (general ejecutiva vs. legislativa
  intermedia), no la paridad del año. Nunca se superponen (los datos que
  tenemos de cada uno son de años distintos), así que no hace falta
  reconciliar dos fuentes el mismo año, solo elegir cuál de las dos
  corresponde a cada punto:

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
  `graficos/cuadros_anualizados/<año>_votos.png` y `<año>_porcentaje.png`.

  ```bash
  PYTHONPATH=src python -m analisis.cuadros_anualizados --anio 2023
  ```

## PASO y balotaje

Además de Generales (`tipo_eleccion=2`, en `data/<año>/<cargo>/generales/`),
el pipeline también trae **PASO** (`tipo_eleccion=1`) para todas las
combinaciones (año, cargo) ya cubiertas, y **balotaje/segunda vuelta**
(`tipo_eleccion=3`) para Presidente en los años en que efectivamente hubo —
2015 y 2023 (2011 y 2019 se definieron en primera vuelta). El caché sigue el
mismo patrón `data/<año>/<cargo>/`, con una subcarpeta por etapa:
`data/<año>/<cargo>/paso/` y, para Presidente, `data/<año>/presidente/balotaje/`
— hermanas de `generales/`, misma estructura simétrica entre las tres.

## Libro de códigos ideológico — estado actual

`campo_ideologico` (columna en `agrupaciones.csv` /
`agrupaciones_legislativas.csv`, escala 1-6 en `campo_ideologico.csv`) es
hoy una clasificación cargada a mano. La unidad de clasificación (alianza vs.
candidatura vs. programa) y el criterio de asignación todavía no están
fijados de forma sistemática — algunas reglas puntuales ya se aplicaron caso
por caso, pero el criterio general queda para una etapa posterior.

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
