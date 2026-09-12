# Datos relevados pero no usables para el panel (cobertura insuficiente)

Complementa a `inventario_fuentes_datos.md`: acá viven las fuentes y
variables relevadas para el proyecto que **no cubren al menos el 80% del
período 2001-2025** (20 de 25 años) — el criterio adoptado para decidir
qué vale la pena mantener evaluado en el inventario principal. No se
descartan por mala calidad; se descartan porque, aunque existieran datos
perfectos, la ventana de años disponible es demasiado corta para aportar
al panel completo. Se conservan acá (no se borran) porque documentan un
relevamiento real, con su fuente y URL, por si en el futuro cambia el
criterio o aparece una serie empalmada que extienda la cobertura hacia atrás.

**Método:** cobertura = años reales con dato dentro de 2001-2025, tomados
de la fecha de inicio declarada en `inventario_fuentes_datos.md` (o, para
períodos con reservas/empalme, la fecha de la serie oficial limpia, no el
empalme de terceros). `< 20 años` (80% de 25) → se mueve acá.

---

## Fuentes completas que se mueven (el ítem entero no llega al 80%)

### CBA/CBT (INDEC) — Canasta Básica Alimentaria y Total

**Fuente:** INDEC, Dirección de Índices de Precios de Consumo. https://www.indec.gob.ar/

**Cobertura real:** serie oficial limpia desde abr 2016 = **10 de 25 años (40%)**. Empalmes anteriores existen vía FIEL y CEDLAS (terceros, no INDEC), no se cuentan como serie oficial equivalente.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Valor de la CBA (adulto equivalente) | Mensual | Abr 2016–presente (serie oficial limpia); empalmes anteriores disponibles vía FIEL y CEDLAS | GBA | Define la línea de indigencia |
| Valor de la CBT (adulto equivalente) | Mensual | Ídem | GBA | Define la línea de pobreza |
| Coeficiente de Engel (inversa) | Mensual | Ídem | GBA | Relación CBA/CBT |
| Valores para hogar tipo (3, 4, 5 integrantes) | Mensual | Ídem | GBA | Permite expresar el umbral en términos más concretos |

**Relevancia (si algún día se extiende la cobertura):** La CBT/CBA en relación al ingreso medio o al RIPTE da un indicador directo de cuántos hogares (o qué proporción del ingreso) se necesita para cubrir necesidades básicas.

---

### Relevamiento de Expectativas de Mercado (REM) — BCRA

**Fuente:** BCRA. https://www.bcra.gob.ar/relevamiento-expectativas-mercado-rem/

**Cobertura real:** relanzado jul 2016 = **~9 de 25 años (36%)**.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Expectativas de inflación (mensual, interanual, próximos 12 y 24 meses) | Mensual | Jul 2016–presente | Mediana y Top 10 |
| Expectativas de tipo de cambio nominal | Mensual | Jul 2016–presente | Promedio mensual $/USD |
| Expectativas de tasa de interés (TAMAR) | Mensual | Jul 2016–presente | |
| Expectativas de desocupación | Mensual | Jul 2016–presente | Trimestral prospectiva |
| Expectativas de PIB | Mensual | Jul 2016–presente | Variación anual |
| Expectativas de resultado fiscal primario | Mensual | Jul 2016–presente | |
| Expectativas de exportaciones e importaciones | Mensual | Jul 2016–presente | |

**Relevancia (si algún día se extiende la cobertura):** La literatura de voto económico prospectivo (MacKuen, Erikson & Stimson) sugiere que la diferencia entre expectativa y realización podría ser un predictor más fuerte que el dato realizado.

---

### Observatorio de la Deuda Social Argentina (ODSA) — UCA

**Fuente:** Universidad Católica Argentina. https://uca.edu.ar/es/observatorio-de-la-deuda-social-argentina

**Cobertura real:** variables publicadas desde 2010 (Bicentenario 2010-2016 + Agenda 2017-2025) = **16 de 25 años (64%)**; "estrés económico/social/subjetivo" desde 2023 = 3 años (12%).

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Pobreza multidimensional (carencias en derechos) | Anual | 2010–presente | Nacional urbano, con desagregación regional | No solo ingreso: vivienda, salud, educación, empleo |
| Inseguridad alimentaria | Anual | 2010–presente | Nacional urbano | Indicador extremo de malestar material |
| Percepción de insuficiencia de ingresos | Anual | 2010–presente | Nacional urbano | % hogares que perciben que sus ingresos no alcanzan |
| Capacidad de ahorro percibida | Anual | 2010–presente | Nacional urbano | Indicador de bienestar económico subjetivo |
| Malestar psicológico (ansiedad, depresión) | Anual | 2010–presente | Nacional urbano | Dimensión de bienestar subjetivo |
| Estrés económico, social y subjetivo | Anual | 2023–presente | Nacional urbano | Nuevo en la EDSA 2025 |

**Relevancia (si algún día se extiende la cobertura):** Aporta dimensiones de malestar subjetivo que los indicadores macro no capturan.

---

### Tipo de cambio paralelo ("dólar blue") — Fuentes no oficiales

**Fuente:** Ámbito Financiero (ambito.com/contenidos/dolar.html), dolarblue.net, series históricas compiladas por investigadores y portales financieros.

**Cobertura real:** ~2011–presente = **15 de 25 años (60%)**; pre-2011 la brecha era marginal, tratable como cero, pero no hay serie estimable con la misma calidad.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Cotización del dólar paralelo (blue) | Diaria | ~2011–presente (con cobertura más firme desde 2012) | No es dato oficial; no existe fuente única canónica |
| Brecha cambiaria (% diferencia blue vs. oficial) | Diaria | Calculable desde 2011 | Indicador de distorsión cambiaria y desconfianza |

**Relevancia (si algún día se extiende la cobertura):** La brecha cambiaria fue tema central del discurso público en los períodos de cepo (2011-2015, 2019-2023).

---

### INDEC — Índice de Salarios (IS)

**Fuente:** INDEC. https://www.indec.gob.ar/

**Cobertura real:** desde oct 2016 = **~9 de 25 años (36%)**. Mismo hueco que el corte "CVS/Índice de Salarios" mencionado dentro de RIPTE en `inventario_fuentes_datos.md` — es la misma fuente, un solo relevamiento.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Índice de Salarios nivel general | Mensual | Oct 2016–presente | Compuesto: privado registrado + público + privado no registrado |
| IS sector privado registrado | Mensual | Oct 2016–presente | Incluye paritarias |
| IS sector público | Mensual | Oct 2016–presente | Salarios estatales |
| IS sector privado no registrado | Mensual | Oct 2016–presente | Única serie oficial de salarios informales |

**Relevancia (si algún día se extiende la cobertura):** El componente de empleo no registrado es la única serie oficial de salarios informales — relevante para los sectores más reactivos electoralmente.

---

### Encuesta Nacional de Gastos de los Hogares (ENGHo) — INDEC

**Fuente:** INDEC. Se realiza cada ~10 años (2004/05, 2012/13, 2017/18). La próxima está en planificación.

**Cobertura real:** 3 relevamientos discretos en 25 años, no una serie continua — no aporta observaciones dentro de la mayoría de las ventanas electorales.

**Relevancia (si algún día se extiende la cobertura):** Útil solo como referencia de estructura de consumo para contextualizar qué mide el IPC, no como input del modelo.

---

### Censos Nacionales de Población (2001, 2010, 2022) — INDEC

**Fuente:** INDEC. Datos desagregados a nivel de radio censal, fracción, departamento.

**Cobertura real:** 3 puntos discretos en 25 años.

**Relevancia (si algún día se retoma el panel espacial):** Los datos a nivel de radio censal (NBI, vivienda, educación, composición demográfica) podrían servir para un análisis secundario por localidad (D8, panel espacial conservado como análisis secundario), no para el panel temporal principal.

---

## Variables específicas que se mueven (el resto del ítem se queda en `inventario_fuentes_datos.md`)

### EPH — Incidencia de pobreza/indigencia y Gini/brecha trimestral

Del ítem 2 (EPH) de `inventario_fuentes_datos.md`. Se muda solo esto —
las tasas de actividad/empleo/desocupación/subocupación/informalidad de
ese mismo ítem cubren 2003-presente (con EPH puntual 2001-2002) y se
quedan.

| Variable | Periodicidad | Cobertura temporal | Cobertura real |
|---|---|---|---|
| Incidencia de pobreza e indigencia (personas y hogares) | Semestral | 2do semestre 2016–presente (empalme ODSA-UCA desde 2010) | 10-16 de 25 años (40-64%) |
| Coeficiente de Gini del ingreso per cápita familiar | Trimestral | 3T 2021–presente | 5 de 25 años (20%) |
| Brecha de ingresos decil 10 / decil 1 | Trimestral | 3T 2021–presente | 5 de 25 años (20%) |

**Alternativa que sí cumple:** `inventario_fuentes_datos.md` ítem 13
(CEDLAS) publica Gini y pobreza empalmados desde 1974/1992 — es la
fuente a usar para estas dos dimensiones, no la serie EPH oficial directa.

### BCRA — Brecha cambiaria

Del ítem 3 (BCRA). El resto del ítem (tipo de cambio oficial/minorista,
variables monetarias, sector externo) tiene series largas y se queda.

| Variable | Periodicidad | Cobertura temporal | Cobertura real |
|---|---|---|---|
| Brecha cambiaria (oficial vs. paralelo) | Diaria | Calculable desde ~2011 | 15 de 25 años (60%) |

Es la misma limitación que el ítem "dólar blue" de arriba — el BCRA no
publica el paralelo, así que esta fila depende de esa misma fuente no oficial.

### RIPTE/CVS — Índice de Salarios y CVS (INDEC)

Del ítem 9 (RIPTE y CVS). RIPTE (Jul 1994–presente, cobertura completa)
se queda; el Índice de Salarios y el CVS son la misma fuente que el ítem
"Índice de Salarios (IS)" de arriba, duplicada en ese ítem 9 — no se
repite la tabla acá, ver esa entrada.

---

## Nota sobre el corte departamental de OEDE

`inventario_fuentes_datos.md` ítem 11 (OEDE) se queda entero porque la
serie **provincial** (PBA) cubre 1996-presente. El corte **departamental**
(Partido de La Plata específicamente) solo existe desde 2019 (~7 de 25
años, 28%) — no cumple el 80%, pero no se separó en una entrada propia
acá porque comparte fila de tabla con la serie provincial en el ítem
original; queda documentado ahí mismo como limitación, no como fuente
recomendada para el panel completo.
