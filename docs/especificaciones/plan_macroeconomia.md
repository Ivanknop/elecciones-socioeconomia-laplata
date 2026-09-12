# Plan: capa macroeconómica nacional (2011-2025)

**Estado:** implementado. `src/macroeconomia/` (cliente + normalización),
`data/macroeconomia/catalogo_series.csv` (20 conceptos de frecuencia
diaria/mensual/trimestral) y `data/macroeconomia/series_macro_2011_2025.csv`
(generado, 180 filas) ya existen y corren contra la API real — ver
`data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md` para el resultado y
las salvedades encontradas durante la implementación (una de ellas corrigió
un id mal elegido en este mismo plan, sección 3.7). Los 2 conceptos de
frecuencia anual (`gasto_deuda_publica_nivel`/`_pib`) viven aparte, en
`data/macroeconomia/catalogo_series_anuales.csv` y
`data/macroeconomia/series_macro_anuales_2011_2025.csv` (ver "Split a
catálogo anual" más abajo).

**Split a catálogo anual (2026-08):** `gasto_deuda_publica_nivel`/`_pib`
(las únicas dos series `anual` del catálogo original de 22) se sacaron de
`catalogo_series.csv`/`series_macro_2011_2025.csv` y pasaron a un catálogo
y CSV propios, de grano anual en vez de mensual. Motivo: dentro de la
tabla fila-por-mes, una serie anual solo puede tener dato real en 1 de
cada 12 filas -- y sin forward-fill (ver "Rediseño posterior" arriba)
ninguna de las otras 11 lo tiene nunca -- así que esas dos columnas
quedaban con 92,8% de celdas vacías (13/180), la peor cobertura de todo
el catálogo por lejos. A grano anual, las mismas dos columnas quedan con
86,7% de celdas reales (13/15 años) -- mismo dato, sin el ruido de un
grano que no le corresponde. `series_anuales.py` reusa
`ConceptoCatalogo`/`cargar_catalogo`/`_parsear_puntos` de `series.py` en
vez de duplicarlos; la regla de "nunca forward-fill" es la misma, solo
cambia la unidad de fila (año en vez de mes).

**Rediseño posterior (celdas vacías en vez de forward-fill):** la primera
versión de este plan (sección 2, decisión original) hacía que series con
frecuencia menor a mensual repitieran el último valor publicado en los
meses siguientes. Se revirtió esa decisión: ahora una celda solo tiene
valor si la fuente publicó exactamente para ese mes -- si no, queda vacía.
El forward-fill le daba apariencia de dato mensual real a series
trimestrales/anuales, obligando a quien lo usara a adivinar (vía
`observaciones`) qué celdas eran repetidas; dejarlas vacías traslada esa
decisión a quien consume el CSV en vez de tomarla por adelantado. Ver
sección 2 (regla vigente) y `SISTEMATIZACION_VARIABLES_MACRO.md` para la
cobertura real resultante.

**Alcance:** un dominio analítico nuevo, `src/macroeconomia/`, con grano
**nacional exclusivamente** — sin apertura regional ni provincial, y sin
circuito ni localidad. Es contexto temporal para la capa electoral y
socioeconómica ya existentes — se relaciona con ellas por fecha, nunca por
unidad espacial.

---

## 1. Fuentes evaluadas y rol de cada una

Se evaluaron tres fuentes (`estadisticasbcra.com`, `api.bcra.gob.ar`,
`datos.gob.ar`). Resultado de la validación:

| Fuente | Rol final | Motivo |
|---|---|---|
| **`datos.gob.ar`** (API Series de Tiempo, `apis.datos.gob.ar/series/api/series`) | **Fuente única activa** | Único agregador con cobertura real de precios, empleo, ingresos y actividad además de lo monetario/cambiario. Sin autenticación. |
| **`estadisticasbcra.com`** | **Auditor externo, no fuente** | Requiere token + límite de 100 consultas/día, y su propio disclaimer dice "sin garantía de funcionamiento". Se usa manualmente, cuando hace falta reauditar, para cotejar cada serie que tenga equivalente ahí — no se integra al pipeline de descarga. Confirmado en la corrida del 2026-08-07 (`SISTEMATIZACION_VARIABLES_MACRO.md` §3): su versión con token de usuario está atrasada entre ~1,5 y 2 años según el endpoint, así que solo sirve para auditar tramos históricos ya cerrados, nunca los datos más recientes del CSV. |
| **`api.bcra.gob.ar`** (oficial v4.0) | **Descartada** | Todo lo que aporta de valor ya está espejado en `datos.gob.ar` para los conceptos de este plan; no se justifica mantener un tercer cliente. |

**Qué puede auditar `estadisticasbcra.com` y qué no** (según su catálogo de
~60 series documentado en `estadisticasbcra.com/api/documentacion`):

- **Sí cubre** (auditable): tipo de cambio, reservas, base monetaria, tasas
  (BADLAR, LELIQ, pases), `inflacion_mensual_oficial` /
  `inflacion_interanual_oficial` (útil para auditar el IPC Nacional).
- **No cubre** (sin auditor posible, se documenta como limitación, no se
  inventa un sustituto): EMAE, PBI, RIPTE, índice de salarios, canasta
  básica, empleo/desocupación, comercio exterior, deuda pública.

---

## 2. Arquitectura

```
src/macroeconomia/
  datos_gob_client.py           # fetch+caché por id de serie, sin transformar (mismo contrato que client.py/eph_client.py)
  series.py                      # lee catalogo_series.csv + caché crudo, resuelve por fuente declarada, escribe el CSV ancho mensual
  series_anuales.py              # ídem, para catalogo_series_anuales.csv -- escribe el CSV ancho anual (reusa ConceptoCatalogo/cargar_catalogo/_parsear_puntos de series.py)
  auditoria_estadisticasbcra.py  # auditoría manual puntual contra estadisticasbcra.com (sección 5, punto 5) -- no forma parte del pipeline regular

data/macroeconomia/
  catalogo_series.csv                  # una fila por concepto de frecuencia diaria/mensual/trimestral: concepto lógico → id en datos.gob.ar → periodicidad de la fuente → cobertura real → auditable sí/no. Hand-curated, append-only (mismo criterio que clasificacion_ideologica_agrupaciones.csv)
  series_macro_2011_2025.csv           # una fila por MES: fecha, una columna por concepto, observaciones
  catalogo_series_anuales.csv          # mismo formato que catalogo_series.csv, solo para conceptos de frecuencia anual
  series_macro_anuales_2011_2025.csv   # una fila por AÑO: anio, una columna por concepto, observaciones
  SISTEMATIZACION_VARIABLES_MACRO.md   # mismo formato que el de EPH: qué se relevó, qué falta, quiebres metodológicos
  _cache/datos_gob/<id>.json           # crudo cacheado, gitignored -- compartido entre series.py y series_anuales.py, mismo cache_dir
```

**Formato ancho, una fila por mes** (`series_macro_2011_2025.csv`), ordenado
por `fecha` ascendente:

- **Columnas:** `fecha`, seguida de una columna por concepto — en el mismo
  orden en que ese concepto aparece como fila en `catalogo_series.csv` (que
  a su vez sigue el orden de la sección 3 de este plan: monetario/cambiario,
  precios, actividad, empleo, ingresos, finanzas públicas, sector externo)
  — y `observaciones` al final. El orden de filas del catálogo es la única
  fuente de verdad del orden de columnas de salida, para que no puedan
  desalinearse entre sí.
- **Ejemplo concreto de encabezado**, con los conceptos ya confirmados en la
  sección 3 (los pendientes de la sección 6 se insertan en su lugar de
  dimensión cuando se resuelvan):

  ```
  fecha,tipo_cambio_oficial,tipo_cambio_mayorista,reservas_internacionales,
  base_monetaria,tasa_badlar,tasa_politica_monetaria,ipc_nacional,
  canasta_basica_alimentaria,canasta_basica_total,emae,pbi,
  tasa_desocupacion,tasa_empleo,tasa_actividad,ripte,indice_salarios_total,
  indice_salarios_privado_registrado,indice_salarios_publico,
  comercio_exterior_cobros,comercio_exterior_pagos,observaciones
  ```
  (implementado tal cual en `data/macroeconomia/catalogo_series.csv` — el
  orden real de columnas del CSV generado es el de ese archivo, esta lista
  es ilustrativa). Los conceptos de frecuencia anual
  (`gasto_deuda_publica_nivel`/`_pib`) no aparecen acá -- viven en
  `catalogo_series_anuales.csv`/`series_macro_anuales_2011_2025.csv`, con
  `anio` en vez de `fecha` como primera columna (ver "Split a catálogo
  anual" al inicio de este documento).
- **Ninguna celda se rellena ni repite un valor anterior** (decisión
  revisada — ver "Rediseño posterior" al inicio de este documento). Una
  celda tiene valor únicamente si la fuente publicó un dato con fecha de
  origen exactamente ese mes; si no, queda **vacía** y `observaciones`
  declara por qué (ej. `"pbi: sin dato (la fuente no publicó para este
  mes)"`). Esto aplica igual a series mensuales, trimestrales, semestrales
  y anuales: una serie trimestral solo tiene valor en el mes de origen de
  cada trimestre (ej. enero/abril/julio/octubre), los otros dos meses de
  cada trimestre quedan vacíos — nunca con el valor del mes anterior. La
  responsabilidad de repetir/interpolar sobre esas celdas vacías, si hace
  falta, queda del lado de quien consuma el CSV, no de este pipeline.
- **Series de frecuencia diaria** (tipo de cambio, BADLAR, base monetaria):
  se agregan a mensual tomando el **último valor hábil del mes** — no
  promedio; esto es agregación de un dato real, no relleno. Si el último
  día hábil del mes no tiene dato publicado (feriado no bursátil, corte de
  fuente), se toma el hábil anterior más cercano dentro del mismo mes y se
  deja constancia en `observaciones`. Si ningún día hábil del mes tiene
  dato, la celda queda vacía.

---

## 3. Catálogo de variables — periodización, qué informan, consideraciones, fuente exacta

### 3.1 Monetario y cambiario

**Tipo de cambio**
- **Periodización:** diaria, 1992-2026 (`175.1_DR_ESTANSE_0_0_20`); también
  mensual, 2003-2026 (`92.1_TCV_0_0_21`).
- **Qué informa:** valor del dólar (valuación BCRA), insumo para deflactar
  cualquier variable en pesos y para leer devaluaciones puntuales.
- **Consideraciones:** hay más de un tipo de cambio en la fuente. **Resuelto
  por completo**: se toman dos columnas separadas, oficial y mayorista, sin
  ponderar entre ellas — no se elige uno solo ni se promedian, porque
  difieren estructuralmente en el período de desdoblamiento cambiario
  2019-2023. Los dos ids se confirmaron filtrando por
  `dataset_theme=Dinero%20y%20Bancos` en la API de búsqueda (más preciso que
  buscar por texto libre, que traía resultados ambiguos): `tipo_cambio_oficial`
  = "Dólar Estadounidense" y `tipo_cambio_mayorista` = "Dólar Referencia
  Comunicación 'A' 3500 (**Mayorista**)" — esta última trae la palabra
  "Mayorista" literal en el título, a diferencia del id que se había
  propuesto antes (`92.1_TCV_0_0_21`, "tipo de cambio de valuación", que es
  en realidad un concepto contable de valuación de reservas, no la
  cotización mayorista de mercado — se descarta).
- **Fuente exacta:** dataset "Tipos de Cambio Históricos" (INDEC/BCRA vía
  Subsecretaría de Programación Macroeconómica),
  `apis.datos.gob.ar/series/api/series/?ids=175.1_DR_ESTANSE_0_0_20`
  (oficial, diaria 1992-2026) y
  `apis.datos.gob.ar/series/api/series/?ids=175.1_DR_REFE500_0_0_25`
  (mayorista, diaria 2002-2026).

**Reservas internacionales**
- **Periodización:** diaria, 2003-2026 (`92.2_RESERVAS_IRES_0_0_32_40`);
  mensual, 2003-2026 (`92.1_RID_0_0_32`, "Reservas internacionales del
  BCRA, en millones de dólares").
- **Qué informa:** stock de reservas del BCRA — variable clave para leer
  presión cambiaria y crisis de balanza de pagos.
- **Consideraciones:** id **actualizado**: `92.1_RID_0_0_32` reemplaza al
  id propuesto en una revisión anterior de este plan
  (`174.1_RRVAS_IDOS_0_0_36`, mensual desde 1940) — se prefiere el nuevo
  porque su título es explícito en unidades ("en millones de dólares") y se
  ubicó filtrando por `dataset_theme=Dinero y Bancos`, más confiable que la
  búsqueda de texto libre usada antes. La serie vieja sigue siendo válida
  si se necesitara cobertura anterior a 2003, pero no hace falta para el
  rango 2011-2025 de este plan.
- **Fuente exacta:** dataset del tema "Dinero y Bancos" (BCRA vía
  Subsecretaría de Programación Macroeconómica),
  `apis.datos.gob.ar/series/api/series/?ids=92.1_RID_0_0_32`.

**Base monetaria**
- **Periodización:** mensual, 2003-2026 (`331.1_SALDO_BASERIA__15`,
  "Saldo de la Base Monetaria"); diaria, 2003-2026
  (`331.2_SALDO_BASERIA__15`).
- **Qué informa:** circulación monetaria total — referencia estándar de
  política monetaria expansiva/contractiva.
- **Consideraciones:** id **actualizado**: reemplaza a `bcra_251`, que
  venía del catálogo legado `bcra` de datos.gob.ar (162 series, en su
  mayoría contabilidad de balance detallada, poco curado). El nuevo id
  salió del mismo filtro por tema "Dinero y Bancos" que resolvió tipo de
  cambio y reservas, con nombre explícito y sin ambigüedad.
- **Fuente exacta:** `apis.datos.gob.ar/series/api/series/?ids=331.1_SALDO_BASERIA__15`.

**Tasa BADLAR**
- **Periodización:** mensual, 1999-2026 (`89.1_TIB_0_0_20`); diaria,
  2003-2026 (`89.2_TS_INTELAR_0_D_20`).
- **Qué informa:** tasa de referencia para depósitos mayoristas — proxy
  estándar del costo del dinero en pesos.
- **Consideraciones:** ninguna particular más allá de elegir mensual vs.
  diaria según el uso (series temporales largas → mensual, para no arrastrar
  ruido diario sin promediar).
- **Fuente exacta:** dataset "Principales tasas de interés",
  `apis.datos.gob.ar/series/api/series/?ids=89.1_TIB_0_0_20`.

**Tasa de política monetaria**
- **Periodización:** mensual/diaria, **desde dic-2015** (`89.1_IR_BCRARIA_0_M_34`,
  `89.2_TS_INTE_PM_0_D_16`).
- **Qué informa:** tasa de referencia del BCRA (equivalente a la tasa LELIQ
  en el período en que existió ese instrumento, y a los pases después).
- **Consideraciones:** **no hay serie homogénea antes de dic-2015** — el
  instrumento de referencia cambió varias veces en el período 2011-2025
  (LEBAC → LELIQ → pases); esta serie parece ser la continuación oficial ya
  empalmada, pero hay que confirmarlo leyendo la metodología del dataset
  antes de tratarla como una sola serie sin quiebres.
- **Fuente exacta:** dataset "Principales tasas de interés",
  `apis.datos.gob.ar/series/api/series/?ids=89.1_IR_BCRARIA_0_M_34`.

### 3.2 Precios y costo de vida

**IPC Nacional, nivel general**
- **Periodización:** mensual, **desde dic-2016** (`148.3_INIVELNAL_DICI_M_26`);
  trimestral desde 2017 (`148.1_IPC_NIVEL_NAL_DICI_T_26`).
- **Qué informa:** inflación oficial de cobertura país completo (no solo
  GBA) — la referencia estándar para deflactar cualquier serie nominal del
  repo, incluida la EPH (`SISTEMATIZACION_VARIABLES.md` §5 ya señala que los
  ingresos EPH están sin deflactar por falta de esta serie).
- **Consideraciones:** **no existe medición nacional homogénea 2011-2016**
  — INDEC no publicaba IPC país completo hasta 2017; antes solo hay IPC-GBA
  (discontinuado 2013) bajo la reserva metodológica 2007-2015 que este mismo
  repo ya documenta en `eph_client.py`. No rellenar ese tramo con IPC-GBA sin
  marcar el quiebre explícitamente (banda gris, mismo patrón que
  `graficos_eph_iaelap.py` ya usa para los cortes de la EPH).
- **Fuente exacta:** dataset del INDEC vía datos.gob.ar,
  `apis.datos.gob.ar/series/api/series/?ids=148.3_INIVELNAL_DICI_M_26`.
  Auditable contra `estadisticasbcra.com` → `inflacion_mensual_oficial`.

**Canasta Básica Alimentaria (CBA) — nacional**
- **Periodización:** mensual, **desde abr-2016** hasta 2026
  (`150.1_CSTA_BARIA_0_D_26`).
- **Qué informa:** valor monetario de la canasta que define la línea de
  indigencia — insumo directo para estimar incidencia de pobreza/indigencia
  cuando se cruce (más adelante, fuera de este plan) contra ingresos.
- **Consideraciones:** hay series históricas 1992-2000 (semestral) y
  2000-2006 (mensual/trimestral) de otra metodología, discontinuadas — no
  mezclar con la vigente. Existe también una apertura por 6 regiones, pero
  el alcance de este plan es exclusivamente nacional — esa apertura no se
  usa. **Unidad — resuelto**: el valor es **por adulto equivalente** (unidad
  de referencia = varón de 30-60 años con actividad física moderada, valor
  1; el resto de la población se pondera contra esa referencia con una
  tabla de equivalencias por sexo/edad — ver "Preguntas frecuentes" de
  INDEC, Notas al pie N°3). Para pasar de "valor por adulto equivalente" a
  "valor para un hogar" hace falta multiplicar por la cantidad de adultos
  equivalentes de ese hogar — no es una conversión automática, y este plan
  no la hace (no se define ningún hogar de referencia). **Nuance
  metodológica importante**: la CBA/CBT que se publica mensualmente y que
  se toma como "nacional" es, en rigor, la del **Gran Buenos Aires**,
  valorizada con los precios del IPC-GBA — las otras 5 regiones se derivan
  de ésa ajustándola por Paridad de Poder de Compra del Consumidor (PPCC),
  no se calculan de forma independiente. Es decir, la serie
  `150.1_CSTA_BARIA_0_D_26` no es un promedio ponderado de las 6 regiones,
  es la serie de GBA usada como referencia nacional — hay que documentarlo
  así y no como "promedio nacional".
- **Fuente exacta:** dataset "Valores de la Canasta Básica de Alimentos y
  Canasta Básica Total" (INDEC),
  `apis.datos.gob.ar/series/api/series/?ids=150.1_CSTA_BARIA_0_D_26`.
  Metodología: INDEC, "Canasta básica alimentaria, Canasta básica total —
  Preguntas frecuentes", Notas al pie N°3, junio de 2020
  (`indec.gob.ar/ftp/cuadros/sociedad/preguntas_frecuentes_cba_cbt.pdf`).

**Canasta Básica Total (CBT) — nacional**
- **Periodización:** igual que CBA — mensual, abr-2016 a 2026
  (`150.1_CSTA_BATAL_0_D_20`).
- **Qué informa:** valor de la canasta que define la línea de pobreza
  (alimentos + no alimentos). Se calcula como CBA × ICE (inversa del
  coeficiente de Engel, la proporción entre gasto total y gasto alimentario
  de la población de referencia).
- **Consideraciones:** mismas que CBA (quiebre pre-2016, apertura regional
  fuera de alcance, unidad = por adulto equivalente, y la serie "nacional"
  es en rigor la de GBA usada como referencia). Sin auditor externo — no
  está en `estadisticasbcra.com`.
- **Fuente exacta:** `apis.datos.gob.ar/series/api/series/?ids=150.1_CSTA_BATAL_0_D_20`.
  Misma metodología que CBA (Notas al pie N°3, INDEC).

### 3.3 Actividad económica

**EMAE (Estimador Mensual de Actividad Económica)**
- **Periodización:** mensual, desde 2004, base 2004=100 (`143.3_NO_PR_2004_A_21`).
- **Qué informa:** proxy mensual del PBI — sirve para leer ciclos
  (recesión/expansión) con mayor frecuencia que el PBI trimestral.
- **Consideraciones:** base 2004 sigue vigente como serie oficial actual, no
  es una versión vieja a reemplazar.
- **Fuente exacta:** dataset "EMAE Base 2004" (INDEC),
  `apis.datos.gob.ar/series/api/series/?ids=143.3_NO_PR_2004_A_21`.

**PBI (Producto Interno Bruto)**
- **Periodización:** trimestral, 2006-2024, base 2004 (`166.2_PPIB_0_0_3`).
- **Qué informa:** nivel de actividad económica total del país.
- **Consideraciones:** **confianza alta** — confirmado como el único
  resultado bajo el nombre exacto "Producto interno bruto" / `pib` dentro
  del dataset "Ingreso nacional, Ahorro nacional y Préstamo neto. Base
  2004", en millones de pesos — es el agregado total, no un componente
  sectorial. Sigue en base 2004 (no hay, al momento de este plan, una base
  más reciente publicada por INDEC para esta serie).
- **Fuente exacta:** `apis.datos.gob.ar/series/api/series/?ids=166.2_PPIB_0_0_3`.

### 3.4 Empleo

**Desocupación, EPH continua, total país**
- **Periodización:** trimestral, 2003-2026 (`42.3_EPH_PUNTUATAL_0_M_30`).
- **Qué informa:** tasa de desocupación nacional — punto de comparación
  directo contra la desocupación de Gran La Plata ya calculada en
  `eph_gran_la_plata.csv` (misma fuente EPH, mismo trimestre, distinto
  grano geográfico).
- **Consideraciones:** mismos quiebres metodológicos generales de la EPH ya
  documentados en el repo (hueco 2015T3-2016T1, cambio de operativo 2020) —
  aplican igual acá por ser la misma encuesta a nivel país.
- **Fuente exacta:** dataset "EPH Continua" (INDEC),
  `apis.datos.gob.ar/series/api/series/?ids=42.3_EPH_PUNTUATAL_0_M_30`.

**Empleo, EPH continua, total país**
- **Periodización:** trimestral, 2003-2026 (`44.2_ECTET_0_T_30`).
- **Qué informa:** tasa de empleo nacional, mismo uso comparativo que la de
  desocupación.
- **Consideraciones:** ídem anterior.
- **Fuente exacta:** `apis.datos.gob.ar/series/api/series/?ids=44.2_ECTET_0_T_30`.

**Tasa de actividad, total país**
- **Periodización:** trimestral, 2003-2026 (`43.2_ECTAT_0_T_33`); también
  anual, 2004-2025 (`43.1_ECTAT_0_A_33`).
- **Qué informa:** proporción de la población económicamente activa
  (ocupada + desocupada que busca trabajo) sobre el total — junto con
  desocupación y empleo, completa el trío estándar de indicadores de
  mercado de trabajo EPH a nivel nacional.
- **Consideraciones:** mismos quiebres metodológicos generales de la EPH ya
  documentados en el repo (hueco 2015T3-2016T1, cambio de operativo 2020).
- **Fuente exacta:** dataset "Principales variables ocupacionales. EPH
  continua. Actividad" (INDEC),
  `apis.datos.gob.ar/series/api/series/?ids=43.2_ECTAT_0_T_33`.

### 3.5 Ingresos

**RIPTE (Remuneración Imponible Promedio de los Trabajadores Estables)**
- **Periodización:** mensual, 1994-2026 (`158.1_REPTE_0_0_5`) — la serie más
  larga y estable de todo el catálogo, sin quiebre dentro de 2011-2025.
- **Qué informa:** salario formal promedio — referencia estándar para
  ajustes salariales y juicios/indexaciones en Argentina.
- **Consideraciones:** ninguna particular — es la serie con mejor
  cobertura temporal de todas las evaluadas.
- **Fuente exacta:** `apis.datos.gob.ar/series/api/series/?ids=158.1_REPTE_0_0_5`.

**Índice de salarios (total, privado registrado, público)**
- **Periodización:** mensual, desde oct-2015/oct-2016 según la serie, hasta
  2026 (`149.1_TL_INDIIOS_OCTU_0_21`, `149.1_TL_REGIADO_OCTU_0_16`,
  `149.1_SOR_PRIADO_OCTU_0_25`, `149.1_SOR_PUBICO_OCTU_0_14`).
- **Qué informa:** evolución salarial en índice (no en pesos), permite
  comparar variación relativa entre sector público y privado registrado.
- **Consideraciones:** no cubre 2011-2015 — mismo tipo de corte que el IPC.
  Complementa a RIPTE (que sí tiene toda la serie) pero con la apertura
  público/privado que RIPTE no ofrece.
- **Fuente exacta:** `apis.datos.gob.ar/series/api/series/?ids=149.1_TL_INDIIOS_OCTU_0_21`.

### 3.6 Finanzas públicas

**Gasto público nacional en servicios de deuda pública**
- **Periodización:** anual, 1980-2023 (nivel `451.3_GPN_SERVICICA_0_0_27_85`;
  % del PBI `451.4_GPN_SERVICPIB_0_0_31_93`).
- **Qué informa:** peso del pago de intereses/capital de deuda sobre el
  gasto público total.
- **Consideraciones:** es una sola función de gasto (deuda), no el
  resultado fiscal completo — no confundir con déficit/superávit.
- **Fuente exacta:** `apis.datos.gob.ar/series/api/series/?ids=451.3_GPN_SERVICICA_0_0_27_85`.

**Resultado fiscal (primario/financiero), real**
- **Omitido del alcance de este plan** (decisión explícita, no pendiente).
  Lo único que había aparecido en la búsqueda era la mediana de expectativas
  del REM (encuesta de mercado del BCRA), que no es el dato de ejecución
  real — se descarta en vez de incluir un proxy de expectativas bajo un
  nombre que sugeriría un dato real. Ver sección 7.

### 3.7 Sector externo

**Cobros y pagos por bienes (proxy exportaciones/importaciones)**
- **Periodización:** mensual, 2003-2026 (`183.1_COBROS_EXPNES_0_M_27`
  cobros/exportaciones; `183.1_PAGOS_IMPONES_0_M_26` pagos/importaciones).
- **Qué informa:** flujo de divisas por comercio de bienes.
- **Consideraciones:** **es dato de Balance Cambiario del BCRA (base caja,
  divisas efectivamente liquidadas), no comercio exterior aduanero de INDEC
  (base FOB/CIF, devengado)**. Los dos conceptos difieren (anticipos,
  prefinanciación de exportaciones, liquidación diferida) — si se usa, debe
  quedar rotulado explícitamente como "cobros/pagos" y no como "exportaciones/
  importaciones" a secas, para no sugerir una precisión aduanera que no tiene.
  **Error detectado y corregido durante la implementación**: la primera
  versión de este plan había tomado
  `184.1_BIENES_COBCIO_0_M_22`/`184.1_BIENES_PAGCIO_0_M_21`, del dataset 184
  ("Cobros y pagos por bienes **sectorial**"), que resultó ser el sector
  "Comercio" puntual (uno más entre ~15 sectores: Agro, Petróleo, Industria
  Automotriz, etc.), no el total del país — se detectó porque los valores
  mensuales resultantes ($100-500 millones) eran demasiado bajos para el
  comercio exterior argentino completo. El total real está en el dataset
  183 ("... por modalidad de pago"), con series dedicadas
  `total_bienes`/`cobros_exportaciones_bienes`/`pagos_importaciones_bienes`
  — valores de referencia ~$1.800-1.900 millones/mes en 2003, consistentes
  con el orden de magnitud esperado.
- **Fuente exacta:** dataset "Cobros y pagos por bienes por modalidad de
  pago - Balance Cambiario",
  `apis.datos.gob.ar/series/api/series/?ids=183.1_COBROS_EXPNES_0_M_27`.

### 3.8 Excluido del alcance

**Riesgo país (EMBI)**
- No está en ninguna de las tres fuentes evaluadas (`datos.gob.ar`,
  `api.bcra.gob.ar`, `estadisticasbcra.com`). Requeriría una cuarta fuente
  fuera del alcance acordado — queda fuera de este plan salvo autorización
  explícita para sumarla.

**Pobreza e indigencia (EPH, % personas/hogares)**
- Solo se encontró la serie vieja de "EPH puntual", discontinuada en 2003.
  La serie moderna (INDEC la retomó en 2016, semestral, sigue vigente) no
  apareció en la búsqueda realizada — no se incluye hasta ubicar su id
  exacto. **Pendiente, ver sección 6.**

---

## 4. Decisiones ya tomadas

- **Fuente única activa: `datos.gob.ar`.** `estadisticasbcra.com` solo
  audita, una vez, al cerrar el catálogo — no es dependencia de runtime.
  `api.bcra.gob.ar` queda fuera.
- **Alcance exclusivamente nacional** — se descarta toda apertura regional o
  provincial (incluida la de CBA/CBT), aunque la fuente la ofrezca. No hace
  falta entonces resolver "qué región le corresponde a La Plata": no se usa
  ninguna.
- **Formato ancho, una fila por mes**, para `series_macro_2011_2025.csv` —
  una columna por concepto, más `observaciones`. Reemplaza el diseño en
  formato largo de la primera versión de este plan. Cuando la fuente
  publica con frecuencia menor a mensual, la celda queda **vacía** en los
  meses sin dato de origen exacto — no se repite el último valor
  publicado (decisión revisada, ver "Rediseño posterior" al inicio de este
  documento) — y `observaciones` lo declara fila por fila (ver detalle en
  sección 2).
- **Ningún cruce a nivel circuito/localidad** — esta capa se relaciona con
  las demás por fecha, nunca por unidad espacial.
- **Ningún quiebre metodológico se disimula**: todo corte (2016 IPC/canasta/
  salarios, cambios de instrumento de tasa de referencia) se documenta
  explícito, mismo criterio que ya aplican `eph_client.py` y
  `graficos_eph_iaelap.py` para los cortes de la EPH.
- **Tipo de cambio de referencia** — tomar oficial y mayorista, ambos, sin
  ponderar (dos columnas separadas, ver sección 3.1).
- **Agregación de series diarias a mensual: último valor hábil del mes**
  (no promedio). Aplica por igual a tipo de cambio, BADLAR y base
  monetaria — una sola regla para todo el catálogo, no una por serie.

---

## 5. Procedimiento de construcción

1. **Cliente genérico** `src/macroeconomia/datos_gob_client.py` — fetch +
   caché en disco por `id` de serie, sin transformar. Se construye una sola
   vez y sirve para todo el catálogo, no solo para canasta básica.
2. **`data/macroeconomia/catalogo_series.csv`** — una fila **por concepto**
   (no por mes) de la sección 3 (los confirmados; los pendientes de la
   sección 6 se agregan cuando se resuelvan), con: concepto lógico, id en
   datos.gob.ar, periodicidad de la fuente, cobertura real,
   auditable_estadisticasbcra (sí/no + id equivalente si corresponde). Sin
   columna de región — alcance nacional únicamente.
3. **`src/macroeconomia/series.py`** — lee el catálogo + los JSON cacheados,
   valida unidad/periodicidad, y arma `series_macro_2011_2025.csv` **una
   fila por mes**: por cada concepto y cada mes del rango 2011-2025, si la
   fuente tiene un dato con fecha de origen exactamente ese mes lo usa; si
   no, la celda queda vacía y `observaciones` deja constancia; si la fuente
   es diaria, la agrega a mensual con el último valor hábil del mes (o
   queda vacía si ningún día hábil de ese mes tiene dato). Nunca repite un
   valor de un mes anterior (decisión revisada — ver "Rediseño posterior"
   al inicio de este documento). Reporta cobertura (qué % de celdas se
   resolvió con dato real vs. vacías) siguiendo el patrón `ReporteCobertura`
   de `src/electoral/localidades.py`.
4. **Piloto concreto primero: canasta básica.** Antes de cargar las ~20
   filas del catálogo completo, se implementa y prueba el flujo completo
   (cliente → catálogo → normalización a fila-por-mes → CSV → doc) solo con
   CBA/CBT nacional, como caso acotado que valida el diseño del cliente
   genérico y de la lógica de celdas vacías/`observaciones` antes de
   escalarlo
   al resto del catálogo.
5. **Auditoría contra `estadisticasbcra.com`** — una corrida manual, al
   cerrar cada tramo del catálogo, comparando el último año-mes que ambas
   fuentes tengan en común (no necesariamente el más reciente de nuestra
   serie — ver hallazgo de atraso más abajo) para cada concepto auditable.
   Implementada en `src/macroeconomia/auditoria_estadisticasbcra.py`
   (requiere token propio, nunca se guarda en el repo). Se documenta el
   resultado (coincide / difiere y por cuánto) en
   `SISTEMATIZACION_VARIABLES_MACRO.md` §3, no se automatiza como parte del
   pipeline regular. **Corrida el 2026-08-07**: corrigió un mapeo de
   catálogo (`tipo_cambio_oficial` apuntaba al dólar informal, no al
   oficial) y encontró que estadisticasbcra.com está atrasada entre ~1,5 y
   2 años según el endpoint — limita su utilidad a auditar tramos
   históricos ya cerrados, no los datos más recientes del CSV.
6. **Tests** de la parte pura (resolución de catálogo, normalización,
   reporte de cobertura) — sin red, mismo split que ya tiene el repo entre
   cliente (sin test) y lógica de parseo/agregación (con test).
7. **Documentación**: `SISTEMATIZACION_VARIABLES_MACRO.md` (formato EPH),
   actualizar README y `CLAUDE.md` con el nuevo dominio y comandos, y
   versionar como **MAJOR** al mergear (nuevo dominio analítico, mismo
   criterio que el salto v1→v2 al sumar socioeconomía).

---

## 6. Pendientes de validación

Ninguno — los seis pendientes originales quedaron todos cerrados: tasa de
actividad, unidad de CBA/CBT, PBI total y tipo de cambio se resolvieron con
id confirmado; resultado fiscal y pobreza/indigencia moderna se omitieron
por decisión explícita (sección 7). El catálogo queda cerrado con lo
confirmado en la sección 3.

**Nota de método, para reutilizar en el resto del catálogo**: filtrar por
`dataset_theme` (ej. `apis.datos.gob.ar/series/api/search/?dataset_theme=Dinero%20y%20Bancos`)
da resultados mucho más limpios y mejor etiquetados que buscar por texto
libre (`q=...`) — así se encontraron los ids definitivos de tipo de cambio,
reservas y base monetaria, reemplazando ids más ambiguos que había dejado
una revisión anterior de este plan. Si en el futuro hace falta revisar o
reconfirmar algún id del catálogo, empezar por el tema correspondiente
(`Dinero y Bancos`, `Precios`, `Trabajo e ingresos`, etc.) antes que por
texto libre.

---

## 7. Fuera de alcance de este plan

- **Resultado fiscal real (primario/financiero)** — omitido por decisión
  explícita. Lo único encontrado había sido la mediana de expectativas del
  REM (BCRA), no un dato de ejecución real; se prefiere no incluir un
  proxy de expectativas bajo el nombre de una variable que sugeriría un
  dato efectivamente ejecutado. Gasto en servicios de deuda pública (3.6)
  sí queda dentro del catálogo — es un dato real, solo que parcial (una
  función de gasto, no el resultado fiscal completo).
- **Pobreza e indigencia moderna (2016-presente)** — omitido por decisión
  explícita. INDEC sigue publicando el dato (informe semestral "Incidencia
  de la pobreza y la indigencia en 31 aglomerados urbanos"), pero no se
  ubicó el id exacto del total de 31 aglomerados en `datos.gob.ar` (lo que
  apareció fue solo la apertura "aglomerados del interior país", parcial).
  Se prefiere dejarlo fuera del catálogo antes que cargar un id que en
  verdad corresponde a un universo distinto (interior sin GBA) bajo el
  nombre de la cifra total del país.
- **Apertura regional o provincial** (ej. CBA/CBT por región EPH) — aunque
  varias fuentes la ofrecen, el alcance de este plan es nacional
  exclusivamente. Si más adelante se necesita comparar contra Gran La Plata
  específicamente, es una extensión a evaluar aparte, no parte de este plan.
- Cruce de CBA/CBT o cualquier variable macro contra los ingresos EPH de
  Gran La Plata ya existentes en el repo — es el follow-up analítico
  natural, pero es un paso posterior y separado, no parte de "obtener los
  datos".
- Sumar riesgo país vía una cuarta fuente — requiere autorización explícita
  aparte.
- Cualquier gráfico o visualización de estas series — este plan cubre
  únicamente adquisición y documentación de los datos.
