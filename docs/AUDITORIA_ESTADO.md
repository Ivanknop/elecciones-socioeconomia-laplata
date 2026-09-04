# Estado de la auditoría (`NOTA_METODOLOGICA.md`, Sección 8) — a v8.0.0 (post-v7.4.0) + sesión actual

Este documento existe porque la nota metodológica es un documento de trabajo
fechado sobre `v1.0.0`. Se actualiza cada vez que se cierra un punto.

Convención: 🟢 resuelto · 🟡 parcial · 🔴 abierto · 🔒 bloqueado (fuera de alcance actual)

**Alcance de esta pasada (v7.4.0 → v8.0.0, 15 commits, + sesión actual
todavía sin commitear):** lo que la pasada anterior describía como
"trabajo de la sesión actual, todavía sin commitear" (escala fija V-Party,
cuadrante real por localidad, limpieza de docstrings) en realidad ya se
había commiteado como `cfb2c39`/**v7.4.0** — este documento quedó
describiendo ese estado como "sin taggear" durante 15 commits más de
historia real. Dos de esas piezas además **se revirtieron** después:
`fb35b41`/`4df9850` sacaron el cuadrante real por localidad (ver hallazgo
en 8.2) al migrar la fuente de datos de la pestaña interactiva a
`data/tfi_data/elecciones/`, que no tiene geometría de circuito para
2001-2009. Esta pasada: (1) corrige esa desincronización de versión, (2)
incorpora un dominio nuevo entero que no existía a v7.4.0 — el panel
temporal de ventanas electorales, `src/ml_models/` (ver "Ampliaciones de
alcance") —, y (3) repite el patrón de la pasada anterior: la sesión que
generó esta actualización hizo su propia auditoría de documentación de
punta a punta (rutas, comandos, nombres de función, cifras) contra el
código y los datos reales, y encontró **un bug funcional real, no solo de
documentación** (ver hallazgo principal más abajo). El resto del
documento (8.1 salvo los ítems 12/14, Sección 10, "Lectura del conjunto")
sigue reflejando la validación completa a v6.0.0 descripta ahí mismo, no
una nueva pasada completa de los 13 puntos (se retiró el ítem de
escrutinio provisorio/definitivo — diferencia ínfima, considerada
irrelevante para el proyecto).

## 8.1 — Correcciones y fragilidades confirmadas

| # | Punto | Estado | Evidencia |
|---|---|---|---|
| 1 | Duhalde 2011 mal codificado | 🟢 | corregido en `909760e` |
| 2 | Progresistas 2015 inconsistente | 🟢 | corregido en `909760e` |
| 3 | Secuencia reproducible borra clasificación manual | 🟢 | append-only, nunca sobrescribe (ver README/CLAUDE.md, `909760e`) |
| 4 | Circuitos no normalizados longitudinalmente | 🟢 | normalización sin ceros a la izq., `circuito_id_correspondencias.csv` |
| 5 | Mesas sin votos / cobertura incompleta | 🟡 | se documenta `mesas_sin_votos_positivos` por circuito; **falta** el % de cobertura por circuito y el análisis de sensibilidad que pide la nota. Nueva evidencia concreta (ver `data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`, hallazgo circuito 493): Gobernador/Intendente/Presidente 2023 tienen `electores=109` con `positivos=0` y `otros=0` en ese circuito — no un caso de "mesas con cero votos positivos" sino de circuito entero sin ningún voto cargado, y solo en 2023. Sigue sin diagnóstico causal. |
| 6 | JSON agregado Presidente 2019 incompleto | 🟢 | documentado en README + `coincide_con_agregado_json`/`advertencia_fuente` |
| 8 | Inconsistencias del README (3 vs 4 columnas, "años pares", instrucción truncada) | 🟢 | README reescrito en `3899006` |
| 9 | Escala ideológica duplicada (CSV sin usar) | 🟢 | `graficos.py` ya lee `campo_ideologico.csv` (vía `_cargar_escala_ideologica()`, ruta resuelta por `__file__` para no depender del cwd) en vez del dict `IDEOLOGIAS` hardcodeado; CSV pasado a separador `,` para consistencia con el resto de `data/agrupaciones/`. Ver `docs/PLAN_CORRECCIONES_ELECTORALES.md` §2.1 |
| 10 | Series unen cargos distintos sin marcarlo | 🟡 | está documentado en README con tabla explícita; el panel/serie separada por cargo que pedía la nota ya existe en dos formas -- `cuadros_anualizados.py` (bar chart por año, cargos lado a lado, sin sumarlos) y, esta sesión, `comparativo_nivel.py` (cuadro Markdown por año con el % de cada agrupación en Municipio/Provincia/Nación más las tres diferencias entre pares). **Sigue faltando**: marcar visualmente el cambio de tipo de elección dentro de la serie fusionada de `serie_temporal.py` en sí (hoy solo está en el sub-label de texto del eje x, no en el trazo) |
| 11 | Gráficos omiten blancos/nulos/abstención; volumen de PNG | 🟡 | resuelta la primera mitad (blancos/nulos/abstención): todo gráfico de `src/analisis/` (barras/torta, las tres series temporales, `cuadros_anualizados`, y las variantes `por_localidad`) suma `blanco_nulo` y `ausentismo` (`electores` del circuito/nivel menos votos válidos) junto al desglose por `campo_ideologico`/`filiacion_politica`, vía `graficos._votos_no_ideologicos` — el % que muestra cada gráfico pasa de "% de los positivos" a "% del padrón" (ver README, sección "Gráficos"). **Corrección a esta misma auditoría**: la nota "cambio sin commitear todavía" que traía este ítem era vieja para cuando se congeló v3.3.0 — el commit real es `e41c8d0`, ya incluido en v3.3.0. `mapa_interactivo.py` (v4-v5) extiende el mismo criterio a su choropleth de "Ausentismo". **Sigue abierto**: el volumen de PNG (miles de archivos por circuito) no cambió. |
| 12 | Dependencia de notebooks y cwd; sin tests de `client.py`/`analisis/` | 🟡 | se agregaron tests de `models.py` (`909760e`); con `d006699` también se agregó cobertura para la capa de localidades (`test_localidades.py`, `test_cuadros_por_localidad.py`) — **corrección a esta misma auditoría**: `test_serie_temporal_por_localidad.py` ya no existe, ese módulo se borró en `fb35b41` (ver 8.2/Plan de trabajo). `11718f9` agregó tests de la lógica pura de `graficos.py`, `cuadros_anualizados.py`, `serie_temporal.py`, `serie_temporal_filiacion.py`, `totales_por_lista.py` y `comparativo_nivel.py`, ya reflejado en `CLAUDE.md`. Los dominios agregados desde entonces (macro, geolocalización, V-Party, ICG, y ahora el panel temporal de `src/ml_models/` — ver "Ampliaciones de alcance") siguen el mismo criterio ya establecido: lógica pura testeada, capa de red/rendering/orquestación no. **526 tests en total a esta sesión** (`pytest -q`; 335 a v7.3.0/sesión previa) — el salto de +191 es casi todo `src/ml_models/` (cinco fases del panel temporal, `tests/ml_models/`) más `tests/visualizacion/test_trayectorias_economicas*.py`; ninguna función de orquestación/plotting nueva (`construir_payload`, `generar_trayectorias_economicas*`, el template HTML) sumó test propio, mismo criterio de siempre. Suite completa en ~9s. |
| 13 | Falta procedencia (hash, fecha, versión del libro de códigos) por archivo derivado | 🔴 | sin cambios conocidos — los nuevos dominios (macro, geolocalización) documentan procedencia en prosa (`SISTEMATIZACION_VARIABLES_MACRO.md`, `LOCALIDADES.md`) pero tampoco embeben hash/fecha/versión por archivo derivado |
| 14 | Repositorio pesado (PNG + datos) | 🟡 | `.gitignore` sigue trackeando sólo `graficos/distrito/serie_temporal/` + `graficos/socioeconomia/eph/` + `graficos/geolocalizacion/` + los JSON de `graficos/agrupaciones/`/`graficos/socioeconomia/iaelap_*` — 65 archivos trackeados en `graficos/` a esta sesión (53 a v6.0.0). La mitad "datos" sigue siendo la real y ahora pesa más porque se sumó un dominio entero más (`src/ml_models/`, panel temporal): `data/distrito/**/*.csv` solo sigue en 227 MB (sin cambios); `data/` completo son 439 MB (413 MB a la pasada anterior, +26 MB por `data/tfi_data/`); el `.git` empaquetado son ~98 MB (`git count-objects -v`, ~95 MB a la pasada anterior). Sigue sin ser bloat desperdiciado — mismo diagnóstico de siempre, ahora con un dominio más cacheando de la misma forma deliberada. **Conclusión sin cambios**: la única palanca real para reducir en serio sigue siendo dejar de trackear `data/distrito/**/*.csv` y aceptar que reproducir el pipeline exige red. |

*(El ítem 7 de esta tabla — "todo el repo usa escrutinio provisorio" —
se retiró: la diferencia contra el escrutinio definitivo se consideró
ínfima e irrelevante para el proyecto. Numeración no reasignada a
propósito, para no romper referencias cruzadas al resto de los ítems.)*

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
v7.1.0; `8faecda`/`6e431fe`/`cfb2c39`, v7.2.0-v7.4.0; y los 15 commits
hasta v8.0.0, ver nota de cabecera). Dos de las tres piezas restantes de la
Sección 5.3 tienen ahora un primer avance:

- **Dimensiones programáticas separadas**: `vparty_economico`,
  `vparty_progresismo`, `vparty_populismo` (dataset V-Party, V-Dem
  Institute, más aproximación propia calibrada donde no hay cobertura
  real — ver `data/agrupaciones/v-party/README.md`) están pobladas para
  **208 de 347 filas** de `clasificacion_ideologica_agrupaciones.csv` —
  **no 151/313**, cifra que este documento traía desde la pasada
  anterior. El crecimiento del total (313→347) viene de `2640650`
  (elecciones 2001-2009/2025 municipal-provincial agregadas al backfill
  de clasificación). **El hueco de procedencia que ya se había detectado
  sigue sin investigarse y creció en la misma proporción**: el desglose
  por fuente de `data/agrupaciones/v-party/README.md` (cruce directo +
  proxy de ola cercana + fila hermana + estimación propia = 121 filas
  documentadas) ya no explica ni siquiera la base sobre la que se
  calculó originalmente, y de las 208 filas reales pobladas hoy quedan
  bastantes más de las ~30 sin fuente documentada que se habían
  detectado a 151/313 — no se recalculó el desglose exacto en esta
  pasada, es una investigación de datos fila por fila, no una corrección
  de texto. `docs/vparty_cuadrantes.md` también repite el "151/313"
  desactualizado. Ese README sigue siendo el único lugar pensado para
  documentar la procedencia de cada fila, pero está más desactualizado
  que antes — no citarlo como fuente completa sin reconciliar primero
  este hueco.

  **Actualización de esta misma sesión**: `clasificacion_ideologica_agrupaciones.csv`
  incorporó 2001-2009 (antes solo cubría 2011-2025) vía la nueva
  `src/analisis/completar_clasificacion_historica.py` (ver `CLAUDE.md`),
  que lee la clasificación ya resuelta a mano en
  `data/tfi_data/elecciones/<año>_<nivel>.csv` para esos años y la
  agrega append-only. El archivo pasó de 347 a **557 filas** (134→237
  agrupaciones únicas); `vparty_economico` poblado pasó de 208 a **356
  filas**. El hueco de procedencia de este bullet **creció en la misma
  proporción** — no se investigó de dónde sale cada una de esas ~235
  filas sin documentar en el README. Aparte, `filiacion_politica` (más
  abajo en esta sección) también perdió cobertura relativa: de 237
  agrupaciones únicas, 193 la tienen poblada (44 no) — antes eran 6 de
  134.
- **Escala comparable entre gráficos**: se agregó en `cfb2c39` como
  `vparty_cuadrantes_local._limites_globales()` (rango fijo y simétrico
  respecto de 0, en vez de uno recalculado por PNG) y sigue vigente, pero
  cambió de dueño: la pestaña interactiva ya no la llama desde ahí —
  `distribucion_ideologica_interactiva.py` usa hoy
  `vparty_distribucion_tfi.limites_globales()` (mismo criterio, fuente de
  datos distinta, ver bullet siguiente). El PNG estático equivalente
  también migró: `analisis.vparty_distribucion_tfi.graficar_cuadrantes_eleccion`
  reemplazó a `vparty_cuadrantes_local.graficar_cuadrantes_partido`
  (deprecado, ver `CLAUDE.md`). **Sigue sin corregirse**, a propósito:
  `vparty_cuadrantes.py::graficar_cuadrantes` (PNG nacional).
- 🔒 **Cuadrante V-Party real por localidad — bloqueado**: el proyecto
  pasó a trabajar a nivel municipal, no circuito/localidad, así que este
  punto queda fuera de alcance hasta que eso cambie (no se retoma la
  discusión de reintroducirlo). Registro histórico de lo que se hizo y
  revirtió, sin más acción prevista: se agregó y se revirtió en el
  mismo período que cubre esta pasada. `cfb2c39` (v7.4.0) había
  reemplazado el placeholder "próximamente" del panel de localidad por
  el cuadrante real (`generar_localidad_por_anio()`, ~567 PNG nuevos por
  localidad/año/nivel). Tres commits después, `4df9850`
  ("rehace la pestaña interactiva sin localidad") y `fb35b41` la
  sacaron de nuevo: al migrar la fuente de datos de la pestaña a
  `data/tfi_data/elecciones/<año>_<nivel>.csv` (ver "Ampliaciones de
  alcance") para cubrir 2001-2025 en vez de solo 2011-2025, se perdió la
  geometría de circuito que ese desglose necesitaba para 2001-2009 — no
  hay todavía un criterio definido para ese caso. **Estado real hoy: sin
  desglose por localidad**, un único bubble chart a nivel distrito por
  (nivel, año) — mismo estado que antes de `cfb2c39`, no una regresión
  nueva sino una decisión explícita documentada en `CLAUDE.md`/skill
  `laplata-visualizacion` ("no reintroducir sin volver a preguntar").
  `generar_localidad_por_anio()`/`_localidad_puntos_por_nivel()` ya no
  existen en el código (`fb35b41` las eliminó junto con sus ~567 PNG).
- **Oficialismo**: `data/agrupaciones/oficialismos.csv`, sin cambios
  desde v7.1.0 — ahora además reusado como insumo del panel temporal de
  `src/ml_models/` (ver "Ampliaciones de alcance").

## Plan de trabajo

| Ítem | Estado |
|---|---|
| Congelar v1.0.0 como punto de partida | 🟢 (tag existe) |
| Corregir el repositorio (8.1 prioridad inmediata) | 🟡 ver tabla arriba |
| Construir el libro de códigos | 🟡 `filiacion_politica` separada de `campo_ideologico` (ver 8.2); posición ideológica ya existía; grado de incertidumbre y justificación existen por agrupación en `tabla_referencia_filiacion_politica.csv` (`confianza_clasificacion`/`nota_clasificacion`, no fusionados al CSV principal) — ese CSV quedó en 121 agrupaciones únicas mientras `clasificacion_ideologica_agrupaciones.csv` ya tiene **237** (347→557 filas, 2001-2009 incorporado esta sesión — ver hallazgo en 8.2), de las cuales **44 no tienen `filiacion_politica` asignada en absoluto** (antes 6 de 134); dimensiones programáticas (V-Party, parcial, 356/557 filas — ver hallazgo de desglose incompleto en 8.2) y oficialismo (`oficialismos.csv`) ahora tienen un primer avance |
| Ampliar etapas y fuentes (PASO/balotaje) | 🟢 base agregada en `909760e`; ampliado sustancialmente en `80a16db` (posterior a v3.3.0) — hoy cubre todo combo (año, nivel, etapa) con PASO/balotaje disponible salvo las excepciones documentadas por diseño (2011/intendente y todo 2025 sin PASO, Ley 27.781; balotaje sólo Presidente 2015/2023) |
| Armonizar territorio y Censo | 🟡 correspondencia espacial circuito↔radio lista (v2.0.0); **variables temáticas del Censo por radio, no extraídas todavía** (REDATAM manual, ver `EXTRACCION_REDATAM.md`) — sin cambios desde v3.3.0 |
| Correspondencia circuito↔localidad (barrio, no censal) | 🔒 bloqueado — el proyecto pasó a trabajar a nivel municipal, no circuito/localidad; se conserva el estado alcanzado pero no hay trabajo previsto acá hasta que eso cambie. Estado al momento de bloquearse: crosswalk armado (`data/geolocalizacion/fuentes_extra/circuito_localidad.csv`): 16/68 circuitos con fuente oficial (Resolución 1990/2007, todos `oficial_confirmada` — 503/503A se reclasificaron a MELCHOR_ROMERO por decisión explícita, ver abajo), 65/68 con alguna fuente de El Día ("barrio por barrio", octubre 2025) — 6/68 con la etiqueta recontrastada contra fuentes web adicionales (`revision_web`), 59/68 sin esa revisión (`periodistico_no_oficial`). Los 16 oficiales auditados contra el detalle completo del anexo, no solo la descripción general (`AUDITORIA_DISCREPANCIAS.md`) — de 14 comparables, 8 resultan `discrepancia_real` contra la etiqueta de El Día (más de lo que sugería `CIRCUITOS_LOCALIDADES.md`), aunque eso ya no determina el agrupamiento de 503/503A. Agregación de resultados (`electoral/localidades.py`, `analisis/cuadros_por_localidad.py`, 22 cuadros 2011-2025, ~99% de cobertura de votos combinando los tres niveles, `SIN_DETERMINAR` siempre visible, hoy solo el circuito 521) ya construida. **Corrección a esta misma auditoría**: `analisis/serie_temporal_por_localidad.py` (132 imágenes), que esta tabla listaba como ya construido, se eliminó en `fb35b41` ("elimina salidas obsoletas") — no hay hoy una serie temporal por localidad activa. Es un tipo de correspondencia territorial distinto y paralelo al de la fila de arriba (esta es para nombres de barrio legibles, no para unir Censo) — no lo reemplaza ni depende de él, y tampoco depende del catálogo de `data/geolocalizacion/` (fila nueva abajo, coordenadas de localidad, otro propósito). **Falta**: subir de nivel los circuitos que quedan en `periodistico_no_oficial` dentro de las familias 504/505/508/509 (504, 508D, 508F y 508G ya subieron a `revision_web`; quedan 504A, 505, 505A, 505B, 508, 508A, 508B, 508C, 508E, 509 y 509A), y diagnóstico causal del hueco de datos de circuito 493/2023 (ver ítem 8.1.5; ya no se ve a simple vista en la fila MELCHOR_ROMERO, diluido por los votos reales de 503/503A) — sin cambios desde v3.3.0 |
| Separar exploración y contraste | 🔴 no hay todavía cruce elecciones↔socioeconomía, elecciones↔macroeconomía ni elecciones↔ICG; sin cambios de fondo pese a que los tres dominios auxiliares ya existen por separado (ver "Ampliaciones de alcance" abajo) |

## Ampliaciones de alcance desde v3.3.0

Estas piezas **no estaban pedidas por `nota_metodologica.md`** (que es anterior a todas ellas) — se agregaron como expansión de alcance del repositorio, no como respuesta a un punto de la auditoría. Se listan acá para que la lectura de este documento no de la falsa impresión de que no pasó nada entre v3.3.0 y hoy; el detalle de cada una vive en su propia documentación, no se duplica acá:

| Dominio | Qué se agregó | Documentación |
|---|---|---|
| Macroeconomía | Series nacionales 2011-2025 (IPC, tipo de cambio, deuda, PBI, mercado laboral), grano exclusivamente nacional, sin `circuito_id` ni localidad — nunca cruzada espacialmente con lo electoral, sólo por fecha | `docs/plan_macroeconomia.md`, `data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` |
| Geolocalización | Catálogo validado de las 36 localidades (Georef-AR × Ministerio de Obras Públicas), lat/lon por localidad — todavía no cruzado con `circuito_id` ni Censo (explícitamente fuera de alcance por ahora) | `data/geolocalizacion/LOCALIDADES.md` |
| Mapa interactivo + GitHub Pages | `docs/mapa_electoral_la_plata.html` (v4-v5), `docs/distribucion_ideologica_la_plata.html` (v7.2.0, cuadrantes V-Party interactivos, selector Nivel+Año, autoplay, hoy sin desglose por localidad — ver 8.2) y, desde los 15 commits hasta v8.0.0, dos pestañas más: `docs/trayectorias_economicas_la_plata.html`/`_bieleccion_la_plata.html` (movimiento trimestral de una ventana electoral, corta o de 4 años, sobre el panel de `src/ml_models/`). Cuatro scripts en `src/visualizacion/` en total. 68 circuitos × 22 combos (año, nivel) generales el primero | `CLAUDE.md`, `docs/FUNCIONALIDADES.md`, skill `laplata-visualizacion` |
| V-Party / oficialismo | `vparty_economico`/`progresismo`/`populismo` (**356/557 filas**, no 208/347 — 2001-2009 incorporado esta sesión, ver hallazgo de desglose incompleto, ahora más grande, en 8.2) y `oficialismos.csv`. `cfb2c39` había agregado escala fija/simétrica entre PNG y cuadro interactivo (sigue vigente) y un cuadrante real por localidad (revertido 3 commits después, ver 8.2) | `data/agrupaciones/v-party/README.md` (desactualizado, ver 8.2), `docs/vparty_cuadrantes.md` |
| ICG (v7.3.0) | Índice de Confianza en el Gobierno (UTDT, microdato externo no redistribuible) — serie mensual La Plata vs. país 2011-presente (ponderada, "país" incluye a La Plata a propósito) más cortes demográficos (sexo/edad/edu, mensual a nivel país y anual a nivel La Plata por tamaño de muestra). Dominio nuevo bajo `src/socioeconomia/`, sin cruce todavía con lo electoral. **Hallazgo de esta pasada**: el directorio del insumo crudo se renombró de `data/socioeconomia/icg/` a `icg-icc/` en `6f09f74`, pero el rename nunca tocó `ICG_RAW_PATH` (`src/constantes.py`) ni ~7 referencias en README/CLAUDE.md/docs que seguían citando la ruta vieja — correr `icg_exportar_csv` tiraba `FileNotFoundError`. Corregido en esta pasada (código y documentación) | `data/socioeconomia/ICG.md`, `data/socioeconomia/icg-icc/README.md` |
| Panel temporal de ventanas electorales (`src/ml_models/`) | Dominio nuevo entero, no existía a v7.4.0: una fila por transición electoral (año×nivel), cruzando resultado electoral local con las series del dominio macro, para modelado futuro. Cinco fases — calendario/oficialismo/ventanas (`construir_calendario.py`), resultado por distrito con fallback a `data/tfi_data/elecciones/` para 2001-2009 (`construir_resultado_distrito.py`), registro de variables económicas (`cargar_series_economicas.py`), features intra/interventana + `panel_ventanas.csv` (`features_ventana.py`/`construir_panel_ventanas.py`), y panel trimestral en formato largo sobre la ventana corta `_vc` (`data/tfi_data/panel/t-1/`) y sobre el bloque largo `_vl` t-2→t (`data/tfi_data/panel/t-2/`, 28 ventanas, no 31 — la primera transición de cada nivel no tiene bloque largo). `cargar_panel()` exige `nivel` sin default a propósito (D7/D10, no pooling accidental de los tres niveles) | `docs/especificacion_panel_temporal.md`, `docs/decisiones_metodologicas.md`, `CLAUDE.md` ("`src/ml_models/`") |

Ninguna de las seis resuelve por sí sola "Separar exploración y contraste" (fila de arriba en "Plan de trabajo") — son insumos nuevos para ese cruce, no el cruce en sí; el panel temporal en particular es el que más cerca está de ese cruce (junta lo electoral con lo macro por fecha), pero es insumo para modelado, no el cruce/análisis descriptivo en sí que pide la Sección 10.

## Sección 10

| Pieza pedida | Estado a v6.0.0 |
|---|---|
| Hoja de pregunta/objetivos/hipótesis | 🟢 esta misma nota, incorporada |
| Libro de códigos político | 🟡 ver "Construir el libro de códigos" arriba y 8.2 |
| Auditoría de mesas, circuitos y cobertura | 🟡 parcial (ver 8.1.5) |
| Primer análisis descriptivo (tamaño de bloques / composición / participación / territorio) | 🔴 — v2.0.0 construyó la capa socioeconómica pero **todavía no la cruzó** con resultados electorales |

## Lectura del conjunto

**Validación completa a v6.0.0** (14 commits desde v3.3.0, revisados uno
por uno para este documento — ver "Ampliaciones de alcance" arriba para
lo que quedó fuera del recuento de 8.1 por no ser parte de lo que pedía
la nota). De los 13 puntos técnicos de 8.1 (se retiró el ítem de
escrutinio provisorio/definitivo en una revisión posterior, ver nota de
cabecera), **el recuento queda: 7 resueltos, 5 parciales, 1 abierto** —
pero dos ítems (11 y 12) tenían evidencia vieja o directamente
incorrecta que esta pasada corrigió (ítem
11: la nota "sin commitear" que arrastraba desde v3.3.0 ya estaba resuelta
en ese mismo tag; ítem 12: la cobertura de tests creció bastante más de lo
que el texto anterior reflejaba — de paso se corrigió la misma afirmación
desactualizada que tenía `CLAUDE.md`). De las 4 piezas del "producto mínimo"
que pedía la Sección 10, la primera (esta nota) está resuelta y el libro de
códigos político pasó a parcial (`filiacion_politica`, y ahora también
dimensiones programáticas V-Party y oficialismo — ver 8.2) — **el cruce
elecciones-socioeconomía/macroeconomía sigue siendo el
trabajo pendiente central del proyecto**, sin movimiento pese a que en el
camino se sumaron tres dominios enteros (macro, geolocalización, V-Party)
que son insumo para ese cruce pero no lo reemplazan. La Sección 8.2
(codificación política) tiene ahora dos avances (familia política, y
dimensiones programáticas + oficialismo parciales); la Sección 6
(protocolo de inferencia) sigue sin atacarse.

**Esta pasada (v7.4.0 → v8.0.0, 15 commits, + sesión actual)** tampoco es
una revalidación completa de 8.1 — se limitó a los ítems 12/14 (tests,
peso del repo, ambos con evidencia nueva verificable) y a 8.2 (V-Party),
más una auditoría de documentación de punta a punta que no estaba
pedida por 8.1/8.2 en sí pero que reveló que este mismo documento venía
arrastrando una desincronización de versión: describía como "sesión
actual, sin commitear" un estado que en realidad llevaba 15 commits de
historia real encima, incluyendo la reversión de una de las piezas que
presentaba como logro vigente (cuadrante real por localidad, ver 8.2).

El hallazgo principal, otra vez, no es una funcionalidad nueva sino un
**error propio detectado** — mismo patrón que la pasada anterior, ahora
en dos niveles distintos:

1. **Un bug funcional real, no solo de documentación**: el rename
   `data/socioeconomia/icg/` → `icg-icc/` (`6f09f74`) nunca actualizó
   `ICG_RAW_PATH` en `src/constantes.py` ni ~7 referencias en
   README/CLAUDE.md/docs — correr el pipeline ICG tiraba
   `FileNotFoundError`. Corregido.
2. **La brecha de procedencia V-Party que ya se había detectado
   (151/313, ~30 filas sin fuente) no se investigó y hoy es más grande**
   en términos absolutos (208/347) — sigue como el mismo tipo de deuda
   señalada la pasada anterior, sin resolver.

Aparte de eso, el trabajo de esta sesión (panel temporal de ventanas
electorales completo — cinco fases, dos pestañas interactivas nuevas —,
convención de comentarios/docstrings "autodescriptivo por defecto"
aplicada a todo `src/`/`tests/`, y la corrección de ~15 referencias
rotas encontradas en esta misma auditoría) agrega un dominio entero y
mejora la consistencia de la documentación existente, pero **no mueve
la prioridad central** (cruce
elecciones-socioeconomía/macroeconomía/ICG) — sigue siendo el trabajo
pendiente central del proyecto. El panel temporal es insumo para ese
cruce (junta lo electoral con lo macro por fecha, ver "Ampliaciones de
alcance"), no el cruce/análisis descriptivo en sí.