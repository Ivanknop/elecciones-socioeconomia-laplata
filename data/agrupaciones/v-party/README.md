# V-Party (V-Dem Institute) — partidos argentinos 2011-2019

`vparty_argentina_2011_2019.csv`: extracto del dataset **V-Party v2**
(Varieties of Party Identity and Organization, V-Dem Institute, publicado
feb. 2022) filtrado a `country_text_id == "ARG"` y `2011 <= year <= 2019`.
35 filas partido-elección (elecciones a Diputados 2011, 2013, 2015, 2017 y
2019), **384 columnas, todas con su nombre técnico original** — no se
renombró, derivó ni mapeó ninguna columna.

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

- **Ninguna variable de V-Party mide "ley y orden"** (punitivismo penal).
  No se agregó ninguna columna sustituta.
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
- La unidad de observación son elecciones a **Diputados** (cámara baja),
  no elecciones presidenciales.

## `vparty_argentina_2011_2019_variables_solicitadas.csv`

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

## `v_party_argentina_2011_2019.csv`

Segundo derivado, calibrado contra un cuestionario propio de expertos
(no versionado en este repo). Mismas 35 filas, 63 columnas:

- **Identificación**: `v2paenname`, `v2paorname`, `v2pashname`, `year`,
  `historical_date`, `v2pavote` (% de votos, dato de contexto — no es
  una variable de posicionamiento).
- **Posicionamiento**, con valor puntual + variantes de incertidumbre
  (`_codelow`, `_codehigh`, `_osp`, `_osp_codelow`, `_osp_codehigh`):
  `v2pariglef`, `v2pawelf`, `v2pawomlab`, `v2palgbt`, `v2paimmig`,
  `v2parelig`, `v2paanteli`, `v2papeople`, `v2paclient` (clientelismo,
  agregada en esta ronda). `v2xpa_popul` solo trae `_codelow`/`_codehigh`
  — es un índice derivado (0–1), no tiene versión `_osp`.

Se revisó el codebook completo buscando columnas adicionales para 4
preguntas del cuestionario propio que todavía no tenían columna
confirmada. Resultado, sin forzar ninguna equivalencia:

- **Regulación económica y mercado** y **política fiscal/tributaria**:
  no son variables separadas — el propio codebook de `v2pariglef` las
  describe como componentes fusionados de ese único índice ("higher
  taxes, more regulation... vs. privatization, lower taxes, less
  regulation"), sin desagregar. No hay columna propia para ninguna de
  las dos.
- **Ley y orden**: cero coincidencias en todo el codebook (ni parciales).
  `v2paviol` (violencia política contra opositores), `v2paminor`
  (mayoría vs. derechos de minorías) y `v2paculsup` (superioridad
  cultural/nacionalismo) tocan temas cercanos pero no son esto — no se
  usaron como sustituto.
- **Discurso sobre democracia representativa**: sin equivalente limpio.
  `ep_people_vs_elite` coincide en la definición exacta pero está vacía
  para Argentina (ver arriba). `v2paplur` (compromiso con elecciones
  libres/multipartidarias y libertades civiles, 0–4) es el candidato
  parcial más cercano si se necesita una referencia aproximada, pero
  mide un concepto más amplio que el discurso refundacional sobre las
  instituciones representativas puntualmente — no está incluida en este
  CSV.

**Filas con las 10 variables de posicionamiento completamente vacías: 9
de 35.** Dos patrones distintos:

1. `Generation for a National Encounter`, `Popular Union`, `Socialist
   Party` (2011): tampoco tienen `v2pavote` — no llegaron al umbral de
   cobertura de expertos (>5% de votos/bancas).
2. `Let's change`/Cambiemos (2015, 2017, 2019) y `alliance: Frente de
   Todos` (2019): sí tienen `v2pavote` (32–45%), pero igual están vacías
   en posicionamiento. No es falta de cobertura — V-Party codificó la
   identidad ideológica de los partidos que integran cada alianza por
   separado (`Republican Proposal`/PRO y `Radical Civic Union`/UCR
   dentro de Cambiemos; `Front for Victory`/FPV-PJ y `Frente
   Justicialista`/PJ dentro de Frente de Todos), no de la alianza como
   entidad. No hay un valor directo para la alianza en el dataset.
