# Estado de la auditoría (`NOTA_METODOLOGICA.md`, Sección 8) — a v2.0.1

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
| 5 | Mesas sin votos / cobertura incompleta | 🟡 | se documenta `mesas_sin_votos_positivos` por circuito; **falta** el % de cobertura por circuito y el análisis de sensibilidad que pide la nota |
| 6 | JSON agregado Presidente 2019 incompleto | 🟢 | documentado en README + `coincide_con_agregado_json`/`advertencia_fuente` |
| 7 | Todo el repo usa escrutinio provisorio | 🔴 | sigue sin sustituir/contrastar con definitivos; falta registrar fecha de descarga por archivo |
| 8 | Inconsistencias del README (3 vs 4 columnas, "años pares", instrucción truncada) | 🟢 | README reescrito en `3899006` |
| 9 | Escala ideológica duplicada (CSV sin usar) | 🔴 | sigue sin verificar en v2.0.0 — revisar si `graficos.py` ya lee `campo_ideologico.csv` o sigue con el diccionario propio |
| 10 | Series unen cargos distintos sin marcarlo | 🟡 | está documentado en README con tabla explícita; **falta** el panel/serie separada por cargo que pide la nota |
| 11 | Gráficos omiten blancos/nulos/abstención; volumen de PNG | 🔴 | sin cambios conocidos |
| 12 | Dependencia de notebooks y cwd; sin tests de `client.py`/`analisis/` | 🟡 | se agregaron tests de `models.py` (`909760e`); `client.py` y `src/analisis/*` siguen sin cobertura (confirmado en `CLAUDE.md` v2.0.0) |
| 13 | Falta procedencia (hash, fecha, versión del libro de códigos) por archivo derivado | 🔴 | sin cambios conocidos |
| 14 | Repositorio pesado (PNG + datos) | 🔴 | sin cambios conocidos; v2.0.0 además suma varios GeoJSON grandes |

## 8.2 — Codificaciones políticas a revisar

🔴 Sin cambios verificados. Los ocho casos señalados (peronismo, familia
progresista, massismo, Patria Grande, Frente NOS, Frente Patriota Federal,
Frente Social de la PBA, Hacemos por Nuestro País) requieren que primero
exista el libro de códigos multidimensional de la Sección 5.2/5.3 — sigue
pendiente.

## Sección 7 — Plan de trabajo

| Ítem | Estado |
|---|---|
| Congelar v1.0.0 como punto de partida | 🟢 (tag existe) |
| Corregir el repositorio (8.1 prioridad inmediata) | 🟡 ver tabla arriba |
| Construir el libro de códigos | 🔴 |
| Ampliar etapas y fuentes (PASO/balotaje) | 🟢 agregado en `909760e` |
| Tabla maestra circuito × elección × cargo × etapa | 🔴 |
| Armonizar territorio y Censo | 🟡 correspondencia espacial circuito↔radio lista (v2.0.0); **variables temáticas del Censo por radio, no extraídas todavía** (REDATAM manual, ver `EXTRACCION_REDATAM.md`) |
| Separar exploración y contraste | 🔴 no hay todavía cruce elecciones↔socioeconomía |

## Sección 10 — Producto mínimo de la próxima versión

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