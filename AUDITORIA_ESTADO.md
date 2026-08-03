# Estado de la auditoría (`NOTA_METODOLOGICA.md`, Sección 8) — a v3.1.1

Este documento existe porque la nota metodológica es un documento de trabajo
fechado sobre `v1.0.0`. Se actualiza cada vez que se cierra un punto.

Convención: 🟢 resuelto · 🟡 parcial · 🔴 abierto

## 8.1 — Correcciones y fragilidades confirmadas

| # | Punto | Estado | Evidencia |
|---|---|---|---|
| 1 | Duhalde 2011 mal codificado | 🟢 | corregido en `909760e` |
| 2 | Progresistas 2015 inconsistente | 🟢 | corregido en `909760e` |
| 3 | Secuencia reproducible borra clasificación manual | 🟢 | append-only, nunca sobrescribe (ver README/CLAUDE.md, `909760e`) |
| 4 | Circuitos no normalizados longitudinalmente | 🟢 | normalización sin ceros a la izq., `circuito_id_correspondencias.csv` |
| 5 | Mesas sin votos / cobertura incompleta | 🟡 | se documenta `mesas_sin_votos_positivos` por circuito; **falta** el % de cobertura por circuito y el análisis de sensibilidad que pide la nota. Nueva evidencia concreta (ver `data/fuentes_extra/AUDITORIA_DISCREPANCIAS.md`, hallazgo circuito 493): Gobernador/Intendente/Presidente 2023 tienen `electores=109` con `positivos=0` y `otros=0` en ese circuito — no un caso de "mesas con cero votos positivos" sino de circuito entero sin ningún voto cargado, y solo en 2023. Sigue sin diagnóstico causal. |
| 6 | JSON agregado Presidente 2019 incompleto | 🟢 | documentado en README + `coincide_con_agregado_json`/`advertencia_fuente` |
| 7 | Todo el repo usa escrutinio provisorio | 🔴 | sigue sin sustituir/contrastar con definitivos; falta registrar fecha de descarga por archivo. El caso del circuito 493/2023 (ítem 5) es compatible con esto — un circuito remoto ("límite incierto", cabecera "Isla Martín García" según `README.md`) sin telegrama cargado al momento de la consulta — pero sigue siendo una hipótesis, no un diagnóstico confirmado |
| 8 | Inconsistencias del README (3 vs 4 columnas, "años pares", instrucción truncada) | 🟢 | README reescrito en `3899006` |
| 9 | Escala ideológica duplicada (CSV sin usar) | 🔴 | sigue sin verificar en v2.0.0 — revisar si `graficos.py` ya lee `campo_ideologico.csv` o sigue con el diccionario propio |
| 10 | Series unen cargos distintos sin marcarlo | 🟡 | está documentado en README con tabla explícita; **falta** el panel/serie separada por cargo que pide la nota |
| 11 | Gráficos omiten blancos/nulos/abstención; volumen de PNG | 🟡 | resuelta la primera mitad (blancos/nulos/abstención): todo gráfico de `src/analisis/` (barras/torta, las tres series temporales, `cuadros_anualizados`, y las variantes `por_localidad`) suma ahora `blanco_nulo` y `ausentismo` (`electores` del circuito/nivel menos votos válidos) junto al desglose por `campo_ideologico`/`filiacion_politica`, vía `graficos._votos_no_ideologicos` — el % que muestra cada gráfico pasa de "% de los positivos" a "% del padrón" (ver README, sección "Gráficos"). Cambio sin commitear todavía. **Sigue abierto**: el volumen de PNG (miles de archivos por circuito) y la tabla maestra analítica que pide la nota como reemplazo no cambiaron. |
| 12 | Dependencia de notebooks y cwd; sin tests de `client.py`/`analisis/` | 🟡 | se agregaron tests de `models.py` (`909760e`); con `d006699` también se agregó cobertura para la capa de localidades (`test_localidades.py`, `test_cuadros_por_localidad.py`, `test_serie_temporal_por_localidad.py`) — pero `client.py` y el resto de `src/analisis/*` (`graficos.py`, `generar_graficos.py`, `serie_temporal.py`, `cuadros_anualizados.py`) siguen sin cobertura |
| 13 | Falta procedencia (hash, fecha, versión del libro de códigos) por archivo derivado | 🔴 | sin cambios conocidos |
| 14 | Repositorio pesado (PNG + datos) | 🟡 |  `.gitignore` solo trackea `graficos/distrito/serie_temporal/` + `graficos/socioeconomia/eph/` — 23 archivos, 3,0 MB — el resto de `graficos/` se regenera on demand y no se sube. La mitad "datos" es la real y sigue pesando: `data/distrito/**/*.csv` (46 CSV crudos por mesa — uno por año/nivel/etapa, incluye PASO) suma 223 MB en el working tree (86 MB empaquetado en `.git`, medido con `git count-objects -v`) y es la gran mayoría del repo (233 MB trackeados en total). Pero no es bloat: son la caché de la API que el propio README pide mantener para no depender de red en cada reproducción del pipeline (notebooks 01-04 ya "ejecutados" contra `resultados.mininterior.gob.ar`, cuyo re-fetch completo no tendría sentido hacer de forma rutinaria). **Conclusión**: no hay bloat desperdiciado para limpiar; si se quisiera reducir en serio, la única palanca real es dejar de trackear `data/distrito/**/*.csv` y aceptar que reproducir el pipeline exige red. |

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
como decisión de codificación aparte. Tampoco están las otras dimensiones
del libro de códigos multidimensional de la Sección 5.3 (oferta electoral,
oficialismo, dimensiones programáticas separadas) — solo familia política.

## Plan de trabajo

| Ítem | Estado |
|---|---|
| Congelar v1.0.0 como punto de partida | 🟢 (tag existe) |
| Corregir el repositorio (8.1 prioridad inmediata) | 🟡 ver tabla arriba |
| Construir el libro de códigos | 🟡 `filiacion_politica` separada de `campo_ideologico` (ver 8.2); posición ideológica ya existía; grado de incertidumbre y justificación existen por agrupación en `tabla_referencia_filiacion_politica.csv` (`confianza_clasificacion`/`nota_clasificacion`, no fusionados al CSV principal); **faltan** oferta electoral, oficialismo, y las dimensiones programáticas separadas de la Sección 5.3 |
| Ampliar etapas y fuentes (PASO/balotaje) | 🟢 agregado en `909760e` |
| Tabla maestra circuito × elección × cargo × etapa | 🔴 |
| Armonizar territorio y Censo | 🟡 correspondencia espacial circuito↔radio lista (v2.0.0); **variables temáticas del Censo por radio, no extraídas todavía** (REDATAM manual, ver `EXTRACCION_REDATAM.md`) |
| Correspondencia circuito↔localidad (barrio, no censal) | 🟡 crosswalk armado (`data/fuentes_extra/circuito_localidad.csv`): 16/68 circuitos con fuente oficial (Resolución 1990/2007, todos `oficial_confirmada` — 503/503A se reclasificaron a MELCHOR_ROMERO por decisión explícita, ver abajo), 65/68 con fuente periodística (El Día). Los 16 oficiales auditados contra el detalle completo del anexo, no solo la descripción general (`AUDITORIA_DISCREPANCIAS.md`) — de 14 comparables, 8 resultan `discrepancia_real` contra la etiqueta de El Día (más de lo que sugería `LOCALIDADES_README.md`), aunque eso ya no determina el agrupamiento de 503/503A. Agregación de resultados (`electoral/localidades.py`, `analisis/cuadros_por_localidad.py`, 22 cuadros 2011-2025, ~99% de cobertura de votos combinando ambos niveles, `SIN_DETERMINAR` siempre visible, hoy solo el circuito 521) y series temporales (`analisis/serie_temporal_por_localidad.py`, 132 imágenes) ya construidas. Es un tipo de correspondencia territorial distinto y paralelo al de la fila de arriba (esta es para nombres de barrio legibles, no para unir Censo) — no lo reemplaza ni depende de él. **Falta**: subir de nivel las familias 504/505/508/509 (hoy solo periodístico), y diagnóstico causal del hueco de datos de circuito 493/2023 (ver ítem 8.1.5; ya no se ve a simple vista en la fila MELCHOR_ROMERO, diluido por los votos reales de 503/503A) |
| Separar exploración y contraste | 🔴 no hay todavía cruce elecciones↔socioeconomía |

## Sección 10

| Pieza pedida | Estado a v3.1.1 |
|---|---|
| Hoja de pregunta/objetivos/hipótesis | 🟢 esta misma nota, incorporada |
| Libro de códigos político | 🟡 ver "Construir el libro de códigos" arriba y 8.2 |
| Auditoría de mesas, circuitos y cobertura | 🟡 parcial (ver 8.1.5) |
| Tabla maestra | 🔴 |
| Primer análisis descriptivo (tamaño de bloques / composición / participación / territorio) | 🔴 — v2.0.0 construyó la capa socioeconómica pero **todavía no la cruzó** con resultados electorales |

## Lectura del conjunto

De los 14 puntos técnicos de 8.1, **6 están resueltos, 5 parciales y 3
abiertos**. De las 5 piezas del "producto mínimo" que pedía la Sección 10,
la primera (esta nota) está resuelta y el libro de códigos político pasó a
parcial (`filiacion_politica`, ver 8.2) — tabla maestra y cruce
elecciones-socioeconomía siguen siendo el trabajo pendiente central del
proyecto. La Sección 8.2 (codificación política) ya tiene un primer avance
(familia política separada de posición ideológica para los ocho casos
señalados); la Sección 6 (protocolo de inferencia) sigue sin atacarse