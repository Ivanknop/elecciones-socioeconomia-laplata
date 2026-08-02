# Estado de la auditoría (`NOTA_METODOLOGICA.md`, Sección 8) — a v3.0.1

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
| 11 | Gráficos omiten blancos/nulos/abstención; volumen de PNG | 🔴 | sin cambios conocidos |
| 12 | Dependencia de notebooks y cwd; sin tests de `client.py`/`analisis/` | 🟡 | se agregaron tests de `models.py` (`909760e`); con `d006699` también se agregó cobertura para la capa de localidades (`test_localidades.py`, `test_cuadros_por_localidad.py`, `test_serie_temporal_por_localidad.py`) — pero `client.py` y el resto de `src/analisis/*` (`graficos.py`, `generar_graficos.py`, `serie_temporal.py`, `cuadros_anualizados.py`) siguen sin cobertura |
| 13 | Falta procedencia (hash, fecha, versión del libro de códigos) por archivo derivado | 🔴 | sin cambios conocidos |
| 14 | Repositorio pesado (PNG + datos) | 🔴 | sin cambios conocidos; v2.0.0 además suma varios GeoJSON grandes |

## 8.2 — Codificaciones políticas a revisar

🔴 Sin cambios verificados. Los ocho casos señalados (peronismo, familia
progresista, massismo, Patria Grande, Frente NOS, Frente Patriota Federal,
Frente Social de la PBA, Hacemos por Nuestro País) requieren que primero
exista el libro de códigos multidimensional de la Sección 5.2/5.3 — sigue
pendiente.

## Plan de trabajo

| Ítem | Estado |
|---|---|
| Congelar v1.0.0 como punto de partida | 🟢 (tag existe) |
| Corregir el repositorio (8.1 prioridad inmediata) | 🟡 ver tabla arriba |
| Construir el libro de códigos | 🔴 |
| Ampliar etapas y fuentes (PASO/balotaje) | 🟢 agregado en `909760e` |
| Tabla maestra circuito × elección × cargo × etapa | 🔴 |
| Armonizar territorio y Censo | 🟡 correspondencia espacial circuito↔radio lista (v2.0.0); **variables temáticas del Censo por radio, no extraídas todavía** (REDATAM manual, ver `EXTRACCION_REDATAM.md`) |
| Correspondencia circuito↔localidad (barrio, no censal) | 🟡 crosswalk armado (`data/fuentes_extra/circuito_localidad.csv`): 16/68 circuitos con fuente oficial (Resolución 1990/2007, todos `oficial_confirmada` — 503/503A se reclasificaron a MELCHOR_ROMERO por decisión explícita, ver abajo), 65/68 con fuente periodística (El Día). Los 16 oficiales auditados contra el detalle completo del anexo, no solo la descripción general (`AUDITORIA_DISCREPANCIAS.md`) — de 14 comparables, 8 resultan `discrepancia_real` contra la etiqueta de El Día (más de lo que sugería `LOCALIDADES_README.md`), aunque eso ya no determina el agrupamiento de 503/503A. Agregación de resultados (`electoral/localidades.py`, `analisis/cuadros_por_localidad.py`, 22 cuadros 2011-2025, ~99% de cobertura de votos combinando ambos niveles, `SIN_DETERMINAR` siempre visible, hoy solo el circuito 521) y series temporales (`analisis/serie_temporal_por_localidad.py`, 132 imágenes) ya construidas. Es un tipo de correspondencia territorial distinto y paralelo al de la fila de arriba (esta es para nombres de barrio legibles, no para unir Censo) — no lo reemplaza ni depende de él. **Falta**: subir de nivel las familias 504/505/508/509 (hoy solo periodístico), y diagnóstico causal del hueco de datos de circuito 493/2023 (ver ítem 8.1.5; ya no se ve a simple vista en la fila MELCHOR_ROMERO, diluido por los votos reales de 503/503A) |
| Separar exploración y contraste | 🔴 no hay todavía cruce elecciones↔socioeconomía |

## Sección 10

| Pieza pedida | Estado a v2.0.1 |
|---|---|
| Hoja de pregunta/objetivos/hipótesis | 🟢 esta misma nota, incorporada |
| Libro de códigos político | 🔴 |
| Auditoría de mesas, circuitos y cobertura | 🟡 parcial (ver 8.1.5) |
| Tabla maestra | 🔴 |
| Primer análisis descriptivo (tamaño de bloques / composición / participación / territorio) | 🔴 — v2.0.0 construyó la capa socioeconómica pero **todavía no la cruzó** con resultados electorales |

## Lectura del conjunto

De los 14 puntos técnicos de 8.1, **6 están resueltos, 3 parciales y 5
abiertos**. De las 5 piezas del "producto mínimo" que pedía la Sección 10,
sólo la primera (esta nota) está resuelta con v2.0.1 — el resto (libro de
códigos, tabla maestra, cruce elecciones-socioeconomía) sigue siendo el
trabajo pendiente central del proyecto. v2.0.0 avanzó la infraestructura de
datos (Sección 5.4) pero no atacó todavía la Sección 8.2 (codificación
política) ni la Sección 6 (protocolo de inferencia)