# ICG (Índice de Confianza en el Gobierno, UTDT) — decisiones metodológicas

Pipeline en `src/socioeconomia/icg_cargar.py` / `icg_construir_series.py` /
`icg_exportar_csv.py` / `icg_graficos.py`, sobre el microdato de
`data/socioeconomia/icg/` (insumo externo no versionado, ver
`data/socioeconomia/icg/README.md` para qué es y cómo conseguirlo). Este
archivo documenta las decisiones que no
son obvias leyendo el código — mismo criterio que
`EXTRACCION_REDATAM.md`/`SISTEMATIZACION_VARIABLES.md` en esta misma
carpeta.

## Cobertura real vs. codebook

El codebook queda desactualizado frente al `.dta` real (detalle y fecha
en `data/socioeconomia/icg/README.md`, no repetido acá).
`icg_construir_series.construir_serie_headline`/`construir_series_demograficas`
no hardcodean un año de corte: `anio_hasta=None` (default) resuelve al año
máximo realmente presente en los datos cargados, así que la serie se
extiende sola si se reemplaza el `.dta` por una versión más nueva.

17 de 314.817 filas del `.dta` (~0,005%) no tienen `año`/`mes` — sin
identificador temporal no hay bucket al que asignarlas, se excluyen en
`icg_cargar.cargar_microdatos` (antes de cualquier agregación).

## Por qué "país" incluye a La Plata

`icg_pais` (y por lo tanto `brecha = icg_la_plata - icg_pais`) se calcula
sobre **todos** los casos del mes, sin filtrar por ciudad — incluye a La
Plata y a los ~600 casos "Interior NS" sin ciudad asignada (zona
"Interior", sin código de ciudad puntual). Es una decisión deliberada, no
un descuido: `ponderacion_UTDT` está documentada en el codebook como
"Factor de ponderación utilizado para asignar a cada ciudad el peso que
le corresponde en la muestra" — su propósito explícito es construir un
promedio nacional pooleado representativo de todas las ciudades
relevadas, que es exactamente lo que replica `icg_pais`. La consecuencia
es que `brecha` se autocontiene (La Plata es parte de su propio término
de referencia) — mismo criterio que usaría la propia fuente para un "ICG
nacional", no una construcción ad hoc de este repo.

## Asimetría de resolución mensual (país) / anual (La Plata)

Los tres cortes demográficos (`sexo`, `edad`, `edu` — la variable
agregada de 3 niveles, no `educacion`, que tiene 11 categorías finas y
generaría celdas demasiado chicas para La Plata) se calculan a
resolución **mensual** para el país entero y **anual** para La Plata.
Es intencional, justificado por el tamaño de muestra real medido:

| Grano | N mensual (min / mediana / max) |
|---|---|
| País (pooled) | 431 / 1.201 / 2.004 |
| La Plata | 6 / 36 / 92 |

Un mes de La Plata con `N=6` dividido en 3 tramos de edad dejaría celdas
de 1-2 casos — no graficable de forma confiable. A resolución anual, La
Plata pasa a ~150-220 casos por año (12-18 meses acumulados), suficiente
para un corte en 2-3 categorías. El país, en cambio, es robusto incluso
partido en 3 categorías a resolución mensual (cientos de casos por
celda). Los 7 CSV de `data/socioeconomia/icg_*.csv` incluyen siempre una
columna `n` (o `n_la_plata`/`n_pais` en el headline) para que quien
consuma el dato pueda juzgar la confiabilidad de cada punto — no hay un
umbral de supresión automática.

## `edu`: nulos

`edu` tiene 126 nulos sobre ~314k filas desde 2011 en adelante (~0,04%,
"Ns/Nc" del encuestado) — se excluyen (`dropna`) solo al construir el
corte por `edu`, sin afectar los cortes por `sexo`/`edad` (que no tienen
nulos) ni el headline (que no usa `edu`).

## Sin variable de ingreso/NSE

El `.dta` no tiene ninguna variable de ingreso ni de nivel
socioeconómico — se revisaron las 33 columnas contra el codebook. Se
documenta como limitación de la fuente; no se buscó ni se construyó una
proxy (ej. a partir de `edu`) para este trabajo.

## Columnas de ponderación no usadas

El `.dta` trae, además de `ponderacion_UTDT` (la única documentada en el
codebook y la que se usa en todo este pipeline), las columnas `PON_ESTR`,
`pond_edu`, `pondef`, `check3` y `pon_estr` — sin entrada en el codebook,
probablemente artefactos internos de construcción de distintas olas
históricas. No se usan acá; si en el futuro se necesitara reproducir una
cifra oficial de la UTDT que no coincida con `ponderacion_UTDT`, revisar
esas columnas primero.
