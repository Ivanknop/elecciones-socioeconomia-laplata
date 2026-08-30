# Especificación: Panel temporal de ventanas electorales

## Rama `especializacion` — Reorientación metodológica del Objetivo 1

**Estado:** Especificación de diseño. Pendiente de confirmación formal con la dirección del TFI antes de ejecutar sobre `main`.

**Destino:** Rama `especializacion`, creada desde el estado actual de `main`.

---

## 1. Contexto y motivo del cambio

### 1.1 Diseño previo (vigente en `main`)

El diseño original planteaba un **panel espacial**: unidad de análisis `localidad × elección × nivel`, con ~15 localidades del Partido de La Plata como unidades de corte transversal, buscando ganar N mediante variación geográfica.

### 1.2 Problema identificado

Las variables macroeconómicas centrales para H1 (inflación, desocupación, tipo de cambio, confianza) **no varían sub-distritalmente**. Son idénticas para todas las localidades del partido en un año dado. En consecuencia:

- Las ~15 localidades no aportan variación en el regresor principal de H1.
- El N efectivo para estimar el efecto económico sigue siendo el número de elecciones, no el de `localidad × elección`.
- Las filas adicionales por localidad son redundantes respecto de la dimensión económica.

A esto se suma una restricción de datos: **los resultados electorales desagregados por localidad no están disponibles para 2003-2009**, mientras que los resultados agregados de distrito sí existen para todo el período.

### 1.3 Reorientación adoptada

El diseño pivota hacia un **panel temporal de ventanas electorales a nivel distrito** (Partido de La Plata agregado, sin desagregación interna).

**Unidad de análisis:** la transición electoral — el par (elección t-1 → elección t) dentro de un nivel de gobierno.

**Lógica:** cada elección es una "foto" de un proceso continuo. Lo que se analiza es qué ocurrió en la ventana de tiempo previa a esa foto, en términos socioeconómicos y de percepción, y cómo eso se relaciona con el cambio en el voto respecto de la elección anterior.

### 1.4 Qué se resigna

- **H2 y H3 pierden leverage.** Ambas dependen de variación en la distancia ideológica; H3 en particular se apoyaba en variación espacial. En el panel temporal, solo pueden probarse a través de la variación de la oferta partidaria en el tiempo, lo que constituye una prueba más débil.
- **La infraestructura de crosswalk y geolocalización** (`circuito_localidad.csv`, `alias_localidad_censal.csv`, las 15 categorías de localidad) deja de alimentar el modelo principal del Objetivo 1 y pasa a tener valor para visualización y análisis secundario.

### 1.5 Qué se gana

- Serie temporal más larga: **2001-2025** en lugar de 2011-2025.
- Diseño más fiel a la literatura de voto económico, que trabaja mayoritariamente con series agregadas temporales.
- Eliminación de una fuente de falsa precisión (N inflado por replicación espacial sin variación en el regresor).
- Posibilidad de estudiar **atribución de responsabilidad por nivel de gobierno**, que se convierte en una pregunta central del diseño.

---

## 2. Arquitectura de la rama

### 2.1 Principio general

Se mantiene el principio de **cambios exclusivamente aditivos** ya establecido en el proyecto. Nada de lo existente se mueve, renombra ni elimina. Todo componente nuevo se agrega.

Ver `CLAUDE.md` en la raíz del repositorio para las convenciones vigentes.

### 2.2 Rama

```
git checkout -b especializacion
```

Creada desde el estado actual de `main`. Todo el trabajo de esta especificación ocurre en `especializacion`. El merge a `main` queda condicionado a la confirmación formal de la reorientación con la dirección del TFI.

### 2.3 Estructura de archivos nueva

Toda ruta indicada es adicional; ninguna reemplaza estructuras existentes.

```
data/tfi_data/
  calendario_electoral.csv          # NUEVO — inventario de elecciones 2001-2025 por nivel
  oficialismo_por_nivel.csv         # NUEVO — quién ocupa el ejecutivo de cada nivel, por período
  resultado_distrito.csv            # NUEVO — resultado agregado de La Plata por elección y nivel
  voto_partido_distrito.csv         # NUEVO — voto por agrupación, distrito, elección y nivel
  elecciones/                       # NUEVO — un CSV por (año, nivel): agrupaciones + BLANCO/NULO, elección general (falta 2001-2009, ver docs/adquisicion_datos_especializacion.md §1.a)
  registro_variables.csv            # NUEVO — catálogo declarativo de variables (extensible)
  series_economicas_mensuales.csv   # NUEVO — panel largo de variables macro, grano mensual
  ventanas.csv                      # NUEVO — definición de cada ventana (transición)
  panel_ventanas.csv                # NUEVO — tabla final de modelado: ventana × nivel × features

src/ml_models/
  construir_calendario.py           # NUEVO
  construir_resultado_distrito.py   # NUEVO
  construir_elecciones.py           # NUEVO — genera data/tfi_data/elecciones/
  cargar_series_economicas.py       # NUEVO
  construir_ventanas.py             # NUEVO
  features_ventana.py               # NUEVO — cálculo de features intra e interventana
  construir_panel_ventanas.py       # NUEVO — orquestador

tests/ml_models/
  test_calendario.py                # NUEVO
  test_ventanas.py                  # NUEVO
  test_features_ventana.py          # NUEVO
  test_panel_ventanas.py            # NUEVO

docs/
  decisiones_metodologicas.md       # EXISTENTE o NUEVO — registrar decisiones D1-D8 (sección 8)
  ESPECIFICACION_PANEL_TEMPORAL.md  # NUEVO — este documento, versionado en el repo
```

### 2.4 Reutilización de código existente

No reimplementar lo que ya existe y está testeado:

- `src/analisis/serie_temporal.py` → `NIVELES`, `CARGO_LABEL`
- `src/electoral/localidades.py` → funciones de carga (para el análisis secundario espacial, no para el panel principal)
- `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv` → fuente única de `campo_ideologico`, `filiacion_politica` y scores V-Party
- `data/agrupaciones/oficalismos.csv` → base para extender el oficialismo hacia atrás hasta 2001

---

## 3. Calendario electoral y estructura de ventanas

### 3.1 Criterio de nivel

Ya establecido en el proyecto: **el nivel es político, no formal de cargo**. Lo que importa es el voto a la agrupación en ese nivel de gobierno, independientemente de si la elección puntual fue ejecutiva o legislativa.

| Nivel | Cargos que computan |
|---|---|
| `municipal` | Intendente + concejales |
| `provincial` | Gobernador + diputados y senadores provinciales |
| `nacional` | Presidente + diputados y senadores nacionales |

El **oficialismo** de cada nivel es siempre quien ocupa el Ejecutivo de ese nivel al momento de la elección.

### 3.2 Calendario 2001-2025

Elecciones cada dos años, en años impares. Corte inferior en 2001 por disponibilidad simultánea de métricas económicas y del Índice de Confianza en el Gobierno (ICG-UTDT, serie desde noviembre 2001).

| Año | Tipo nacional | Nivel municipal | Nivel provincial | Nivel nacional |
|---|---|---|---|---|
| 2001 | Legislativa | ✓ | ✓ | ✗ (sin desagregado La Plata) |
| 2003 | Presidencial | ✓ | ✓ | ✗ |
| 2005 | Legislativa | ✓ | ✓ | ✗ |
| 2007 | Presidencial | ✓ | ✓ | ✗ |
| 2009 | Legislativa | ✓ | ✓ | ✗ |
| 2011 | Presidencial | ✓ | ✓ | ✓ |
| 2013 | Legislativa | ✓ | ✓ | ✓ |
| 2015 | Presidencial | ✓ | ✓ | ✓ |
| 2017 | Legislativa | ✓ | ✓ | ✓ |
| 2019 | Presidencial | ✓ | ✓ | ✓ |
| 2021 | Legislativa | ✓ | ✓ | ✓ |
| 2023 | Presidencial | ✓ | ✓ | ✓ |
| 2025 | Legislativa | ✓ | ✓ | ✓ |

**Resultado en transiciones:**

| Nivel | Elecciones | Transiciones (ventanas) |
|---|---|---|
| `municipal` | 13 (2001-2025) | 12 |
| `provincial` | 13 (2001-2025) | 12 |
| `nacional` | 8 (2011-2025) | 7 |
| **Total** | | **31** |

### 3.3 Desdoblamiento

La única elección desdoblada del período es **2025** (provincial/municipal en fecha propia, separada por pocos meses de la nacional). Dada la magnitud de la ventana (24 meses), un corrimiento de uno o dos meses en la fecha de cierre es despreciable. **No se aplica normalización por duración variable de ventana.**

Se registra en `calendario_electoral.csv` la fecha exacta de cada elección por nivel, de modo que el corte de las series económicas sea preciso aun en 2025.

### 3.4 Definición de ventana

Para cada transición `(nivel, t-1 → t)`:

- **Ventana corta:** desde la fecha de la elección `t-1` hasta la fecha de la elección `t`. Duración nominal ~24 meses.
- **Bloque largo:** desde la fecha de la elección `t-2` hasta la fecha de la elección `t`. Duración nominal ~48 meses.

**Decisión clave (D3, ver sección 8):** el bloque largo **no genera una observación adicional**. Genera *features adicionales de la misma observación*. Esto evita la pseudo-replicación que resultaría de apilar ventanas superpuestas como si fueran independientes.

Cada fila del panel corresponde a una transición y contiene:
- Features calculados sobre la ventana corta (`_vc`)
- Features calculados sobre el bloque largo (`_vl`)
- Features de comparación entre la ventana corta actual y la anterior (`_delta`)

---

## 4. Series económicas: variables y agregación

### 4.1 El conjunto de variables es abierto y extensible

**Principio de diseño (D9, ver sección 8):** el conjunto de variables económicas y sociales **no es fijo**. Nuevos datasets pueden incorporarse en cualquier momento del proyecto, y la arquitectura debe permitirlo sin refactorizar código.

Esto tiene una consecuencia directa sobre la implementación: **las variables no se declaran en el código, se declaran en un registro externo**. `features_ventana.py` debe operar sobre ese registro de forma genérica, iterando sobre las variables declaradas. Agregar una serie nueva debe requerir únicamente:

1. Agregar la serie a `series_economicas_mensuales.csv` (o al mecanismo de carga correspondiente).
2. Agregar una fila al registro de variables.

Sin tocar la lógica de cálculo de features.

### 4.2 Registro de variables

Se crea **`data/tfi_data/registro_variables.csv`** como catálogo declarativo. Columnas:

| Columna | Descripción |
|---|---|
| `id_variable` | Identificador canónico, usado como prefijo de todos sus features |
| `descripcion` | Descripción legible |
| `fuente` | Organismo o institución de origen |
| `url_fuente` | URL de descarga o referencia |
| `periodicidad_nativa` | `diaria` / `mensual` / `trimestral` / `semestral` / `anual` |
| `cobertura_desde` | Primer período disponible (AAAA-MM) |
| `cobertura_hasta` | Último período disponible, o `presente` |
| `nivel_geografico` | `nacional` / `provincial` / `aglomerado` / `departamental` |
| `polaridad` | `positiva` / `negativa` / `ambigua` (ver 5.4) |
| `es_flujo` | Booleano — determina si aplica el feature `_acum` |
| `nominal` | Booleano — si requiere deflactación |
| `bloque_tematico` | `real` / `nominal_cambiario` / `percepcion` / `fiscal` / `social` / `sin_asignar` |
| `estado` | `nucleo` / `complementaria` / `exploratoria` |
| `nota_metodologica` | Empalmes, discontinuidades, reservas |

El campo `estado` gobierna qué entra en la especificación principal (`nucleo`), qué se usa en modelos secundarios y de sensibilidad (`complementaria`), y qué está cargado pero aún sin rol definido (`exploratoria`). Cambiar el rol de una variable es editar este campo, no modificar código.

### 4.3 Variables iniciales

El siguiente es el **estado inicial del registro**, no una lista cerrada. Ver `inventario_fuentes_datos.md` para el detalle completo de fuentes, URLs y notas metodológicas, incluyendo variables adicionales relevadas pero aún no incorporadas.

**Estado `nucleo` (cobertura 2001-2025):**

| `id_variable` | Descripción | Fuente | Periodicidad | Polaridad | Bloque |
|---|---|---|---|---|---|
| `ipc` | Índice de precios al consumidor (empalmado) | INDEC | Mensual | negativa | nominal_cambiario |
| `desocupacion` | Tasa de desocupación, aglomerado Gran La Plata | INDEC-EPH | Trimestral | negativa | real |
| `icg` | Índice de Confianza en el Gobierno | UTDT | Mensual | positiva | percepcion |
| `icc` | Índice de Confianza del Consumidor | UTDT | Mensual | positiva | percepcion |
| `salario_real` | RIPTE deflactado por IPC | Min. Trabajo + INDEC | Mensual | positiva | real |
| `tc_oficial` | Tipo de cambio de referencia $/USD | BCRA | Diaria | negativa | nominal_cambiario |
| `resultado_fiscal` | Resultado primario del SPN no financiero | Hacienda | Mensual | ambigua | fiscal |
| `reservas` | Reservas internacionales BCRA, USD | BCRA | Diaria | positiva | nominal_cambiario |

**Estado `complementaria` (cobertura parcial):**

| `id_variable` | Cobertura | Polaridad | Bloque |
|---|---|---|---|
| `emae` | Desde 2004 | positiva | real |
| `pobreza` | Semestral, empalme CEDLAS | negativa | social |
| `gini` | Semestral, empalme CEDLAS | negativa | social |
| `brecha_cambiaria` | Desde ~2011 | negativa | nominal_cambiario |
| `empleo_registrado_pba` | Trimestral, OEDE | positiva | real |

**Candidatas relevadas, aún no incorporadas** (ver `inventario_fuentes_datos.md`): REM del BCRA (expectativas, desde 2016), Índice de Salarios con componente informal (desde 2016), OEDE departamental La Plata (desde 2019), indicadores multidimensionales del ODSA-UCA (anual, desde 2010), ventas en supermercados (INDEC, mensual desde 2003), índice de costo de la construcción (INDEC, mensual desde 1993), IPI manufacturero.

### 4.4 Requisitos para incorporar una variable nueva

Una variable puede sumarse al registro en cualquier momento, siempre que:

1. Tenga **periodicidad mensual, trimestral o superior**. Las series anuales aportan 1-2 puntos por ventana de 24 meses, lo que impide calcular `_pendiente` y `_volatilidad` de forma significativa. Pueden incorporarse con `estado = exploratoria` y solo el feature `_nivel`.
2. Su **procedencia y decisiones de empalme estén documentadas** en `nota_metodologica`.
3. Se declare su **polaridad** explícitamente, o se marque `ambigua` para excluirla del feature `_mejoro`.
4. Se registre su **cobertura real**, para que el pipeline pueda detectar y marcar los tramos faltantes en lugar de imputarlos.

Incorporar variables **agrava el problema de p >> n** descrito en 5.5. La extensibilidad del registro no debe confundirse con una invitación a inflar el espacio de features: cada variable nueva multiplica las columnas por el número de features calculados. La reducción por bloques temáticos (5.5) es el mecanismo que absorbe esa expansión.

### 4.5 Normalización previa

Antes de calcular cualquier feature:

1. **Deflactar** todo lo marcado como `nominal = true` en el registro, por IPC, base a definir.
2. **Homogeneizar a grano mensual**, según la `periodicidad_nativa` declarada en el registro. Series trimestrales o semestrales se interpolan o se replican dentro del período — registrar la decisión y aplicarla de forma consistente. Series diarias se promedian por mes.
3. **Estandarizar** (z-score) al momento de modelar, no al construir la tabla. La tabla guarda valores en unidades originales para trazabilidad; la estandarización es un paso del pipeline de modelado.

Los tres pasos deben leer sus parámetros del registro de variables, no de constantes hardcodeadas, para que una variable nueva quede cubierta automáticamente.

### 4.6 Tratamiento del período 2007-2015

Las series oficiales del INDEC de ese período están sujetas a reservas por intervención del organismo. Afecta a `ipc`, `desocupacion` y `pobreza`, e indirectamente a `salario_real`.

**Decisión (D6, ver sección 8):** se usan las series oficiales, se marca el período con una columna `periodo_intervenido` (booleana, por mes), y se realiza análisis de sensibilidad comparando resultados con y sin ese subperíodo, y con fuentes alternativas (IPC Congreso, CEDLAS) donde estén disponibles.

**No se excluyen observaciones a priori.** El período incluye ~4 elecciones por nivel; excluirlo destruiría un tercio del panel.

---

## 5. Diccionario de features

### 5.1 Concepto de similitud adoptado

El objetivo del análisis no es únicamente estimar un efecto causal, sino **caracterizar la reacción del electorado platense ante escenarios socioeconómicos comparables**. Esto requiere una definición operativa de "escenario similar".

**Definición adoptada:** unificación de similitud por **trayectoria** (la forma de lo ocurrido dentro de la ventana) y por **posición relativa** (cómo se compara esa ventana con la anterior).

Se descarta explícitamente la similitud por *nivel absoluto* como criterio principal: en el contexto argentino, un mismo valor de inflación significó cosas distintas en momentos distintos, dado que el electorado recalibra expectativas continuamente.

### 5.2 Features intraventana (trayectoria)

Los features se calculan **iterando sobre el registro de variables** (sección 4.2), no sobre una lista fija en código. Para cada variable `X` declarada en el registro, sobre la ventana corta (`_vc`) y sobre el bloque largo (`_vl`):

| Feature | Sufijo | Fórmula / definición |
|---|---|---|
| Nivel promedio | `_nivel` | Media de los valores mensuales de `X` en la ventana |
| Pendiente | `_pendiente` | Coeficiente de la regresión lineal de `X` sobre el índice temporal dentro de la ventana |
| Volatilidad | `_volatilidad` | Desvío estándar de los valores mensuales de `X` en la ventana |
| Tramo final | `_final` | Media de `X` en los últimos 6 meses antes de la elección `t` |
| Acumulado | `_acum` | Para variables de flujo (inflación): variación acumulada en la ventana |

### 5.3 Features interventana (posición relativa)

Comparación entre la ventana corta actual y la ventana corta inmediatamente anterior del mismo nivel:

| Feature | Sufijo | Fórmula / definición |
|---|---|---|
| Delta de nivel | `_delta_nivel` | `X_nivel_vc(t) − X_nivel_vc(t−1)` |
| Delta de pendiente | `_delta_pendiente` | `X_pendiente_vc(t) − X_pendiente_vc(t−1)` |
| Signo de mejora | `_mejoro` | Booleano: ¿la variable evolucionó favorablemente respecto de la ventana anterior? Requiere definir polaridad por variable (ver 5.4) |

### 5.4 Polaridad de las variables

Cada variable necesita una polaridad explícita para que `_mejoro` y los signos de pendiente sean interpretables de forma homogénea. La polaridad **se lee del campo `polaridad` del registro de variables** (sección 4.2), no de una constante en código:

- `positiva` — un valor mayor representa una mejora (ej. `icg`, `salario_real`, `reservas`)
- `negativa` — un valor menor representa una mejora (ej. `ipc`, `desocupacion`, `tc_oficial`)
- `ambigua` — no se fuerza dirección; la variable queda **excluida del feature `_mejoro`** (ej. `resultado_fiscal`)

Una variable sin polaridad declarada en el registro debe hacer fallar la construcción con error explícito, no asumir un valor por defecto.

### 5.4.1 Features aplicables según tipo de variable

No todos los features aplican a todas las variables. El registro gobierna cuáles se calculan:

| Condición en el registro | Consecuencia |
|---|---|
| `es_flujo = true` | Se calcula `_acum`; si es `false`, se omite |
| `polaridad = ambigua` | Se omite `_mejoro` |
| `periodicidad_nativa = anual` | Se calcula solo `_nivel`; se omiten `_pendiente`, `_volatilidad` y `_final` por insuficiencia de puntos en la ventana |
| Cobertura parcial (tramo faltante dentro de la ventana) | El feature se calcula sobre los meses disponibles y se marca con una columna de flag `<id_variable>_cobertura_parcial` |

Esta lógica debe estar implementada de forma genérica, de modo que incorporar una variable con características distintas a las existentes no requiera modificar `features_ventana.py`.

### 5.5 Reducción de dimensionalidad

**Problema:** con las 8 variables iniciales del núcleo, ~5 features intraventana × 2 ventanas + 3 features interventana ≈ 100+ columnas potenciales, contra 7-12 observaciones por serie. Régimen de p >> n severo. **Y el conjunto de variables es abierto (D9), de modo que este número crece con cada incorporación.**

Esto convierte a la reducción de dimensionalidad en un requisito estructural del diseño, no en un paso opcional de afinamiento.

**Estrategia obligatoria antes de modelar:**

1. **Selección teórica, no algorítmica.** Elegir a priori qué forma de agregación corresponde a cada variable según lo que postula cada hipótesis, en lugar de generar todas las combinaciones y dejar que un selector automático elija. Con N≈12, la selección data-driven es esencialmente ruido.

2. **Bloques temáticos.** Las variables económicas son fuertemente colineales entre sí en el contexto argentino. La agrupación se define por el campo `bloque_tematico` del registro, de modo que una variable nueva se asigne a un bloque existente en lugar de sumar una dimensión más:
   - **`real`:** `desocupacion`, `salario_real`, `emae`, `empleo_registrado_pba`
   - **`nominal_cambiario`:** `ipc`, `tc_oficial`, `reservas`, `brecha_cambiaria`
   - **`percepcion`:** `icg`, `icc`
   - **`fiscal`:** `resultado_fiscal`
   - **`social`:** `pobreza`, `gini`

   Construcción de cada índice vía PCA (primer componente) o promedio de z-scores, según cuál resulte más estable. Esto reduce p de ~100 a ~15-20, y **mantiene p acotado aunque se incorporen variables nuevas**, siempre que se asignen a bloques existentes.

   Crear un bloque nuevo debe ser una decisión deliberada y registrada, no el resultado automático de incorporar una variable que no encaja.

3. La tabla `panel_ventanas.csv` **guarda todos los features calculados**. La reducción ocurre en el pipeline de modelado, no en la construcción de la tabla, de modo que la decisión sea reversible y auditable.

---

## 6. Variable dependiente

### 6.1 Definición principal

`delta_v` = cambio en el share de voto de la agrupación oficialista **de ese nivel**, entre la elección `t-1` y la elección `t`, sobre el total del distrito La Plata.

```
delta_v = share_oficialismo(t) − share_oficialismo(t−1)
```

### 6.2 Complicación: continuidad del oficialismo

No siempre la agrupación oficialista en `t` es la misma que en `t-1`, ni la misma etiqueta electoral persiste entre elecciones (cambios de nombre de frentes, rupturas, refundaciones).

Se requiere una columna `continuidad_oficialismo` con valores:
- `continua` — misma agrupación, misma etiqueta
- `continua_renombrada` — misma fuerza política, etiqueta distinta
- `ruptura` — el oficialismo no compite o se fragmenta
- `sin_oficialismo` — casos extremos (2001-2003, colapso del gobierno)

`delta_v` solo es interpretable directamente en los dos primeros casos. Los otros requieren tratamiento explícito, no imputación silenciosa.

### 6.3 Variables dependientes secundarias (H2 y H3)

- `delta_posicion_ideologica` — cambio en la posición ideológica ponderada del electorado del distrito, calculada como promedio de scores V-Party ponderado por share de voto de cada agrupación. **Nunca atribuir la ideología del ganador al distrito entero** (disciplina anti-falacia ecológica, ya establecida en el proyecto).
- `distancia_oficialismo_alternativa` — distancia ideológica entre el oficialismo y la principal fuerza opositora disponible, para probar H3.

---

## 7. Tres series paralelas y atribución de responsabilidad

### 7.1 Decisión estructural

Las tres series (`municipal`, `provincial`, `nacional`) **corren en paralelo y no se apilan en un panel único con `nivel` como covariable**.

**Razón:** el objeto de estudio es precisamente la atribución de responsabilidad por nivel. Si los tres niveles se mezclan en un modelo común con `nivel` como control, la atribución pasa a ser un parámetro incidental en lugar del fenómeno bajo estudio.

### 7.2 Implicación técnica

Los regresores económicos son **idénticos** para las tres series en una ventana dada (la economía es la misma). Lo único que varía entre series es la variable dependiente, porque varía quién es el oficialismo.

En consecuencia:
- Las diferencias entre los coeficientes estimados de cada serie son **directamente interpretables como diferencias de atribución de responsabilidad**.
- Apilar las tres series trataría 31 observaciones como independientes cuando hay solo ~12-13 shocks económicos distintos, inflando artificialmente la precisión.

### 7.3 Implementación en datos

Una única tabla `panel_ventanas.csv` con columna `nivel`, pero **el grano de análisis es la serie, no la fila**. El filtrado por nivel ocurre al momento de modelar. Esto simplifica la construcción sin comprometer la decisión metodológica, siempre que quede documentado.

### 7.4 Pooling parcial: decisión abierta

La serie `nacional` tiene solo 7 observaciones. Existe una vía intermedia entre pooling completo (que destruiría la pregunta) y sin pooling (que deja la serie nacional muy débil): **modelo jerárquico bayesiano con parcial pooling entre niveles**, donde cada nivel conserva su propio coeficiente de respuesta pero comparte información a través de una distribución común.

Trade-off: introduce el supuesto de intercambiabilidad a priori entre niveles.

**Esta decisión queda abierta (D7) y debe resolverse empíricamente, comparando ambas especificaciones.**

---

## 8. Registro de decisiones metodológicas

A incorporar en `docs/decisiones_metodologicas.md`:

| ID | Decisión | Estado |
|---|---|---|
| D1 | Pivote de panel espacial (localidad) a panel temporal de ventanas a nivel distrito | **Pendiente de confirmación formal con la dirección del TFI** |
| D2 | Corte temporal inferior en 2001, por disponibilidad conjunta de series económicas e ICG | Adoptada |
| D3 | El bloque largo (t-2 → t) genera features adicionales de la misma observación, no observaciones nuevas — evita pseudo-replicación | Adoptada |
| D4 | Ventanas de largo homogéneo (~24 meses); no se normaliza por duración variable (único desdoblamiento en 2025, de pocos meses) | Adoptada |
| D5 | Similitud definida como unificación de trayectoria intraventana + posición relativa interventana; se descarta el nivel absoluto como criterio principal | Adoptada |
| D6 | Período 2007-2015 (INDEC intervenido): se incluye, se marca con flag, se hace análisis de sensibilidad. No se excluye a priori | Adoptada |
| D7 | Tres series paralelas por nivel, no panel apilado. Pooling parcial entre niveles queda por resolver empíricamente | Adoptada (pooling abierto) |
| D8 | El panel espacial por localidad se conserva como análisis secundario y para visualización, no se elimina | Adoptada |
| D9 | El conjunto de variables es abierto y extensible. Se declara en `registro_variables.csv`, no en código. `features_ventana.py` opera genéricamente sobre ese registro. Incorporar una variable nueva no requiere refactorizar | Adoptada |

---

## 9. Alcance del trabajo a ejecutar

### 9.1 Fase 1 — Estructura temporal

1. Construir `calendario_electoral.csv`: para cada elección 2001-2025 y cada nivel, la fecha exacta, el tipo de elección (ejecutiva/legislativa), y si hubo desdoblamiento.
2. Construir `oficialismo_por_nivel.csv`: extender `data/agrupaciones/oficalismos.csv` hacia atrás hasta 2001, cubriendo los tres niveles. Incluir `continuidad_oficialismo`.
3. Construir `ventanas.csv`: para cada transición, `id_transicion`, `nivel`, `anio_t`, `anio_t_menos_1`, `fecha_inicio_vc`, `fecha_fin_vc`, `fecha_inicio_vl`, `tipo_eleccion_t`, `tipo_eleccion_t_menos_1`.

### 9.2 Fase 2 — Resultados electorales de distrito

4. Construir `resultado_distrito.csv` y `voto_partido_distrito.csv` a partir de `data/distrito/`, agregando al total del partido sin desagregación por circuito ni localidad.
5. Verificar cobertura: si faltan años (particularmente 2001-2009 en algún nivel), documentar el hueco explícitamente, no imputar.
6. Calcular `delta_v` y las variables dependientes secundarias.

### 9.3 Fase 3 — Series económicas

7. Construir `registro_variables.csv` con el esquema de la sección 4.2, poblado con las variables iniciales de 4.3. Este archivo es el punto de extensión del sistema: agregar una variable futura debe ser agregar una fila acá más la serie correspondiente.
8. Construir `series_economicas_mensuales.csv`: grano mensual, 2001-2025, con las variables declaradas en el registro. Columna `periodo_intervenido`.
9. Documentar la procedencia de cada serie y las decisiones de empalme e interpolación en el campo `nota_metodologica` del registro o en un `README` adjunto.
10. La carga debe ser **genérica respecto del registro**: agregar una variable no debe requerir modificar `cargar_series_economicas.py` más allá del mecanismo de descarga o lectura específico de esa fuente.

### 9.4 Fase 4 — Features y panel final

11. Implementar `features_ventana.py` con las fórmulas de la sección 5, **operando genéricamente sobre el registro de variables**. No hardcodear la lista de variables ni sus polaridades.
12. Construir `panel_ventanas.csv`: 31 filas (12 municipales + 12 provinciales + 7 nacionales), con todas las columnas de identificación, dependientes y features.
13. Tests: verificar el N esperado por nivel, la ausencia de nulos no documentados, la coherencia de fechas, la correcta polaridad de los features, y **que agregar una fila ficticia al registro produzca sus features automáticamente sin tocar código** (test de extensibilidad).

### 9.5 Fuera de alcance de esta especificación

- El modelado propiamente dicho (bayesiano jerárquico, reducción por bloques, clustering de ventanas). Se abordará una vez construida y validada la tabla.
- La visualización temporal (panel nuevo de "película" con ventanas resaltadas).
- Cualquier modificación al panel espacial por localidad existente.

---

## 10. Criterios de aceptación

El trabajo se considera completo cuando:

- La rama `especializacion` existe y contiene todos los archivos nuevos, sin haber modificado, movido ni renombrado ningún archivo preexistente.
- `panel_ventanas.csv` tiene exactamente 31 filas, con la distribución 12/12/7 por nivel.
- Todo hueco de datos está documentado explícitamente (columna de flag o nota metodológica), sin imputaciones silenciosas.
- La suite de tests existente (19 tests) sigue pasando sin modificaciones.
- Los tests nuevos de `tests/ml_models/` pasan.
- `docs/decisiones_metodologicas.md` registra las decisiones D1-D9 con su estado.
- **Prueba de extensibilidad:** agregar una variable nueva al `registro_variables.csv` y su serie correspondiente produce sus features en `panel_ventanas.csv` sin modificar `features_ventana.py`.
- Ningún archivo fuente original fue sobrescrito; los CSV intermedios son auditables y trazables a su fuente.

---

*Documento de especificación. Versión inicial, 27 de agosto de 2026.*
