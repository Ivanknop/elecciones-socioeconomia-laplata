# La capa electoral del repositorio *elecciones-socioeconomia-laplata*: uso, datos obtenidos y visualizaciones

**Repositorio:** `Ivanknop/elecciones-socioeconomia-laplata` (v4.x.x)
**Alcance de este documento:** exclusivamente la capa electoral (`src/electoral/`, `src/analisis/`, `data/distrito/`). La capa socioeconómica (EPH/Censo) queda fuera, en línea con la separación arquitectónica ya adoptada en el proyecto.

---

## 1. Objetivo y alcance

Esta capa reconstruye, para el municipio de La Plata (Buenos Aires, Argentina), los resultados electorales oficiales a nivel de circuito para el período 2011–2025, y produce a partir de ellos series temporales, cuadros comparativos y visualizaciones por posición ideológica y por filiación partidaria. La unidad de análisis mínima es el **circuito electoral** (`circuito_id`); todos los productos derivados (totales por agrupación, series temporales, agrupamiento por localidad) se construyen agregando sobre esa unidad, nunca a partir de datos ya agregados por la fuente.

El diseño distingue explícitamente tres roles:

- **Adquisición** (`src/electoral/client.py`): habla con la API oficial y cachea en disco.
- **Modelado** (`src/electoral/models.py`, `src/electoral/totales.py`): tipa y agrega los datos crudos.
- **Análisis y visualización** (`src/analisis/`): produce cuadros y gráficos reutilizables a partir de los datos ya modelados, sin volver a tocar la API.

---

## 2. Fuente de datos

**API de Resultados Electorales, Ministerio del Interior** (`resultados.mininterior.gob.ar`). El repositorio usa dos endpoints:

| Endpoint | Uso | Particularidad |
|---|---|---|
| `GET /api/resultados/getResultados` | JSON agregado (totalizado o por mesa), según los parámetros que reciba | Documentado públicamente |
| `GET /api/resultado/totalizadocsv` | CSV con **todas las mesas** de una categoría en un solo pedido | No documentado; se identificó leyendo el bundle JS del sitio (`app.js`). Es la vía preferida: más rápida, no genera cientos de archivos de caché |

**Parámetros de alcance geográfico** usados en todo el proyecto (fijos para La Plata, pero el cliente los recibe como argumento — no están hardcodeados en `client.py`):

- `distritoId = 2` → Buenos Aires
- `seccionProvincialId = 8` → Sección Capital
- `seccionId = 63` → La Plata

**Categorías cubiertas** (`categoriaId` / `idCargo`, estable en los años relevados para esta sección):

| Cargo | categoriaId | Nivel |
|---|---|---|
| Presidente | 1 | nacional (ejecutivo) |
| Senador Nacional (solo 2017) | 2 | nacional |
| Diputados Nacionales | 3 | nacional (legislativo) |
| Gobernador | 4 | provincial (ejecutivo) |
| Senadores Provinciales | 5 | provincial |
| Diputados Provinciales | 6 | provincial (legislativo) |
| Intendente | 7 | municipal (ejecutivo) |
| Concejales | 10 | municipal (legislativo) |

**Instancias electorales**: Generales (`tipoEleccion=2`) para todos los años y cargos; PASO (`tipoEleccion=1`) para todas las combinaciones ya cubiertas; balotaje (`tipoEleccion=3`) para Presidente en 2015 y 2023, únicos años en que hubo segunda vuelta.

**Cobertura temporal**: cargos ejecutivos 2011/2015/2019/2023; cargos legislativos 2013/2017/2021/2025.

---

## 3. Pipeline: de la API cruda al dato analítico

### 3.1 Descarga y caché (`ResultadosClient`)

Cada consulta se cachea en disco antes de devolverse; una segunda ejecución no vuelve a golpear la API salvo `force_refresh=True`. La estructura de caché sigue el patrón `data/distrito/<año>/<cargo>/<etapa>/`, con dos artefactos por consulta: el JSON agregado crudo y el CSV oficial con detalle de mesa.

### 3.2 Normalización de `circuito_id`

El mismo circuito se identifica con distinto ancho de ceros según el año (`"0460"` en 2011/2015, `"000460"` en 2019, `"00460"` en 2023). Se normaliza a una forma canónica (sin ceros a la izquierda, conservando sufijos de letra por subdivisión — ej. `"0496F"` → `"496F"`) antes de agregar. La correspondencia entre el id crudo de cada año y el canónico queda versionada (`data/agrupaciones/circuito_id_correspondencias.csv`).

### 3.3 Libro de códigos ideológico

`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` es un archivo curado a mano, nunca regenerado ni sobrescrito automáticamente: cada corrida compara las agrupaciones que devuelve la API contra las ya clasificadas y, si hay una nueva, la agrega con la clasificación vacía en vez de fallar en silencio o inventar un valor. Trae dos columnas de clasificación, ortogonales entre sí:

- **`campo_ideologico`** (escala 1–6, izquierda → derecha radical): posición ideológico-programática, puede variar elección a elección para una misma alianza.
- **`filiacion_politica`**: familia/identidad partidaria (peronistas, progresistas, liberales, marxistas, nacionalistas, conservadores, peronismo provincial, otros), estable en el tiempo para una misma agrupación. Se incorporó para evitar que una genealogía política continua (ej. FPV → Unidad Ciudadana → Frente de Todos → Unión por la Patria) se leyera como ideológicamente errática solo por el cambio de nombre de lista.

El cruce contra `circuito_<nivel>.json` es un join exacto por año/nivel/nombre; si una agrupación no está clasificada, el pipeline falla explícitamente (`KeyError`) en vez de guardar el dato sin clasificar.

### 3.4 `circuito_<nivel>.json`: el dato analítico central

`data/distrito/<año>/<nivel>/generales/circuito_<nivel>.json` agrega, por `circuito_id`, los votos `positivos` (por agrupación, con `campo_ideologico`) y los `otros` (blanco, nulo, recurrido, impugnado, comando — lo que exista ese año). Se construye **siempre desde el CSV oficial**, no desde el JSON agregado crudo de la API. Cada archivo trae además:

- `fuente`, `coincide_con_agregado_json`, `advertencia_fuente`: trazabilidad de si la suma por circuito coincide con el agregado crudo de la misma consulta.
- `cobertura`: mesas totalizadas, electores, votantes, % de participación, tal como los expone la API.
- `mesas_sin_votos_positivos` por circuito: señal para revisión manual, no una clasificación automática de causa.

**Anomalías detectadas y documentadas explícitamente (no corregidas por omisión):**

- *Presidente 2019*: el JSON agregado crudo subestima ~16x los votos positivos reales (27.567 vs. 418.164 del CSV oficial). `circuito_presidente.json` de ese año ya sale del CSV correcto, pero el JSON agregado crudo se conserva en el repositorio tal cual se cacheó, con la discrepancia marcada en sus propios metadatos.
- *Circuitos con más votos emitidos que electores registrados* (`ausentismo` negativo): en al menos una combinación (año, nivel) apareció este caso, asociado a un problema de asignación de electores entre subdivisiones de circuito y no a un error de conteo. Como la numeración de circuitos es propia de cada distrito y no generaliza, el pipeline no identifica estos casos por `circuito_id` puntual en el código ni en este documento — los detecta genéricamente cualquier vez que ocurren: `graficar_torta` reconoce cualquier categoría negativa y muestra un aviso en vez de graficar una torta imposible; `graficar_barras` sí grafica el valor negativo tal cual, para no ocultar la anomalía subyacente de padrón.

### 3.5 Totales agregados

`src/electoral/totales.py` suma los `positivos` de todos los circuitos de un (año, nivel) con una función de propósito general (`totalizar_agrupaciones`), y escribe `data/totales/<nivel>/<año>/resultado_total.csv`. Es el nivel de agregación final del pipeline central: distrito completo, por (año, nivel).

**Extensión opcional — agrupamiento por localidad/barrio.** El repositorio incluye además un mecanismo (`src/electoral/localidades.py`) para reagrupar los mismos resultados en unidades intermedias entre circuito y distrito (localidad/barrio), pero esto depende de una fuente externa de correspondencia `circuito_id → localidad` que **no existe de forma estandarizada para cualquier distrito** — para La Plata se construyó a partir de una resolución ministerial puntual (1990/2007) complementada con relevamiento periodístico, con niveles de confianza declarados y sin mezclar por defecto. Al tratarse de una fuente ad hoc, esta capa se documenta como una posibilidad de extensión del pipeline, condicionada a que el distrito de interés cuente con una fuente equivalente, y no como parte del flujo central descripto en las secciones 3.1–3.4.

---

## 4. Datos que se obtienen: resumen por artefacto

| Artefacto | Ruta | Granularidad | Contenido |
|---|---|---|---|
| JSON agregado crudo | `data/distrito/<año>/<cargo>/<etapa>/*.json` | consulta completa | tal cual lo devuelve la API |
| CSV oficial | `data/distrito/<año>/<cargo>/<etapa>/*.csv` | mesa | detalle oficial de votos por mesa |
| `circuito_<nivel>.json` | `data/distrito/<año>/<nivel>/generales/` | circuito | positivos por agrupación + campo ideológico, otros, cobertura, metadatos de procedencia |
| `resultado_total.csv` | `data/totales/<nivel>/<año>/` | (año, nivel) | votos y % por agrupación, todo el distrito |

*(La agrupación por localidad, al depender de una fuente de correspondencia específica de cada distrito, se trata aparte como extensión opcional — ver sección 3.5.)*

---

## 5. Visualizaciones producidas

Todo gráfico que desglosa por campo ideológico o filiación política suma siempre `blanco_nulo` (votos en blanco + nulos) y `ausentismo` (electores del alcance menos sus votos válidos, restando también los procedimentales del año aunque estos últimos no se grafican como categoría propia), en gris, para no competir con la paleta divergente azul-rojo de la ideología. Esto significa que el porcentaje que muestra cada categoría es, en rigor, "% del padrón" y no "% de los votos positivos".

| Módulo | Qué produce | Unidad temporal/espacial | Comando |
|---|---|---|---|
| `graficos.py` | Barras y torta por campo ideológico, para un circuito puntual o el acumulado del (año, nivel) | funciones reutilizables, sin escribir archivo por sí solas | uso programático (notebook) |
| `generar_graficos.py` | Barras + torta circuito por circuito, más un acumulado, para un (año, nivel) | por circuito y agregado | `python -m analisis.generar_graficos --anio 2011 --nivel intendente` |
| `serie_temporal.py` | Un gráfico por nivel de gobierno (nacional/provincial/municipal), línea por campo ideológico, 2011–2025, combinando cargo ejecutivo + legislativo en una serie continua | serie temporal, todo el distrito | `python -m analisis.serie_temporal` |
| `serie_temporal_filiacion.py` | Igual formato que el anterior pero por `filiacion_politica` en vez de `campo_ideologico`; solo versión en porcentaje | serie temporal, todo el distrito | `python -m analisis.serie_temporal_filiacion` |
| `cuadros_anualizados.py` | Un gráfico por año, con todos los cargos disputados ese año lado a lado (sin sumarlos entre sí) | foto de un año, por cargo | `python -m analisis.cuadros_anualizados --anio 2023` |
| `totales_por_lista.py` | Barras horizontales, resultado total por agrupación (lista) + blanco/nulo, un gráfico por (año, nivel) | (año, nivel), todo el distrito | `python -m analisis.totales_por_lista --anio 2023 --nivel intendente` |
| `comparativo_nivel.py` | Cuadro Markdown por año: % de cada agrupación en Municipio/Provincia/Nación + diferencias en puntos porcentuales | (año), tres cargos comparados | `python -m analisis.comparativo_nivel --anio 2019` |

Además de esta tabla, existen dos módulos (`cuadros_por_localidad.py`, `serie_temporal_por_localidad.py`) que replican los cuadros y series temporales anteriores pero a nivel de localidad/barrio en vez de distrito completo. Se dejan fuera de la tabla central porque, a diferencia del resto, no dependen únicamente de `circuito_<nivel>.json`: requieren la fuente de correspondencia circuito→localidad descripta como extensión opcional en la sección 3.5.

**Convenciones de salida**: `graficos/distrito/serie_temporal/` y `graficos/distrito/totales_por_lista/` están versionados en git; el resto de `graficos/distrito/<año>/<nivel>/` (circuito por circuito) se regenera on demand y está en `.gitignore`, por volumen (miles de archivos) y porque se reconstruye en segundos desde `data/`.

---

## 6. Decisiones metodológicas relevantes para una lectura académica del dato

- **Nunca se recorta ni se oculta una anomalía**: se documenta en los metadatos del propio artefacto (`advertencia_fuente`, avisos en gráfico) y se sigue usando el dato, salvo que directamente invalide la visualización (torta con valor negativo).
- **Ausentismo y blanco/nulo son categorías de primera clase**, no un residuo: aparecen en todo desglose ideológico o de filiación, lo que cambia la lectura de "% de los positivos" a "% del padrón".
- **Ideología y filiación son ejes distintos y ambos declarados a mano**, con su criterio de clasificación documentado aparte (no inferido automáticamente de los datos electorales).
- **Ningún total se calcula dos veces con criterios distintos**: `totales_por_lista.py` reutiliza `resultado_total_por_agrupacion`; `comparativo_nivel.py` reutiliza esos mismos porcentajes en vez de recalcularlos.
- **El cruce entre cargos del mismo año se hace por nombre exacto de agrupación**, verificado contra los datos (no asumido) que las alianzas corren con el mismo nombre en los tres niveles ese año.

---

## 7. Modo exacto de uso

### 7.1 Instalación

```bash
pip install -r requirements.txt
```

No requiere API key (endpoint público); sí requiere acceso de red saliente a `resultados.mininterior.gob.ar`. Las dependencias relevantes para esta capa son `requests`, `pandas` y `pytest`; `geopandas`/`dbfread` son de la capa socioeconómica, fuera de este documento.

### 7.2 Orden de ejecución para reconstruir los datos desde cero

El pipeline se ejecuta con notebooks, en este orden, porque cada uno depende de artefactos que escribe el anterior:

1. **`notebooks/01_explorar_resultados.ipynb`** — no escribe datos de uso posterior; solo muestra cómo se usa `ResultadosClient` y `ResultadoElectoral.from_json` sobre un caso único, a modo de introducción a la API cruda (ver ejemplo mínimo en 7.3).
2. **`notebooks/02_la_plata_cargos_ejecutivos.ipynb`** — trae CSV oficial + JSON agregado de cada (año, cargo ejecutivo), y valida/actualiza `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`.
3. **`notebooks/03_la_plata_legislativas.ipynb`** — mismo patrón que el anterior, para los cargos legislativos.
4. **`notebooks/04_totales_por_circuito.ipynb`** — normaliza `circuito_id`, agrega por circuito, cruza contra el libro de códigos ideológico, y escribe `circuito_<nivel>.json` (el insumo del que dependen todos los módulos de `src/analisis/`).

Si la caché en `data/` ya existe, los notebooks corren instantáneo (leen de disco, no repiten la consulta a la API); para forzar una actualización real hay que pasar `force_refresh=True` a los métodos del cliente.

### 7.3 Ejemplo mínimo de uso programático del cliente

```python
import sys
from pathlib import Path
sys.path.insert(0, "src")

from electoral.client import ResultadosClient
from electoral.models import ResultadoElectoral

client = ResultadosClient(cache_dir=Path("data") / "distrito")

consulta = dict(
    anio_eleccion=2011,
    categoria_nombre="presidente/generales",  # organiza el caché en data/distrito/2011/presidente/generales/
    tipo_eleccion=2,          # Generales
    categoria_id=1,           # PRESIDENTE
    distrito_id=2,            # Buenos Aires
    seccion_provincial_id=8,  # Sección Capital
    seccion_id=63,            # La Plata
)

raw = client.get_resultados(**consulta)                    # JSON crudo, cacheado en disco
resultado = ResultadoElectoral.from_json(raw, consulta=consulta)  # parseo tipado

for agrupacion in sorted(resultado.valores_totalizados_positivos, key=lambda v: v.votos, reverse=True):
    print(f"{agrupacion.votos_porcentaje:5.2f}%  {agrupacion.votos:>7}  {agrupacion.nombre_agrupacion}")
```

### 7.4 Comandos exactos para generar cuadros y gráficos

Una vez que existe `circuito_<nivel>.json` (paso 4 de 7.2), los módulos de `src/analisis/` se ejecutan como scripts desde la raíz del repositorio, con `PYTHONPATH=src`:

```bash
# Totales por agrupación (data/totales/)
PYTHONPATH=src python -m electoral.totales --anio 2023 --nivel intendente
PYTHONPATH=src python -m electoral.totales                    # todas las combinaciones disponibles

# Barras + torta, circuito por circuito y acumulado (graficos/distrito/<año>/<nivel>/)
PYTHONPATH=src python -m analisis.generar_graficos --anio 2011 --nivel intendente

# Serie temporal por campo ideológico, un gráfico por nivel de gobierno
PYTHONPATH=src python -m analisis.serie_temporal                    # los 3 niveles
PYTHONPATH=src python -m analisis.serie_temporal --nivel provincial # uno puntual

# Serie temporal por filiación política
PYTHONPATH=src python -m analisis.serie_temporal_filiacion

# Cuadro por año con todos los cargos de ese año lado a lado
PYTHONPATH=src python -m analisis.cuadros_anualizados --anio 2023
PYTHONPATH=src python -m analisis.cuadros_anualizados               # todos los años disponibles

# Barras horizontales por agrupación (lista), un gráfico por (año, nivel)
PYTHONPATH=src python -m analisis.totales_por_lista --anio 2023 --nivel intendente
PYTHONPATH=src python -m analisis.totales_por_lista                 # todo lo disponible

# Cuadro Markdown comparativo Municipio/Provincia/Nación, por año
PYTHONPATH=src python -m analisis.comparativo_nivel --anio 2019
PYTHONPATH=src python -m analisis.comparativo_nivel                 # todos los años disponibles
```

Cada comando admite `--data-dir`/`--graficos-dir`/`--salida-dir` (según el módulo) para redirigir la lectura/escritura si no se corre desde la raíz del repositorio; por defecto apuntan a `data/distrito`, `graficos/distrito` y `data/totales` respectivamente.

### 7.5 Tests

```bash
pytest
```

`pytest.ini` fija `pythonpath = src` y `testpaths = tests`, así que no hace falta exportar `PYTHONPATH` a mano para correr la suite.

---

## 8. Reproducibilidad

Todo el pipeline corre en caché local una vez descargado: los notebooks 01–04 no vuelven a golpear la API salvo pedido explícito. La secuencia completa (adquisición → normalización → clasificación → agregación por circuito → totales/localidades → gráficos) queda determinada por los datos en `data/`, no por estado oculto, lo que permite reconstruir cualquier gráfico desde cero solo con el repositorio y sin credenciales de acceso a la API.