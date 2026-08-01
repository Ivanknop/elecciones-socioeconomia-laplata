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

The README.md is extensive and authoritative on data semantics, known
anomalies, and the ideological classification methodology — read it before
touching `data/`, the notebooks, or `src/analisis/`. Do not duplicate its
content here; this file only orients you to commands and architecture.

## Commands

```bash
pip install -r requirements.txt        # deps: pandas, geopandas, statsmodels, matplotlib, seaborn, jupyter, requests, pytest

pytest                                  # run the full test suite (pythonpath=src, testpaths=tests, configured in pytest.ini)
pytest tests/test_models.py::TestValorAgrupacion::test_from_json_campos_basicos  # single test

PYTHONPATH=src python -m analisis.generar_graficos --anio 2011 --nivel intendente  # per-circuit + accumulated charts for one (año, nivel)
PYTHONPATH=src python -m analisis.serie_temporal    # one chart per nivel (nacional/provincial/municipal), 2011-2025
PYTHONPATH=src python -m analisis.cuadros_anualizados --anio 2023  # one chart per año, all cargos side by side
PYTHONPATH=src python -m analisis.cuadros_por_localidad --anio 2023 --nivel intendente  # votes-by-locality table for one (año, nivel)
PYTHONPATH=src python -m analisis.serie_temporal_por_localidad --nivel municipal  # per-locality time series, reads the tables above
```

There is no build/lint step configured. Tests cover `src/electoral/models.py`
(pure parsing, no network) and the locality-aggregation layer added on top of
it — `src/electoral/localidades.py`, `src/analisis/cuadros_por_localidad.py`,
and the non-plotting helpers of `src/analisis/serie_temporal_por_localidad.py`
(pure logic and file I/O, no network; see `tests/test_localidades.py`,
`tests/test_cuadros_por_localidad.py`, `tests/test_serie_temporal_por_localidad.py`).
`src/electoral/client.py` and the rest of `src/analisis/*` (`graficos.py`,
`generar_graficos.py`, `serie_temporal.py`, `cuadros_anualizados.py`, plus the
matplotlib-rendering half of the locality scripts) still have no automated
tests; changes there are validated by re-running the notebooks end to end
(see README "Cómo reproducir") or by running the scripts against `data/` directly.

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
    distrito/año and must be resolved empirically (see README "Extender a
    otro distrito, sección o cargo").
  - Every model dataclass keeps an `extra: dict` of unmodeled JSON fields
    (see `_extra()` in `models.py`) so an API field added later shows up
    there instead of breaking parsing or silently vanishing — tests in
    `tests/test_models.py` specifically assert on this behavior.

- **`data/distrito/<año>/<categoría|nivel>/<etapa>/`** where `etapa` is `generales`,
  `paso`, or `balotaje` (only for Presidente, only 2015/2023). Each leaf has
  the raw aggregate `.json`, the official `.csv`, and (for `generales`) a
  derived `circuito_<nivel>.json` built by notebook 04 from the CSV (not the
  JSON aggregate — see README's "Anomalía conocida: JSON agregado de
  Presidente 2019").

- **`data/agrupaciones/`** holds the cross-cutting reference tables:
  `agrupaciones.csv` / `agrupaciones_legislativas.csv` (party lists +
  hand-classified `campo_ideologico`, 1-6 left→radical-right) and
  `circuito_id_correspondencias.csv` (raw per-year circuito ids → canonical
  form). **These are hand-curated and must never be regenerated from
  scratch** — notebooks 02/03 only append newly-seen agrupaciones (with
  empty `campo_ideologico`, printed as a warning) and never overwrite
  existing rows; this is what keeps re-running the pipeline from clobbering
  manual classification work. If you touch this merge logic, preserve that
  invariant.

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
  git-tracked — regenerated in seconds, same as `graficos/`).
  `src/analisis/serie_temporal_por_localidad.py` reads those CSVs and
  plots to `graficos/por_localidad/`. Details, coverage-by-circuito, and
  the discrepancy audit between the two source levels are in
  `data/fuentes_extra/LOCALIDADES_README.md` and
  `AUDITORIA_DISCREPANCIAS.md` — read those before changing the crosswalk
  or the grouping precedence.

- **`src/analisis/`** reads only the derived `circuito_<nivel>.json` files
  (never the client/models layer directly) and plots by `campo_ideologico`.
  `graficos.py` has the reusable `graficar_barras`/`graficar_torta`
  functions; `generar_graficos.py`, `serie_temporal.py`, and
  `cuadros_anualizados.py` are scripts that call them to bulk-write PNGs
  under `graficos/distrito/`. Only `graficos/distrito/serie_temporal/` is
  git-tracked — the rest of `graficos/` is `.gitignore`d and regenerated
  on demand from `data/`.

- **Circuito id normalization**: the same circuito is zero-padded
  differently across years in the raw source data (`"0460"` vs `"000460"`
  vs `"00460"`). Notebook 04 normalizes to a canonical form (no leading
  zeros, letter suffixes preserved, e.g. `"0496F"` → `"496F"`) before any
  aggregation — never compare raw `circuito_id` values across years without
  going through this normalization.

## Working conventions specific to this repo

- Code, comments, and docs in this repo are in **Spanish** (Rioplatense) —
  match that when editing existing files.
- `campo_ideologico` is an intentionally strict join: `notebooks/04_totales_por_circuito.ipynb`
  raises `KeyError` if an agrupación isn't classified, by design — don't add
  a fallback/default that would silently mask an unclassified party.
  `agrupacion` names are uppercased for the join key (see README) except
  where noted for Generales 2011.
- `mesas_esperadas` / `mesas_totalizadas_porcentaje` are always `0` in the
  already-downloaded data (the API only fills them for live elections) —
  don't treat this as a bug to fix or backfill.
- A prior audit (formerly `PLAN_CORRECCIONES_ELECTORALES.md`, now removed
  from the repo per the most recent commit) tracked known data-quality
  issues and fixes; check `git log` if you need that history.
