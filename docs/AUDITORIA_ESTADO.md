# Estado de la auditoría (`NOTA_METODOLOGICA.md`, Sección 8) — a v7.1.0

Este documento existe porque la nota metodológica es un documento de trabajo
fechado sobre `v1.0.0`. Se actualiza cada vez que se cierra un punto.

Convención: 🟢 resuelto · 🟡 parcial · 🔴 abierto

**Alcance de esta pasada (v6.0.0 → v7.1.0):** re-auditada solo la Sección
8.2 (V-Party), por ser lo que tocó el commit `cfb6309` (tag `v7.1.0`) —
ver el bloque actualizado más abajo. Los commits de v7.0.0
(`a9b84d5`..`72b54d2`, reconstrucción del flujo por localidad sobre
geolocalización) no se re-auditaron en esta pasada; el resto del
documento (8.1, Sección 10, "Lectura del conjunto") sigue reflejando la
validación completa a v6.0.0 descripta ahí mismo, no una nueva pasada
completa a v7.1.0.

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
| 12 | Dependencia de notebooks y cwd; sin tests de `client.py`/`analisis/` | 🟡 | se agregaron tests de `models.py` (`909760e`); con `d006699` también se agregó cobertura para la capa de localidades (`test_localidades.py`, `test_cuadros_por_localidad.py`, `test_serie_temporal_por_localidad.py`). **Actualización relevante desde v3.3.0**: `11718f9` agregó tests de la lógica pura (no el renderizado matplotlib en sí) de `graficos.py`, `cuadros_anualizados.py`, `serie_temporal.py`, `serie_temporal_filiacion.py`, `totales_por_lista.py` y `comparativo_nivel.py` — la afirmación de `CLAUDE.md` de que esos módulos "still have no automated tests" quedó desactualizada por ese mismo commit y debería corregirse ahí también. Los tres dominios nuevos (macro, geolocalización, V-Party) siguen el mismo criterio ya establecido: lógica pura testeada, capa de red/rendering no — `macroeconomia/series.py` y `series_anuales.py` (`7e5e01d`/`b4ec146`), `geolocalizacion/catalogo.py` (`4746cbe`), y la lógica de agregación de `mapa_interactivo.py` (`dd12bb3`/`e45d43f`) tienen tests; `electoral/client.py`, `macroeconomia/datos_gob_client.py`/`graficos.py`/`auditoria_estadisticasbcra.py`, `geolocalizacion/georef_client.py`/`mapa.py`, `analisis/vparty_cuadrantes.py`/`vparty_cuadrantes_local.py` (plotting) y el resto de renderizado matplotlib siguen sin cobertura, por diseño (necesitan red o producen imágenes, no lógica a aserción directa) — `generar_v_party_propio.py` y la lógica pura de `vparty_cuadrantes_local.py` (join/agregación/color, `cfb6309`) sí la tienen. 322 tests en total a v7.1.0 (`pytest -q`, eran 265 a v6.0.0), suite completa en ~5s. |
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

🟡 Parcial, actualizado (commits `a9b84d5`/`8c5fa23`, v6.0.0; y `cfb6309`,
v7.1.0 — el resto de esta sección no fue reauditado, ver nota de cabecera
del documento). Dos de las tres piezas restantes de la Sección 5.3 tienen
ahora un primer avance:

- **Dimensiones programáticas separadas**: `vparty_economico`,
  `vparty_progresismo`, `vparty_populismo` (dataset V-Party, V-Dem
  Institute) se agregaron a `clasificacion_ideologica_agrupaciones.csv`
  para 115 de 313 filas (a v6.0.0 eran 62) — de qué fuente viene cada
  fila puntual (V-Party real por match directo o proxy de ola, fila
  hermana del mismo nombre exacto, o estimación propia calibrada por
  encuesta de expertos) está documentado en un único lugar,
  `data/agrupaciones/v-party/README.md` — no se duplica más en
  `docs/vparty_cuadrantes.md` ni en `CLAUDE.md` (`cfb6309`, consolidación
  de redundancia). Cobertura parcial por diseño: V-Party real sólo cubre
  Diputados Nacionales 2011-2019, no todos los `nivel`/año de este repo;
  el resto de la cobertura viene de la estimación propia
  (`src/analisis/generar_v_party_propio.py`, calibrada por regresión
  lineal contra los partidos con valor real, a partir de una encuesta a
  expertos anonimizada y ahora git-tracked —
  `data/agrupaciones/v-party/encuesta_partidos_propia.csv`). Nuevo en
  `cfb6309`: `src/analisis/vparty_cuadrantes_local.py` grafica estas tres
  variables contra los votos reales de La Plata (no el dataset nacional)
  — un cuadrante económico×progresismo por partido, coloreado por familia
  política y con tamaño = % de votos, un PNG por (año, nivel) para todo
  el distrito (`graficos/agrupaciones/<año>/v_party_<nivel>.png`,
  git-tracked) más un PNG por (nivel, localidad) (`graficos/por_localidad/vparty/`,
  no tracked).
- **Oficialismo**: `data/agrupaciones/oficialismos.csv` agrega, por
  `(año, nivel)` 2011-2025, quién ganó y si ya era oficialismo
  (`era_oficialismo`) — primera vez que esa dimensión queda explícita en
  el repo.
- **Oferta electoral** (tamaño/fragmentación de la oferta por circuito o
  distrito) sigue sin ninguna pieza — 🔴, sin cambios.

## Plan de trabajo

| Ítem | Estado |
|---|---|
| Congelar v1.0.0 como punto de partida | 🟢 (tag existe) |
| Corregir el repositorio (8.1 prioridad inmediata) | 🟡 ver tabla arriba |
| Construir el libro de códigos | 🟡 `filiacion_politica` separada de `campo_ideologico` (ver 8.2); posición ideológica ya existía; grado de incertidumbre y justificación existen por agrupación en `tabla_referencia_filiacion_politica.csv` (`confianza_clasificacion`/`nota_clasificacion`, no fusionados al CSV principal); dimensiones programáticas (V-Party, parcial, 115/313 filas a v7.1.0) y oficialismo (`oficialismos.csv`) ahora tienen un primer avance (ver 8.2 actualizado); **sigue faltando** oferta electoral |
| Ampliar etapas y fuentes (PASO/balotaje) | 🟢 base agregada en `909760e`; ampliado sustancialmente en `80a16db` (posterior a v3.3.0) — hoy cubre todo combo (año, nivel, etapa) con PASO/balotaje disponible salvo las excepciones documentadas por diseño (2011/intendente y todo 2025 sin PASO, Ley 27.781; balotaje sólo Presidente 2015/2023) |
| Tabla maestra circuito × elección × cargo × etapa | 🔴 |
| Armonizar territorio y Censo | 🟡 correspondencia espacial circuito↔radio lista (v2.0.0); **variables temáticas del Censo por radio, no extraídas todavía** (REDATAM manual, ver `EXTRACCION_REDATAM.md`) — sin cambios desde v3.3.0 |
| Correspondencia circuito↔localidad (barrio, no censal) | 🟡 crosswalk armado (`data/geolocalizacion/fuentes_extra/circuito_localidad.csv`): 16/68 circuitos con fuente oficial (Resolución 1990/2007, todos `oficial_confirmada` — 503/503A se reclasificaron a MELCHOR_ROMERO por decisión explícita, ver abajo), 65/68 con alguna fuente de El Día ("barrio por barrio", octubre 2025) — 6/68 con la etiqueta recontrastada contra fuentes web adicionales (`revision_web`), 59/68 sin esa revisión (`periodistico_no_oficial`). Los 16 oficiales auditados contra el detalle completo del anexo, no solo la descripción general (`AUDITORIA_DISCREPANCIAS.md`) — de 14 comparables, 8 resultan `discrepancia_real` contra la etiqueta de El Día (más de lo que sugería `CIRCUITOS_LOCALIDADES.md`), aunque eso ya no determina el agrupamiento de 503/503A. Agregación de resultados (`electoral/localidades.py`, `analisis/cuadros_por_localidad.py`, 22 cuadros 2011-2025, ~99% de cobertura de votos combinando los tres niveles, `SIN_DETERMINAR` siempre visible, hoy solo el circuito 521) y series temporales (`analisis/serie_temporal_por_localidad.py`, 132 imágenes) ya construidas. Es un tipo de correspondencia territorial distinto y paralelo al de la fila de arriba (esta es para nombres de barrio legibles, no para unir Censo) — no lo reemplaza ni depende de él, y tampoco depende del catálogo de `data/geolocalizacion/` (fila nueva abajo, coordenadas de localidad, otro propósito). **Falta**: subir de nivel los circuitos que quedan en `periodistico_no_oficial` dentro de las familias 504/505/508/509 (504, 508D, 508F y 508G ya subieron a `revision_web`; quedan 504A, 505, 505A, 505B, 508, 508A, 508B, 508C, 508E, 509 y 509A), y diagnóstico causal del hueco de datos de circuito 493/2023 (ver ítem 8.1.5; ya no se ve a simple vista en la fila MELCHOR_ROMERO, diluido por los votos reales de 503/503A) — sin cambios desde v3.3.0 |
| Separar exploración y contraste | 🔴 no hay todavía cruce elecciones↔socioeconomía ni elecciones↔macroeconomía; sin cambios desde v3.3.0 pese a que ambos dominios auxiliares ya existen por separado (ver "Ampliaciones de alcance" abajo) |

## Ampliaciones de alcance desde v3.3.0

Estas piezas **no estaban pedidas por `nota_metodologica.md`** (que es anterior a todas ellas) — se agregaron como expansión de alcance del repositorio, no como respuesta a un punto de la auditoría. Se listan acá para que la lectura de este documento no de la falsa impresión de que no pasó nada entre v3.3.0 y v6.0.0; el detalle de cada una vive en su propia documentación, no se duplica acá:

| Dominio | Qué se agregó | Documentación |
|---|---|---|
| Macroeconomía | Series nacionales 2011-2025 (IPC, tipo de cambio, deuda, PBI, mercado laboral), grano exclusivamente nacional, sin `circuito_id` ni localidad — nunca cruzada espacialmente con lo electoral, sólo por fecha | `docs/plan_macroeconomia.md`, `data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` |
| Geolocalización | Catálogo validado de las 36 localidades (Georef-AR × Ministerio de Obras Públicas), lat/lon por localidad — todavía no cruzado con `circuito_id` ni Censo (explícitamente fuera de alcance por ahora) | `data/geolocalizacion/LOCALIDADES.md` |
| Mapa interactivo + GitHub Pages | `docs/mapa_electoral_la_plata.html`, único artefacto interactivo del repo, 68 circuitos × 22 combos (año, nivel) generales, choropleth por campo ideológico/familia política/ausentismo | `CLAUDE.md`, sección `mapa_interactivo.py` |
| V-Party / oficialismo | `vparty_economico`/`progresismo`/`populismo` (115/313 filas de `clasificacion_ideologica_agrupaciones.csv` a v7.1.0, antes 62/313) y `oficialismos.csv` (oficialismo por año-nivel 2011-2025) — ver 8.2 arriba | `data/agrupaciones/v-party/README.md` (fuente única de la metodología de carga), `docs/vparty_cuadrantes.md` |

Ninguna de las cuatro resuelve por sí sola "Separar exploración y contraste" (fila de arriba) — son insumos nuevos para ese cruce, no el cruce en sí.

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