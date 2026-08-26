# Estado de la auditoría (`NOTA_METODOLOGICA.md`, Sección 8) — a v7.3.0 + sesión actual

Este documento existe porque la nota metodológica es un documento de trabajo
fechado sobre `v1.0.0`. Se actualiza cada vez que se cierra un punto.

Convención: 🟢 resuelto · 🟡 parcial · 🔴 abierto

**Alcance de esta pasada (v7.1.0 → v7.3.0 + trabajo de la sesión actual,
todavía sin commitear):** re-auditada de nuevo la Sección 8.2 (V-Party) —
la cifra de cobertura que traía este documento desde `3277a60` (115/313)
ya estaba mal en el momento en que se escribió, no cambió después; ver
hallazgo nuevo más abajo. Cubre además `8faecda` (v7.2.0, pestaña
interactiva de distribución ideológica + split de `src/visualizacion/`),
`6e431fe` (v7.3.0, pipeline ICG/UTDT) y trabajo de esta sesión sin
taggear todavía (escala fija y centrado en 0,0 para los PNG de V-Party,
cuadrante real por localidad en la pestaña interactiva reemplazando el
placeholder "próximamente", limpieza de docstrings y de documentación
redundante entre `CLAUDE.md` y `docs/FUNCIONALIDADES.md`). El resto del
documento (8.1 salvo el ítem 12, Sección 10, "Lectura del conjunto")
sigue reflejando la validación completa a v6.0.0/v7.1.0 descripta ahí
mismo, no una nueva pasada completa.

## 8.1 — Correcciones y fragilidades confirmadas

| # | Punto | Estado | Evidencia |
|---|---|---|---|
| 1 | Duhalde 2011 mal codificado | 🟢 | corregido en `909760e` |
| 2 | Progresistas 2015 inconsistente | 🟢 | corregido en `909760e` |
| 3 | Secuencia reproducible borra clasificación manual | 🟢 | append-only, nunca sobrescribe (ver README/CLAUDE.md, `909760e`) |
| 4 | Circuitos no normalizados longitudinalmente | 🟢 | normalización sin ceros a la izq., `circuito_id_correspondencias.csv` |
| 5 | Mesas sin votos / cobertura incompleta | 🟡 | se documenta `mesas_sin_votos_positivos` por circuito; **falta** el % de cobertura por circuito y el análisis de sensibilidad que pide la nota. Nueva evidencia concreta (ver `data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`, hallazgo circuito 493): Gobernador/Intendente/Presidente 2023 tienen `electores=109` con `positivos=0` y `otros=0` en ese circuito — no un caso de "mesas con cero votos positivos" sino de circuito entero sin ningún voto cargado, y solo en 2023. Sigue sin diagnóstico causal. |
| 6 | JSON agregado Presidente 2019 incompleto | 🟢 | documentado en README + `coincide_con_agregado_json`/`advertencia_fuente` |
| 7 | Todo el repo usa escrutinio provisorio | 🔴 | sigue sin sustituir/contrastar con definitivos; falta registrar fecha de descarga por archivo. El caso del circuito 493/2023 (ítem 5) es compatible con esto — un circuito remoto ("límite incierto", cabecera "Isla Martín García" según `README.md`) sin telegrama cargado al momento de la consulta — pero sigue siendo una hipótesis, no un diagnóstico confirmado |
| 8 | Inconsistencias del README (3 vs 4 columnas, "años pares", instrucción truncada) | 🟢 | README reescrito en `3899006` |
| 9 | Escala ideológica duplicada (CSV sin usar) | 🟢 | `graficos.py` ya lee `campo_ideologico.csv` (vía `_cargar_escala_ideologica()`, ruta resuelta por `__file__` para no depender del cwd) en vez del dict `IDEOLOGIAS` hardcodeado; CSV pasado a separador `,` para consistencia con el resto de `data/agrupaciones/`. Ver `docs/PLAN_CORRECCIONES_ELECTORALES.md` §2.1 |
| 10 | Series unen cargos distintos sin marcarlo | 🟡 | está documentado en README con tabla explícita; el panel/serie separada por cargo que pedía la nota ya existe en dos formas -- `cuadros_anualizados.py` (bar chart por año, cargos lado a lado, sin sumarlos) y, esta sesión, `comparativo_nivel.py` (cuadro Markdown por año con el % de cada agrupación en Municipio/Provincia/Nación más las tres diferencias entre pares). **Sigue faltando**: marcar visualmente el cambio de tipo de elección dentro de la serie fusionada de `serie_temporal.py` en sí (hoy solo está en el sub-label de texto del eje x, no en el trazo) |
| 11 | Gráficos omiten blancos/nulos/abstención; volumen de PNG | 🟡 | resuelta la primera mitad (blancos/nulos/abstención): todo gráfico de `src/analisis/` (barras/torta, las tres series temporales, `cuadros_anualizados`, y las variantes `por_localidad`) suma `blanco_nulo` y `ausentismo` (`electores` del circuito/nivel menos votos válidos) junto al desglose por `campo_ideologico`/`filiacion_politica`, vía `graficos._votos_no_ideologicos` — el % que muestra cada gráfico pasa de "% de los positivos" a "% del padrón" (ver README, sección "Gráficos"). **Corrección a esta misma auditoría**: la nota "cambio sin commitear todavía" que traía este ítem era vieja para cuando se congeló v3.3.0 — el commit real es `e41c8d0`, ya incluido en v3.3.0. `mapa_interactivo.py` (v4-v5) extiende el mismo criterio a su choropleth de "Ausentismo". **Sigue abierto**: el volumen de PNG (miles de archivos por circuito) y la tabla maestra analítica que pide la nota como reemplazo no cambiaron. |
| 12 | Dependencia de notebooks y cwd; sin tests de `client.py`/`analisis/` | 🟡 | se agregaron tests de `models.py` (`909760e`); con `d006699` también se agregó cobertura para la capa de localidades (`test_localidades.py`, `test_cuadros_por_localidad.py`, `test_serie_temporal_por_localidad.py`). **Actualización relevante desde v3.3.0**: `11718f9` agregó tests de la lógica pura (no el renderizado matplotlib en sí) de `graficos.py`, `cuadros_anualizados.py`, `serie_temporal.py`, `serie_temporal_filiacion.py`, `totales_por_lista.py` y `comparativo_nivel.py` — la afirmación de `CLAUDE.md` de que esos módulos "still have no automated tests" quedó desactualizada por ese mismo commit y debería corregirse ahí también. Los tres dominios nuevos (macro, geolocalización, V-Party) siguen el mismo criterio ya establecido: lógica pura testeada, capa de red/rendering no — `macroeconomia/series.py` y `series_anuales.py` (`7e5e01d`/`b4ec146`), `geolocalizacion/catalogo.py` (`4746cbe`), y la lógica de agregación de `mapa_interactivo.py` (`dd12bb3`/`e45d43f`) tienen tests; `electoral/client.py`, `macroeconomia/datos_gob_client.py`/`graficos.py`/`auditoria_estadisticasbcra.py`, `geolocalizacion/georef_client.py`/`mapa.py`, `analisis/vparty_cuadrantes.py`/`vparty_cuadrantes_local.py` (plotting) y el resto de renderizado matplotlib siguen sin cobertura, por diseño (necesitan red o producen imágenes, no lógica a aserción directa) — `generar_v_party_propio.py` y la lógica pura de `vparty_cuadrantes_local.py` (join/agregación/color, `cfb6309`) sí la tienen. 335 tests en total a esta sesión (`pytest -q`; 322 a v7.1.0, 265 a v6.0.0) — los 13 nuevos son `icg_cargar.py`/`icg_construir_series.py` (v7.3.0, `pandas.read_stata` monkeypatcheado, nunca el `.dta` real de 22 MB); las funciones nuevas de V-Party de esta sesión (`_limites_globales`, `generar_localidad_por_anio`, `_localidad_puntos_por_nivel` en `distribucion_ideologica_interactiva.py`) no sumaron tests propios, mismo criterio ya establecido de no testear orquestación/plotting. Suite completa en ~5s. |
| 13 | Falta procedencia (hash, fecha, versión del libro de códigos) por archivo derivado | 🔴 | sin cambios conocidos — los nuevos dominios (macro, geolocalización) documentan procedencia en prosa (`SISTEMATIZACION_VARIABLES_MACRO.md`, `LOCALIDADES.md`) pero tampoco embeben hash/fecha/versión por archivo derivado |
| 14 | Repositorio pesado (PNG + datos) | 🟡 |  `.gitignore` sigue trackeando sólo `graficos/distrito/serie_temporal/` + `graficos/socioeconomia/eph/` + `graficos/geolocalizacion/` — 53 archivos trackeados en `graficos/` a v6.0.0 (creció por la incorporación de geolocalización, antes 23). La mitad "datos" sigue siendo la real y ahora pesa más porque se sumaron 3 dominios enteros desde v3.3.0 (macroeconomía, geolocalización, V-Party): `data/distrito/**/*.csv` solo (crudo por mesa, incluye PASO/balotaje, creció con `80a16db`) suma 227 MB en el working tree; `data/` completo son 413 MB; el `.git` empaquetado son ~95 MB (`git count-objects -v`, antes 86 MB). Sigue sin ser bloat desperdiciado — mismo diagnóstico que a v3.3.0, ahora con más dominios cacheando de la misma forma deliberada (macro cachea `datos.gob.ar`/BCRA en `data/macroeconomia/_cache/`, geolocalización cachea Georef-AR en `data/geolocalizacion/_cache/`, ninguno trackeado). **Conclusión sin cambios**: la única palanca real para reducir en serio sigue siendo dejar de trackear `data/distrito/**/*.csv` y aceptar que reproducir el pipeline exige red. |

## 8.2 — Codificaciones políticas a revisar

🟡 Parcial. Se agregó `filiacion_politica` (familia/identidad partidaria,
separada de `campo_ideologico` — ver Sección 5.2 de la nota — en
`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`, fusionada
desde `data/agrupaciones/tabla_referencia_filiacion_politica.csv`, 121
agrupaciones). Verificado contra los ocho casos señalados: los seis
alias peronistas (FPV, Frente para la Victoria, Frente de Todos, Unidad
Ciudadana, Unión por la Patria, Frente Renovador/massismo) comparten
`filiacion_politica=peronistas`; la familia progresista (FAP, Frente Amplio
Progresista, Frente Progresista Cívico y Social) comparte `progresistas`;
Patria Grande y Frente Social de la Pcia./Provincia de Buenos Aires (ambas
grafías) también quedan en `progresistas`; Frente NOS y Frente Patriota
Federal quedan en `nacionalistas`, distinto de `liberales` (donde cae la
oferta de Espert); Hacemos por Nuestro País queda en `peronismo provincial`
(subcategoría distinta de `peronistas` genérico, no fusionada con él). Esto
resuelve el señalamiento de fondo (una sola columna aplanaba genealogía
partidaria y posición ideológica) para los ocho casos: ya no hace falta
leer un `campo_ideologico` estable en el tiempo como "inconsistencia" del
dataset si `filiacion_politica` explica la continuidad de familia.
**Sigue sin tocarse** (no era el objetivo de este cambio): los valores de
`campo_ideologico` en sí para esos ocho casos no se modificaron — si
alguien quiere disputar, por ejemplo, que Frente Patriota Federal 2025 sea
`campo_ideologico=5` (derecha) y no `6` (derecha radical), eso sigue abierto
como decisión de codificación aparte.

🟡 Parcial, actualizado (commits `a9b84d5`/`8c5fa23`, v6.0.0; `cfb6309`,
v7.1.0; `8faecda`/`6e431fe`, v7.2.0/v7.3.0; y trabajo de la sesión actual
sin commitear — ver nota de cabecera). Dos de las tres piezas restantes
de la Sección 5.3 tienen ahora un primer avance:

- **Dimensiones programáticas separadas**: `vparty_economico`,
  `vparty_progresismo`, `vparty_populismo` (dataset V-Party, V-Dem
  Institute) están pobladas para **151 de 313 filas** de
  `clasificacion_ideologica_agrupaciones.csv` — **no 115/313**, cifra que
  este documento traía desde `3277a60` y que ya estaba mal en ese commit
  (confirmado con `git show cfb6309:...`, ya daba 151 en ese momento; no
  cambió después). **Hallazgo nuevo de esta pasada**: el desglose por
  fuente de `data/agrupaciones/v-party/README.md` (cruce directo 62 filas
  + proxy de ola cercana 6 + fila hermana 13 + estimación propia 40 = 121)
  solo explica ~121 de las 151 filas reales — quedan **~30 filas con
  `vparty_economico` poblado sin fuente documentada** en ese README. No
  se investigó la causa en esta pasada; `docs/vparty_cuadrantes.md`
  también repite el "115 de 313" desactualizado. Ese README sigue siendo
  el único lugar pensado para documentar la procedencia de cada fila,
  pero quedó desactualizado — no citarlo como fuente completa sin
  reconciliar primero este hueco.
- **Escala comparable entre gráficos** (corrección de esta sesión, no
  pedida por la nota original pero directamente relevante para leer el
  cuadrante V-Party como dato, no solo como ilustración): los PNG de
  `vparty_cuadrantes_local.graficar_cuadrantes_partido` calculaban el
  rango de cada eje a partir de los datos de ese PNG puntual —
  asimétrico respecto de 0 y distinto de un (año, nivel) a otro, así que
  la posición de un partido en un gráfico no era comparable contra la de
  otro. `_limites_globales()` calcula ahora un rango fijo y simétrico
  respecto de 0 sobre toda la cobertura V-Party, usado sin cambios en
  los ~22 PNG de `graficos/agrupaciones/<año>/` y en el cuadro
  interactivo de `distribucion_ideologica_interactiva.py` (payload
  `eje_limites`, nunca recalculado por render). **Sigue sin corregirse**,
  a propósito: `vparty_cuadrantes.py::graficar_cuadrantes` (PNG nacional
  y el modo combinado-por-años de `generar_localidad()`).
- **Cuadrante V-Party real por localidad, ya no "próximamente"**: la
  pestaña interactiva mostraba, al clickear un circuito, un placeholder
  fijo — pese a que `vparty_cuadrantes_local.tabla_localidades()` ya
  calculaba esos mismos puntos para los PNG estáticos. Ahora el panel de
  localidad muestra el cuadrante real (color calculado sobre el universo
  de partidos a nivel distrito de ese año, para que un partido tenga el
  mismo color en cualquier localidad; mismo `eje_limites` fijo que el
  panel distrital). `generar_localidad_por_anio()` agrega además ~567 PNG
  nuevos en `graficos/agrupaciones/por_localidad/<año>/` (uno por
  localidad/año/nivel, mismo encoding que el distrito) — explícitamente
  no versionados, mismo criterio que `graficos/por_localidad/`. No
  reemplaza `generar_localidad()` (años combinados, color por año, en
  `graficos/por_localidad/vparty/`) — las dos vistas se siguen generando.
- **Oficialismo**: `data/agrupaciones/oficialismos.csv`, sin cambios
  desde v7.1.0.
- **Oferta electoral** (tamaño/fragmentación de la oferta por circuito o
  distrito) sigue sin ninguna pieza — 🔴, sin cambios.

## Plan de trabajo

| Ítem | Estado |
|---|---|
| Congelar v1.0.0 como punto de partida | 🟢 (tag existe) |
| Corregir el repositorio (8.1 prioridad inmediata) | 🟡 ver tabla arriba |
| Construir el libro de códigos | 🟡 `filiacion_politica` separada de `campo_ideologico` (ver 8.2); posición ideológica ya existía; grado de incertidumbre y justificación existen por agrupación en `tabla_referencia_filiacion_politica.csv` (`confianza_clasificacion`/`nota_clasificacion`, no fusionados al CSV principal); dimensiones programáticas (V-Party, parcial, 151/313 filas — ver hallazgo de desglose incompleto en 8.2) y oficialismo (`oficialismos.csv`) ahora tienen un primer avance; **sigue faltando** oferta electoral |
| Ampliar etapas y fuentes (PASO/balotaje) | 🟢 base agregada en `909760e`; ampliado sustancialmente en `80a16db` (posterior a v3.3.0) — hoy cubre todo combo (año, nivel, etapa) con PASO/balotaje disponible salvo las excepciones documentadas por diseño (2011/intendente y todo 2025 sin PASO, Ley 27.781; balotaje sólo Presidente 2015/2023) |
| Tabla maestra circuito × elección × cargo × etapa | 🔴 |
| Armonizar territorio y Censo | 🟡 correspondencia espacial circuito↔radio lista (v2.0.0); **variables temáticas del Censo por radio, no extraídas todavía** (REDATAM manual, ver `EXTRACCION_REDATAM.md`) — sin cambios desde v3.3.0 |
| Correspondencia circuito↔localidad (barrio, no censal) | 🟡 crosswalk armado (`data/geolocalizacion/fuentes_extra/circuito_localidad.csv`): 16/68 circuitos con fuente oficial (Resolución 1990/2007, todos `oficial_confirmada` — 503/503A se reclasificaron a MELCHOR_ROMERO por decisión explícita, ver abajo), 65/68 con alguna fuente de El Día ("barrio por barrio", octubre 2025) — 6/68 con la etiqueta recontrastada contra fuentes web adicionales (`revision_web`), 59/68 sin esa revisión (`periodistico_no_oficial`). Los 16 oficiales auditados contra el detalle completo del anexo, no solo la descripción general (`AUDITORIA_DISCREPANCIAS.md`) — de 14 comparables, 8 resultan `discrepancia_real` contra la etiqueta de El Día (más de lo que sugería `CIRCUITOS_LOCALIDADES.md`), aunque eso ya no determina el agrupamiento de 503/503A. Agregación de resultados (`electoral/localidades.py`, `analisis/cuadros_por_localidad.py`, 22 cuadros 2011-2025, ~99% de cobertura de votos combinando los tres niveles, `SIN_DETERMINAR` siempre visible, hoy solo el circuito 521) y series temporales (`analisis/serie_temporal_por_localidad.py`, 132 imágenes) ya construidas. Es un tipo de correspondencia territorial distinto y paralelo al de la fila de arriba (esta es para nombres de barrio legibles, no para unir Censo) — no lo reemplaza ni depende de él, y tampoco depende del catálogo de `data/geolocalizacion/` (fila nueva abajo, coordenadas de localidad, otro propósito). **Falta**: subir de nivel los circuitos que quedan en `periodistico_no_oficial` dentro de las familias 504/505/508/509 (504, 508D, 508F y 508G ya subieron a `revision_web`; quedan 504A, 505, 505A, 505B, 508, 508A, 508B, 508C, 508E, 509 y 509A), y diagnóstico causal del hueco de datos de circuito 493/2023 (ver ítem 8.1.5; ya no se ve a simple vista en la fila MELCHOR_ROMERO, diluido por los votos reales de 503/503A) — sin cambios desde v3.3.0 |
| Separar exploración y contraste | 🔴 no hay todavía cruce elecciones↔socioeconomía, elecciones↔macroeconomía ni elecciones↔ICG; sin cambios de fondo pese a que los tres dominios auxiliares ya existen por separado (ver "Ampliaciones de alcance" abajo) |

## Ampliaciones de alcance desde v3.3.0

Estas piezas **no estaban pedidas por `nota_metodologica.md`** (que es anterior a todas ellas) — se agregaron como expansión de alcance del repositorio, no como respuesta a un punto de la auditoría. Se listan acá para que la lectura de este documento no de la falsa impresión de que no pasó nada entre v3.3.0 y hoy; el detalle de cada una vive en su propia documentación, no se duplica acá:

| Dominio | Qué se agregó | Documentación |
|---|---|---|
| Macroeconomía | Series nacionales 2011-2025 (IPC, tipo de cambio, deuda, PBI, mercado laboral), grano exclusivamente nacional, sin `circuito_id` ni localidad — nunca cruzada espacialmente con lo electoral, sólo por fecha | `docs/plan_macroeconomia.md`, `data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` |
| Geolocalización | Catálogo validado de las 36 localidades (Georef-AR × Ministerio de Obras Públicas), lat/lon por localidad — todavía no cruzado con `circuito_id` ni Censo (explícitamente fuera de alcance por ahora) | `data/geolocalizacion/LOCALIDADES.md` |
| Mapa interactivo + GitHub Pages | `docs/mapa_electoral_la_plata.html` (v4-v5) y, desde v7.2.0, `docs/distribucion_ideologica_la_plata.html` (cuadrantes V-Party interactivos, selector Nivel+Año, autoplay) — ambos movidos a `src/visualizacion/` (nuevo módulo, separado de `src/analisis/`) en v7.2.0. 68 circuitos × 22 combos (año, nivel) generales el primero; el segundo agrega desde esta sesión un cuadrante real por localidad (antes placeholder "próximamente", ver 8.2) | `CLAUDE.md`, `docs/FUNCIONALIDADES.md`, skill `laplata-visualizacion` |
| V-Party / oficialismo | `vparty_economico`/`progresismo`/`populismo` (**151/313 filas**, no 115/313 como decía este documento — ver hallazgo de desglose incompleto en 8.2) y `oficialismos.csv`; esta sesión además: escala fija/simétrica entre todos los PNG y el cuadro interactivo, cuadrante real por localidad, y ~567 PNG nuevos por (localidad, año, nivel) en `graficos/agrupaciones/por_localidad/` (no versionados) — ver 8.2 arriba | `data/agrupaciones/v-party/README.md` (desactualizado, ver 8.2), `docs/vparty_cuadrantes.md` |
| ICG (v7.3.0) | Índice de Confianza en el Gobierno (UTDT, microdato externo no redistribuible) — serie mensual La Plata vs. país 2011-presente (ponderada, "país" incluye a La Plata a propósito) más cortes demográficos (sexo/edad/edu, mensual a nivel país y anual a nivel La Plata por tamaño de muestra). Dominio nuevo bajo `src/socioeconomia/`, sin cruce todavía con lo electoral | `data/socioeconomia/ICG.md`, `data/socioeconomia/icg/README.md` |

Ninguna de las cinco resuelve por sí sola "Separar exploración y contraste" (fila de arriba en "Plan de trabajo") — son insumos nuevos para ese cruce, no el cruce en sí.

## Sección 10

| Pieza pedida | Estado a v6.0.0 |
|---|---|
| Hoja de pregunta/objetivos/hipótesis | 🟢 esta misma nota, incorporada |
| Libro de códigos político | 🟡 ver "Construir el libro de códigos" arriba y 8.2 |
| Auditoría de mesas, circuitos y cobertura | 🟡 parcial (ver 8.1.5) |
| Tabla maestra | 🔴 |
| Primer análisis descriptivo (tamaño de bloques / composición / participación / territorio) | 🔴 — v2.0.0 construyó la capa socioeconómica pero **todavía no la cruzó** con resultados electorales |

## Lectura del conjunto

**Validación completa a v6.0.0** (14 commits desde v3.3.0, revisados uno
por uno para este documento — ver "Ampliaciones de alcance" arriba para
lo que quedó fuera del recuento de 8.1 por no ser parte de lo que pedía
la nota). De los 14 puntos técnicos de 8.1, **el recuento no cambia: 7
resueltos, 5 parciales, 2 abiertos** — pero dos ítems (11 y 12) tenían
evidencia vieja o directamente incorrecta que esta pasada corrigió (ítem
11: la nota "sin commitear" que arrastraba desde v3.3.0 ya estaba resuelta
en ese mismo tag; ítem 12: la cobertura de tests creció bastante más de lo
que el texto anterior reflejaba — de paso se corrigió la misma afirmación
desactualizada que tenía `CLAUDE.md`). De las 5 piezas del "producto mínimo"
que pedía la Sección 10, la primera (esta nota) está resuelta y el libro de
códigos político pasó a parcial (`filiacion_politica`, y ahora también
dimensiones programáticas V-Party y oficialismo — ver 8.2) — **tabla
maestra y cruce elecciones-socioeconomía/macroeconomía siguen siendo el
trabajo pendiente central del proyecto**, sin movimiento pese a que en el
camino se sumaron tres dominios enteros (macro, geolocalización, V-Party)
que son insumo para ese cruce pero no lo reemplazan. La Sección 8.2
(codificación política) tiene ahora dos avances (familia política, y
dimensiones programáticas + oficialismo parciales); la Sección 6
(protocolo de inferencia) sigue sin atacarse.

**Esta pasada (v7.1.0 → v7.3.0 + sesión actual)** no es una revalidación
completa de 8.1 — se limitó a 8.2 (V-Party) más el ítem 12 (tests), el
único de 8.1 con trabajo nuevo verificable en este período. El hallazgo principal
no es una funcionalidad nueva sino un **error propio detectado**: la
cobertura V-Party que este documento reportaba (115/313) estaba mal
desde que se escribió, y el desglose por fuente de
`data/agrupaciones/v-party/README.md` tampoco explica el total real
(151/313) — quedan ~30 filas sin procedencia documentada, sin
investigar todavía. Aparte de eso, el trabajo de la sesión (escala fija
entre gráficos V-Party, cuadrante real por localidad reemplazando
"próximamente", pipeline ICG completo, limpieza de docstrings/documentación
redundante) mejora la calidad y consistencia de piezas ya existentes,
pero **no mueve ninguna de las dos prioridades centrales** (tabla
maestra, cruce elecciones-socioeconomía/macroeconomía/ICG) — siguen
siendo el trabajo pendiente central del proyecto, ahora con un insumo
auxiliar más (ICG) en la misma situación que macro/geolocalización.