# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A client + data pipeline for the public Resultados Electorales API of
Argentina's Ministerio del Interior (`https://resultados.mininterior.gob.ar/api`),
scoped to La Plata (Buenos Aires): executive offices (Presidente, Gobernador,
Intendente, 2011-2023) and legislative offices (national/provincial/municipal,
2013-2025), including PASO and balotaje where applicable. No API key needed,
but outbound network access to `resultados.mininterior.gob.ar` is required to
refresh the cache.

`README.md` is a short landing page (structure, install, reproduce order,
what's git-tracked vs. derived); `docs/FUNCIONALIDADES.md` is the
extensive, authoritative doc on data semantics, known anomalies, and the
ideological classification methodology (split out of README to keep it
from growing without bound — see README's own "Dónde está cada cosa"
table for the full map of docs). `docs/` holds every root-level narrative
doc (methodology, specs, per-domain functionality, audit status) — the
domain-specific docs that live next to their data
(`data/fuentes_extra/*.md`, `data/macroeconomia/*.md`,
`data/socioeconomia/*.md`) stay where they are, on purpose, not in
`docs/`. Read `docs/FUNCIONALIDADES.md` before touching `data/`, the
notebooks, or `src/analisis/`. Do not duplicate its content here; this
file only orients you to commands and architecture.

## Commands

```bash
pip install -r requirements.txt        # deps: pandas, geopandas, statsmodels, matplotlib, seaborn, jupyter, requests, pytest, dbfread

pytest                                  # run the full test suite (pythonpath=src, testpaths=tests, configured in pytest.ini)
pytest tests/test_models.py::TestValorAgrupacion::test_from_json_campos_basicos  # single test

PYTHONPATH=src python -m analisis.generar_graficos --anio 2011 --nivel intendente  # per-circuit + accumulated charts for one (año, nivel)
PYTHONPATH=src python -m analisis.serie_temporal    # one chart per nivel (nacional/provincial/municipal), 2011-2025
PYTHONPATH=src python -m analisis.serie_temporal_filiacion  # same, by filiacion_politica instead of campo_ideologico
PYTHONPATH=src python -m analisis.cuadros_anualizados --anio 2023  # one chart per año, all cargos side by side
PYTHONPATH=src python -m analisis.cuadros_por_localidad --anio 2023 --nivel intendente  # votes-by-locality table for one (año, nivel)
PYTHONPATH=src python -m analisis.serie_temporal_por_localidad --nivel municipal  # per-locality time series, reads the tables above
PYTHONPATH=src python -m electoral.totales --anio 2023 --nivel intendente  # total votes per agrupación, generales by default; add --etapa paso/balotaje for those
PYTHONPATH=src python -m analisis.totales_por_lista --anio 2023 --nivel intendente  # bar chart of that total, one per (año, nivel)
PYTHONPATH=src python -m analisis.comparativo_nivel --anio 2019  # Municipio/Provincia/Nación comparison table, one per año
PYTHONPATH=src python -m macroeconomia.series  # national macroeconomic series, one CSV row per month 2011-2025 (needs network to refresh; runs from cache otherwise)
ESTADISTICASBCRA_TOKEN=... PYTHONPATH=src python -m macroeconomia.auditoria_estadisticasbcra  # manual one-off cross-check against estadisticasbcra.com; needs a user token (never committed), not part of the regular pipeline
```

There is no build/lint step configured. Tests cover `src/electoral/models.py`
(pure parsing, no network), `src/electoral/totales.py` (pure logic and file
I/O, no network — see `tests/test_totales.py`), and the locality-aggregation
layer added on top of it — `src/electoral/localidades.py`,
`src/analisis/cuadros_por_localidad.py`, and the non-plotting helpers of
`src/analisis/serie_temporal_por_localidad.py`
(pure logic and file I/O, no network; see `tests/test_localidades.py`,
`tests/test_cuadros_por_localidad.py`, `tests/test_serie_temporal_por_localidad.py`).
`src/electoral/client.py` and the rest of `src/analisis/*` (`graficos.py`,
`generar_graficos.py`, `serie_temporal.py`, `cuadros_anualizados.py`,
`serie_temporal_filiacion.py`, `totales_por_lista.py`, `comparativo_nivel.py`,
plus the matplotlib-rendering half of the locality scripts) still have no
automated tests; changes there are validated by re-running the notebooks
end to end (see README "Cómo reproducir") or by running the scripts
against `data/` directly.
`src/socioeconomia/eph_client.py` (URL/filename resolution, the historical
DBF-era file lookup, and the labor-indicator aggregation core — no
network) is covered by `tests/test_eph_client.py`; `src/socioeconomia/geo.py`
(circuito_id canonicalization and the area-weighted circuito↔radio spatial
join, tested against synthetic polygons, not real data) by
`tests/test_geo.py`; the pure gap-detection helpers of
`src/socioeconomia/graficos_eph_iaelap.py` by
`tests/test_graficos_eph_iaelap.py` — same split as everywhere else in the
repo, pure logic tested, the matplotlib-rendering and IAELaP-loading parts
of `graficos_eph_iaelap.py` itself validated by running notebooks 05/06.
`src/macroeconomia/series.py`'s normalization logic (catalog loading,
monthly resolution for daily/monthly/quarterly/annual sources, coverage
report) is covered by `tests/test_macroeconomia_series.py`, no network;
`src/macroeconomia/datos_gob_client.py` (the fetch+cache HTTP layer) and
`src/macroeconomia/auditoria_estadisticasbcra.py` (fetch+compare against a
third-party HTTP API) have no automated tests, same criterion as
`electoral/client.py`.

## Architecture

**Two-layer split**: `src/electoral/client.py` fetches and disk-caches raw
API data (JSON or CSV) and never transforms it; `src/electoral/models.py`
parses that raw JSON into typed dataclasses. Notebooks are the actual
pipeline runner — they call the client, drive `models`, and write everything
under `data/`. There is no orchestration script; **the notebooks (run in
order, 01→04) are the pipeline**.

- `ResultadosClient` wraps two distinct, differently-shaped endpoints of the
  same site: `get_resultados` (JSON, `GET /api/resultados/getResultados`)
  and `get_resultados_csv` (CSV, `GET /api/resultado/totalizadocsv` — an
  **undocumented** endpoint discovered by reading the site's JS bundle; it
  returns every mesa for a category in one request and is the recommended
  way to pull data, as opposed to `iter_mesas`, which round-trips per mesa
  and is for spot-checking only).
  - Disk cache path: `<cache_dir>/<anio_eleccion>/<categoria_nombre>/...`
    (`cache_dir=data/distrito` in this repo's notebooks, so in practice
    `data/distrito/<anio_eleccion>/<categoria_nombre>/...`).
    `categoria_nombre` (e.g. `"presidente"`) is a caller-chosen label, not
    something the API returns — `categoriaId` mappings are local to
    distrito/año and must be resolved empirically (see
    `docs/FUNCIONALIDADES.md` "Extender a otro distrito, sección o
    cargo").
  - Every model dataclass keeps an `extra: dict` of unmodeled JSON fields
    (see `_extra()` in `models.py`) so an API field added later shows up
    there instead of breaking parsing or silently vanishing — tests in
    `tests/test_models.py` specifically assert on this behavior.

- **`data/distrito/<año>/<categoría|nivel>/<etapa>/`** where `etapa` is
  `generales` (always present), `paso` (present for every combo except
  2011/intendente and all of 2025, per Ley 27.781 suspending PASO), or
  `balotaje` (Presidente only, 2015/2023 only — no second round elsewhere).
  Each leaf has the raw aggregate `.json`, the official `.csv`, and a
  derived `circuito_<nivel>.json` built by notebook 04 from the CSV (not
  the JSON aggregate — see `docs/FUNCIONALIDADES.md`'s "Anomalía
  conocida: JSON agregado de Presidente 2019") — notebook 04 §1-5 builds
  it for `generales`, §6-7 for `paso`/`balotaje`, discovering which (año,
  nivel) combos actually have a cached raw CSV for that etapa instead of
  assuming a fixed list.

- **`data/agrupaciones/`** holds the cross-cutting reference tables:
  `clasificacion_ideologica_agrupaciones.csv` (party lists + hand-classified
  `campo_ideologico`, 1-6 left→radical-right, covering both executive and
  legislative `nivel` values, plus `filiacion_politica` — party family/
  tradition, e.g. `peronistas`, `progresistas`, `liberales`, distinct from
  the per-election ideological position; see below) and
  `circuito_id_correspondencias.csv` (raw per-year circuito ids → canonical
  form). **These are hand-curated and must never be regenerated from
  scratch** — notebooks 02 (executive) and 03 (legislative) both append
  newly-seen agrupaciones to the shared classification file (with empty
  `campo_ideologico`, printed as a warning) and never overwrite existing
  rows, including rows added by the other notebook; this is what keeps
  re-running the pipeline from clobbering manual classification work. If
  you touch this merge logic, preserve that invariant.

  `filiacion_politica` was merged in from `data/agrupaciones/tabla_referencia_filiacion_politica.csv`,
  which stays as the reference source for the classification's justification
  and confidence per agrupación (`confianza_clasificacion`: alta/media/baja,
  `nota_clasificacion`: source/rationale) — those two columns were
  deliberately **not** merged into `clasificacion_ideologica_agrupaciones.csv`
  to keep it lean; consult the reference file directly to audit a
  `filiacion_politica` value. Addresses the "familia política vs. posición
  ideológica" gap flagged in `docs/nota_metodologica.md` §5.2 and
  `docs/AUDITORIA_ESTADO.md` §8.2 — e.g. FPV/Unidad Ciudadana/Frente de
  Todos/Unión por la Patria all share `filiacion_politica=peronistas` despite
  different `campo_ideologico` values across years, which is now expected
  (same family, different programmatic position) rather than a dataset
  inconsistency.

- **`data/fuentes_extra/circuito_localidad.csv`** is a second, unrelated
  hand-curated crosswalk (`circuito_id` -> `localidad`/barrio name, not
  census geography) built from an official 2007 resolution plus a
  newspaper survey — same "never regenerate, never silently overwrite"
  spirit as `data/agrupaciones/`, but there is no notebook step that
  builds or appends to it; it's edited by hand. `src/electoral/localidades.py`
  has the pure grouping logic (never drops a vote — anything unmapped goes
  to a `SIN_DETERMINAR` row) and `src/analisis/cuadros_por_localidad.py`
  applies it on top of the `circuito_<nivel>.json` files notebook 04
  already produces, writing CSVs to `data/por_localidad/` (derived, not
  git-tracked — regenerated in seconds, same as `graficos/`). Each row has,
  besides the 6 `campo_ideologico` columns, `blanco_nulo`, `otros`
  (procedural: impugnado/recurrido/comando) and `ausentismo` (circuit
  `electores` minus its valid votes).
  `src/analisis/serie_temporal_por_localidad.py` reads those CSVs and
  plots to `graficos/por_localidad/`. Details, coverage-by-circuito, and
  the discrepancy audit between the two source levels are in
  `data/fuentes_extra/LOCALIDADES_README.md` and
  `AUDITORIA_DISCREPANCIAS.md` — read those before changing the crosswalk
  or the grouping precedence.

- **`src/electoral/totales.py`** (not `src/analisis/`, since it stays inside
  the electoral layer next to `models.py`) sums the `circuito_<nivel>.json`
  files into one row per agrupación — total votes for the whole (año,
  nivel, etapa), via `models.totalizar_agrupaciones` (a general-purpose
  combinator: sums any `ValorAgrupacion` list by `id_agrupacion` and
  recomputes `votos_porcentaje`, usable for mesas or circuitos alike, not
  tied to this one script). `etapa` defaults to `"generales"` everywhere
  (backward compatible) and writes to the historical
  `data/totales/<nivel>/<año>/resultado_total.csv` path; `"paso"`/
  `"balotaje"` write to the sibling
  `data/totales/<nivel>/<año>/<etapa>/resultado_total.csv` instead — both
  derived, not git-tracked, same criterion as `graficos/`.
  `_combos_disponibles` discovers every `circuito_<nivel>.json` on disk
  under `data/distrito/`, generales/paso/balotaje alike, rather than
  hardcoding which combos have which etapa. Reads `circuito_<nivel>.json`
  (CSV-derived) rather than the raw aggregate JSON on purpose — that JSON is
  known-wrong for Presidente 2019 (see `docs/FUNCIONALIDADES.md`'s
  "Anomalía conocida: JSON agregado de Presidente 2019").
  `src/analisis/totales_por_lista.py` charts that same total plus
  `blanco_nulo` (via `resultado_total_por_agrupacion`, not by rereading the
  CSV — `blanco_nulo` is added and `votos_porcentaje` is recalculated over
  the new total with `models.totalizar_agrupaciones`): one horizontal bar
  chart per (año, nivel), one bar per agrupación (not grouped by ideology),
  all ranked together by votes, colored by `campo_ideologico` via a live
  join against `clasificacion_ideologica_agrupaciones.csv` (same pattern as
  `serie_temporal_filiacion.py`; `blanco_nulo` gets the same gray used
  everywhere else). Writes to
  `graficos/distrito/totales_por_lista/`, which **is** git-tracked (explicit
  `.gitignore` exception, same as `graficos/distrito/serie_temporal/`) even
  though the rest of `graficos/distrito/<año>/` is not.
  `src/analisis/comparativo_nivel.py` writes a Markdown table (not a chart)
  per año to `graficos/distrito/totales_por_lista/comparativos_nivel/`
  (inherits the tracked exception from its parent dir, no extra
  `.gitignore` rule needed): each agrupación's % in
  Municipio/Provincia/Nación that year plus the three pairwise diffs, by
  exact-name join across the three same-year cargos (empirically the same
  alliance keeps one name across categories within a year). Skips years
  with only one cargo (2025).

- **`src/analisis/`** reads only the derived `circuito_<nivel>.json` files
  (never the client/models layer directly) and plots by `campo_ideologico`.
  Every chart (this module, `serie_temporal_filiacion.py`, and the
  `por_localidad` variants) always adds two more series alongside the
  ideological/filiación breakdown — `blanco_nulo` and `ausentismo`
  (`electores` minus votos válidos) — computed by
  `graficos._votos_no_ideologicos`, in neutral gray so they don't compete
  with the ideology palette.
  `graficos.py` has the reusable `graficar_barras`/`graficar_torta`
  functions; `generar_graficos.py`, `serie_temporal.py`, and
  `cuadros_anualizados.py` are scripts that call them to bulk-write PNGs
  under `graficos/distrito/`. `serie_temporal_filiacion.py` is a parallel,
  narrower script: same `circuito_<nivel>.json` inputs, but plots by
  `filiacion_politica` instead (joined live against
  `clasificacion_ideologica_agrupaciones.csv` by `agrupacion` name, not
  embedded in the JSON — `circuito_<nivel>.json`/notebook 04 were
  deliberately left untouched when this was added) and only writes the
  `_filiacion_porcentaje.png` time series, no per-circuito bar/pie or raw-votes
  variant. Only `graficos/distrito/serie_temporal/`,
  `graficos/distrito/totales_por_lista/`, and
  `graficos/socioeconomia/eph/` (the EPH charts from
  `src/socioeconomia/graficos_eph_iaelap.py`, not the IAELaP or
  EPH-vs-IAELaP contrast ones) are git-tracked — the rest of `graficos/`
  is `.gitignore`d and regenerated on demand from `data/`.

- **Circuito id normalization**: the same circuito is zero-padded
  differently across years in the raw source data (`"0460"` vs `"000460"`
  vs `"00460"`). Notebook 04 normalizes to a canonical form (no leading
  zeros, letter suffixes preserved, e.g. `"0496F"` → `"496F"`) before any
  aggregation — never compare raw `circuito_id` values across years without
  going through this normalization.

- **`src/macroeconomia/`** is a separate analytical domain from
  electoral/socioeconomic: **national-grain only** (no circuito, no
  localidad, no region), related to the rest of the repo by date, never by
  spatial join — see `docs/plan_macroeconomia.md` for the full source
  evaluation and per-variable design, and
  `data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` for what actually
  got pulled and its coverage. `datos_gob_client.py` fetches+caches raw
  series from `datos.gob.ar`'s Series de Tiempo API (paginating past its
  5000-row-per-request cap); `series.py` reads
  `data/macroeconomia/catalogo_series.csv` (hand-curated, append-only, same
  spirit as `clasificacion_ideologica_agrupaciones.csv`) and builds
  `data/macroeconomia/series_macro_2011_2025.csv` — one row per **month**,
  one column per concept, plus `observaciones`. **No cell is ever
  forward-filled or repeated** — a cell only has a value if the source
  published data with an origin date exactly matching that month; a
  quarterly/annual source therefore only fills its origin month (e.g.
  Jan/Apr/Jul/Oct for quarterly), every other month in the period is left
  blank rather than inheriting the prior value. Daily sources collapse to
  the month's last business-day value (falling back to the nearest earlier
  business day within the month if that day has no data; if no business
  day in the month has data, the cell is blank too) — this is aggregation
  of a real data point, not filling. Every blank cell is flagged in
  `observaciones` with the reason; months before a series' first-ever data
  point are blank for the same reason (no exact-month data), never
  invented. This is a deliberate design choice (revised from an earlier
  forward-fill design — see `docs/plan_macroeconomia.md`, "Rediseño
  posterior"):
  a filled-forward value makes a sparse series look like it has real
  monthly granularity, so the CSV leaves gaps explicit and pushes any
  repeat/interpolate decision onto the consumer instead of making it
  silently. Neither the cache (`data/macroeconomia/_cache/`) nor the
  generated CSV are git-tracked — `catalogo_series.csv` is (same criterion
  as `data/totales/` vs. `clasificacion_ideologica_agrupaciones.csv`).
  `auditoria_estadisticasbcra.py` is a separate, manually-run script (not
  part of the regular pipeline, needs a user-supplied token never stored in
  the repo) that cross-checks each `auditable_estadisticasbcra` concept
  against `estadisticasbcra.com` — see
  `SISTEMATIZACION_VARIABLES_MACRO.md` §3 for the last run's results,
  including a catalog mapping fix it caught (`tipo_cambio_oficial` was
  pointed at the informal/blue-dollar endpoint, not the official one) and
  the finding that endpoint is unevenly stale (~1.5-2 years behind
  depending on the series), so it only audits closed historical stretches,
  never the CSV's most recent months.

## Working conventions specific to this repo

- Code, comments, and docs in this repo are in **Spanish** (Rioplatense) —
  match that when editing existing files.
- `campo_ideologico` is an intentionally strict join: `notebooks/04_totales_por_circuito.ipynb`
  raises `KeyError` if an agrupación isn't classified, by design — don't add
  a fallback/default that would silently mask an unclassified party.
  `agrupacion` names are uppercased for the join key (see
  `docs/FUNCIONALIDADES.md`) except where noted for Generales 2011.
- `mesas_esperadas` / `mesas_totalizadas_porcentaje` are always `0` in the
  already-downloaded data (the API only fills them for live elections) —
  don't treat this as a bug to fix or backfill.
- A prior audit (`docs/PLAN_CORRECCIONES_ELECTORALES.md`) tracked known
  data-quality issues and fixes; it's still on disk but untracked
  (`.gitignore`d as an internal working document, not deleted) — check it
  directly, or `git log` for the commit that stopped tracking it (it was
  untracked before the `docs/` move, so `git log` won't show it under its
  new path).
