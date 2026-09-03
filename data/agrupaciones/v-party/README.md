# V-Party (V-Dem Institute) — partidos argentinos 2001-2019

## Fuentes de `vparty_economico`/`progresismo`/`populismo` en `clasificacion_ideologica_agrupaciones.csv`

Estas tres columnas están pobladas en 151 de las 313 filas de
`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` (el archivo
hand-curated que ya trae `campo_ideologico`/`filiacion_politica` por
agrupación/año/nivel, ver `CLAUDE.md` sección `data/agrupaciones/`: nunca
se regenera desde cero, se edita a mano). **Este README debería ser el
único lugar del repo donde se documenta de qué fuente viene cada fila**
 La carga es puntual (no hay
script que la repita ni la mantenga sincronizada — si se agregan filas
nuevas a `clasificacion_ideologica_agrupaciones.csv` o se corrige
`oficialismos.csv`, hay que reaplicar el criterio de abajo a mano) y
cada fila documentada tiene un único origen — nunca se mezcla un valor
real de V-Party con uno estimado.

**1 — Cruce directo con V-Party** (`v_party_argentina_2001_2019_espaniol.csv`),
por nombre exacto de agrupación normalizado (mayúsculas, sin acentos, sin
puntuación) en el mismo año — 8 partidos, 62 filas:

| Año | `agrupacion` en este repo | Partido V-Party |
|---|---|---|
| 2011 | ALIANZA FRENTE AMPLIO PROGRESISTA | alianza: Frente Amplio Progresista (el prefijo `alianza:` de V-Party ≡ la convención local `ALIANZA <NOMBRE>`) |
| 2013 | FRENTE PARA LA VICTORIA | Front for Victory (FPV-PJ) |
| 2013 | FRENTE PROGRESISTA CIVICO Y SOCIAL | Progressive, Civic and Social Front (FPCyS) |
| 2013 | FRENTE RENOVADOR | Renewal Front (RF) |
| 2015 | FRENTE PARA LA VICTORIA | Front for Victory (FPV-PJ) — fila distinta de "ALIANZA FRENTE PARA LA VICTORIA" (también 2015, completada vía fuente 3) |
| 2017 | FRENTE JUSTICIALISTA | Frente Justicialista-Justicialist [Peronist] Party (FP-PJ) |
| 2017 | UNIDAD CIUDADANA | Citizen's Unity (CU) |
| 2019 | CONSENSO FEDERAL | Consensus Federal (CF) |

**1b — Cruce directo, ola pre-2001.** V-Party tiene olas argentinas desde
1991 (no solo 2001-2019, que es simplemente el recorte que usa el resto de
este repo) -- para estos dos partidos se consultó la ola más vieja
disponible en el `.RData` completo (`cargar_argentina(..., anio_min=1990)`,
no forma parte del pipeline regular de `generar_v_party_argentina.py`, que
sigue filtrando 2001-2019 por defecto):

| `agrupacion` en este repo | Partido V-Party | Ola usada |
|---|---|---|
| UNION DEL CENTRO DEMOCRATICO / UNION DE CENTRO DEMOCRATICO (2001/2007/2023, según grafía del año) | Union of the Democratic Centre (UCeDé) | 1991 (única ola de UCeDé en el dataset) |
| ACCION POR LA REPUBLICA (2001) | Action for the Republic | 1999 (ola más cercana a 2001; único año con esta agrupación en el dataset) |


**2 — Proxy de la ola V-Party más cercana, cuando no hay superposición de
año.** Caso: **COALICIÓN CÍVICA ARI / COALICIÓN CÍVICA - AFIRMACIÓN PARA
UNA REPÚBLICA IGUALITARIA ARI / COALICIÓN CÍVICA - A.R.I.** — mismo
partido, tres grafías en distintos años de este repo (2011:
gobernación/intendente/presidente; 2025: nacional), en años donde V-Party
**no** tiene ola propia (solo cubre 2015/2017/2019 para este partido). Se
usó la ola más cercana en cada dirección: 2011 toma **2015** (la primera
ola, no hay ola anterior para "prestar"), 2025 toma **2019** (la última
ola, mismo criterio de arrastre que ya usa `oficialismos.csv` para
2021+). El eje económico de este partido no se mueve entre 2015/2017/2019
(`v2pariglef = 0.452` las tres olas), lo que da algo más de confianza al
proxy hacia atrás; el de progresismo sí varía año a año (0.299 en 2015,
usado para 2011; 0.288 en 2019, usado para 2025) — es una aproximación,
no un dato medido para esos años puntuales.

**3 — Fila hermana o de la ola más cercana, mismo nombre exacto de
`agrupacion`.** A diferencia de la fuente 2 (grafías *distintas* del
mismo partido), esta completa huecos donde el nombre es **idéntico** en
ambas filas — una tiene vparty poblado y su hermana (mismo año, otro
nivel; o mismo nivel, año adyacente) no, típicamente porque una carga
anterior sólo tocó una fila y no todas las que comparten nombre — 5
partidos, 13 filas:

| `agrupacion` | Filas completadas | Valor tomado de |
|---|---|---|
| ALIANZA FRENTE PARA LA VICTORIA | 2015 gobernacion, 2015 intendente | 2015 presidente (misma elección, real V-Party vía fuente 1) |
| AVANZA LIBERTAD | 2021 municipal | 2021 nacional/provincial (misma elección, idénticos entre sí) |
| FRENTE DE TODOS | 2021 municipal/nacional/provincial | 2019 (ola inmediata anterior, mismo criterio de arrastre que la fuente 2) |
| JUNTOS POR EL CAMBIO | 2023 intendente | 2023 gobernacion/presidente (misma elección) |
| MOVIMIENTO AL SOCIALISMO | 2015 y 2021, los 3 niveles cada uno | presidente 2019/2023 (única fila poblada de este partido; extrapola 4-8 años/niveles a la vez, más agresivo que los otros 4 casos de esta fuente) |


**4 — Mapeo por identidad real de partido, alianza local distinta.** A
diferencia de las fuentes 2/3 (mismo partido, otra grafía o hueco de año),
acá una alianza *local* de La Plata está dominada por un partido nacional
que sí tiene V-Party real, bajo un nombre de lista que no coincide ni por
similitud de string — el mapeo es por identidad política, a mano, no por
join automático — 3 casos, 7 filas:

| `agrupacion` en este repo | Año(es)/nivel(es) | Valor tomado de |
|---|---|---|
| ALIANZA UNIDOS POR UNA NUEVA ALTERNATIVA (UNA) | 2015, gobernacion/intendente/presidente | FRENTE RENOVADOR 2013 (Massa; real V-Party, fuente 1) |
| FRENTE SOCIAL DE LA PROVINCIA DE BUENOS AIRES | 2013 municipal | FRENTE PARA LA VICTORIA 2013 (escisión del FPV; real V-Party, fuente 1) |
| FRENTE SOCIAL DE LA PCIA. BS.AS. | 2011 intendente | FRENTE PARA LA VICTORIA/ALIANZA FRENTE PARA LA VICTORIA 2011 (ídem, ola 2011) |
| ALIANZA UNIÓN PARA EL DESARROLLO SOCIAL | 2011, gobernacion/intendente/presidente | Unión Cívica Radical, ola 2011 (de Narváez + UCR; ola real más cercana a 2011, tomada directo de `v_party_argentina_2001_2019_espaniol.csv` -- no es la fila `#Union Civica Radical` calibrada de `v_party_propio.csv`, que es solo de referencia/calibración, ver más abajo) |
| UNIDOS POR LA LIBERTAD Y EL TRABAJO | 2013, municipal/nacional/provincial | mismo valor que ALIANZA UNIÓN PARA EL DESARROLLO SOCIAL (fila de arriba) -- también espacio de F. de Narváez, mismo criterio |

Para la fila de UCR, los tres ejes se recalcularon a mano desde el dataset
real (no está en `v_party_argentina_2001_2019_espaniol.csv` con estos
nombres de columna) con la misma fórmula que usa el resto del repo:
`vparty_economico = v2pariglef`, `vparty_populismo = v2xpa_popul`,
`vparty_progresismo = promedio(v2palgbt, v2pawomlab, v2paimmig, v2parelig)`
-- verificada contra las filas ya cargadas de FRENTE RENOVADOR 2013 y
FRENTE PARA LA VICTORIA 2013 antes de aplicarla (coincide a 3 decimales).

## `v_party_propio.csv` — estimación propia para partidos sin cobertura V-Party

Para los partidos sin cobertura V-Party (ni match directo ni proxy de ola
cercana, fuentes 1/2 de arriba), `src/analisis/generar_v_party_propio.py`
estima `vparty_economico`/`vparty_progresismo`/`vparty_populismo` a
partir de una encuesta propia a expertos (`encuesta_partidos_propia.csv`),
calibrada por regresión lineal contra los partidos que sí tienen valor
real de V-Party — pipeline completo en el docstring del script, no se
repite acá. 

`encuesta_partidos_propia.csv` es la versión **anonimizada** del export
crudo de Google Forms: cada fila trae una columna `ID` secuencial que
solo sirve para referenciar la fila real del formulario si hace falta
revisarla — el export crudo con esos datos personales no vive en este
repo. Por eso, a diferencia del export original, `encuesta_partidos_propia.csv`
**sí está versionado**.

Solo los partidos sin match real se volcaron a
`clasificacion_ideologica_agrupaciones.csv` — 42 filas en total, uno de
los seis partidos encuestados (Frente de Izquierda) cubre solas 22 filas
por abarcar el frente FIT/FIT-U a lo largo de todos sus renombres
2011-2025:

| Partido (encuesta) | Agrupación(es) en `clasificacion_ideologica_agrupaciones.csv` | Filas |
|---|---|---|
| Frente de Izquierda | ALIANZA FRENTE DE IZQUIERDA Y DE LOS TRABAJADORES (2011/2015) / FRENTE DE IZQUIERDA Y DE LOS TRABAJADORES (2013/2017) / FRENTE DE IZQUIERDA Y DE TRABAJADORES - UNIDAD (2019-2025) — mismo frente, tres grafías por renombre | 22 |
| La Libertad Avanza | LA LIBERTAD AVANZA (2023, gobernacion/intendente/presidente) / ALIANZA LA LIBERTAD AVANZA (2025, municipal/nacional/provincial) | 6 |
| Proyecto Sur | ALIANZA PROYECTO SUR / PROYECTO SUR (2011) / MOVIMIENTO POLÍTICO SOCIAL Y CULTURAL PROYECTO SUR (2025, nombre legal completo del mismo partido) | 4 |
| Principios y Valores | PRINCIPIOS Y VALORES (2023) | 3 |
| Patria Grande | PATRIA GRANDE (2015/2017) | 4 |
| Encuentro Republicano Federal | REPUBLICANO FEDERAL (2021) — nombre no idéntico, único candidato en el archivo | 3 |

### Mapeos por similitud (extensión manual más allá de los 6 partidos encuestados)

Además de los 6 partidos de la tabla de arriba, se mapearon a mano otras
agrupaciones por similitud ideológica según el marco de alianzas que
integraron, tomando el valor ya cargado del partido más afín en vez de
correr una nueva estimación:

- Nuevo Encuentro = Patria Grande
- Ciudad Nueva = Patria Grande
- Libres del Sur = Proyecto Sur
- MST = FIT
- NMAS = FIT
- liber.ar = LLA

## `v_party_propio_ad_hoc.csv` — partidos evaluados por un subconjunto de expertos

Caso distinto de `v_party_propio.csv`: partidos que **no forman parte de
la encuesta fija de 12 agrupaciones** (`PARTIDOS` en
`generar_v_party_propio.py`) porque solo unos pocos expertos del panel
llegaron a evaluarlos — no tiene sentido correr la calibración completa
del script para un partido con 3-5 respuestas en vez de 9-11.
`data/agrupaciones/v-party/v_party_propio_ad_hoc.csv` guarda esas
respuestas sueltas: columnas `id_experto`, `partido`, y los 11 valores
crudos A1-D1 (mismo formato que un bloque de `encuesta_partidos_propia.csv`,
sin el campo de confianza D2). Cada partido nuevo agrega sus filas ahí a
medida que se cargan, no hay un tamaño de panel fijo.

`estimar_partido_cobertura_parcial(respuestas, calib)` (en
`generar_v_party_propio.py`, sección "AD HOC" del archivo, marcada como
tal en el propio código) toma ese subconjunto de respuestas, calcula
econ/prog/pop por experto con la misma fórmula que `cargar_encuesta`,
agrega por mediana, y aplica la calibración (`calib`, el mismo diccionario
`(a, b)` por eje que devuelve `calibrar()` sobre el panel completo de
10/11 expertos) — no corre su propia regresión, reusa la ya ajustada.
No está integrada a `main()`/`estimar()`/`escribir_salida()`: se llama a
mano, un partido a la vez, con el `calib` que ya se tiene de una corrida
normal del script.

## Procedencia

Paquete de R oficial para acceder a los datasets:

```
https://raw.githubusercontent.com/vdeminstitute/vdemdata/master/data/vparty.RData
```

Cargado con `pyreadr` (Python). Verificación de integridad: el archivo
completo tiene 11.898 filas, que coincide exactamente con lo que declara
el codebook oficial ("3467 parties... 11898 party-election year units"),
confirmando que es el dataset V-Party v2 genuino y sin recortar.

`src/analisis/generar_v_party_argentina.py` descarga (con caché en
`data/agrupaciones/v-party/cache/vparty.RData`, gitignoreado), filtra
Argentina 2001-2019 y escribe los dos CSV de abajo, incluyendo la
traducción `v2paenname_espaniol` (join estricto contra un diccionario
`TRADUCCIONES` en el propio script — falla si aparece un partido nuevo
sin traducir, mismo criterio que `campo_ideologico`). Comando:

```bash
PYTHONPATH=src python -m analisis.generar_v_party_argentina [--anio-min 2001] [--anio-max 2019] [--forzar-descarga]
```

Codebook de referencia (no versionado en este repo, solo citado):
`https://www.v-dem.net/documents/6/vparty_codebook_v2.pdf` — "Codebook
Varieties of Party Identity and Organization (V-Party) V2", Lindberg et
al. 2022, V-Dem Institute, Universidad de Gotemburgo.

## Notas de uso

- Las columnas `ep_*` (importadas de Chapel Hill Expert Survey / Global
  Party Survey, no son producto de V-Dem) están **vacías o casi vacías**
  para Argentina: `ep_people_vs_elite`, `ep_galtan`, `ep_antielite_salience`,
  `ep_corrupt_salience`, `ep_members_vs_leadership`, `ep_galtan_salience`
  (CHES) tienen 0/56 valores — CHES no cubre Latinoamérica.
  `ep_type_populism`, `ep_type_populist_values`, `ep_v8_popul_rhetoric`,
  `ep_v9_popul_saliency`, `ep_v6_lib_cons`, `ep_v7_lib_cons_saliency`
  (Global Party Survey, Norris 2020) tienen apenas 2/56.
- Cada variable tipo C (codificada por expertos país) trae, cuando
  aplica, la familia completa de sufijos del modelo de medición V-Dem:
  `_codelow`/`_codehigh` (intervalo HPD 68%), `_sd`, `_osp` (+ sus
  propios `_osp_codelow`/`_osp_codehigh`), `_ord`, `_mean` y `_nr`
  (cantidad de codificadores). V-Dem recomienda explícitamente no usar
  estimaciones puntuales con `_nr` ≤ 3 — este CSV no filtra esas filas,
  queda a criterio de quien lo consuma.
- `v2parelig` está en escala invertida respecto de lo intuitivo: 0 =
  invoca religión siempre, 4 = nunca.


## `vparty_argentina_2001_2019_variables_solicitadas.csv` (nunca existió en este repo, ver nota al inicio)

Derivado del CSV completo de arriba: mismas 56 filas, recortado a
identificadores de partido/elección + solo el **valor puntual** (escala
del modelo, sin sufijo — la versión que V-Dem recomienda para uso
estadístico) de las variables de posicionamiento pedidas:
`v2pariglef`, `v2pawelf`, `v2pawomlab`, `v2palgbt`, `v2paimmig`,
`v2parelig`, `v2paanteli`, `v2papeople`, `v2xpa_popul`.

Los intervalos de incertidumbre (`_codelow`/`_codehigh`) y las demás
versiones de escala (`_osp`, `_ord`, etc.) de estas mismas variables
siguen disponibles en el CSV completo (`v_party_argentina_2001_2019.csv`).

## `v_party_argentina_2001_2019.csv` (gitignoreado, ver nota al inicio)

Segundo derivado, calibrado contra un cuestionario propio de expertos.
56 filas (una por partido-elección, Argentina 2001-2019), 63 columnas:

- **Identificación**: `v2paenname`, `v2paorname`, `v2pashname`, `year`,
  `historical_date`, `v2pavote` (% de votos, dato de contexto — no es
  una variable de posicionamiento).
- **Posicionamiento**, con valor puntual + variantes de incertidumbre
  (`_codelow`, `_codehigh`, `_osp`, `_osp_codelow`, `_osp_codehigh`):
  `v2pariglef`, `v2pawelf`, `v2pawomlab`, `v2palgbt`, `v2paimmig`,
  `v2parelig`, `v2paanteli`, `v2papeople`, `v2paclient` (clientelismo,
  agregada en esta ronda). `v2xpa_popul` solo trae `_codelow`/`_codehigh`
  — es un índice derivado (0–1), no tiene versión `_osp`.


## `v_party_argentina_2001_2019_espaniol.csv`

Mismo archivo que `v_party_argentina_2001_2019.csv` (56 filas, misma
procedencia, mismas 63 columnas de identificación/posicionamiento) más
una columna agregada: `v2paenname_espaniol`, la traducción al español de
`v2paenname` (nombre del partido en inglés) — 64 columnas en total. Es
**el archivo que corresponde usar** para cualquier cruce contra los CSV de
este repo (`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`