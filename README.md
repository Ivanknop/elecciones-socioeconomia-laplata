# Análisis Política y Economía — Resultados Electorales (La Plata)

Cliente y pipeline de datos para la API pública de Resultados Electorales del
Ministerio del Interior (`https://resultados.mininterior.gob.ar/api`), con foco
en La Plata (Provincia de Buenos Aires): los cargos ejecutivos —Presidente,
Gobernador, Intendente— entre 2011 y 2023, y los cargos legislativos —nacional
(Diputados/Senadores Nacionales), provincial (Diputados/Senadores
Provinciales), municipal (Concejales)— entre 2013 y 2025.


## Estructura del repo

```
src/electoral/
  client.py     
  models.py     
src/analisis/
  graficos.py           # graficar_barras / graficar_torta (por campo ideológico) a partir de circuito_<nivel>.json
  generar_graficos.py   # script: para un (año, nivel), genera todos los PNG (circuito por circuito + acumulado)
  serie_temporal.py      # script: por nivel de gobierno (nacional/provincial/municipal), línea por ideología 2011-2025
notebooks/
  01_explorar_resultados.ipynb           # cómo usar el cliente + el modelo de dominio
  02_la_plata_cargos_ejecutivos.ipynb    # pipeline: cargos ejecutivos, 2011-2023
  03_la_plata_legislativas.ipynb         # pipeline: cargos legislativos, 2013-2025
  04_totales_por_circuito.ipynb         
data/<año>/<categoría o nivel>/          # caché: .json (agregado) + .csv (oficial) + circuito_<nivel>.json
data/agrupaciones/agrupaciones.csv                 # año/agrupación/nivel — cargos ejecutivos
data/agrupaciones/agrupaciones_legislativas.csv    # año/agrupación/nivel — cargos legislativos
data/agrupaciones/campo_ideologico.csv             # escala 1-6 izquierda→derecha radical (provisto)
graficos/<año>/<nivel>/                 
graficos/serie_temporal/                 
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
   disco quedó limpio (2 archivos por carpeta), y arma
   `data/agrupaciones/agrupaciones.csv` (año, agrupación, nivel) a partir de
   los agregados JSON.
4. Abrir y correr `notebooks/03_la_plata_legislativas.ipynb`: mismo patrón
   pero para los cargos legislativos (nacional/provincial/municipal,
   2013-2025), y arma `data/agrupaciones/agrupaciones_legislativas.csv`.
5. Abrir y correr `notebooks/04_totales_por_circuito.ipynb`: agrega por
   `circuito_id` los totales de cada agrupación y de los "otros" (blanco,
   nulo, recurrido, impugnado...) para cada (año, nivel) ya descargado, y
   escribe `data/<año>/<nivel>/circuito_<nivel>.json`.
6. Si ya existe la caché en `data/`, los notebooks corren instantáneo (leen
   de disco, no vuelven a pedirle nada a la API). Para forzar una actualización
   real, pasar `force_refresh=True` a los métodos del cliente.

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

`data/<2011|2015|2019|2023>/<presidente|gobernador|intendente>/`, cada una
con 2 archivos: el agregado de la sección (`.json`) y el CSV oficial
(`.csv`). Todo scopeado a **La Plata**:

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

`data/<2013|2017|2021|2025>/<nacional|provincial|municipal>/`. Mismo
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
`agrupaciones.csv` (`anio`, `agrupacion`, `nivel`). Cuando un nivel tuvo dos
cargos el mismo año, sus agrupaciones se juntan bajo ese `nivel` y se
deduplican.

### Totales por circuito

`data/<año>/<nivel>/circuito_<nivel>.json` — agrega, por `circuito_id`, los
positivos por agrupación y los "otros" (blanco/nulo/recurrido/impugnado/
comando, lo que exista ese año). Sale del CSV oficial. 

`2017/nacional` tuvo dos cargos ese año (Senador Nacional idCargo=2, solo
2017; Diputados Nacionales idCargo=3, todos los años) compartiendo la misma
carpeta. `circuito_nacional.json` usa Diputados Nacionales, por ser el
consistente en los 4 años legislativos — Senador Nacional 2017 queda afuera
de este archivo.

Cada agrupación dentro de `positivos` suma el campo `campo_ideologico`,
copiado tal cual de `agrupaciones.csv` / `agrupaciones_legislativas.csv`
(join exacto por año/nivel/nombre; `"gobernador"` se mapea a
`"gobernacion"`.

## Gráficos (`src/analisis/`, salida en `graficos/`)

Barras y torta por **campo ideológico** (izquierda → derecha radical, con
una paleta divergente azul↔rojo — es un dato de polaridad, no de identidad),
a partir de `circuito_<nivel>.json`.

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
  ejecutivo (años pares) y su cargo legislativo (años impares) en una sola
  serie continua — nunca se superponen (los datos que tenemos de cada uno
  son de años distintos), así que no hace falta reconciliar dos fuentes el
  mismo año, solo elegir cuál de las dos corresponde a cada punto:

  | nivel | ejecutivo | legislativo | puntos | rango |
  |---|---|---|---|---|
  | nacional | Presidente | Diputados Nacionales | 8 | 2011-2025 completo |
  | provincial | Gobernador | Diputados Provinciales | 7 | 2011-2023 (sin 2025 ) |
  | municipal | Intendente | Concejales | 7 | 2011-2023 (sin 2025) |

## Extender a otro distrito, sección o cargo

1. Encontrar `distritoId`/`seccionProvincialId`/`seccionId` (no hay endpoint
   para listarlos; en este proyecto se resolvieron con un CSV oficial de
   referencia y, para los códigos de distrito, con el GeoJSON embebido en el
   bundle del sitio).
2. **No asumir** el mapeo de `categoriaId` de la tabla de arriba — es local a
   distrito/año. Resolverlo pidiendo `get_resultados_csv` con distintos
   `categoria_id` y leyendo el campo `cargo_nombre` de la respuesta (ver
   sección 1 de `02_la_plata_cargos_ejecutivos.ipynb`).
3. Usar `get_resultados_csv` para traer los datos
