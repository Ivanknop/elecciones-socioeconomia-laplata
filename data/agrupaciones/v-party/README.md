# V-Party (V-Dem Institute) — partidos argentinos 2011-2019

**De los archivos descriptos en este README, sólo dos están efectivamente
versionados en esta carpeta**: este `README.md` y
`v_party_argentina_2011_2019_espaniol.csv` (ver su sección propia más
abajo — **es el que se usa para cruzar contra
`clasificacion_ideologica_agrupaciones.csv` y `oficialismos.csv`**, porque
las agrupaciones de este repo están en español, y es el que lee
`src/analisis/vparty_cuadrantes.py`). Dos archivos más existen en el
filesystem pero **no** están versionados, por dos motivos distintos —no
confundir uno con otro:

- `v_party_argentina_2011_2019.csv` (sin traducir, ver su sección más
  abajo): existe en disco pero está en `.gitignore` a propósito — es
  estrictamente un subconjunto de columnas de
  `v_party_argentina_2011_2019_espaniol.csv` (le falta sólo
  `v2paenname_espaniol`), así que versionar los dos sería duplicar datos;
  sólo se conserva localmente por comparación con el nombre en inglés. Si
  falta tras un clon nuevo del repo, no rompe nada: ningún script de este
  repo lo lee.
- El CSV crudo de 384 columnas y el derivado `_variables_solicitadas` que
  se describen a continuación **nunca llegaron a existir en este
  repositorio** — fueron pasos intermedios de la extracción original,
  hechos fuera de este repo. Se documentan igual por procedencia/
  trazabilidad; quien necesite reproducirlos parte de la fuente en
  "Procedencia" de abajo.

`vparty_argentina_2011_2019.csv` (nunca existió en este repo, ver nota arriba): extracto
del dataset **V-Party v2** (Varieties of Party Identity and Organization,
V-Dem Institute, publicado feb. 2022) filtrado a `country_text_id == "ARG"`
y `2011 <= year <= 2019`. 35 filas partido-elección (elecciones a Diputados
2011, 2013, 2015, 2017 y 2019), **384 columnas, todas con su nombre técnico
original** — no se renombró, derivó ni mapeó ninguna columna.

## Procedencia

El dataset no tiene descarga directa pública: el formulario oficial en
v-dem.net pide email/género/opt-in a newsletter, y el portal de QoG
Data Finder (`datafinder.qog.gu.se/dataset/vparty`) requiere un selector
interactivo en JS sin link directo. Se obtuvo en cambio el archivo de
datos real, sin gate, desde el repositorio público de GitHub del propio
V-Dem Institute (`vdeminstitute/vdemdata`, el paquete de R oficial para
acceder a sus datasets):

```
https://raw.githubusercontent.com/vdeminstitute/vdemdata/master/data/vparty.RData
```

Cargado con `pyreadr` (Python). Verificación de integridad: el archivo
completo tiene 11.898 filas, que coincide exactamente con lo que declara
el codebook oficial ("3467 parties... 11898 party-election year units"),
confirmando que es el dataset V-Party v2 genuino y sin recortar.

Codebook de referencia (no versionado en este repo, solo citado):
`https://www.v-dem.net/documents/6/vparty_codebook_v2.pdf` — "Codebook
Varieties of Party Identity and Organization (V-Party) V2", Lindberg et
al. 2022, V-Dem Institute, Universidad de Gotemburgo.

## Notas de uso

- Las columnas `ep_*` (importadas de Chapel Hill Expert Survey / Global
  Party Survey, no son producto de V-Dem) están **vacías o casi vacías**
  para Argentina: `ep_people_vs_elite`, `ep_galtan`, `ep_antielite_salience`,
  `ep_corrupt_salience`, `ep_members_vs_leadership`, `ep_galtan_salience`
  (CHES) tienen 0/35 valores — CHES no cubre Latinoamérica.
  `ep_type_populism`, `ep_type_populist_values`, `ep_v8_popul_rhetoric`,
  `ep_v9_popul_saliency`, `ep_v6_lib_cons`, `ep_v7_lib_cons_saliency`
  (Global Party Survey, Norris 2020) tienen apenas 2/35.
- Cada variable tipo C (codificada por expertos país) trae, cuando
  aplica, la familia completa de sufijos del modelo de medición V-Dem:
  `_codelow`/`_codehigh` (intervalo HPD 68%), `_sd`, `_osp` (+ sus
  propios `_osp_codelow`/`_osp_codehigh`), `_ord`, `_mean` y `_nr`
  (cantidad de codificadores). V-Dem recomienda explícitamente no usar
  estimaciones puntuales con `_nr` ≤ 3 — este CSV no filtra esas filas,
  queda a criterio de quien lo consuma.
- `v2parelig` está en escala invertida respecto de lo intuitivo: 0 =
  invoca religión siempre, 4 = nunca.


## `vparty_argentina_2011_2019_variables_solicitadas.csv` (nunca existió en este repo, ver nota al inicio)

Derivado del CSV completo de arriba: mismas 35 filas, recortado a
identificadores de partido/elección + solo el **valor puntual** (escala
del modelo, sin sufijo — la versión que V-Dem recomienda para uso
estadístico) de las variables de posicionamiento pedidas:
`v2pariglef`, `v2pawelf`, `v2pawomlab`, `v2palgbt`, `v2paimmig`,
`v2parelig`, `v2paanteli`, `v2papeople`, `v2xpa_popul`.

Dos de las dimensiones originalmente pedidas **no están** en este
derivado, sin sustituto, porque no hay una columna real que las mida sin
forzar un mapeo:

- **Ley y orden**: ninguna variable de V-Party mide esto.
- **Discurso sobre democracia representativa**: la variable literal
  (`ep_people_vs_elite`, importada de CHES) está vacía para Argentina
  (0/35). `v2paplur` existe y tiene datos, pero mide compromiso con
  elecciones libres/pluralismo partidario en general, no específicamente
  la tensión democracia directa vs. representativa — se dejó afuera en
  vez de usarla como sustituto.

Los intervalos de incertidumbre (`_codelow`/`_codehigh`) y las demás
versiones de escala (`_osp`, `_ord`, etc.) de estas mismas variables
siguen disponibles en el CSV completo (`vparty_argentina_2011_2019.csv`).

## `v_party_argentina_2011_2019.csv` (gitignoreado, ver nota al inicio)

Segundo derivado, calibrado contra un cuestionario propio de expertos.
Mismas 35 filas, 63 columnas:

- **Identificación**: `v2paenname`, `v2paorname`, `v2pashname`, `year`,
  `historical_date`, `v2pavote` (% de votos, dato de contexto — no es
  una variable de posicionamiento).
- **Posicionamiento**, con valor puntual + variantes de incertidumbre
  (`_codelow`, `_codehigh`, `_osp`, `_osp_codelow`, `_osp_codehigh`):
  `v2pariglef`, `v2pawelf`, `v2pawomlab`, `v2palgbt`, `v2paimmig`,
  `v2parelig`, `v2paanteli`, `v2papeople`, `v2paclient` (clientelismo,
  agregada en esta ronda). `v2xpa_popul` solo trae `_codelow`/`_codehigh`
  — es un índice derivado (0–1), no tiene versión `_osp`.


## `v_party_argentina_2011_2019_espaniol.csv`

Mismo archivo que `v_party_argentina_2011_2019.csv` (35 filas, misma
procedencia, mismas 63 columnas de identificación/posicionamiento) más
una columna agregada: `v2paenname_espaniol`, la traducción al español de
`v2paenname` (nombre del partido en inglés) — 64 columnas en total. Es
**el archivo que corresponde usar** para cualquier cruce contra los CSV de
este repo (`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`,
`data/agrupaciones/oficialismos.csv`), porque ahí las agrupaciones están
en español y el cruce se hace por coincidencia (exacta o cuasi-exacta,
salvando puntuación) de nombre normalizado — `v_party_argentina_2011_2019.csv`
(sin traducir) no sirve para ese propósito y se mantiene sólo por
procedencia/comparación con el original en inglés.
