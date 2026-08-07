# Sistematización de variables macroeconómicas nacionales (2011-2025)

Documento de referencia de la capa `src/macroeconomia/`: qué se relevó, con
qué cobertura real, qué salvedades aparecieron al implementarlo, y qué queda
fuera de alcance a propósito. El diseño completo (fuentes evaluadas,
decisiones, catálogo variable por variable) está en `docs/plan_macroeconomia.md`.

## 1. Qué se relevó

**Fuente única activa: `datos.gob.ar`** (API Series de Tiempo, sin
autenticación). `estadisticasbcra.com` es auditor externo declarado en el
catálogo (columna `auditable_estadisticasbcra`), no dependencia del
pipeline — la auditoría efectiva contra esa fuente se corrió y está
documentada en la sección 3.1.

22 conceptos, todos de grano **nacional** (sin apertura regional), en
`data/macroeconomia/catalogo_series.csv`, volcados a
`data/macroeconomia/series_macro_2011_2025.csv`: una fila por mes
(2011-01 a 2025-12, 180 filas), una columna por concepto, más
`observaciones`.

**Rediseño (2026-08): sin forward-fill.** La primera versión de este
pipeline repetía el último valor publicado en los meses siguientes para
series trimestrales/anuales. Se rediseñó para que **ninguna celda repita
un valor anterior** — solo tiene dato el mes de origen exacto de cada
publicación; el resto queda vacío (`""`), con la razón en `observaciones`.
Ver `docs/plan_macroeconomia.md` ("Rediseño posterior") para el detalle de la
decisión. Esto bajó el total de celdas con dato real (ya no se cuentan las
que antes eran "repetidas") pero elimina el riesgo de que alguien lea una
celda repetida como si fuera un dato nuevo de ese mes.

## 2. Cobertura real por concepto

| Concepto | Con dato real | Vacíos | Primer dato – último dato |
|---|---:|---:|---|
| tipo_cambio_oficial | 180 | 0 | 2011-01 a 2025-12 |
| tipo_cambio_mayorista | 180 | 0 | 2011-01 a 2025-12 |
| reservas_internacionales | 180 | 0 | 2011-01 a 2025-12 |
| base_monetaria | 179 | 1 | 2011-01 a 2025-11 |
| tasa_badlar | 180 | 0 | 2011-01 a 2025-12 |
| tasa_politica_monetaria | 114 | 66 | 2016-01 a 2025-06 |
| ipc_nacional | 109 | 71 | 2016-12 a 2025-12 |
| canasta_basica_alimentaria | 117 | 63 | 2016-04 a 2025-12 |
| canasta_basica_total | 117 | 63 | 2016-04 a 2025-12 |
| emae | 180 | 0 | 2011-01 a 2025-12 |
| pbi | 56 | 124 | 2011-01 a 2024-10 |
| tasa_desocupacion | 58 | 122 | 2011-01 a 2025-10 |
| tasa_empleo | 58 | 122 | 2011-01 a 2025-10 |
| tasa_actividad | 58 | 122 | 2011-01 a 2025-10 |
| ripte | 180 | 0 | 2011-01 a 2025-12 |
| indice_salarios_total | 111 | 69 | 2016-10 a 2025-12 |
| indice_salarios_privado_registrado | 123 | 57 | 2015-10 a 2025-12 |
| indice_salarios_publico | 123 | 57 | 2015-10 a 2025-12 |
| gasto_deuda_publica_nivel | 13 | 167 | 2011-01 a 2023-01 |
| gasto_deuda_publica_pib | 13 | 167 | 2011-01 a 2023-01 |
| comercio_exterior_cobros | 180 | 0 | 2011-01 a 2025-12 |
| comercio_exterior_pagos | 180 | 0 | 2011-01 a 2025-12 |

Total: **2689/3960 celdas con dato real (67,9%)**, 1271 vacías (32,1%).
"Primer dato – último dato" es el rango entre la primera y la última celda
con valor real de esa columna — **no implica cobertura continua dentro de
ese rango**: para las series trimestrales/anuales (`pbi`,
`tasa_desocupacion`/`_empleo`/`_actividad`, `gasto_deuda_publica_*`), la
mayoría de los meses dentro de ese rango están vacíos por diseño (solo el
mes de origen de cada publicación tiene valor — ver `observaciones` fila
por fila). Para las demás series, "vacío" es siempre un mes anterior al
primer dato publicado (nunca un hueco en medio de la cobertura real) — es
lo esperado dado que varias series (IPC nacional, canasta básica, índice de
salarios, tasa de política monetaria) recién existen a nivel nacional desde
2015/2016, no antes (ver `docs/plan_macroeconomia.md` §3 para el porqué de cada
corte).

**Caso a mirar con atención al usar el CSV**: `gasto_deuda_publica_nivel`/
`_pib` tienen solo 13 valores reales (2011-2023, publicación anual) — la
fuente todavía no publicó 2024/2025 al momento de esta corrida, así que
esos dos años quedan vacíos para estas dos columnas (antes del rediseño,
arrastraban el valor de 2023 sin que se pudiera distinguir eso de un
"repetido normal" de mitad de año). `pbi` real termina en 2024-10 (Q4 2024)
por el mismo motivo de rezago de publicación de INDEC — todo 2025 queda
vacío para esa columna.

## 3. Auditoría externa contra `estadisticasbcra.com`

Corrida el 2026-08-07 con `src/macroeconomia/auditoria_estadisticasbcra.py`
(token del usuario, no guardado en el repo — ver docstring del script).
Metodología: para cada concepto marcado `auditable_estadisticasbcra` en el
catálogo, se compara nuestro dato crudo de datos.gob.ar contra el de
estadisticasbcra.com **en el año-mes más reciente que ambas fuentes tengan
en común** (no en el mes más reciente de nuestra propia serie — ver más
abajo, la fuente auditora está atrasada).

| Concepto | Año-mes comparado | Nuestro valor | estadisticasbcra | Diferencia | Resultado |
|---|---|---:|---:|---:|---|
| tipo_cambio_oficial | 2024-04 | 876,50 (30/04) | 864,75 (09/04) | +1,36% | próximo — ver nota 1 |
| tipo_cambio_mayorista | 2024-04 | 876,75 (30/04) | 864,75 (09/04) | +1,39% | próximo — ver nota 1 |
| reservas_internacionales | 2024-04 | 29.203,40 (01/04) | 28.765,00 (05/04) | +1,52% | próximo — ver nota 1 |
| base_monetaria | 2024-04 | 13.672.428 (01/04) | 11.744.788 (05/04) | +16,41% | **difiere — ver nota 2** |
| tasa_badlar | 2024-04 | 62,67 (01/04) | 71,50 (08/04) | -12,35% | **difiere — ver nota 2** |
| tasa_politica_monetaria | 2024-03 | 87,37 (01/03) | 80,00 (15/03, tasa LELIQ) | +9,21% | próximo — ver nota 3 |
| ipc_nacional (var. % m/m) | 2024-02 | 13,24% | 13,20% | +0,31% | **coincide** |

**Nota 1 (cambiario, reservas):** diferencias chicas (1,4-1,5%) explicadas
por que las dos fuentes no comparten fecha exacta dentro del mes (hasta 21
días de distancia — ver columna "Año-mes comparado") y ambas variables se
mueven día a día; no hay indicio de error de dato, solo falta de una fecha
en común más cercana.

**Nota 2 (base_monetaria, tasa_badlar) — diferencia mayor a lo esperable
solo por la distancia de fechas (16,4% y 12,3% con 4-7 días de diferencia):**
posible diferencia de definición entre fuentes (ej. "base monetaria
amplia" vs. una medida más restringida; BADLAR "total" vs. solo "bancos
privados") — **no se ajustó ningún dato para forzar coincidencia** (regla
del repo: nunca se toca un dato para que un número dé mejor). Queda como
punto a investigar si se necesita una lectura fina de estas dos series;
mientras tanto, el dato de `datos.gob.ar` (fuente única activa del
pipeline) sigue siendo el que se usa, sin cambios.

**Nota 3 (tasa_politica_monetaria vs. `tasa_leliq`):** ya documentado en
`catalogo_series.csv` como aproximación ("aprox.") — la tasa de referencia
cambiaba con frecuencia en ese tramo (dic-2023/2024), así que 14 días de
distancia entre fechas alcanzan para explicar +9,2 puntos porcentuales sin
que sea un error.

**Corrección de catálogo encontrada durante la auditoría:**
`tipo_cambio_oficial` apuntaba a `usd` en estadisticasbcra.com, que
resultó ser el **dólar informal/blue**, no el oficial — la primera corrida
de la auditoría (antes de corregir esto) dio -26,9% de diferencia
(953 vs. 1305 en 2024-08), consistente con la brecha cambiaria real de ese
momento, no con un error de dato. Se corrigió `auditable_estadisticasbcra`
a `usd_of` en `catalogo_series.csv` (ver nota en esa fila) — la tabla de
arriba ya refleja el mapeo corregido.

**Hallazgo sobre `estadisticasbcra.com` como fuente auditora:** su versión
gratuita/con token de usuario está **desactualizada de forma dispareja
entre endpoints** — el último dato disponible por endpoint al momento de
esta auditoría fue `usd`: 2024-08-30, `usd_of`/`reservas`/`base`/
`tasa_badlar`: abril de 2024, `tasa_leliq`: 2024-03-15,
`inflacion_mensual_oficial`: 2024-02-29 — es decir, entre año y medio y dos
años de atraso respecto a hoy (2026-08-07), y varía según la serie, no es
un corte parejo. Esto confirma el rol que ya le daba el plan (auditor
puntual, no fuente ni referencia de actualidad) y limita cuánto se puede
auditar con esta fuente: solo sirve para cotejar un tramo histórico ya
cerrado (~2024 o antes), nunca los datos más recientes del CSV.

**`canasta_basica_alimentaria`/`_total`, `emae`, `pbi`, las tres tasas EPH,
`ripte`, los índices de salarios, `gasto_deuda_publica_*` y
`comercio_exterior_*` no tienen equivalente en estadisticasbcra.com**
(`auditable_estadisticasbcra=no` en el catálogo) — sin cambios respecto al
diseño original, ver `docs/plan_macroeconomia.md` §1.

## 4. Salvedades encontradas al revisar `pbi` y `tasa_desocupacion` en detalle

- **`pbi` real termina en 2024-10 (Q4 2024) exactamente** — los 56 valores
  reales cubren 2011Q1-2024Q4 sin ningún hueco en el medio; todo 2025 queda
  vacío porque INDEC todavía no publicó esos trimestres al momento de esta
  corrida. Es rezago de publicación, no un error de id ni un hueco real
  dentro del período cubierto.
- **`tasa_desocupacion`/`tasa_empleo`/`tasa_actividad` tienen un hueco real
  de 2 trimestres (2015-10 y 2016-01)**, no 3. Esto **no coincide** con el
  hueco de la EPH que ya documenta este mismo repo para la microdata de
  Gran La Plata (`src/socioeconomia/eph_client.py`:
  `TRIMESTRES_NO_PUBLICADOS`, 2015T3+2015T4+2016T1) — el agregado nacional
  publicado por INDEC sí trae un valor para 2015T3, aunque la microdata de
  ese trimestre tenga la reserva metodológica. Al comparar esta serie
  nacional contra la de Gran La Plata hay que tener presente que el borde
  del hueco no es el mismo trimestre en las dos fuentes.
- **Inconsistencia de unidad entre tasas, confirmada en la metadata de la
  propia API** (no es un problema de esta implementación, es así en el
  origen): `tasa_desocupacion`/`tasa_empleo`/`tasa_actividad` guardan una
  **fracción 0-1** (`0.074` = 7,4%) pese a que su descripción dice
  "Porcentaje", igual que las demás. En cambio `tasa_badlar`
  (`"Porcentaje (0-100)"` explícito en su metadata),
  `tasa_politica_monetaria` y `gasto_deuda_publica_pib` ya vienen
  multiplicadas por 100 (`11.09` = 11,09%; `1.9` = 1,9% del PBI). No se
  puede asumir "porcentaje" como una convención uniforme dentro de este
  mismo CSV.

## 5. Salvedad importante encontrada al implementar (no en el plan original)

El id elegido en una primera pasada para `comercio_exterior_cobros`/`_pagos`
(dataset 184, "Cobros y pagos por bienes **sectorial**") resultó ser el
sector "Comercio" puntual, uno entre ~15 sectores de esa apertura (Agro,
Petróleo, Industria Automotriz, etc.) — no el total del país. Se detectó
porque los valores mensuales ($100-500 millones) eran demasiado bajos para
el comercio exterior argentino completo. Se corrigió usando el dataset 183
("... por modalidad de pago"), que sí trae series de total agregado
(`cobros_exportaciones_bienes` / `pagos_importaciones_bienes`) — valores
ahora en el orden de $5.000-6.000 millones/mes, consistente con lo
esperado. Corregido en `docs/plan_macroeconomia.md` §3.7 y en
`catalogo_series.csv` antes de la corrida final; se documenta acá para que
quede visible que el error existió y cómo se detectó (comparación de orden
de magnitud contra un valor de referencia conocido, no solo lectura del
nombre de la serie).

## 6. Qué falta / fuera de alcance a propósito

Heredado de `docs/plan_macroeconomia.md` §7, con la auditoría ya corrida (§3):

- **Riesgo país** — no está en ninguna de las tres fuentes evaluadas.
- **Resultado fiscal real** (primario/financiero) — solo había mediana de
  expectativas REM, se prefirió omitir antes que incluir un proxy bajo el
  nombre de un dato real.
- **Pobreza e indigencia moderna (2016+)** — INDEC la sigue publicando, pero
  no se ubicó el id exacto del total de 31 aglomerados en `datos.gob.ar`
  (solo apareció una apertura parcial, "aglomerados del interior país").
- **Apertura regional o provincial** — alcance de este dominio es nacional
  exclusivamente, por decisión explícita.
- **Cruce con ingresos EPH de Gran La Plata** u otras capas del repo — esta
  capa es de adquisición y documentación únicamente, cualquier cruce queda
  para un paso posterior explícito.
- **Diferencias sin resolver de `base_monetaria` y `tasa_badlar` contra
  estadisticasbcra.com** (+16,4% y -12,3%, ver §3 nota 2) — posible
  diferencia de definición entre fuentes, no investigada en profundidad
  todavía.

## 7. Cómo regenerar

```bash
PYTHONPATH=src python -m macroeconomia.series                    # usa caché si existe
PYTHONPATH=src python -m macroeconomia.series --force-refresh    # vuelve a pedir todo a la API
```

Corre en segundos con caché (`data/macroeconomia/_cache/datos_gob/`, un
JSON crudo por concepto, no versionado); sin caché hace 22 pedidos a
`apis.datos.gob.ar` (algunas series diarias largas pagina en más de un
pedido internamente, ver `macroeconomia/datos_gob_client.py`).
`data/macroeconomia/series_macro_2011_2025.csv` tampoco está versionado
(se regenera en segundos, mismo criterio que `data/totales/`) —
`catalogo_series.csv` sí, es la curaduría manual.

Para repetir la auditoría externa de la sección 3 (por ejemplo, si se
agregan conceptos auditables nuevos al catálogo):

```bash
ESTADISTICASBCRA_TOKEN=<tu_token> PYTHONPATH=src python -m macroeconomia.auditoria_estadisticasbcra
```

Requiere un token propio de `estadisticasbcra.com/api/registracion`
(gratuito, 100 consultas/día) — nunca se guarda en el repo. No es parte de
`macroeconomia.series` ni corre en cada regeneración del CSV, según lo
decidido en `docs/plan_macroeconomia.md` §5 punto 5.
