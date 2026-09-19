# Inventario de fuentes de datos disponibles

## Proyecto: Condiciones macroeconómicas y comportamiento electoral en el Partido de La Plata (2001–2025)

### Contexto de uso

Este inventario detalla todas las variables extraíbles de las fuentes ya identificadas para el proyecto, más fuentes adicionales relevantes no contempladas originalmente. Cada variable se evalúa en función de tres criterios operativos para el diseño de panel de ventanas electorales:

- **Periodicidad**: qué tan frecuente es la serie (diaria, mensual, trimestral, semestral, anual).
- **Cobertura temporal**: desde cuándo hay datos consistentes — el corte del panel es 2001.
- **Nivel geográfico**: si el dato es nacional, provincial (PBA), de aglomerado (Gran La Plata), o de partido (La Plata).

La estructura del panel requiere variables que puedan agregarse dentro de ventanas de ~24 o ~48 meses entre elecciones. Variables con periodicidad mensual o trimestral son ideales; variables anuales solo aportan 1-2 puntos por ventana y limitan el tipo de agregación posible (no permiten calcular tendencia o volatilidad intraventana).

**Criterio de inclusión — cobertura mínima:** solo se mantienen acá las
fuentes/variables con al menos el 80% de cobertura real dentro de
2001-2025 (20 de 25 años). Lo que releva pero no cumple ese piso vive en
`docs/especificaciones/datos_relevados_no_usables.md`, no se descarta —
queda documentado por si en el futuro cambia el criterio o aparece un
empalme que extienda la cobertura hacia atrás.

**Nota (post-implementación):** este documento es la evaluación previa a
la decisión de qué incorporar. `icg`, `desocupacion`, `ipc`, `tc_oficial`,
`reservas`, `icc`, `emae`, `salario_real` y `resultado_fiscal` (Parte I y
parte de la Parte II) ya están adoptadas — su cobertura real y estado
vigente vive en `data/tfi_data/registro_variables.csv` y
`data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md`, no acá (la
evaluación previa completa, `plan_macroeconomia.md`, quedó como trabajo
interno no versionado). El resto de la
Parte II y toda la Parte III siguen siendo candidatas sin incorporar — ver
también la lista corta en `especificacion_panel_temporal.md` §4.3.

---

## PARTE I: FUENTES YA IDENTIFICADAS

---

### 1. INDEC — Índice de Precios al Consumidor (IPC)

**Fuente:** Instituto Nacional de Estadística y Censos, https://www.indec.gob.ar/

**Nota metodológica crítica:** La serie del IPC tiene discontinuidades conocidas. De 2007 a 2015, las estadísticas oficiales del INDEC fueron intervenidas y son consideradas no confiables (la propia institución publicó reservas sobre el período). Desde junio de 2016 se publica el IPC-GBA (base dic 2016=100), y desde julio de 2017 se amplió a cobertura nacional con seis regiones. Para el período 2007-2015 existen índices alternativos (IPC Congreso, IPC provincias, consultoras privadas) que la literatura académica argentina utiliza como empalme, pero que introducen su propio error de medición. La serie empalmada desde 1943 existe para GBA (IPC-GBA base abril 2008=100, empalmando bases 1943, 1960, 1974, 1988, 1999), pero su confiabilidad para el subperíodo 2007-2015 requiere documentación metodológica explícita.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| IPC nivel general (índice, base dic 2016=100) | Mensual | Jun 2016–presente | Nacional + 6 regiones (incl. GBA y Pampeana) | Serie principal post-normalización |
| IPC nivel general — serie empalmada histórica | Mensual | 1943–presente (con reservas 2007-2015) | GBA | Empalme de 6 bases; usar con cautela 2007-2015 |
| Variación mensual del IPC (inflación mensual) | Mensual | Desde 2016 (limpia) o empalme desde antes | Ídem | Derivable del índice |
| Variación interanual del IPC (inflación interanual) | Mensual | Ídem | Ídem | Derivable del índice |
| Inflación acumulada en un período | Calculable | Ídem | Ídem | Agregación dentro de ventana electoral |
| IPC por división (12 divisiones COICOP) | Mensual | Jul 2017–presente | Nacional + 6 regiones | Alimentos y bebidas, transporte, vivienda, salud, etc. |
| IPC regulados vs. estacionales vs. núcleo | Mensual | Jul 2017–presente | Nacional + 6 regiones | Permite distinguir inflación de precios controlados vs. de mercado |

**Relevancia para el proyecto:** Variable central para H1. La inflación es el indicador más directo de "sufrimiento económico" percibido por el electorado. Para el panel 2001-2025, se necesita la serie empalmada; la discontinuidad 2007-2015 debe documentarse como limitación. La desagregación por división permite construir indicadores más finos (ej. inflación en alimentos como proxy de impacto en sectores vulnerables).

**Derivaciones posibles para la ventana electoral:**
- Inflación acumulada en la ventana (24 o 48 meses)
- Inflación promedio mensual de la ventana
- Tendencia (pendiente de la inflación dentro de la ventana — ¿acelerando o desacelerando?)
- Volatilidad (desvío estándar mensual dentro de la ventana)
- Valor del último trimestre antes de la elección (efecto recencia)

---

### 2. INDEC — Encuesta Permanente de Hogares (EPH)

**Fuente:** Instituto Nacional de Estadística y Censos, https://www.indec.gob.ar/

**Nota metodológica crítica:** Hasta mayo 2003 la EPH era puntual (dos ondas: mayo y octubre). Desde el tercer trimestre de 2003 es continua (trimestral). Las series publicadas entre 1T 2007 y 4T 2015 están sujetas a reservas por intervención del INDEC. El aglomerado Gran La Plata (código 2) incluye los partidos de La Plata, Berisso y Ensenada — no coincide exactamente con el Partido de La Plata, pero es el proxy más fino disponible sin procesar microdatos. Durante 3T 2007, Gran La Plata no fue relevado (causas administrativas).

**Variables extraíbles — indicadores publicados por aglomerado:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Tasa de actividad | Trimestral | 2003–presente (puntual antes) | Aglomerado Gran La Plata | % PEA / Población total |
| Tasa de empleo | Trimestral | Ídem | Aglomerado Gran La Plata | % Ocupados / Población total |
| Tasa de desocupación | Trimestral | Ídem | Aglomerado Gran La Plata | % Desocupados / PEA |
| Tasa de subocupación (demandante y no demandante) | Trimestral | Ídem | Aglomerado Gran La Plata | Ocupados que trabajan menos de 35 hs y quieren trabajar más |
| Tasa de empleo no registrado (informalidad) | Trimestral | Ídem | Aglomerado Gran La Plata | Asalariados sin descuento jubilatorio |
| Ingreso medio y mediano de la ocupación principal | Trimestral | Publicado regularmente | Por aglomerado (disponible para Gran La Plata en microdatos) | Requiere procesamiento de microdatos para Gran La Plata específico |

**Variables extraíbles — procesamiento de microdatos EPH (Gran La Plata, código 2):**

Los microdatos trimestrales de la EPH (bases individuales y de hogares) están disponibles para descarga pública. Filtrando por APTS=2 (Gran La Plata) se pueden construir:

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Distribución del ingreso per cápita familiar (deciles, quintiles) | Trimestral | 2003–presente | Permite calcular Gini específico de Gran La Plata |
| Ingreso laboral real (deflactado por IPC) | Trimestral | 2003–presente | Proxy de salario real del aglomerado |
| Composición del empleo por calificación ocupacional | Trimestral | 2003–presente | Permite ver precarización vs. mejora de calidad del empleo |
| Tasa de asalarización, cuentapropismo, patrones | Trimestral | 2003–presente | Estructura del mercado laboral local |
| Acceso a cobertura de salud, educación | Trimestral | 2003–presente | Variables sociales complementarias |

**Pobreza, indigencia y Gini/brecha trimestral — movidos.** La incidencia de pobreza/indigencia oficial (2do semestre 2016, empalme ODSA desde 2010) y el Gini/brecha de ingresos trimestral de la EPH (desde 3T 2021) no llegan al 80% de cobertura — ver `datos_relevados_no_usables.md`. Para Gini y pobreza con cobertura completa, usar el ítem 10 (CEDLAS) de este documento.

**Herramientas de procesamiento:** El paquete `eph` de R (rOpenSci) permite descargar y procesar microdatos automáticamente, incluyendo cálculo de pobreza con canastas regionales. CEDLAS (UNLP) publica series procesadas a partir de EPH con desagregación por aglomerado y región en su portal ISA (Indicadores Socioeconómicos de Argentina).

**Relevancia para el proyecto:** La desocupación es, junto con la inflación, la variable central de H1 en la literatura de voto económico. La serie de Gran La Plata permite capturar la coyuntura del mercado laboral local como proxy de La Plata.

---

### 3. Banco Central de la República Argentina (BCRA)

**Fuente:** https://www.bcra.gob.ar/

El BCRA publica un catálogo de más de 1.100 series estadísticas en formato TXT descargable, con metadatos de descripción, unidad de medida, periodicidad y cobertura temporal. Las series más relevantes para el proyecto son las siguientes:

**Variables de tipo de cambio:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Tipo de cambio de referencia ($/USD, Com. A 3500) | Diaria | Feb 2003–presente | Cotización oficial mayorista; promediable por mes |
| Tipo de cambio minorista ($/USD, Com. B 9791) | Diaria | Disponible | Cotización para público general |

**Brecha cambiaria (oficial vs. paralelo) — movida.** Solo calculable desde ~2011 (60% de cobertura); depende además de una fuente no oficial para el paralelo. Ver `datos_relevados_no_usables.md`.

**Variables monetarias y financieras:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Base monetaria | Diaria | Serie larga disponible | Indicador de política monetaria expansiva/contractiva |
| Reservas internacionales | Diaria | Serie larga disponible | Indicador de solvencia externa; muy saliente en crisis |
| Tasa de interés de referencia (BADLAR, TAMAR, tasa de política monetaria) | Diaria/Mensual | Serie larga disponible | BADLAR: depósitos >$1M, 30-35 días; relevante como proxy de costo del crédito |
| Depósitos totales del sistema financiero (en pesos y en dólares) | Mensual | Serie larga disponible | Indicador de confianza en el sistema bancario |
| Préstamos al sector privado | Mensual | Serie larga disponible | Indicador de acceso al crédito |
| Circulante en poder del público | Diaria | Serie larga disponible | Componente de la base monetaria |

**Variables del sector externo:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Balance comercial (exportaciones e importaciones FOB/CIF) | Mensual | Serie larga disponible | Relevante como indicador macro de contexto, no como causa directa |

**Relevancia para el proyecto:** El tipo de cambio es una variable altamente saliente para el electorado argentino. La devaluación del peso (medida como variación del tipo de cambio oficial) puede funcionar como shock económico percibido con impacto electoral directo. Las reservas son un leading indicator de crisis cambiarias.

---

### 4. Ministerio de Economía — Portal de datos abiertos (datos.gob.ar)

**Fuente:** https://datos.gob.ar/ y https://www.economia.gob.ar/datos/

El portal concentra más de 1.200 datasets de múltiples organismos. Los más relevantes para el proyecto:

**Variables fiscales y de gasto público:**

| Variable/Dataset | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Informe Mensual de Ingresos y Gastos del SPN no financiero (IMIG) | Mensual | 2001–presente | Nacional (SPN) | Ingresos tributarios, gasto primario, resultado fiscal primario y financiero |
| Gasto Público Consolidado (GPC) | Anual | 1980–2023 (última actualización) | Nacional, provincial y municipal | Desagregado por finalidad-función (servicios sociales, económicos, etc.) y nivel de gobierno |
| Gasto público del Gobierno Nacional en programas de seguridad social y transferencias | Trimestral | Disponible | Nacional | Incluye AUH, jubilaciones, pensiones |
| Resultado fiscal primario del SPN | Mensual | 2001–presente | Nacional | Variable central en el discurso político argentino reciente |

**Variables de actividad económica:**

| Variable/Dataset | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Series del EMAE disponibles vía API de datos.gob.ar | Mensual | 2004–presente | Nacional | Accesible también directo de INDEC |

**Relevancia para el proyecto:** El resultado fiscal (superávit/déficit) y el gasto social son variables relevantes como indicadores de política económica del oficialismo. Su nivel geográfico es nacional, no local, lo cual es coherente con el diseño de panel temporal por distrito donde todas las variables económicas son igualmente nacionales.

---

### 5. Índice de Confianza en el Gobierno (ICG) — Universidad Torcuato Di Tella

**Fuente:** Escuela de Gobierno, UTDT. https://www.utdt.edu/icg

**Descripción:** Encuesta mensual de opinión pública que mide la confianza de la sociedad en el gobierno nacional. Se publica ininterrumpidamente desde noviembre de 2001. Elaborado por Poliarquía Consultores. Muestra de ~1.000 casos en ~40 localidades de todo el país, representativa a nivel nacional. Escala de 0 (mínima confianza) a 5 (máxima confianza).

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| ICG nivel general | Mensual | Nov 2001–presente | Nacional | Índice compuesto de 5 dimensiones |
| Evaluación general del gobierno | Mensual | Nov 2001–presente | Nacional | Subíndice: imagen global |
| Preocupación por el interés general | Mensual | Nov 2001–presente | Nacional | Subíndice: ¿gobierna para todos o para sectores? |
| Eficiencia en la administración del gasto público | Mensual | Nov 2001–presente | Nacional | Subíndice |
| Honestidad de los funcionarios | Mensual | Nov 2001–presente | Nacional | Subíndice |
| Capacidad del gobierno para resolver problemas | Mensual | Nov 2001–presente | Nacional | Subíndice |
| Desagregación por región (CABA, GBA, Interior) | Mensual | Disponible | Regional | La desagregación fina (por localidad) tiene costo |
| Desagregación por sexo, edad, nivel educativo | Mensual | Disponible | Nacional | Permite análisis de heterogeneidad en percepción |

**Relevancia para el proyecto:** Esta es posiblemente la variable más importante del proyecto después de los indicadores económicos duros, porque captura directamente la percepción del electorado sobre el gobierno — que es el mecanismo causal intermedio entre economía y voto en la teoría del voto económico. El ICG es un indicador de percepción/confianza conceptualmente distinto de la inflación o el desempleo: mide cómo el votante *evalúa* al gobierno, no cómo *está* la economía. La serie arranca justo en noviembre de 2001, coincidiendo con el corte temporal del panel.

**Acceso a datos:** Las series históricas del ICG general y desagregado por región y subíndice se descargan gratuitamente desde el sitio de la UTDT. La información más detallada tiene costo. Contacto: cgervasoni@utdt.edu (Prof. Carlos Gervasoni, UTDT).

---

## PARTE II: FUENTES ADICIONALES RELEVANTES

---

### 6. Índice de Confianza del Consumidor (ICC) — Universidad Torcuato Di Tella

**Fuente:** Centro de Investigación en Finanzas (CIF), UTDT. https://www.utdt.edu/ver_contenido.php?id_contenido=2575&id_item_menu=4982

**Descripción:** Encuesta mensual que mide las percepciones de los individuos sobre el estado de la economía, su situación económica personal y las expectativas a mediano plazo. Se publica desde 1998. Elaborado por Poliarquía Consultores en ~40 aglomerados urbanos. Metodología inspirada en el Consumer Confidence Index de la Universidad de Michigan (EE.UU.).

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| ICC nivel general | Mensual | 1998–presente | Nacional | Escala 0-100 |
| Subíndice: Situación personal (retrospectiva y prospectiva) | Mensual | 1998–presente | Nacional | ¿Mejoró o empeoró tu situación vs. hace un año? ¿Mejorará en un año? |
| Subíndice: Situación macroeconómica (1 y 3 años) | Mensual | 1998–presente | Nacional | ¿Será mejor o peor la economía del país en 1/3 años? |
| Subíndice: Compras de bienes durables e inmuebles | Mensual | 1998–presente | Nacional | ¿Buen momento para comprar electrodomésticos? ¿Para comprar auto/casa? |
| Desagregación por región (CABA, GBA, Interior) | Mensual | Disponible | Regional | Serie histórica descargable gratuitamente |
| Desagregación por nivel socioeconómico y edad | Mensual | Disponible | Nacional | Información más detallada tiene costo |

**Relevancia para el proyecto:** Complementa al ICG con un ángulo distinto: el ICG mide confianza en el gobierno, el ICC mide percepción económica de los hogares. En la literatura de voto económico, la distinción entre voto sociotrópico (cómo percibo que está el país) y voto egotrópico (cómo percibo que estoy yo) es central — el ICC captura ambas dimensiones separadamente.

**Acceso a datos:** Series históricas del ICC y desagregación por región y subíndices descargables gratuitamente desde la página del CIF-UTDT. Información más desagregada tiene costo.

---

### 7. INDEC — Estimador Mensual de Actividad Económica (EMAE)

**Fuente:** INDEC, Dirección Nacional de Cuentas Nacionales. https://www.indec.gob.ar/

**Descripción:** Indicador provisorio de la evolución del PIB a precios constantes (base 2004=100). Se difunde con un rezago de 50-60 días. Es un índice Laspeyres que agrega el valor agregado a precios básicos de cada actividad económica. Es mensual, a diferencia del PIB trimestral.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| EMAE nivel general (índice, base 2004=100) | Mensual | Ene 2004–presente | Nacional | Serie original, desestacionalizada y tendencia-ciclo |
| Variación interanual del EMAE | Mensual | Ene 2004–presente | Nacional | Proxy de crecimiento/recesión mensual |
| EMAE por sector de actividad (16 sectores) | Mensual | Ene 2004–presente | Nacional | Agricultura, industria, construcción, comercio, etc. |

**Relevancia para el proyecto:** Es el proxy mensual más directo de "cómo va la economía" en términos de actividad real. Cubre desde 2004 (88% del período), por lo que pierde los primeros años del panel (2001-2003).

---

### 8. RIPTE — Ministerio de Trabajo

**Fuente:** Secretaría de Trabajo, Empleo y Seguridad Social.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| RIPTE (Remuneración Imponible Promedio de Trabajadores Estables) | Mensual | Jul 1994–presente | Nacional | Solo empleo registrado con 13+ meses de antigüedad; no refleja empleo informal |

**El Índice de Salarios y el CVS (INDEC) — movidos.** Solo cubren desde oct 2016 (36%), ver `datos_relevados_no_usables.md`.

**Relevancia para el proyecto:** El salario real (RIPTE deflactado por IPC) es probablemente el indicador más directo de poder adquisitivo. Su evolución dentro de la ventana electoral captura si los trabajadores están "ganándole a la inflación" o no — una pregunta central en el voto económico egotrópico. Para todo el período 2001-2025, el RIPTE es la única serie mensual de salarios disponible a nivel nacional con cobertura completa.

**Derivación clave:** Salario real = RIPTE / IPC. Esta serie derivada permite calcular, dentro de cada ventana, si el salario real subió, bajó, cuánto y con qué tendencia.

---

### 9. OEDE — Observatorio de Empleo y Dinámica Empresarial (Ministerio de Trabajo)

**Fuente:** Dirección Nacional de Estadísticas y Estudios Laborales. https://www.argentina.gob.ar/trabajo/estadisticas/oede-estadisticas-provinciales

**Descripción:** Construye indicadores a partir de registros administrativos del SIPA (Sistema Integrado Previsional Argentino), el padrón de contribuyentes y Simplificación Registral. Permite desagregación provincial y, desde 2019, departamental.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Empleo asalariado registrado privado | Trimestral/Mensual | ~1996–presente | Provincial (PBA) | Basado en SIPA. El corte departamental (Partido de La Plata, desde 2019, ~28% de cobertura) no cumple el piso del 80% — ver `datos_relevados_no_usables.md` |
| Remuneración promedio de trabajadores registrados | Trimestral/Mensual | ~1996–presente | Provincial | Nominal; deflactar por IPC |
| Cantidad de empresas empleadoras | Trimestral | ~1996–presente | Provincial | Indicador de dinámica empresarial |
| Tasa de entrada y salida de empresas | Trimestral | ~1996–presente | Provincial | Apertura y cierre de empresas |
| Empleo por sector de actividad (CIIU) | Trimestral | ~1996–presente | Provincial | Permite ver estructura productiva |

**Relevancia para el proyecto:** La serie provincial (PBA) cubre el período completo y es un proxy razonable para un distrito de la conurbación bonaerense que es capital provincial. La dinámica empresarial (apertura/cierre de empresas) captura una dimensión del malestar económico distinta del desempleo.

---

### 10. CEDLAS (Centro de Estudios Distributivos, Laborales y Sociales) — UNLP

**Fuente:** Facultad de Ciencias Económicas, UNLP. https://www.cedlas.econo.unlp.edu.ar/wp/estadisticas/isa/

**Descripción:** Procesa microdatos de la EPH y publica series de indicadores sociolaborales (ISA — Indicadores Socioeconómicos de Argentina) con desagregación por aglomerado y región, empalmando discontinuidades metodológicas.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Coeficiente de Gini por aglomerado y región | Semestral/Trimestral | 1974–presente (con empalmes) | Serie empalmada larga, útil para tendencia histórica |
| Brecha de ingresos decil 10/decil 1 | Trimestral | Disponible | |
| Ingreso laboral por nivel educativo y región | Semestral | Disponible | Deflactado por línea de pobreza regional |
| Tasa de pobreza empalmada (serie larga) | Semestral | 1992–presente | Empalme propio del CEDLAS |
| Retornos a la educación | Anual | Disponible | Indicador estructural, no coyuntural |

**Relevancia para el proyecto:** El valor principal del CEDLAS es que produce series empalmadas de indicadores que el INDEC no empalma oficialmente (especialmente para el período 2007-2015) y con cobertura completa del panel 2001-2025 — es la fuente a usar para Gini y pobreza, no la serie EPH oficial directa (ver nota en el ítem 2). Además, al estar en la UNLP, hay acceso institucional directo.

---

### 11. Resultado fiscal primario — Secretaría de Hacienda

**Fuente:** Ministerio de Economía, Secretaría de Hacienda. Series disponibles vía datos.gob.ar y Oficina Nacional de Presupuesto (https://www.economia.gob.ar/onp/estadisticas/).

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Resultado primario del SPN no financiero | Mensual | 1993–presente | Nacional | Superávit/déficit antes de intereses |
| Resultado financiero del SPN | Mensual | 1993–presente | Nacional | Incluye pago de intereses de deuda |
| Ingresos tributarios nacionales | Mensual | 1993–presente | Nacional | IVA, Ganancias, derechos de exportación, etc. |
| Gasto primario del SPN | Mensual | 1993–presente | Nacional | Jubilaciones, salarios, transferencias, capital |

**Relevancia para el proyecto:** El resultado fiscal es una variable de política económica del oficialismo que el votante puede (o no) percibir. Su inclusión es relevante como control o como moderador, no necesariamente como predictor principal.

---

## PARTE III: FUENTES DE POTENCIAL INTERÉS COMPLEMENTARIO

---

### 12. Datos electorales — Dirección Nacional Electoral / Junta Electoral PBA

**Fuente:** Atlas Electoral de Andy Tow (andy.towsa.com), datos abiertos del Ministerio del Interior (datos.gob.ar), DINE.

**Variables:** Resultado total del Partido de La Plata para intendente, gobernador y presidente (2001-2025). Estas variables ya están parcialmente en el repositorio (`data/distrito/`); lo que falta para el panel temporal es construir la serie de ventanas (delta_v entre elecciones) a nivel agregado de distrito.

---

### 13. Encuesta de Supermercados y Autoservicios Mayoristas — INDEC

**Fuente:** INDEC. Ventas de supermercados (en valores corrientes y constantes). Mensual, desde 2003. Nacional con desagregación por región.

**Relevancia:** Proxy de consumo de los hogares. La caída de ventas en supermercados es un indicador de contracción del consumo privado, muy visible y con periodicidad mensual.

---

### 14. Indicador Sintético de Servicios Públicos (ISSP) — INDEC

**Fuente:** INDEC. Mensual, desde 2004.

**Relevancia:** Incluye telefonía, electricidad, gas, agua, transporte. Puede reflejar el impacto de las políticas de tarifas (quita de subsidios, aumento de servicios) que tienen alto impacto perceptivo en el electorado.

---

### 15. Índice de Producción Industrial Manufacturero (IPI) — INDEC

**Fuente:** INDEC. Mensual, base 2004=100 (nueva base 2018 también disponible).

**Relevancia:** La Plata tiene un perfil económico particular (capital administrativa, universitaria, con presencia industrial moderada en la periferia). El IPI nacional puede no ser el mejor proxy, pero la actividad industrial es un componente visible del empleo formal en el conurbano.

---

### 16. Índice de Costo de la Construcción (ICC) — INDEC

**Fuente:** INDEC. Mensual, GBA. Desde 1993.

**Relevancia:** La construcción es un sector altamente cíclico en Argentina y un gran empleador de mano de obra no calificada. Su evolución puede capturar una dimensión del malestar laboral en sectores populares que el desempleo formal no registra (mucha informalidad).

---

### 17. Precio del dólar como commodity informacional

**Fuente:** Múltiples (BCRA para oficial, portales financieros para paralelo, MEP, CCL).

**Relevancia:** En Argentina, "el dólar" no es solo un tipo de cambio: es un termómetro político. La evolución del tipo de cambio (oficial, paralelo, MEP, CCL) y especialmente los saltos discretos (devaluaciones) son eventos con alto impacto perceptivo. Podría operacionalizarse como variable dummy (¿hubo devaluación discreta en la ventana?) o como variación acumulada — sobre la serie oficial (ítem 3), que sí cumple el piso de cobertura; el componente paralelo depende de la fuente movida a `datos_relevados_no_usables.md`.

---

## PARTE IV: MATRIZ DE COBERTURA TEMPORAL Y PERIODICIDAD

---

| Variable / Fuente | 2001 | 2002-06 | 2007-15 | 2016-25 | Periodicidad | Nivel geográfico más fino |
|---|---|---|---|---|---|---|
| IPC (empalme) | ✓ | ✓ | ⚠ (intervenido) | ✓ | Mensual | GBA / Nacional |
| Desocupación EPH | ✓ (puntual) | ✓ | ⚠ (con reservas) | ✓ | Trimestral | Aglomerado Gran La Plata |
| EMAE | ✗ | ✓ (desde 2004) | ⚠ | ✓ | Mensual | Nacional |
| RIPTE | ✓ | ✓ | ✓ | ✓ | Mensual | Nacional |
| Tipo de cambio oficial | ✓ | ✓ | ✓ | ✓ | Diaria | Nacional |
| ICG (UTDT) | ✓ (desde nov) | ✓ | ✓ | ✓ | Mensual | Nacional (con desag. regional) |
| ICC (UTDT) | ✓ | ✓ | ✓ | ✓ | Mensual | Nacional (con desag. regional) |
| Resultado fiscal primario | ✓ | ✓ | ✓ | ✓ | Mensual | Nacional |
| Reservas BCRA | ✓ | ✓ | ✓ | ✓ | Diaria | Nacional |
| OEDE empleo registrado (PBA) | ✓ | ✓ | ✓ | ✓ | Trimestral | Provincial |
| Gini (CEDLAS empalme) | ✓ | ✓ | ✓ (empalmado) | ✓ | Semestral | Aglomerado |

**Leyenda:** ✓ = disponible sin reservas; ⚠ = disponible con reservas metodológicas (período de intervención INDEC); ✗ = no disponible.

Filas quitadas de esta matriz por no cumplir el piso del 80% (ver
`datos_relevados_no_usables.md`): Pobreza EPH, Brecha cambiaria, REM,
Índice de Salarios, OEDE empleo (La Plata depto.), CBA/CBT, ODSA-UCA.

---

## PARTE V: CONSIDERACIONES PARA EL DISEÑO DE VENTANAS

---

### Núcleo de variables recomendado (cobertura completa 2001-2025, periodicidad mensual o trimestral)

Las siguientes variables tienen cobertura completa o casi completa desde 2001, periodicidad suficiente para agregar dentro de ventanas de 24/48 meses, y relevancia teórica directa para H1:

1. **Inflación** (IPC empalmado, mensual) — con documentación de las reservas 2007-2015
2. **Desocupación** (EPH Gran La Plata, trimestral)
3. **ICG** (UTDT, mensual) — percepción/confianza en el gobierno
4. **ICC** (UTDT, mensual) — percepción económica de los hogares
5. **RIPTE / salario real** (mensual, nacional)
6. **Tipo de cambio oficial** (BCRA, diaria → promediable mensual)
7. **Resultado fiscal primario** (Hacienda, mensual)
8. **Reservas internacionales** (BCRA, diaria → promediable mensual)

### Variables complementarias (cobertura parcial o periodicidad menor, pero ≥80%)

9. **EMAE** (desde 2004, mensual) — actividad económica real
10. **Pobreza y Gini** (semestral, empalme CEDLAS — no la serie EPH oficial directa, que no cumple el piso)
11. **Empleo registrado PBA** (OEDE, trimestral) — mercado laboral formal provincial

Las variables con cobertura <80% (REM, Índice de Salarios, OEDE
departamental, ODSA-UCA, CBA/CBT, dólar blue/brecha cambiaria) se movieron
a `datos_relevados_no_usables.md` y no forman parte de este núcleo ni de
las complementarias.

---

## PARTE VI: NOTA SOBRE EL PERÍODO 2007-2015

---

La intervención del INDEC entre 2007 y 2015 afecta la confiabilidad de varias series centrales (IPC, EPH, pobreza). Para el proyecto, esto genera un dilema metodológico: ese período incluye dos mandatos presidenciales completos (CFK 2007-2011, CFK 2011-2015), con al menos 4 elecciones dentro del panel, que representan ~30% de las observaciones. Las opciones son:

1. **Usar las series oficiales con una nota de reserva** — la posición más simple, pero potencialmente introduce sesgo de medición.
2. **Usar empalmes alternativos** (IPC Congreso, IPC provinciales, CEDLAS para pobreza) — más defensible metodológicamente, pero introduce heterogeneidad de fuentes.
3. **Incluir el período pero agregar una dummy de "período intervenido"** — permite al modelo capturar si hay un efecto diferencial, sin excluir observaciones.
4. **Documentar la decisión como limitación y hacer análisis de sensibilidad** — probar los modelos con y sin el período, o con distintas fuentes para la misma variable.

La opción 4 es probablemente la más robusta para una tesis académica. Esta decisión debería registrarse en `docs/decisiones_metodologicas.md`.

---

*Documento generado el 27 de agosto de 2026. Todas las URLs verificadas a esa fecha. Reorganizado el 12 de septiembre de 2026 separando las fuentes con cobertura <80% de 2001-2025 a `datos_relevados_no_usables.md`.*
