# Plan de correcciones y ampliaciones — Resultados electorales La Plata (2011–2025)

> Documento de trabajo. Responde puntualmente a la parte técnica (sección 8, "Auditoría del repositorio v1.0.0") de `Nota_metodologica_La_Plata_para_Ivan.docx`, acotado al código y los datos de este repositorio. **No** aborda la agenda de investigación sociológica de la nota (problema de investigación, hipótesis H1–H8, plan de variables de clase/censo/EPH) — eso queda para discutir aparte.
>
> Alcance temporal: 2011–2025 (el rango real del repo y de la nota). Cada punto fue verificado directamente contra el código y los datos del commit `f2e0382`, no solo tomado de la nota — donde la verificación agrega o corrige algo, se indica.
>
> **Estado (actualizado):** del punto 1 (prioridad inmediata) está resuelto **todo**, incluido el 1.1 (tachados abajo, con nota de qué se hizo realmente en cada caso). 1.1 se resolvió con un mecanismo de detección de agrupaciones nuevas en vez de la separación en dos archivos que proponía originalmente el punto (esa separación queda como mejora opcional a futuro). Del punto 2, **2.3 y 2.5 están parcialmente resueltos** (2.3: traer PASO y balotaje; 2.5: capa socioeconómica EPH/Censo — ambos tachados abajo); 2.1, 2.2 y 2.4 y el punto 3 siguen enteros, sin empezar. Del punto 4, sigue sin empezar lo específico del pipeline electoral, pero hay progreso lateral (tests nuevos, `geopandas` en uso) — ver abajo.
>
> **Validación de esta corrida**: se reejecutaron los 4 notebooks (01→04) de punta a punta, `generar_graficos.py` para los 22 (año, nivel), `serie_temporal.py` y la suite de `pytest` (26/26). Todo corrió sin errores. **El bug de §1.1 se reprodujo en vivo** (los notebooks 02/03 volvieron a pisar `agrupaciones.csv`/`agrupaciones_legislativas.csv` con la versión de 3 columnas) — se restauró la clasificación desde una copia antes de correr el notebook 04, como ya viene siendo la rutina manual para evitar perderla. De paso se encontraron y borraron 2.902 PNG huérfanos (nombres de circuito con el formato viejo, pre-normalización de §1.3). **Actualización posterior**: ese mismo bug se resolvió después en esta sesión — ver §1.1 más abajo, ya tachado. Reejecutar 02→03 ahora dos veces sobre el estado actual (con y sin cambios reales) confirmó que el archivo queda intacto cuando no hay agrupaciones nuevas.
>
> **Actualización (v3.1.0, revisión completa de esta sección):** verificado contra el estado real del repo, no asumido. **2.2 resuelto** (`filiacion_politica`, ver más abajo) — corrige la creencia inicial de que seguía entero. **2.1 sigue sin resolver** — verificado de nuevo con grep sobre todo el repo: `campo_ideologico.csv` sigue con cero lecturas, `graficos.py` sigue con el dict `IDEOLOGIAS` hardcodeado. **2.3 sigue igual que antes** (parcial) — notebook 04 sigue sin generar `circuito_<nivel>.json` para `paso/`/`balotaje`, y el mapeo de nombres con grafía distinta más allá de mayúsculas tampoco se hizo (ver ejemplo verificado en 2.3). La Sección 3 tiene progreso real desde la última revisión (de ~9 filas sin `campo_ideologico` a 4) y ahora además tiene `filiacion_politica` como columna nueva. La Sección 4 no tuvo movimiento propio en esta sesión (los puntos siguen abiertos), salvo un dato nuevo: el patrón de manejo de errores demasiado amplio que señalaba se replicó sin querer en `serie_temporal_filiacion.py` (nuevo en v3.1.0) — ver detalle abajo.
>
> **Actualización (auditoría posterior a la reorganización `data/distrito/` y a la capa de macroeconomía, con la suite en 181 tests):** revisión completa de todo el documento contra el estado real del repo (no contra lo que este documento asumía). Varios puntos que seguían "parciales" avanzaron sin que nadie actualizara esta nota: **2.3 ya no es parcial en la mitad que importaba** — `notebooks/04_totales_por_circuito.ipynb` sí genera `circuito_<nivel>.json` para `paso`/`balotaje` (44 archivos totales: 22 generales + 20 paso + 2 balotaje, verificado exhaustivamente contra disco) y `electoral/totales.py` ya soporta `etapa` con tests dedicados (`test_etapa_paso_lee_su_propio_circuito_json`, etc.) — la sección de abajo se corrige para reflejar esto y documentar el gap real que queda (la capa de análisis/gráficos, no la de agregación). **Sección 3 mejoró de nuevo** sin quedar registrado: de las 4 agrupaciones sin clasificar que señalaba la revisión anterior, siguen sin clasificar solo esas mismas 4 (verificado por nombre exacto, ver más abajo) — es decir no empeoró, pero tampoco nadie las cerró. **2.1 y 2.4 siguen exactamente igual** (re-verificado, no solo asumido). En esta sesión además: (a) se agregaron 47 tests nuevos cubriendo la lógica pura de `src/analisis/graficos.py`, `serie_temporal.py`, `serie_temporal_filiacion.py`, `totales_por_lista.py`, `comparativo_nivel.py` y `cuadros_anualizados.py` (0 tests antes de hoy en los seis; suite 181→228), cerrando la mitad de la sección "Sin tests" de §4 que seguía abierta; (b) se resolvió "Rutas frágiles" de §4 (los 6 notebooks, incluidos 05/06 que no existían cuando se escribió ese punto, dependían de `Path.cwd().parent`). El resto de §4 (manejo de errores amplio, `requirements.txt` sin versiones, falta de procedencia, peso del repo) no se tocó y sigue exactamente como estaba.

## Cómo está armado este documento

Cada ítem tiene: **qué archivo(s) toca**, **qué está mal hoy** (con evidencia concreta) y **qué habría que hacer**. Están agrupados en las mismas tres prioridades que propone la nota, porque el orden ya es razonable: primero lo que corrompe datos o bloquea reproducir el pipeline, después lo que amplía cobertura, al final lo que endurece el proyecto técnicamente.

---

## 1. Prioridad inmediata

### ~~1.1 El pipeline reproducible borra la clasificación ideológica manual~~

**Estado: resuelto**, con un enfoque distinto al que proponía originalmente este punto. En vez de separar en dos archivos (oferta automática + libro de códigos manual, unidos por un merge explícito — la opción "correcta" a largo plazo, todavía no hecha), se optó por una solución más chica y ya probada: los notebooks 02 y 03 ya no regeneran `agrupaciones.csv`/`agrupaciones_legislativas.csv` desde cero. El último paso de cada uno ahora arma la tabla que devuelve la API, la compara por clave exacta (`anio`, `nivel`, `agrupacion`) contra el archivo ya existente en disco, y:
- si no hay agrupaciones nuevas, **no toca el archivo** (lo informa nada más);
- si hay alguna nueva, la **imprime explícitamente** (aviso, no falla silenciosa) y la agrega al final con `campo_ideologico` vacío, sin sobrescribir ni reordenar las filas existentes.

Se probaron ambos caminos corriendo los notebooks 02 y 03 de punta a punta: (a) sin cambios reales, el archivo queda **bit a bit idéntico** (mismo `md5sum` antes y después); (b) sacando a mano una fila ya clasificada (simulando una agrupación "nueva"), el notebook la detectó, avisó, y la agregó con `campo_ideologico` vacío sin tocar el resto — se restauró el valor original después de confirmar el comportamiento. README actualizado (ya no hace falta la advertencia de "hacer una copia antes de correr 02/03").

**Qué queda pendiente, más allá de esto**: la separación en dos archivos (automático + libro de códigos manual) sigue siendo la solución más prolija a largo plazo — hoy `agrupaciones.csv` sigue siendo un solo archivo con dos roles mezclados, solo que ahora protegido contra sobrescritura accidental en vez de separado. Si en algún momento se decide hacer esa separación, este mismo mecanismo de detección de "nuevas" se puede trasladar ahí.

- ~~**Archivos**: `notebooks/02_la_plata_cargos_ejecutivos.ipynb`, `notebooks/03_la_plata_legislativas.ipynb`, `data/agrupaciones/agrupaciones.csv`, `data/agrupaciones/agrupaciones_legislativas.csv`.~~
- ~~**Qué está mal**: el notebook 02 arma `df_agrupaciones` con las columnas `anio, agrupacion, nivel` y hace `df_agrupaciones.to_csv(destino / "agrupaciones.csv", index=False)`. El notebook 03 hace lo mismo para `agrupaciones_legislativas.csv`. Ambos escriben **3 columnas**. Pero los archivos que hoy están en disco tienen **4 columnas** (`anio,agrupacion,nivel,campo_ideologico`), y esa 4ª columna fue agregada a mano por fuera del código de los notebooks. El notebook 04 (`04_totales_por_circuito.ipynb`) necesita esa columna: `cargar_clasificacion()` la lee con `csv.DictReader` y `agregar_campo_ideologico()` hace `CLASIFICACION[(str(anio), nivel_csv, info["nombre"])]`, que tira `KeyError` si la clave no está. Conclusión: **volver a correr el pipeline desde cero (notebook 01→04, como indica el README) sobrescribe la clasificación manual y rompe el paso 4**. Este riesgo ya está documentado explícitamente en el README (sección "Advertencia sobre `campo_ideologico`"), pero el problema de fondo (dos roles mezclados en un mismo archivo) sigue sin resolverse.~~
- **Qué hacer** (lo que falta, opcional): separar en dos archivos con roles distintos —
  1. Un archivo *automático* de oferta electoral (lo que ya generan los notebooks 02/03: `anio, agrupacion, nivel`), que se puede regenerar sin costo.
  2. Un archivo *manual y versionado* del libro de códigos (`agrupacion → campo_ideologico`, sin repetir año/nivel si la clasificación no depende de eso, o con año/nivel si sí depende — ver §3).
  3. Un paso de `merge` explícito (left join de 1 sobre 2, por la clave que se decida) que sea el único lugar donde `agrupaciones.csv`/`agrupaciones_legislativas.csv` con 4 columnas se generan.

### ~~1.2 Clasificaciones ideológicas con error confirmado~~

**Estado: resuelto.** Se corrigió `data/agrupaciones/agrupaciones.csv`: Frente Popular (Duhalde) 2011 pasó de `2` a `3` en `gobernacion`/`intendente`/`presidente`; Progresistas 2015 pasó de `3` a `2` en `gobernacion`/`presidente` (ya estaba en `2` en `intendente`, ahora consistente en los tres cargos). Los valores finales los fijó Ivan explícitamente (no una inferencia automática). Se regeneraron los `circuito_<nivel>.json` de 2011 y 2015 corriendo el notebook 04 contra la caché en disco. El resto de la clasificación ideológica (§3) sigue sin tocarse.

- ~~**Archivo**: `data/agrupaciones/agrupaciones.csv` (y el libro de códigos manual que salga de 1.1).~~
- ~~**Frente Popular (Duhalde) 2011**: hoy `campo_ideologico=2` (centroizquierda) en los tres cargos ejecutivos (`gobernacion`, `intendente`, `presidente`). Con la escala 1–6 del proyecto (1=izquierda … 6=derecha radical), ubicar a Duhalde en centroizquierda no es defendible sin una justificación explícita — la nota calcula el peso de este cambio: Presidente 27.275 votos (7,69% de los positivos), Gobernador 19.745 (5,97%), Intendente 24.291 (6,90%). Corregir el valor y regenerar cualquier gráfico/serie que dependa de `circuito_<nivel>.json` para 2011.~~
- ~~**Progresistas 2015**: hoy `campo_ideologico=3` (centro) para `gobernacion` y `presidente`, pero `2` (centroizquierda) para `intendente` — misma alianza, mismo año, clasificación distinta según el cargo. Si la unidad que se clasifica es la alianza (no la candidatura/programa por nivel), esto es una inconsistencia a resolver. La alianza reunió GEN, Partido Socialista y Libres del Sur y se presentó públicamente como centroizquierda, así que sostener "centro" en Presidente/Gobernador requiere justificación específica si no se corrige.~~
- ~~**Qué hacer**: fijar el valor correcto para ambos casos (documentando la razón, no solo el número), y dejar registrado en el libro de códigos (§3) si la unidad de clasificación es la alianza o el nivel/candidatura — para que este tipo de caso no vuelva a aparecer como "inconsistencia accidental".~~

### ~~1.3 `circuito_id` no está normalizado entre años~~

**Estado: resuelto.** `notebooks/04_totales_por_circuito.ipynb` normaliza `circuito_id` a una forma canónica (sin ceros a la izquierda, conservando sufijos de letra por subdivisión como `0496F`→`496F`) antes de agregar, y versiona la correspondencia cruda→canónica en `data/agrupaciones/circuito_id_correspondencias.csv`. Verificado tras normalizar: 66 circuitos comunes a los 4 años ejecutivos de La Plata, con `493`, `496F`, `504C` como casos variables — coincide con el orden de magnitud que reporta la nota (66 comunes a los ocho puntos de la serie nacional, mismos tres casos variables) y quedan marcados para revisión manual de límites, no re-normalizados a la fuerza.

- ~~**Archivos**: `notebooks/04_totales_por_circuito.ipynb` (función `agregar_por_circuito`), `data/<año>/<nivel>/circuito_<nivel>.json`.~~
- ~~**Qué está mal**: el mismo circuito aparece con formato distinto según el año — verificado leyendo los 4 `circuito_intendente.json`: `"0460"` (2011), `"0460"` (2015), `"000460"` (2019), `"00460"` (2023). El único tratamiento que existe hoy sobre `circuito_id` es `df["circuito_id"] = df["circuito_id"].str.strip()` (recorte de espacios en blanco) — nunca se homogeneizan ceros a la izquierda. `src/electoral/client.py` no toca `circuito_id` en absoluto. La única normalización de IDs que existe en el proyecto (`normalizar_id`, con `lstrip("0")`) se usa para comparar `agrupacion_id`, no `circuito_id`. Consecuencia directa: **cualquier cruce de un mismo circuito entre años (serie temporal por circuito, cruce con Censo) falla en silencio por no-match de string**, sin ningún error que lo señale.~~
- ~~**Qué hacer**: elegir una representación canónica de `circuito_id` (ej. sin ceros a la izquierda, o con un ancho fijo documentado) y aplicarla al leer el CSV oficial, antes de cualquier agregación — no como parche posterior. Construir y versionar una tabla de correspondencias entre los identificadores crudos de cada año y el id canónico. La nota reporta que, tras normalizar el relleno de ceros, hay 66 identificadores comunes a los ocho puntos de la serie nacional, con `0493`, `0496F` y `0504C` como casos variables que requieren revisión manual de límites (altas/bajas/subdivisiones de circuito), no solo normalización de formato.~~

### ~~1.4 Falta un indicador de cobertura por circuito~~

**Estado: resuelto, con una salvedad real.** Cada circuito en `circuito_<nivel>.json` trae ahora `mesas_sin_votos_positivos` (verificado: 37 en Presidente 2023, 47 en Gobernador e Intendente 2023, en 26 circuitos — el 37 coincide exacto con la nota, el 46/47 difiere en 1 mesa, probablemente por método de conteo levemente distinto). Cada archivo trae además `cobertura`, reutilizando `EstadoRecuento` (`src/electoral/models.py`) tal como pide el plan. **Salvedad no anticipada al escribir el plan**: `mesas_esperadas` y `mesas_totalizadas_porcentaje` vienen siempre en `0` para las 22 combinaciones (año, nivel) ya descargadas, porque la API no completa esos campos para elecciones cerradas/históricas (solo tendrían valor en una consulta en vivo). Se documentó esto en el README en vez de simular un % de cobertura que la fuente no da. La clasificación causal de las mesas en cero (padrón sin categoría vs. no escrutado real) sigue sin hacerse — `mesas_sin_votos_positivos` es la señal, no el diagnóstico.

- ~~**Archivos**: `notebooks/04_totales_por_circuito.ipynb`, `src/electoral/models.py` (`EstadoRecuento`).~~
- ~~**Qué está mal**: el pipeline cuenta mesas y electores por circuito, pero no calcula ningún indicador de cobertura/completitud. Verificado: 37 mesas con 0 votos positivos en Presidente 2023 (agrupando el CSV oficial por `mesa_id`), consistente con lo que reporta la nota (37 para Presidente, 46 para Gobernador e Intendente, en 26 circuitos). También hay mesas nativas marcadas `NO ESCRUTADO` en 2025 según la nota. Hoy no hay ninguna variable que distinga "mesa con cero votos legítimo" (ej. padrón de extranjeros en categorías nacionales) de "mesa con cero votos porque falta escrutar".~~
- ~~**Qué hacer**: agregar, por circuito, un indicador de cobertura (mesas escrutadas / mesas esperadas, electores computados / electores del padrón) reutilizando los campos que `EstadoRecuento` (`src/electoral/models.py`) ya expone crudos de la API (`mesas_esperadas`, `mesas_totalizadas`, `mesas_totalizadas_porcentaje`) en vez de recalcularlos desde cero. Clasificar los casos de cero votos (padrón de extranjeros vs. no escrutado real) y dejar la clasificación documentada, no borrar los ceros ni tratarlos todos como faltantes.~~

### ~~1.5 Anomalía del JSON agregado de Presidente 2019 — falta documentarla, no corregir datos~~

**Estado: resuelto.** Cada `circuito_<nivel>.json` trae ahora `fuente` (siempre `"csv"`), `coincide_con_agregado_json` y `advertencia_fuente`; para 2019/presidente estos dos últimos quedan en `false` y con el texto de la anomalía, respectivamente. El README documenta el caso en una sección propia ("Anomalía conocida: JSON agregado de Presidente 2019"). El JSON agregado crudo en caché no se tocó (es el crudo tal como lo devolvió la API en su momento); lo que cambió es que ahora hay una señal explícita, dentro del dato mismo, de que no hay que usarlo.

- ~~**Archivos**: `data/2019/presidente/` (JSON agregado crudo vs. CSV oficial vs. `circuito_presidente.json`), `README.md`.~~
- ~~**Qué está mal**: el JSON agregado crudo en caché reporta `mesasTotalizadas=96` y 27.567 votos positivos; el CSV oficial de la misma consulta tiene 1.517 mesas y 418.164 votos positivos — una subestimación de ~16x. **Verificación importante**: el archivo derivado que realmente se usa para graficar/analizar, `circuito_presidente.json`, ya está bien — se construye desde el CSV (no desde el JSON agregado) y su suma da exactamente 418.164. O sea, el dato analítico ya es correcto; lo que falta es la señal de que hubo que descartar el agregado crudo por no confiable, y que el README no menciona esta anomalía en ningún lado (el único uso de "2019" en el README es en la lista de años cubiertos).~~
- ~~**Qué hacer**: (a) agregar una nota en el README sobre este caso conocido y por qué el pipeline usa el CSV y no el JSON agregado para construir `circuito_<nivel>.json`; (b) agregar un metadato dentro de cada `circuito_<nivel>.json` (o un archivo de acompañamiento) que registre la fuente operativa usada (CSV vs. JSON agregado) y si hubo descarte de una fuente por inconsistencia, para que un análisis futuro no tenga que releer los notebooks para saberlo. Ningún paso futuro debería tomar los totales del JSON agregado de este caso.~~

### ~~1.6 README con afirmaciones que no corresponden al estado real de los datos~~

**Estado: resuelto**, salvo el punto sobre la capa socioeconómica y el libro de códigos, que se documentaron como pendientes en vez de resueltos (correctamente, porque siguen sin existir). El README ahora aclara las 4 columnas reales vs. las 3 que generan los notebooks (con advertencia de que re-correr 02/03 sobrescribe la clasificación manual — ligado a §1.1, que sigue abierto), corrige la afirmación de años pares/impares, documenta la anomalía 2019, el indicador de cobertura y su limitación, agrega una sección de estado de la capa socioeconómica, una sección de estado del libro de códigos, y completa el paso 3 de "Extender a otro distrito, sección o cargo" con el resto del flujo (agregación normalizada + join con libro de códigos).

- ~~**Archivo**: `README.md`.~~
- ~~**Qué está mal (verificado)**:~~
  - ~~Describe `agrupaciones.csv`/`agrupaciones_legislativas.csv` como `(anio, agrupacion, nivel)` — 3 columnas — cuando los archivos reales en disco tienen 4 (`+ campo_ideologico`).~~
  - ~~Dice que "cada nivel combina su cargo ejecutivo (**años pares**) y su cargo legislativo (**años impares**)" — falso: todos los años del dataset son impares (ejecutivos 2011/2015/2019/2023, legislativos 2013/2017/2021/2025). No hay ningún año par en el proyecto.~~
  - ~~No documenta la anomalía de 2019 (§1.5), ni la existencia de mesas con cero votos o no escrutadas (§1.4), ni el libro de códigos ni sus casos dudosos (§3).~~
  - ~~No aclara que la capa socioeconómica (Censo/EPH) anunciada en el nombre del repositorio todavía no existe.~~
  - ~~La última línea del README (`3. Usar get_resultados_csv para traer los datos`) es gramaticalmente completa —no está cortada a mitad de oración, a diferencia de lo que sugiere la nota— pero sí es escueta comparada con el detalle de los pasos 1 y 2 de la misma lista: no dice qué hacer después de traer el CSV (correr la agregación por circuito, unir con el libro de códigos, etc.).~~
- ~~**Qué hacer**: corregir las 4 columnas, corregir "años pares/impares" por "todas las elecciones son en años impares — se listan generales ejecutivas y legislativas intermedias", agregar una sección sobre estado de la capa socioeconómica (no implementada todavía), documentar la anomalía 2019 y las mesas con cobertura incompleta, y completar el último paso de la sección "Extender a otro distrito, sección o cargo" con el resto del flujo (agregación + join con libro de códigos).~~

---

## 2. Segunda etapa

### ~~2.1 Fuente de la escala ideológica duplicada~~

**Estado: resuelto.** `graficos.py` ya no hardcodea el dict `IDEOLOGIAS` — lo carga de `data/agrupaciones/campo_ideologico.csv` en tiempo de import, vía `_cargar_escala_ideologica()` (ruta resuelta con `Path(__file__).resolve().parents[2]`, no depende del cwd desde el que se importe el módulo — mismo criterio de robustez que se aplicó a los notebooks en §4). El CSV se pasó de `;` a `,` como separador, consistente con el resto de `data/agrupaciones/`. `IDEOLOGIAS` sigue siendo un dict de módulo con el mismo contenido y el mismo orden (izquierda→derecha radical) que antes, así que los cinco consumidores existentes (`cuadros_anualizados.py`, `totales_por_lista.py`, `cuadros_por_localidad.py`, `serie_temporal.py`, `serie_temporal_por_localidad.py`) no necesitaron ningún cambio — se verificó con la suite completa (230/230) y regenerando en vivo los 22 gráficos de `totales_por_lista`, la serie temporal de los 3 niveles, `cuadros_anualizados`/`generar_graficos`/`cuadros_por_localidad`/`serie_temporal_por_localidad` (spot check). Se agregaron 2 tests (`TestCargarEscalaIdeologica` en `test_graficos.py`) que fijan el comportamiento: orden de inserción preservado, y `IDEOLOGIAS` idéntico a lo que devuelve `_cargar_escala_ideologica()` sobre el CSV versionado — evita que alguien vuelva a hardcodear la escala sin que un test lo note. La nota sobre ordinalidad (1-6 no son cardinales, no promediar) quedó documentada en el docstring de `_cargar_escala_ideologica`, no en el CSV en sí (un CSV leído con `csv.DictReader` no admite líneas de comentario sin romper el parseo).

**Bug real encontrado y corregido en el proceso, sin relación con este punto**: al regenerar los gráficos para verificar el fix, `analisis/totales_por_lista.py` crasheaba (`ValueError: too many values to unpack`) en cualquier invocación — `electoral.totales._combos_disponibles` pasó a devolver tuplas `(año, nivel, etapa)` cuando se agregó soporte a PASO/balotaje (`80a16db`, ver §2.3), pero este script seguía desempaquetando `for anio, nivel in combos`. Se corrigió filtrando a `etapa == "generales"` antes de desempaquetar (el script sigue sin soportar otra etapa — mismo gap de §2.3, no se expandió el alcance acá) — los 22 PNG de `graficos/distrito/totales_por_lista/` se regeneraron sin error después del fix.

### ~~2.2 Falta separar familia política de posición ideológica~~

**Estado: resuelto (v3.1.0).** Se agregó `filiacion_politica` a
`clasificacion_ideologica_agrupaciones.csv` (fusionada desde
`data/agrupaciones/tabla_referencia_filiacion_politica.csv`, 121 agrupaciones,
cobertura 1:1), separada de `campo_ideologico` y sin variar por año/nivel.
Verificado contra el caso que motivaba este punto: FPV, Frente para la
Victoria, Frente de Todos, Unidad Ciudadana, Unión por la Patria y Frente
Renovador (massismo) comparten `filiacion_politica=peronistas` aunque su
`campo_ideologico` siga fijo en `3` (centro) — la genealogía partidaria ya
no depende de que la posición ideológica se mantenga constante para
"tener sentido". Se agregó además `src/analisis/serie_temporal_filiacion.py`
(serie temporal por filiación política, mismo formato que `serie_temporal.py`).
Detalle completo en `AUDITORIA_ESTADO.md` §8.2.

- ~~**Archivo**: libro de códigos que salga de §1.1/§3.~~
- ~~**Qué está mal**: hoy una sola columna (`campo_ideologico`) mezcla identidad partidaria y posición ideológico-programática. Esto fuerza, por ejemplo, a que FPV/Unidad Ciudadana/Frente de Todos/Unión por la Patria/Fuerza Patria — verificado en `agrupaciones.csv`/`agrupaciones_legislativas.csv`: los seis quedan siempre en `3` (centro), 2011–2025 — aparezcan siempre en la misma posición, aunque hayan tenido programas y coaliciones distintas según el período.~~
- ~~**Qué hacer**: agregar una columna de familia/identidad política (peronismo/kirchnerismo, radicalismo, PRO, izquierda, libertarios, etc.) separada de la posición ideológica por elección, permitiendo que una misma familia cambie de posición entre períodos sin que eso se vea como "inconsistencia" del dataset.~~
- **Qué queda pendiente, más allá de esto**: `confianza_clasificacion`/`nota_clasificacion` (grado de incertidumbre y justificación por agrupación) quedaron deliberadamente solo en `tabla_referencia_filiacion_politica.csv`, no fusionadas al CSV principal. Las demás dimensiones del libro de códigos multidimensional que pide la nota metodológica (§5.3: oferta electoral, oficialismo, dimensiones programáticas separadas) siguen sin existir — esto resuelve específicamente familia vs. posición, no todo el libro de códigos.

### ~~2.3 Ampliar etapas electorales~~ (la agregación por circuito ya está resuelta; ver gap nuevo más abajo)

**Re-verificado en la auditoría posterior a la reorganización `data/distrito/`**: la afirmación de la revisión v3.1.0 ("notebook 04 sigue sin generar `circuito_<nivel>.json` para paso/balotaje") **ya no es cierta** — se resolvió en un commit posterior (`80a16db`, "Agrega circuito_<nivel>.json y resultado_total.csv para PASO y balotaje") sin que esta nota se actualizara. Verificado contra disco: **44 `circuito_<nivel>.json`** (22 `generales` + 20 `paso` + 2 `balotaje`, uno por cada `(año, nivel, etapa)` que efectivamente tuvo esa instancia) y **44 `resultado_total.csv`** correspondientes bajo `data/totales/`, generados por `electoral/totales.py` (ya soporta `etapa` como parámetro, con tests dedicados: `test_etapa_paso_lee_su_propio_circuito_json`, `test_etapa_balotaje_lee_su_propio_circuito_json`, `test_default_etapa_es_generales_no_se_mezcla_con_paso`). Esa parte del punto queda cerrada, ya no es parcial.

El mapeo de nombres con grafía distinta más allá de mayúsculas sigue sin hacerse — verificado de nuevo: `"COALICION CIVICA ARI"`, `"COALICIÓN CÍVICA - AFIRMACIÓN PARA UNA REPÚBLICA IGUALITARIA ARI"` y `"COALICIÓN CÍVICA - A.R.I."` siguen como tres filas separadas en `clasificacion_ideologica_agrupaciones.csv` (con el mismo `campo_ideologico`/`filiacion_politica` asignado a mano en cada una, pero sin fusionar como una sola agrupación).

**Gap nuevo, no contemplado cuando se escribió este punto**: los datos de PASO/balotaje ya están agregados en disco, pero **ninguno de los scripts de `src/analisis/` puede leerlos**. `analisis/graficos.py:_cargar_circuito` tiene hardcodeada la ruta `.../generales/circuito_{nivel}.json`, y de ahí lo heredan (directa o indirectamente) `serie_temporal.py`, `serie_temporal_filiacion.py`, `cuadros_anualizados.py`, `generar_graficos.py`; `totales_por_lista.py`/`comparativo_nivel.py` llaman a `resultado_total_por_agrupacion` sin pasar `etapa`, que por default cae en `"generales"`. No hay forma de pedirle a ningún gráfico o cuadro del repo "mostrame la PASO 2023 de intendente", pese a que el dato ya existe y ya está sumado.

**Estado: traer los datos, la estructura de carpetas y la agregación por circuito (incluida PASO/balotaje) están resueltos; falta que la capa de análisis/gráficos sepa leer otra etapa que no sea `generales` (ver "Gap nuevo" arriba) y el mapeo de nombres con grafía distinta.** Los notebooks 02 y 03 ahora también traen PASO (`tipo_eleccion=1`) para las 21 combinaciones (año, cargo) que la tuvieron, y balotaje (`tipo_eleccion=3`) para Presidente en 2015 y 2023 (los únicos años con segunda vuelta en el rango del proyecto), cacheando en `data/<año>/<cargo>/paso/` y `data/<año>/presidente/balotaje/`. Los archivos de Generales (crudos + `circuito_<nivel>.json`) se movieron a `data/<año>/<cargo>/generales/`, hermana de `paso/` y `balotaje/` — estructura ya simétrica entre las tres etapas. Se actualizaron todos los lugares que dependían de la ruta vieja: `notebooks/02`, `03` y `04` (categoria_nombre de caché + destino de escritura), y `src/analisis/graficos.py`, `generar_graficos.py` y `serie_temporal.py` (lectura de `circuito_<nivel>.json`). Verificado en el proceso: 2011/intendente no tuvo PASO (posible candidatura única, no confirmado con fuente externa), Gobernador e Intendente no tienen balotaje en la Provincia de Buenos Aires, y las PASO de 2025 no existen (Ley 27.781). También se agregaron a `agrupaciones.csv` (97 filas) y `agrupaciones_legislativas.csv` (82 filas) las agrupaciones que compitieron en la PASO y no llegaron a Generales, con `campo_ideologico` vacío (a clasificar en la etapa analítica — no se inventó ningún valor). **Hallazgo nuevo, verificado**: la API devuelve el nombre de una misma agrupación con grafía distinta según la etapa/año (ej. `"Coalición Cívica - Afirmación para una República Igualitaria ARI"` en Generales 2011 vs. `"COALICION CIVICA ARI"` en la PASO 2011). 

Ese hallazgo de grafías distintas se resolvió parcialmente: `agrupacion` en ambos CSV se normalizó a **mayúsculas** (la convención que ya traía la API en casi todos los años; solo Generales 2011 ejecutivo venía capitalizado), fusionando las 9 filas de `agrupaciones.csv` que coincidían exactamente tras subir a mayúsculas (ninguna en `agrupaciones_legislativas.csv`, porque ahí Generales ya era todo mayúsculas) y trasladando el `campo_ideologico` ya asignado a la fila fusionada — sin conflictos de valor entre las filas fusionadas (verificado antes de fusionar). `agregar_por_circuito` (notebook 04) ahora sube a mayúsculas el `agrupacion_nombre` leído del CSV oficial antes de armar `positivos`, así que `circuito_<nivel>.json` quedó regenerado con nombres en mayúsculas, consistente con la clave de join. Lo que **no** se resolvió (y sigue como duplicado aparente) son los casos de grafía distinta más allá de mayúsculas — abreviatura/puntuación distinta (ej. `"COALICIÓN CÍVICA - AFIRMACIÓN PARA UNA REPÚBLICA IGUALITARIA ARI"` vs. `"COALICION CIVICA ARI"`) — ahí sigue faltando un mapeo de nombres.

~~**Sigue pendiente**: `notebooks/04_totales_por_circuito.ipynb` todavía no procesa PASO/balotaje — no hay `circuito_<nivel>.json` con esas etapas ni un campo que marque a qué etapa corresponde cada fila en una tabla combinada.~~ (resuelto, ver arriba — sí procesa PASO/balotaje desde `80a16db`). Sigue pendiente el mapeo de nombres de agrupación con grafía distinta más allá de mayúsculas (abreviaturas/puntuación), antes de poder clasificar o cruzar del todo las filas nuevas que trajo la PASO.

- ~~**Archivos**: `src/electoral/client.py`, notebooks 02/03/04.~~
- ~~**Qué está mal**: el pipeline solo trae Generales (`tipo_eleccion=2`). El cliente ya soporta el parámetro (`tipo_eleccion`: 1=PASO, 2=Generales, 3=Segunda vuelta/balotaje), pero no se usa para nada más que Generales en ningún notebook.~~
- ~~mover los archivos de Generales a su propia subcarpeta para que el patrón quede simétrico entre etapas~~
- ~~agregar a `agrupaciones.csv`/`agrupaciones_legislativas.csv` las agrupaciones que aparecen en la PASO~~
- ~~normalizar `agrupacion` a mayúsculas y fusionar duplicados exactos, trasladando `campo_ideologico`; adaptar `circuito_<nivel>.json` a los nombres normalizados~~
- ~~extender `notebooks/04_totales_por_circuito.ipynb` para agregar también PASO y balotaje por circuito, marcando claramente a qué etapa corresponde cada fila~~ (resuelto en `80a16db`, ver "Gap nuevo" arriba)
- **Qué hacer** (lo que falta): (a) exponer `etapa` (`generales`/`paso`/`balotaje`) como parámetro en `src/analisis/*` — empezando por `analisis/graficos.py:_cargar_circuito`, de donde lo heredan el resto de los scripts — para que la PASO/balotaje ya agregados sean consumibles por algún gráfico o cuadro; (b) resolver el mapeo de nombres de agrupación con grafía distinta (más allá de mayúsculas) antes de clasificar las filas nuevas.

### Nuevo, fuera del plan original: `cuadros_anualizados/`

Se agregó `src/analisis/cuadros_anualizados.py` y `graficos/cuadros_anualizados/`: un gráfico de barras por año (votos y % — 16 imágenes, 2011-2025) que junta, uno al lado del otro, el total (todos los circuitos) de cada cargo disputado ese año por campo ideológico — **sin sumarlos entre sí**, por la misma razón que señala §2.4 más abajo (sumar Presidente+Gobernador+Intendente sugeriría más comparabilidad de la que hay). No resuelve §2.4 (que es sobre `serie_temporal.py` specÍficamente), pero cubre una necesidad relacionada: comparar los cargos de un mismo año lado a lado en vez de a lo largo del tiempo.

### Nuevo, fuera del plan original: capa circuito↔localidad (`data/geolocalizacion/fuentes_extra/`)

Se construyó, en una sesión posterior a este plan, un crosswalk circuito
electoral → localidad/barrio de La Plata
(`data/geolocalizacion/fuentes_extra/circuito_localidad.csv`), con dos niveles de
cobertura documentados y nunca mezclados sin pedirlo explícitamente:

- `oficial_confirmada`/`oficial_no_agrupable`: transcripción de la
  Resolución 1990/2007 del Ministerio del Interior (16 circuitos: 14
  agrupables + 503/503A sin localidad dominante).
- `periodistico_no_oficial`: relevamiento barrio-por-barrio de El Día
  (octubre 2025), 65/68 circuitos.

Se auditaron los 16 circuitos oficiales contra el **detalle completo** del
anexo de la resolución (todos los códigos de localidad INDEC de cada
circuito, no solo la descripción general que ya traía el crosswalk), en
`data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`. Resultado, de los 14
circuitos comparables (496E y 496F no tienen etiqueta de El Día): 3
coincidencia exacta, 3 sub-localidad válida (diferencia de granularidad,
no error) y **8 discrepancia real** — bastante más discrepante de lo que
sugería `CIRCUITOS_LOCALIDADES.md`, que señalaba a 496A como "el único caso
real": la auditoría completa lo reclasifica como sub_localidad_valida (la
etiqueta de El Día sí figura en la tabla del propio 496A) y encuentra el
problema real en otro lado (496C, 496D, 497C-F, 503, 503A) — tres de esos
ocho son casos donde la etiqueta de El Día es un código oficial válido,
pero de la tabla del circuito **vecino**, no del etiquetado.

Sobre ese crosswalk se construyeron `src/electoral/localidades.py`
(agrupación + `ReporteCobertura`, con `SIN_DETERMINAR` siempre visible y
nunca redistribuido — ni siquiera cuando el nivel periodístico sí trae una
etiqueta para un circuito marcado `oficial_no_agrupable`),
`src/analisis/cuadros_por_localidad.py` (22 cuadros CSV, 2011-2025, un
archivo por año/nivel, ~96-97% de cobertura de votos en todos, con
metadata de cobertura y referencia a la auditoría como comentario `#` en
cada archivo) y `src/analisis/serie_temporal_por_localidad.py` (132
gráficos PNG, reusando la fusión ejecutivo+legislativo ya existente en
`serie_temporal.py`). Se agregaron 27 tests nuevos (`test_localidades.py`:
17, `test_cuadros_por_localidad.py`: 10) — la suite pasó de 70 (§4) a 97.
Se verificó, para los 22 cuadros, que el total agrupado (incluido
`SIN_DETERMINAR`) coincide exacto con el total de `circuito_<nivel>.json`
de origen, y que el conteo de circuitos también se conserva (68/67/69
según el año) — ningún voto se pierde ni se duplica.

**Bug real encontrado y corregido en el proceso**: la primera versión de
`_votos_por_circuito` sumaba las categorías de `otros` (blanco/nulo/etc.)
por una lista fija de nombres (`"NULO"`, `"EN BLANCO"`, ...), pero la API
nombra esas categorías distinto en 2021 (`"NULOS"`, `"BLANCOS"`, ...) —
eso perdía ~19.000-20.000 votos en silencio en los tres cuadros de 2021,
detectado recién al comparar el total agrupado contra el total de origen.
Se corrigió sumando el diccionario `otros` completo sin filtrar por
nombre, y se agregó un test de regresión específico
(`test_no_pierde_votos_de_otros_con_nombres_de_categoria_distintos`). Es
la misma familia de problema que ya señala §2.3 más arriba sobre nombres
de agrupación con grafía distinta entre años/etapas — la API es
inconsistente entre años en cómo nombra las mismas categorías, y cualquier
código nuevo que lea campos de la API directamente (no a través de
`circuito_<nivel>.json` ya normalizado) debería tenerlo presente.

**Pendiente**: subir de nivel las familias 504, 505, 508 y 509
(504A; 505A/505B; 508A-G; 509A — hoy solo tienen etiqueta periodística, sin
resolución equivalente encontrada todavía, ver `CIRCUITOS_LOCALIDADES.md`
sección "Qué falta"); diagnóstico causal del hueco de circuito 493/2023.

### 2.4 Series que mezclan cargos distintos

- **Archivo**: `src/analisis/serie_temporal.py`.
- **Qué está mal**: cada serie por nivel de gobierno combina cargo ejecutivo y legislativo como una sola línea continua (nacional: Presidente + Diputados Nacionales; provincial: Gobernador + Diputados Provinciales; municipal: Intendente + Concejales). Es útil como narrativa descriptiva si está bien etiquetado, pero una línea continua sugiere más comparabilidad de la que realmente hay entre cargos distintos.
- **Qué hacer**: producir también series/paneles separados por cargo, y marcar visualmente en el gráfico combinado el cambio de tipo de elección en cada punto, para no leer cada pendiente como si midiera exactamente el mismo comportamiento electoral.

### ~~2.5 Cruce territorial con Censo (para la futura capa socioeconómica)~~ (parcialmente resuelto)

- ~~**Archivos**: nuevos, a definir (no existen hoy en `data/`).~~
- ~~**Qué está mal / falta**: no hay ningún dato de Censo, EPH ni ninguna variable socioeconómica en el repositorio todavía, pese a que el nombre del proyecto la anuncia.~~
- ~~**Qué hacer del lado de código**: construir la tabla de correspondencia entre `circuito_id` (canónico, ver §1.3 — ya resuelto) y radios/fracciones censales, documentando qué límites se verificaron y cuáles quedan pendientes. Esto es un prerrequisito técnico antes de poder unir cualquier variable de Censo 2010/2022 o EPH Gran La Plata al dataset electoral.~~
- **Qué falta**: extraer las variables temáticas del Censo 2010/2022 por radio vía REDATAM (parámetros exactos en `EXTRACCION_REDATAM.md`) y correrlas por `unir_censo_a_circuitos` (ya implementado en el notebook 05, esperando el insumo). Sin eso, la tabla de correspondencia sigue sin nada que unir — y la construcción de hipótesis/variables sociológicas sobre esos datos sigue quedando fuera de este documento.

---

## 3. Libro de códigos político — decisiones a fijar antes de reclasificar nada

**Estado: en inicio** (no por un criterio sistemático — ese sigue siendo trabajo de la etapa analítica, junto con la separación de §1.1). Además de los dos casos de §1.2 (Duhalde 2011, Progresistas 2015), se aplicaron dos reglas por nombre a las filas sin clasificar que trajo la PASO en `agrupaciones.csv`/`agrupaciones_legislativas.csv`. Se regeneraron los `circuito_<nivel>.json` correspondientes.

**Auditoría de consistencia de `agrupaciones.csv`** (ejecutivos): se revisó todo el archivo buscando el mismo `(año, agrupación)` con valores distintos —o con un cargo vacío y otro clasificado— entre `gobernacion`/`intendente`/`presidente`. Se encontraron y corrigieron, con verificación externa donde hizo falta:
- **PARTIDO DIGNIDAD POPULAR 2019** tenía `2` (centroizquierda) en gobernación y `6` (derecha radical) en intendente — es un partido de extrema derecha/neonazi (fundado 2015 por Ernesto Raúl Habrá, confirmado por Wikipedia y prensa); se corrigió gobernación a `6`.
- **FRENTE PATRIOTA FEDERAL 2023** tenía `6` en gobernación, vacío en intendente y `4` en presidente — es el mismo partido de Alejandro Biondini (extrema derecha/neonazi/ultranacionalista, confirmado por Wikipedia) que ya está clasificado `6` en 2019 como "FRENTE PATRIOTA"; se unificaron los tres cargos en `6`.
- **CELESTE PRO VIDA 2023** (`6` en gobernación, vacío en intendente): partido provida aliado a La Libertad Avanza en 2023 para darle personería a Milei; se completó intendente en `6`.
- **TODOS POR BUENOS AIRES 2023** y **VOCACIÓN SOCIAL 2023** tenían gobernación vacía con intendente ya clasificado (`3` y `2` respectivamente, sin evidencia de que debieran diferir por cargo — "Todos por Buenos Aires" ya tenía `3` en 2015); se completó gobernación con el mismo valor.
- **Caso dejado sin tocar a propósito**: Política Abierta para la Integridad Social (PAIS) 2023 tiene intendente=`4` y gobernación vacía. El PAIS nacional fue fundado en 1995 por Bordón como escisión centroizquierda del PJ, lo que contradice un `4` — pero es común que partidos chicos alquilen su personería a candidatos locales sin relación con el origen del partido, y no hay forma de confirmar sin identificar al candidato real de La Plata 2023 bajo esa lista. Queda marcado para revisión manual, no completado.

Los tres partidos corregidos (Dignidad Popular, Frente Patriota Federal, Celeste Pro Vida) solo compitieron en la PASO y nunca llegaron a Generales — no aparecen en ningún `circuito_<nivel>.json` todavía, así que la corrección vive por ahora solo en `agrupaciones.csv`, a la espera de que se extienda el pipeline a PASO (§2.3).

**Auditoría de consistencia de `agrupaciones_legislativas.csv`, usando `agrupaciones.csv` como parámetro**: se cruzó cada agrupación de `agrupaciones_legislativas.csv` contra `agrupaciones.csv` por coincidencia exacta de nombre. Con confirmación explícita de Ivan en cada punto:
- **FRENTE PATRIOTA FEDERAL 2025 (nacional)** tenía `5` (derecha) contra el `6` (derecha radical) ya fijado en ejecutivos con evidencia externa — es el mismo caso dudoso que señalaba la nota original ("Frente Patriota Federal 2025 = derecha, no derecha radical"); se corrigió a `6`. Este sí llegó a Generales, así que `circuito_nacional.json` de 2025 ya quedó regenerado con el valor correcto.
- **PATRIA GRANDE 2017 (nacional)**, vacío, se completó con `2` — el mismo valor que ya tenía provincial 2017, **no** el `1` de ejecutivos 2015. Es a propósito: sigue siendo el caso dudoso de §3 (¿el movimiento cambió de posición entre 2015 y 2017, o es inconsistencia de clasificación?) — se buscó solo consistencia interna dentro de 2017, sin resolver la pregunta de fondo.
- Se completaron por coincidencia exacta de nombre y sin valor en conflicto: **Compromiso Federal** (2013, 3 filas) → `4`; **Frente Patriota** (2021, 3 filas) → `6`; **Justicia y Dignidad Patriótica** (2021) → `6`; **Movimiento Organización Democrática** (2017+2021, 3 filas) → `3`; **Política Obrera** (2021) → `1`; **Todos por Buenos Aires** (2017+2021, 6 filas) → `3`; **Vocación Social** (2021, 3 filas) → `2`; **Celeste Pro Vida** (2021) → `6`; **Del Campo Popular** (2017) → `4`.
- Además, dos inconsistencias puramente internas de `agrupaciones_legislativas.csv` (sin equivalente en ejecutivos): **Frente Popular Democrático y Social (PODEMOS)** 2013 nacional (vacío, con municipal/provincial ya en `2`) y **Unión con Fe** 2013 municipal/provincial (vacíos, con nacional ya en `4`) — se completaron por consistencia interna del mismo año.
- Se regeneraron los `circuito_<nivel>.json` correspondientes (sin errores); los partidos nuevos que solo compitieron en PASO 2021 no aparecen todavía en ningún `circuito_<nivel>.json`, mismo motivo que en ejecutivos.

**Segunda auditoría** (tras completarse a mano varios valores en ambos CSV entre una revisión y otra): se repitió el chequeo de consistencia interna en los dos archivos y aparecieron casos nuevos.

- **Bug de tipeo corregido**: `agrupaciones_legislativas.csv`, UNION CON FE 2013 provincial tenía `campo_ideologico="45"` (fuera de la escala 1-6) — se corrigió a `4`, igual que municipal y nacional del mismo año.
- **Completados por coincidencia exacta sin conflicto** (mismo tratamiento que antes): en `agrupaciones.csv`, BUENOS AIRES PRIMERO (BAP), CONFIANZA PÚBLICA y MOVIMIENTO DE INTEGRACIÓN FEDERAL (MIF) —intendente 2023— y ESPERANZA DEL PUEBLO —gobernación 2023—; en `agrupaciones_legislativas.csv`, Partido Lealtad y Dignidad de la Pcia. de Bs. As. (provincial 2013), Corriente de Pensamiento Bonaerense (CO.PE.BO) (municipal 2017), Encuentro Popular por Tierra Techo y Trabajo (municipal+nacional 2017), Federal (municipal+nacional 2017).
- **Conflictos reales resueltos por Ivan directamente** (valores distintos entre niveles del mismo partido/año en legislativas 2021, sin evidencia externa propia): Corriente de Pensamiento Bonaerense → `4` en los tres niveles (municipal y provincial ya coincidían; nacional era el outlier en `6`); Unión Celeste y Blanco → `5`; Unión por Todos → `5`.
- **Gente en Acción (2013) y Frente Patriota Bandera Vecinal (2017)** → `6`: según la misma fuente (Wikipedia) usada para clasificar Frente Patriota Federal, son las dos organizaciones que se fusionaron en 2018 para formarlo — se heredó la clasificación.
- **Movimiento Avanzada Socialista 2013 (nacional)** → `1`, por coincidencia exacta de nombre con la misma agrupación ya clasificada `1` en 2025 dentro del propio `agrupaciones_legislativas.csv`, y con "Movimiento de Avanzada Socialista" (con "de") ya `1` en `agrupaciones.csv`.

Tras esta segunda pasada, ambos archivos quedan **sin inconsistencias internas** (ni valores fuera de escala, ni el mismo partido/año con valores distintos entre cargos, ni mezcla de vacío+valor). Siguen sin clasificar, sin evidencia disponible: en `agrupaciones.csv`, Frente Federal de Acción Solidaria de la Pcia. de Bs. As. (2023), Frente H.A.C.E.R. por Progreso Social (2023) y Unidad Social (2023, gobernación); en `agrupaciones_legislativas.csv`, Creo, Frente Socialista y Popular, Movimiento Amplio de Trabajadores y Jubilados, Partido Socialista y UVEP-U. Vecinalista Platense (todos 2017).

Estos casos (sección 8.2 de la nota) son evidencia de que falta una regla explícita de qué se está clasificando.

**Actualización (auditoría posterior, `clasificacion_ideologica_agrupaciones.csv` ya unificado)**: `agrupaciones.csv`/`agrupaciones_legislativas.csv` no existen más como archivos separados — se consolidaron en `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` (ver CLAUDE.md). Verificado contra ese archivo: quedan exactamente **4 filas sin `campo_ideologico`** — `PARTIDO SOCIALISTA` (2017, municipal y provincial), `FRENTE SOCIALISTA Y POPULAR` (2017, nacional) y `FRENTE FEDERAL DE ACCIÓN SOLIDARIA DE LA PROVINCIA DE BUENOS AIRES` (2023, gobernación). El resto de los casos que esta sección daba como "sin clasificar, sin evidencia disponible" (Creo, Movimiento Amplio de Trabajadores y Jubilados, UVEP, Frente H.A.C.E.R., Unidad Social) se cerraron en algún momento entre esa revisión y esta sin quedar documentado acá — no se investigó cuándo ni por qué en esta auditoría, solo se confirmó el conteo actual contra el CSV.

---

## 4. Robustecimiento técnico

**Estado: lo específico del pipeline electoral sigue sin empezar; hay varios puntos con movimiento lateral** (tests nuevos, `geopandas` en uso, y ahora también tests de `src/analisis/*` y rutas robustas en los notebooks — ver abajo).

- ~~**Sin tests**~~ (parcialmente resuelto): se agregó `tests/` (`conftest.py` + `test_models.py`, 26 tests) y `pytest.ini` (`pythonpath = src`), cubriendo `src/electoral/models.py` — parseo de cada dataclass desde JSON crudo (con fixtures recortadas de datos reales ya cacheados), captura de campos `extra` no documentados, y las tres propiedades derivadas de `ResultadoElectoral` (`ganador` —incluido el caso de empate—, `total_votos_positivos`, `es_mesa`). `pytest` se agregó a `requirements.txt`. **Sigue faltando** lo que motivó el ítem originalmente: pruebas de integridad del pipeline (que `circuito_<nivel>.json` sume exactamente el CSV oficial como test ejecutable, no solo el `assert` puntual del notebook 04; que el join contra el libro de códigos no deje agrupaciones sin clasificar; que `circuito_id` normalizado sea consistente entre años) — no hay tests todavía de `client.py`, `agregar_por_circuito`, ni de los scripts de `src/analisis/`. **Actualización**: la suite creció a 70 tests (`test_eph_client.py`, `test_geo.py`, agregados en la sesión de la capa socioeconómica) — pero cubren el código nuevo (`eph_client.py`, `geo.py`), no lo que este ítem señalaba originalmente: `client.py`, `agregar_por_circuito` y `src/analisis/*` siguen sin ningún test. **Actualización 2 (auditoría posterior, con la suite ya en 181 tests por trabajo de localidades/macroeconomía)**: se agregaron 47 tests nuevos que cubren la lógica pura (no la mitad de renderizado matplotlib) de `src/analisis/graficos.py` (`tests/test_graficos.py`, 15), `serie_temporal.py` (`test_serie_temporal.py`, 8, incluida la ruta de `ValueError` por año duplicado en `_puntos_del_nivel` que hoy queda silenciada por el `except Exception` de más abajo), `serie_temporal_filiacion.py` (`test_serie_temporal_filiacion.py`, 7, incluido el `KeyError` cuando una agrupación no tiene `filiacion_politica` asignada), `totales_por_lista.py` (`test_totales_por_lista.py`, 4), `comparativo_nivel.py` (`test_comparativo_nivel.py`, 9) y `cuadros_anualizados.py` (`test_cuadros_anualizados.py`, 4) — suite 181→228. **Sigue sin tests**: `client.py` (red, sin cache fixture) y `generar_graficos.py` (orquestación fina, sin lógica propia más allá de lo ya cubierto) — mismo criterio de "no testear I/O de red ni el renderizado matplotlib en sí" que ya usa el resto del repo (ver CLAUDE.md).
- **`geopandas` ya se usa** (actualiza un supuesto del punto siguiente): `src/socioeconomia/geo.py` lo importa y lo usa para el join espacial circuito↔radio censal (ver §2.5) — ya no es una dependencia sin uso.
- **Manejo de errores demasiado amplio**: `src/analisis/serie_temporal.py:137` hace `except Exception: puntos = []` alrededor de `_puntos_del_nivel(...)`, lo que puede ocultar tanto un año sin datos (caso esperado) como un `ValueError` real (ej. año duplicado, que la propia función puede levantar y que ahora tiene test — ver arriba) o un error de I/O — sin distinguir causa. El mismo patrón se replicó en `serie_temporal_filiacion.py:164` (verificado, sigue así). **Sigue sin resolverse en esta sesión** — se priorizó agregar los tests que documentan el comportamiento actual (incluido el que este bug puede esconder) antes de tocar el manejo de errores en sí; acotar a las excepciones esperables (`FileNotFoundError`) y dejar que `ValueError`/errores de I/O se propaguen sigue pendiente.
- ~~**Rutas frágiles**~~ (resuelto): los 6 notebooks (4 originales + 05/06, agregados después de escribirse este punto) dependían de `Path.cwd().parent` para ubicar `src/`/`data/`, lo que solo funcionaba si Jupyter arrancaba con cwd = `notebooks/`. Se agregó `_raiz_repo()` a la celda de setup de cada uno — sube desde el cwd del kernel buscando `pytest.ini` como marca de la raíz del repo, en vez de asumir el cwd — así que ahora corren igual desde la raíz del repo, desde `notebooks/`, o vía `nbconvert`/CI. Verificado: los 6 JSON siguen siendo válidos y `_raiz_repo()` devuelve la raíz correcta llamado desde `notebooks/`, la raíz, y `src/electoral/` (simulado fuera del notebook).
- **`requirements.txt` sin versiones fijadas** (sigue igual) se sumó `dbfread` (usado en `eph_client.py` para parsear los trimestres históricos de EPH en formato DBF).
- **Falta de procedencia en los archivos derivados**: ni los JSON agregados crudos ni `circuito_<nivel>.json` guardan hash, fecha de extracción, tipo de escrutinio, cobertura ni versión del libro de códigos usada en el join.
- ~~**Peso del repositorio**~~ (resuelto para los PNG): 3.040 PNG (verificado exacto, antes de esta corrida) más ~68 MB de datos. Al reejecutar `generar_graficos.py` para los 22 (año, nivel) tras normalizar `circuito_id` (§1.3), además quedaron 2.902 PNG huérfanos con el nombre de circuito viejo (con ceros a la izquierda) conviviendo con los nuevos (canónicos) — se detectaron y borraron. Con eso confirmado, se tomó la decisión que este ítem dejaba pendiente: `.gitignore` ahora excluye `graficos/*` salvo `graficos/serie_temporal/` (`git rm -r --cached` sobre las 3.034 imágenes por circuito/año ya versionadas, sin borrarlas de disco) — los PNG de `generar_graficos.py` y `cuadros_anualizados.py` se generan on demand y ya no se versionan; solo la serie temporal (6 archivos) sigue en git. **Sigue sin resolverse**: si el repo se abre al público, agregar licencia, forma de citar, y nota de fuente oficial.
- ~~**Worktrees git huérfanos**~~ (resuelto, fuera del plan original): habían quedado 4 worktrees en `.claude/worktrees/` (`macro-catalogo-anual`, `macroeconomia-rediseno-csv`, `split-readme-funcionalidades`, `totales-paso-balotaje`) de sesiones de trabajo anteriores. Verificado antes de tocar nada: las 4 ramas estaban 100% mergeadas a `main` (`git log main..<rama>` vacío en los 4 casos) y sin cambios propios sin commitear salvo un diff idéntico y trivial de `.devcontainer/devcontainer.json` (el mismo que ya está modificado sin commitear en el working tree principal, no es trabajo real). Se removieron los 4 worktrees (`git worktree remove`, con `--force` solo en el que tenía ese diff trivial) y se borraron las 4 ramas (`git branch -d`, sin forzar — confirma que estaban mergeadas).

