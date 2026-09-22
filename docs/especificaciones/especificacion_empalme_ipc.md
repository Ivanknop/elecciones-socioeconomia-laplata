# Especificación: empalme de IPC sin rebasar (D33)

**Estado: implementado (pasos 1-4 de 5).** Especificación de diagnóstico y fix, encontrada
auditando el diseño de `panel_k` (D32, `docs/especificaciones/especificacion_panel_temporal.md`
no lo cubre porque es posterior a ese documento). Fuente de fix: FACPCE, Res. JG 539/18 (§4).
Falta solo el paso 5 (re-correr `01.1`/`01.3` para reevaluar los dos coeficientes sospechosos de
§3.3 con los datos ya corregidos) -- lo ejecuta el usuario directamente, no bloquea nada más.

**Bloqueaba** el barrido `05_5_barrido_k.ipynb` de D32 (panel_k) -- **ya no**, los pasos 1-4
están resueltos. Formalmente el barrido queda para después del paso 5 (ver orden abajo), pero el
bloqueo por datos corruptos en sí ya no existe.

**Orden de implementación acordado -- estado real:**
1. ✅ Auditoría programática primero (§6, §6.1) -- corrida antes de tocar
   `cargar_series_economicas.py`, confirmó el alcance real de la contaminación.
2. ✅ Reemplazo de la serie `ipc` por FACPCE (§4.3) + documentación en `registro_variables.csv`
   y corrección a D6 (§4.3, punto 5) -- ambas hechas.
3. ✅ Recalcular `salario_real` de punta a punta con el nuevo `ipc` (§4.3, punto 6) -- ocurre en
   la misma corrida que el paso 2 (`construir_tabla_mensual` deflacta todo lo `nominal=true` de
   una sola vez), confirmado.
4. ✅ Regenerar los 5 archivos derivados (§8) -- hecho; auditoría programática re-corrida (§6.2),
   confirma que las filas de §3.2 ya no aparecen en ninguno de los tres archivos auditados.
5. ⏳ Re-correr `01.1_lasso_voto_valido.ipynb`/`01.3_lasso_voto_exit.ipynb` (§9) -- pendiente, lo
   corre el usuario. Recién ahí, formalmente, habilitar el barrido `05_5` de `panel_k` (D32).

---

## 1. Hallazgo

`src/ml_models/cargar_series_economicas.py` (`_cargar_datos_gob`, líneas 120-131) encadena
series de datos.gob.ar por variable. La lógica es:

```python
por_fecha: dict[date, float] = {}
for serie_id in ids:
    crudo = client.get_serie(serie_id, start_date=start_date, force_refresh=True)
    for fecha, valor in _parsear_puntos(crudo["data"]):
        por_fecha[fecha] = valor
return sorted(por_fecha.items())
```

Para `ipc` (`_DATOS_GOB_IDS["ipc"]`), esto encadena **3 vintages**:

| Vintage | ID | Cobertura declarada | Base |
|---|---|---|---|
| 1 | `178.1_NL_GENERAL_0_0_13` | hasta 2008-04 | abr-2008=100 |
| 2 | `97.2_ING_2008_M_17` | 2008-04 a 2013-12 | abr-2008=100 |
| 3 | `148.3_INIVELNAL_DICI_M_26` | desde 2016-12 | **dic-2016=100** |

`por_fecha[fecha] = valor` no aplica ningún factor de reescala entre vintages -- simplemente
sobrescribe por fecha, "el último de la lista gana si hay solapamiento". **No hay solapamiento
entre el vintage 2 y el 3**: el vintage 2 termina 2013-12, el vintage 3 empieza 2016-12, con un
hueco real de 35 meses (2014-01 a 2016-11, documentado ya en `registro_variables.csv`'s
`nota_metodologica` de `ipc` como "hueco real... no es una falla de búsqueda"). Lo que esa nota
no documenta es que, además del hueco, **las dos series que rodean el hueco no están en la
misma base** -- y la función que las junta no lo corrige.

Confirmado en `series_economicas_mensuales.csv`:

```
2013-11-01  164.5100
2013-12-01  166.8400   <- último dato real, vintage 2 (base abr-2008=100)
   ... 35 meses NaN ...
2016-12-01  100.0000   <- primer dato real, vintage 3 (base dic-2016=100, literalmente arranca en 100)
2017-01-01  101.5859
```

El borde 1→2 (2008-04), en cambio, es continuo (99.18 → 100.00 → 100.56) -- confirma que
comparten base, como dice `registro_variables.csv`. **El problema es exclusivamente el borde 2→3.**

## 2. No es un artefacto de carga -- es la intervención INDEC 2007-2015

El corte coincide con el período de intervención del IPC-INDEC que el repo ya trata como un
evento aparte: `D6`/corrección a D6 (`docs/decisiones_metodologicas.md`) documenta el flag
histórico `periodo_intervenido` (retirado del panel por falta de lectores, pero la decisión
sustantiva -- incluir el período 2007-2015 sin excluirlo a priori, con reserva documentada --
sigue vigente). El INDEC oficial no fue considerado confiable en esos años; el organismo relanzó
metodología con una base nueva (dic-2016=100) recién en dic-2016. El "vintage 3" de este
registro es exactamente esa serie nueva. No es casualidad que las dos series no se toquen: es
el mismo evento de intervención, visto del lado de la reconstrucción de series en vez del panel
electoral.

## 3. Alcance de la contaminación -- confirmado con datos reales, no solo teórico

### 3.1 No es puntual -- es un quiebre de escala persistente desde dic-2016

```
municipal_2011_2013: salario_real_nivel_vc=4560.66  ipc_nivel_vc=147.80
municipal_2013_2015: salario_real_nivel_vc=5267.12   ipc_nivel_vc=164.78   <- último punto, base vieja
municipal_2015_2017: salario_real_nivel_vc=21062.98  ipc_nivel_vc=109.90   <- primer punto, base nueva (¡MENOR!)
municipal_2017_2019: salario_real_nivel_vc=19654.62  ipc_nivel_vc=176.82
municipal_2019_2021: salario_real_nivel_vc=17876.37  ipc_nivel_vc=388.05
municipal_2021_2023: salario_real_nivel_vc=17371.72  ipc_nivel_vc=1193.53
municipal_2023_2025: salario_real_nivel_vc=15350.78  ipc_nivel_vc=6778.58
```

`ipc_nivel_vc` cae entre dos transiciones consecutivas -- imposible con inflación positiva en
el medio. No hace falta que una ventana *cruce* el hueco: **toda transición que cae enteramente
después de dic-2016 ya está en la base nueva**, y queda ahí -- el salto es un evento único en el
borde, pero como `salario_real = RIPTE_nominal / ipc * 100` sigue dividiendo por el `ipc` en
base nueva indefinidamente hacia adelante, el nivel deflactado queda permanentemente
~1.5-4x más alto que si la base no hubiera cambiado. No se "corrige solo" con el tiempo.

### 3.2 Ya contamina archivos en uso, no solo `panel_k` (trabajo nuevo)

| Archivo | Columna(s) | Transición(es) | Valor observado |
|---|---|---|---|
| `panel_ventanas.csv` | `ipc_acum_vl`, `ipc_pendiente_vl`, `ipc_volatilidad_vl` | `*_2015_2017` (municipal/provincial/nacional, idéntico -- misma serie nacional) | `acum=-26.78%` (imposible, implica deflación de ese orden) |
| `panel_ventanas.csv` | `salario_real_nivel_vc`, `salario_real_delta_nivel` | `*_2015_2017` en adelante | ver §3.1; `salario_real_delta_nivel` de esa fila puntual = ~15796 (salto espurio) |
| `panel_ventanas_bieleccion.csv` | `ipc_nivel_trim`, `ipc_volatilidad_trim` | `municipal_2013_2017` | `nivel_trim=-4.04%` (imposible), `volatilidad_trim=19.69` (inflada por el mismo outlier) |
| `panel_trimestral_<nivel>.csv` | `ipc` (fila `orden` con `fecha_inicio=2016-11-01`) | `*_2015_2017`, los 3 niveles | `ipc=-39.11%` (variación contra el ancla pre-hueco, cruza el corte de base) |

`ipc_acum_vc`/`ipc_pendiente_vc`/`ipc_volatilidad_vc` (ventana corta, ~24 meses) parecen haber
escapado en las 36 transiciones de `panel_ventanas.csv` -- ninguna ventana corta es lo bastante
larga para tener dato real de los dos lados del hueco de 35 meses. **Confirmado
programáticamente en §6, no solo por inspección** -- ver resultado real ahí.

### 3.3 Resultados ya publicados que usan columnas afectadas

| Notebook | Coeficiente | Contexto |
|---|---|---|
| `notebooks/ml/ventana_t-1/01.1_lasso_voto_valido.ipynb` | `salario_real_delta_nivel` (3.15), `alpha_min`, municipal | Construido sobre el salto espurio de `*_2015_2017` (§3.1). |
| `notebooks/ml/ventana_t-1/01.3_lasso_voto_exit.ipynb` | `salario_real_delta_pendiente` (0.50 en tabla principal, 0.36 en chequeo de estabilidad), nacional | Mismo mecanismo. |
| `03_desplazamiento_ideologico.ipynb`, `04_lasso_eph_local.ipynb` | Ninguno (confirmado por grep de sus outputs) | `04` no incluye `ipc`/`salario_real` como candidatas; `03` no seleccionó ninguna en su tabla de coeficientes. |

Adicional: `PRIORIDAD_TEORICA` (usada en el colapso de colinealidad de `01.1`-`01.3`, `04`, y la
copia local de `03`) pone `"ipc"` primero en la lista de prioridad teórica -- si una columna de
`ipc` queda en un cluster correlacionado con otra variable sana, el colapso prefiere quedarse
con la de `ipc`. No se auditó cluster por cluster de cada notebook -- eso es parte de §6.

## 4. Opción C resuelta: FACPCE, Res. JG 539/18 -- serie de empalme oficial, ya cargada en el repo

`data/macroeconomia/indice-FACPCE.xlsx` -- "IPC Nacional Empalme IPIM", el índice que usan los
contadores argentinos para el ajuste por inflación de estados contables (RT6), publicado
mensualmente por FACPCE, empalmando IPC con IPIM durante la intervención INDEC **exactamente
para este problema**. Verificado de forma independiente (no solo confiando en la descripción):

- Una hoja (`ipc empalme ipim`), 407 filas, 1993-01 a 2026-09. `2026-09` es la única fila sin
  valor numérico real: `"*"`, con nota al pie del archivo explicando que INDEC publica ese dato
  el 14/10/2026 -- se lee como faltante real, no como error de parseo. Confirmado: 2 filas
  finales adicionales son metadata/nota, no datos (hay que recortarlas al parsear).
- **`2013-12 = 49.43`, `2016-12 = 100.00`** -- exactamente los valores citados. La serie sube
  mes a mes sin discontinuidad en todo 2014-2016 (verificado fila por fila, no solo los dos
  extremos).

### 4.1 Verificación de solapamiento pedida -- resultado, no solo confirmación

Comparé `ipc_facpce` contra la serie ya cargada en `series_economicas_mensuales.csv` en los dos
tramos donde ambas tienen dato (265 meses en común):

**Post-2016 (109 meses): razón `ipc / ipc_facpce` = 1.000000 casi exacto (media 0.999996, desvío
0.00004).** Confirma que el vintage 3 de datos.gob.ar (`148.3_INIVELNAL_DICI_M_26`) **es
literalmente la misma serie que FACPCE de dic-2016 en adelante** -- no una serie distinta que
casualmente coincide, coinciden dato a dato.

**Pre-2014 (156 meses): la razón NO es constante -- va de 3.38 a 6.17 (media 4.06, desvío 0.66),
con una deriva sistemática decreciente en el tiempo** (5.94 en 2001, 3.50 en 2013). Correlación
de nivel alta (0.997) pero **no es un simple cambio de base (un factor constante)** -- las dos
series miden algo consistente en tendencia pero divergen gradualmente en magnitud dentro del
tramo que se suponía "sano" (pre-intervención). No indagué la causa exacta (posibles bases
intermedias adicionales en uno de los dos empalmes, metodología de ponderación distinta) -- pero
el hallazgo en sí es lo que importa para la decisión de abajo.

**Consecuencia directa para la disyuntiva que dejaste abierta (parchear vs. re-basar todo):**
como la razón pre-2014 no es un factor fijo, **"parchear" (reemplazar solo 2014-2016 y mantener
los vintages 1-2 de datos.gob.ar para el resto) dejaría una costura con una inconsistencia
metodológica real en el borde 2013-12/2014-01** -- las dos series no empalman limpio ahí, aunque
no haya un salto brusco de nivel visible a simple vista. **Usar FACPCE de punta a punta
(1993/2001-2025) evita ese problema por construcción**: es una sola serie, una sola
metodología, ya continua en todo el rango que necesita el repo (2001-2025 completo, con margen).

**Decisión tomada:** reemplazar `ipc` por FACPCE como fuente única para todo 2001-2025, no solo
el tramo roto.

### 4.2 Por qué la razón pre-2014 no era constante -- verificado, no es un cambio de base

La hipótesis (FACPCE empalma IPC con IPIM "durante la intervención INDEC") se verificó contra
la metodología pública de la Res. JG 539/18, con dos fuentes secundarias independientes que
citan el texto de la resolución (no se pudo leer el PDF original de FACPCE -- está comprimido/no
extraíble como texto con las herramientas de esta sesión; ambas fuentes coinciden en el mismo
detalle, tomado como corroborado, no como definitivo sin el texto primario):

| Tramo | Fuente que usa FACPCE | Nota |
|---|---|---|
| 1993-01 a 2015-10 | **IPIM** (índice de precios **mayoristas**) de INDEC, con factor de enlace a la base dic-2016 | No es IPC, es un índice de precios **mayoristas** reescalado para verse continuo con el IPC posterior. |
| 2015-11 a 2016-12 | IPIM propio de FACPCE (Res. JG 517/16, no el de INDEC) | INDEC tampoco publicaba IPIM confiable en ese tramo puntual. |
| 2017-01 en adelante | IPC Nacional de INDEC, oficial | Recién acá es genuinamente IPC. |

**Esto corrige la hipótesis original en un punto importante: el tramo IPIM no es solo
`periodo_intervenido` (2007-2015, D6) -- es TODO 1993 a dic-2016.** Explica por qué la razón
pre-2014 no era un factor constante (§4.1): no es un cambio de base sobre la misma serie, son
**dos series económicas distintas** (precios mayoristas vs. minoristas) que se mueven parecido
en tendencia (correlación 0.997) pero no en magnitud exacta -- consistente con que mayorista y
minorista divergen estructuralmente en el tiempo (márgenes, composición de la canasta, etc.),
no con un simple error de escala.

**Consecuencia para 2001-2025, decidida explícitamente pese a esto:** usar FACPCE de punta a
punta significa que **`ipc`/`salario_real` para 2001-2016 (8 de las 13 elecciones nacionales
del panel: 2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015) queda construido sobre un proxy
mayorista, no sobre inflación al consumidor** -- incluidos 2001-2006, años **no** cuestionados
por la intervención INDEC, donde el repo ya tenía IPC oficial genuino y sin disputa (vintages
1-2 de datos.gob.ar). Se prioriza una sola fuente consistente y sin costuras (§4.1) sobre la
fidelidad del constructo económico en los años no intervenidos. **Esto tiene que quedar
documentado explícitamente, no como nota al pie**, porque cambia la interpretación de cualquier
coeficiente de `ipc_*`/`salario_real_*` para elecciones hasta 2015 en H1 (voto económico): no
miden "cuánto le importó al votante el aumento de precios que paga", miden un proxy mayorista de
eso. Ver §8, punto de documentación en `registro_variables.csv`.

### 4.3 Qué faltaba para implementarlo -- todo hecho salvo el punto 7 (notebooks)

1. ✅ **Dependencia nueva evitada**: se optó por convertir el `.xlsx` a CSV **una sola vez**
   (`data/macroeconomia/indice-FACPCE.csv`, generado a mano con `openpyxl` instalado solo en el
   entorno de esta sesión, nunca agregado a `requirements.txt`) en vez de parsear el binario en
   cada corrida del pipeline -- cero dependencia nueva.
2. ⏳ **Reproducibilidad de la fuente -- sin resolver, documentado como limitación conocida**:
   FACPCE no tiene URL estable por archivo (publica un `.xlsx` nuevo cada mes, confirmado por
   patrón de URLs con fecha, ej. `.../indice-res-jg-539-18-octubre-de-2025/`) -- el CSV queda
   como snapshot versionado a mano, mismo criterio que el `.dta` de ICG
   (`data/socioeconomia/icg-icc/README.md`). Re-descargar y regenerar el CSV a mano si se
   necesita extender la cobertura más allá de sep-2026.
3. ✅ **Parseo**: hecho -- header en la fila 3, recorte de filas finales sin fecha, `"*"` tratado
   como faltante. `_cargar_facpce()` en `cargar_series_economicas.py`, con test dedicado.
4. ✅ **`ipc` reemplazado**: sale de `_DATOS_GOB_IDS`, pasa a `_LOADERS["ipc"] = _cargar_facpce`.
5. ✅ **Documentación, los dos lugares**: `registro_variables.csv` (`ipc`, `salario_real` y
   `resultado_fiscal` actualizados, las tres notas citaban el hueco viejo) y
   `docs/decisiones_metodologicas.md` ("Corrección a D6 (2026-09-21) -- post-D33").
6. ✅ **`salario_real` recalculado** de punta a punta -- confirmado en la misma corrida que 4/5.
7. ✅ **Los 5 archivos derivados de §8, regenerados** -- ver §6.2 para la verificación. ⏳ Re-correr
   `01.1_lasso_voto_valido.ipynb`/`01.3_lasso_voto_exit.ipynb` (§9) queda para el usuario.

**Las opciones A/B (reset de ancla / excluir ventanas que cruzan el corte) quedan descartadas**
como solución principal -- eran necesarias solo en ausencia de una fuente continua real, y
FACPCE la provee. Podrían quedar como fallback documentado si en la implementación surge algún
problema con la fuente FACPCE (ej. si la reproducibilidad del punto 2 no se puede resolver), pero
no son el plan por defecto.

**`resultado_fiscal` no tiene una fuente equivalente conocida todavía** -- sigue en el alcance
de la auditoría programática de §6/§7, sin resolver acá.

## 5. `panel_k` (D32): ya no hace falta la mitigación provisoria -- `panel_k.py` no está escrito todavía

Esta sección describía qué debía hacer `panel_k.py` **mientras D33 no estuviera resuelto**. D33
ya está resuelto (pasos 1-4) y `panel_k.py` **todavía no se escribió** (commit 3 de la secuencia
acordada en la sesión de D32, quedó pendiente de que existiera este plan) -- así que nada de lo
de abajo llegó a implementarse con la mitigación provisoria, se implementa directamente con
`ipc` ya sano:

- `trimestre_contaminado_ipc()`/el listado data-driven de trimestres atípicos de IPC **siguen
  siendo una buena idea como guarda general** (útil si aparece otro corte de vintage en el
  futuro, en `ipc` o en cualquier otra variable), pero ya no hacen falta como mitigación de
  *este* problema puntual -- se pueden incluir en `panel_k.py`/`05_0` como chequeo de rutina, sin
  el apuro de "que no se corra nada hasta entonces".
- `salario_real_*` **ya no necesita quedar excluida** del universo de candidatas en los
  notebooks de `panel_k` -- la exclusión estaba motivada por el quiebre de escala, que ya no
  existe.
- El barrido `05_5` ya no está bloqueado por este motivo (sigue pendiente de que `panel_k.py` se
  escriba, eso es aparte).

## 6. Auditoría programática pedida (no manual, no una transición por vez)

Con FACPCE como fix elegido (§4), esta auditoría deja de ser "insumo para elegir entre
opciones" y pasa a ser **la verificación de que el fix realmente lo resuelve** (correr antes y
después del reemplazo, confirmar que las filas de §3.2 dejan de aparecer) -- más su alcance
original para `resultado_fiscal`, que FACPCE no cubre:

1. **Por ventana × variable derivada de un índice encadenado** (`ipc`, `salario_real`, y
   `resultado_fiscal` con prioridad baja -- ver §7): para cada ventana (`vc`, `vl` de
   `panel_ventanas.csv`; `W_t`/`W_{t-1}` de `panel_k` una vez que exista), marcar si contiene
   dato real de ambos lados de un corte de vintage conocido (2013-12/2016-12 para IPC -- debería
   dejar de aplicar una vez reemplazado por FACPCE; los cortes de `resultado_fiscal` según lo
   que confirme el punto 3).
2. **Saltos de escala entre transiciones consecutivas** (no solo dentro de una ventana): script
   que calcule la razón `nivel(t)/nivel(t-1)` entre transiciones consecutivas de la misma
   variable y marque las que excedan un umbral a definir (ej. razón >2x o <0.5x sin una razón
   económica esperable) -- esto es lo que hubiera encontrado `salario_real_nivel_vc` de forma
   automática en vez de por inspección manual (§3.1).
3. **Repetir 1 y 2 sobre los 4 archivos derivados**: `panel_ventanas.csv`,
   `panel_ventanas_bieleccion.csv`, `panel_trimestral_<nivel>.csv`,
   `panel_bieleccion_trimestral_<nivel>.csv` -- no solo `panel_ventanas.csv`.

### 6.1 Resultado real del punto 1 (corrido, no simulado)

Implementado en `src/auditoria_interna/auditoria_empalme_vintage.py` (7 tests,
`tests/auditoria_interna/test_auditoria_empalme_vintage.py`), reporte completo en
`docs/auditoria_interna/auditoria_empalme_vintage.md` (gitignored, se regenera con
`PYTHONPATH=src python -m auditoria_interna.auditoria_empalme_vintage`). No audita
`panel_ventanas_bieleccion.csv` por separado -- es una agregación derivada de
`panel_bieleccion_trimestral_<nivel>.csv` sin ventana propia adicional, auditar la fuente ya lo
cubre (documentado en el módulo).

**Confirma exactamente lo ya encontrado a mano, generalizado a las 3 variables y sin dejar
ningún caso sin mirar:**

- `panel_ventanas.csv`: **solo `_vl`** de `*_2015_2017` (los 3 niveles) tiene hueco interno --
  `ipc`, `salario_real` y `resultado_fiscal` los tres, mismas fechas (2014-01/2016-11, 35
  meses). **Ninguna `_vc` tiene hueco interno** -- confirma programáticamente, sobre las 36
  transiciones reales (no 34, corregido acá -- el dato viejo de esta sección era de antes de
  D31), lo que antes era solo una inspección visual de la tabla completa.
- `panel_trimestral_<nivel>.csv` (D13, ventana corta trimestralizada, la que consume `panel_k`):
  **sin huecos internos en ninguna transición** -- las ventanas de ~8 trimestres no llegan a
  tener dato real de los dos lados del hueco de 35 meses (o caen enteras dentro del hueco, o
  tocan un solo borde). Relevante para D32/`panel_k`: confirma que el `trimestre_contaminado_ipc()`
  hardcodeado (rango fijo) de §5 no tiene ningún falso negativo por huecos internos en este
  archivo -- el riesgo ahí es otro (ventanas *dentro* del hueco quedan todas `None`, ya
  cubierto por `cobertura_parcial`/`k_efectivo`, no por este chequeo).
- `panel_bieleccion_trimestral_<nivel>.csv` (D14, bloque largo, ~16 trimestres): **`*_2013_2017`,
  los 3 niveles**, `ipc`/`salario_real`/`resultado_fiscal` con hueco interno de 11 trimestres
  (`orden` 2 a 12) -- confirma y **extiende** el hallazgo manual anterior (que solo había
  verificado `municipal_2013_2017`) a `provincial_2013_2017` y `nacional_2013_2017` también.

**Hallazgo adicional, no buscado, aclara §7**: `resultado_fiscal` muestra **exactamente las
mismas fechas de hueco que `ipc`** en los tres archivos, no un hueco propio derivado de sus 3
vintages declarados. Coincide con lo que ya dice `registro_variables.csv`'s `nota_metodologica`
de `resultado_fiscal` (`nominal=true, deflactado por 'ipc' igual que salario_real, mismo hueco
heredado 2014-2016`) -- el hueco de `resultado_fiscal` es **heredado por deflactación**, no un
problema independiente de sus propios vintages. Esto significa que **arreglar `ipc` (FACPCE)
resuelve automáticamente el hueco de `resultado_fiscal` también**, sin tocar nada de
`resultado_fiscal` en sí -- el riesgo que quedaba abierto en §7 (que sus propios 3 vintages
tuvieran otro problema de escala, independiente del de IPC) sigue sin auditarse (punto 2 de esta
sección, pendiente), pero el hueco que se ve hoy no es evidencia de eso.

### 6.2 Resultado real "después" -- fix aplicado, auditoría re-corrida

Tras el paso 4 (los 5 archivos regenerados con FACPCE), se volvió a correr
`auditoria_interna.auditoria_empalme_vintage`: **los tres reportes pasan a "Sin huecos internos
detectados"** -- `panel_ventanas.csv`, `panel_trimestral_<nivel>.csv` y
`panel_bieleccion_trimestral_<nivel>.csv` -- exactamente las filas de §3.2/§6.1 dejaron de
aparecer, ninguna fila nueva.

Verificación puntual de los valores que estaban rotos (`panel_ventanas.csv`, municipal):

| | antes | después |
|---|---|---|
| `ipc_acum_vl` de `*_2015_2017` | -26.78% (imposible) | **+148.04%** (monótono con el resto de la serie) |
| `salario_real_nivel_vc` de `*_2015_2017` | 21062.98 (salto x4 desde 19023 del período anterior) | **20581.49** (continuo) |
| `salario_real_delta_nivel` de esa fila | ~15796 (espurio) | **1558.16** |

**Alcance del cambio, confirmado columna por columna**: en `panel_ventanas.csv` cambiaron 32 de
151 columnas (todas `ipc_*`/`salario_real_*`/`resultado_fiscal_*` -- ningún electoral, EPH, ni
el resto de las macro tocado), 36 filas antes y después (sin pérdida). Mismo patrón en
`panel_ventanas_bieleccion.csv` (15/90 columnas, 33 filas). `pytest`: 506 passed en cada paso.

## 7. `resultado_fiscal` -- prioridad baja dentro de esta tarea

También encadena 3 vintages (`379.4_RESULTADO_006__36_27`, `379.5_RESULTADO_014__36_68`,
`379.9_RESULTADO_017__31_73`, ver `registro_variables.csv`). Verificación manual rápida,
`resultado_fiscal_nivel_vc` (municipal), alrededor del mismo corte:

```
-7847 (2011_2013) -> -29702 (2013_2015) -> -30382 (2015_2017) -> -22263 (2017_2019)
```

Crece gradualmente, **sin el salto discontinuo x4 de `salario_real`**. No descarta otro
problema (podría estar en otra unidad entre tramos, no verificado), pero no hay evidencia del
mismo patrón de quiebre de escala. Se audita con el mismo script programático de §6, sin
dedicarle el mismo esfuerzo dirigido que a IPC/`salario_real` mientras la auditoría no arroje
algo -- no bloquea el resto de esta tarea.

## 8. Alcance del fix -- ✅ hecho

Tocó `src/ml_models/cargar_series_economicas.py` (reemplazo del loader de `ipc`, §4.3) y obligó
a regenerar, una sola vez, sin red (reusando la caché local de `datos.gob.ar` para las variables
que no cambiaron -- comparación antes/después aislada, ver §6.2):

- ✅ `data/tfi_data/series_economicas_mensuales.csv`
- ✅ `data/tfi_data/panel_ventanas.csv`
- ✅ `data/tfi_data/panel_ventanas_bieleccion.csv`
- ✅ `data/tfi_data/panel/t-1/panel_trimestral_<nivel>.csv`
- ✅ `data/tfi_data/panel/t-2/panel_bieleccion_trimestral_<nivel>.csv`

**Nota para cuando se regenere `nacional` 2001-2009** (extensión pendiente de sesiones
anteriores, no parte de D33): esa regeneración va a volver a tocar estos mismos 5 archivos --
no hace falta repetir el fix de IPC en esa pasada, ya queda incorporado (el loader de `ipc`
usa FACPCE de forma permanente, no es un parche de una sola vez).

## 9. Notebooks a re-correr -- ⏳ pendiente, lo hace el usuario

`notebooks/ml/ventana_t-1/01.1_lasso_voto_valido.ipynb` y `01.3_lasso_voto_exit.ipynb` (los dos
coeficientes sospechosos de §3.3) -- confirmar si `salario_real_delta_nivel`/
`salario_real_delta_pendiente` siguen sobreviviendo la selección de LASSO una vez corregida la
escala, o si eran puramente un artefacto del quiebre. Verificado antes de esto (sin correr el
LOOCV completo) que no hay ninguna referencia rota: mismo target, mismas columnas, mismo patrón
de exclusión por NaN (`N=10`, excluye `*_2001_2003`/`*_2003_2005`, causado por cobertura de
EMAE, no por IPC/`salario_real`) -- lo único desactualizado es la prosa markdown que describe
los coeficientes viejos, que se actualiza con el resultado real una vez corrido.

---

*Documento de especificación. Implementado (pasos 1-4 de 5) -- falta solo re-correr `01.1`/`01.3`
(§9) y, con eso, dar por cerrado D33 y habilitar el barrido `05_5` de D32 (`panel_k`, todavía sin
escribir).*
