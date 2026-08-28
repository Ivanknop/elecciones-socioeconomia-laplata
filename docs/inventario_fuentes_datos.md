# Inventario de fuentes de datos disponibles

## Proyecto: Condiciones macroeconómicas y comportamiento electoral en el Partido de La Plata (2001–2025)

### Contexto de uso

Este inventario detalla todas las variables extraíbles de las fuentes ya identificadas para el proyecto, más fuentes adicionales relevantes no contempladas originalmente. Cada variable se evalúa en función de tres criterios operativos para el diseño de panel de ventanas electorales:

- **Periodicidad**: qué tan frecuente es la serie (diaria, mensual, trimestral, semestral, anual).
- **Cobertura temporal**: desde cuándo hay datos consistentes — el corte del panel es 2001.
- **Nivel geográfico**: si el dato es nacional, provincial (PBA), de aglomerado (Gran La Plata), o de partido (La Plata).

La estructura del panel requiere variables que puedan agregarse dentro de ventanas de ~24 o ~48 meses entre elecciones. Variables con periodicidad mensual o trimestral son ideales; variables anuales solo aportan 1-2 puntos por ventana y limitan el tipo de agregación posible (no permiten calcular tendencia o volatilidad intraventana).

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
| Incidencia de pobreza (personas y hogares) | Semestral | 2do semestre 2016–presente (con empalme ODSA-UCA desde 2010) | Aglomerado Gran La Plata o agregado | Método LP (línea de pobreza = CBT) |
| Incidencia de indigencia (personas y hogares) | Semestral | Ídem | Ídem | Método LP (línea de indigencia = CBA) |
| Coeficiente de Gini del ingreso per cápita familiar | Trimestral | 3T 2021–presente (antes en informes anuales) | Total 31 aglomerados (no individual por aglomerado en la publicación trimestral) | Indicador de desigualdad |
| Brecha de ingresos decil 10 / decil 1 | Trimestral | Ídem | Ídem | Proxy de polarización económica |
| Ingreso medio y mediano de la ocupación principal | Trimestral | Publicado regularmente | Por aglomerado (disponible para Gran La Plata en microdatos) | Requiere procesamiento de microdatos para Gran La Plata específico |

**Variables extraíbles — procesamiento de microdatos EPH (Gran La Plata, código 2):**

Los microdatos trimestrales de la EPH (bases individuales y de hogares) están disponibles para descarga pública. Filtrando por APTS=2 (Gran La Plata) se pueden construir:

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Distribución del ingreso per cápita familiar (deciles, quintiles) | Trimestral | 2003–presente | Permite calcular Gini específico de Gran La Plata |
| Tasa de pobreza e indigencia específica de Gran La Plata | Semestral | 2003–presente (con reservas 2007-2015) | Cruzando con CBA/CBT publicadas |
| Ingreso laboral real (deflactado por IPC) | Trimestral | 2003–presente | Proxy de salario real del aglomerado |
| Composición del empleo por calificación ocupacional | Trimestral | 2003–presente | Permite ver precarización vs. mejora de calidad del empleo |
| Tasa de asalarización, cuentapropismo, patrones | Trimestral | 2003–presente | Estructura del mercado laboral local |
| Acceso a cobertura de salud, educación | Trimestral | 2003–presente | Variables sociales complementarias |

**Herramientas de procesamiento:** El paquete `eph` de R (rOpenSci) permite descargar y procesar microdatos automáticamente, incluyendo cálculo de pobreza con canastas regionales. CEDLAS (UNLP) publica series procesadas a partir de EPH con desagregación por aglomerado y región en su portal ISA (Indicadores Socioeconómicos de Argentina).

**Relevancia para el proyecto:** La desocupación es, junto con la inflación, la variable central de H1 en la literatura de voto económico. La serie de Gran La Plata permite capturar la coyuntura del mercado laboral local como proxy de La Plata. La pobreza y la desigualdad aportan dimensiones complementarias del "malestar económico" que pueden ser más relevantes que la inflación en ciertos períodos.

---

### 3. Banco Central de la República Argentina (BCRA)

**Fuente:** https://www.bcra.gob.ar/

El BCRA publica un catálogo de más de 1.100 series estadísticas en formato TXT descargable, con metadatos de descripción, unidad de medida, periodicidad y cobertura temporal. Las series más relevantes para el proyecto son las siguientes:

**Variables de tipo de cambio:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Tipo de cambio de referencia ($/USD, Com. A 3500) | Diaria | Feb 2003–presente | Cotización oficial mayorista; promediable por mes |
| Tipo de cambio minorista ($/USD, Com. B 9791) | Diaria | Disponible | Cotización para público general |
| Brecha cambiaria (oficial vs. paralelo) | Diaria | Calculable desde ~2011 en adelante (dólar blue) | El BCRA no publica el paralelo; requiere fuente complementaria (Ámbito Financiero, dolarblue.net) |

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

**Relevancia para el proyecto:** El tipo de cambio y la brecha cambiaria son variables altamente salientes para el electorado argentino — probablemente más que la tasa de interés o la base monetaria. La devaluación del peso (medida como variación del tipo de cambio oficial o como ampliación de la brecha) puede funcionar como shock económico percibido con impacto electoral directo. Las reservas son un leading indicator de crisis cambiarias. La brecha cambiaria, en particular, es un indicador de distorsión/represión financiera que tiene correlato directo con la percepción de "las cosas no van bien" aunque requiere una fuente complementaria al BCRA para el dólar paralelo.

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

**Relevancia para el proyecto:** El resultado fiscal (superávit/déficit) y el gasto social son variables relevantes como indicadores de política económica del oficialismo — podrían funcionar como proxy de "esfuerzo redistributivo" del gobierno, mediando entre la economía objetiva y la percepción electoral. Sin embargo, su nivel geográfico es nacional, no local, lo cual es coherente con el diseño de panel temporal por distrito donde todas las variables económicas son igualmente nacionales.

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

**Relevancia para el proyecto:** Complementa al ICG con un ángulo distinto: el ICG mide confianza en el gobierno, el ICC mide percepción económica de los hogares. En la literatura de voto económico, la distinción entre voto sociotrópico (cómo percibo que está el país) y voto egotrópico (cómo percibo que estoy yo) es central — el ICC captura ambas dimensiones separadamente. La altísima correlación histórica entre el ICC y el desempeño electoral del oficialismo en Argentina ha sido documentada por la propia UTDT, lo que refuerza su relevancia teórica.

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

**Relevancia para el proyecto:** Es el proxy mensual más directo de "cómo va la economía" en términos de actividad real. A diferencia de la inflación (que mide precios) o el desempleo (que mide mercado laboral), el EMAE captura la producción de bienes y servicios. La variación interanual del EMAE permite distinguir períodos de recesión de períodos de crecimiento dentro de cada ventana electoral. La serie sectorial permite ver si el deterioro es generalizado o concentrado. Cubre desde 2004, por lo que pierde los primeros años del panel (2001-2003) — esas observaciones deberían cubrirse con el PIB trimestral de cuentas nacionales.

---

### 8. INDEC — Canasta Básica Alimentaria (CBA) y Canasta Básica Total (CBT)

**Fuente:** INDEC, Dirección de Índices de Precios de Consumo. https://www.indec.gob.ar/

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Valor de la CBA (adulto equivalente) | Mensual | Abr 2016–presente (serie oficial limpia); empalmes anteriores disponibles vía FIEL y CEDLAS | GBA | Define la línea de indigencia |
| Valor de la CBT (adulto equivalente) | Mensual | Ídem | GBA | Define la línea de pobreza |
| Coeficiente de Engel (inversa) | Mensual | Ídem | GBA | Relación CBA/CBT |
| Valores para hogar tipo (3, 4, 5 integrantes) | Mensual | Ídem | GBA | Permite expresar el umbral en términos más concretos |

**Relevancia para el proyecto:** La CBT/CBA en relación al ingreso medio o al RIPTE da un indicador directo de cuántos hogares (o qué proporción del ingreso) se necesita para cubrir necesidades básicas. La brecha entre salario y canasta básica es un indicador potente de malestar material con correlato electoral directo. Más útil como componente de un indicador compuesto que como variable aislada.

---

### 9. RIPTE y Coeficiente de Variación Salarial (CVS) — Ministerio de Trabajo / INDEC

**Fuente:** Secretaría de Trabajo, Empleo y Seguridad Social (RIPTE); INDEC (CVS e Índice de Salarios).

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| RIPTE (Remuneración Imponible Promedio de Trabajadores Estables) | Mensual | Jul 1994–presente | Nacional | Solo empleo registrado con 13+ meses de antigüedad; no refleja empleo informal |
| Índice de Salarios (INDEC) | Mensual | Oct 2016–presente | Nacional | Distingue sector privado registrado, público, y privado no registrado |
| CVS — variación salarial por sector | Mensual | Oct 2016–presente | Nacional | Permite calcular salario real (deflactando por IPC) |

**Relevancia para el proyecto:** El salario real (RIPTE o Índice de Salarios deflactado por IPC) es probablemente el indicador más directo de poder adquisitivo. Su evolución dentro de la ventana electoral captura si los trabajadores están "ganándole a la inflación" o no — una pregunta central en el voto económico egotrópico. La limitación del RIPTE (solo empleo registrado estable) puede compensarse parcialmente con el componente de empleo no registrado del Índice de Salarios (desde 2016). Para el período 2001-2016, el RIPTE es la única serie mensual de salarios disponible a nivel nacional.

**Derivación clave:** Salario real = RIPTE / IPC (o Índice de Salarios / IPC). Esta serie derivada permite calcular, dentro de cada ventana, si el salario real subió, bajó, cuánto y con qué tendencia.

---

### 10. Relevamiento de Expectativas de Mercado (REM) — BCRA

**Fuente:** BCRA. https://www.bcra.gob.ar/relevamiento-expectativas-mercado-rem/

**Descripción:** Encuesta mensual a ~45 consultoras, bancos y centros de investigación que pronostica las principales variables macro. Relanzado en julio 2016; existía en formato anterior desde antes.

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

**Relevancia para el proyecto:** Las expectativas son un canal teóricamente distinto de los datos realizados: la literatura de voto económico prospectivo (MacKuen, Erikson & Stimson) argumenta que los votantes castigan o premian al gobierno no solo por lo que pasó sino por lo que creen que va a pasar. La diferencia entre expectativa y realización (el "error de expectativa" o la "sorpresa" económica) podría ser un predictor más fuerte que el dato realizado en sí. La limitación principal es que la serie solo arranca en 2016, cubriendo solo las últimas ~4-5 elecciones del panel.

---

### 11. OEDE — Observatorio de Empleo y Dinámica Empresarial (Ministerio de Trabajo)

**Fuente:** Dirección Nacional de Estadísticas y Estudios Laborales. https://www.argentina.gob.ar/trabajo/estadisticas/oede-estadisticas-provinciales

**Descripción:** Construye indicadores a partir de registros administrativos del SIPA (Sistema Integrado Previsional Argentino), el padrón de contribuyentes y Simplificación Registral. Permite desagregación provincial y, desde 2019, departamental.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Empleo asalariado registrado privado | Trimestral/Mensual | ~1996–presente | Provincial (PBA) y desde 2019 departamental (Partido de La Plata) | Basado en SIPA |
| Remuneración promedio de trabajadores registrados | Trimestral/Mensual | Ídem | Provincial y desde 2019 departamental | Nominal; deflactar por IPC |
| Cantidad de empresas empleadoras | Trimestral | ~1996–presente | Provincial | Indicador de dinámica empresarial |
| Tasa de entrada y salida de empresas | Trimestral | ~1996–presente | Provincial | Apertura y cierre de empresas |
| Empleo por sector de actividad (CIIU) | Trimestral | ~1996–presente | Provincial | Permite ver estructura productiva |

**Relevancia para el proyecto:** La serie departamental (desde 2019) es la única fuente de empleo formal desagregada a nivel Partido de La Plata — más fina que Gran La Plata de la EPH. Sin embargo, su cobertura temporal (desde 2019) es insuficiente para el panel completo 2001-2025. La serie provincial (PBA) cubre el período completo y es un proxy razonable para un distrito de la conurbación bonaerense que es capital provincial. La dinámica empresarial (apertura/cierre de empresas) captura una dimensión del malestar económico distinta del desempleo: no solo se pierden empleos, sino que desaparecen empresas.

---

### 12. Observatorio de la Deuda Social Argentina (ODSA) — UCA

**Fuente:** Universidad Católica Argentina. https://uca.edu.ar/es/observatorio-de-la-deuda-social-argentina

**Descripción:** Desde 2004 realiza la Encuesta de la Deuda Social Argentina (EDSA) con ~5.700 hogares en áreas urbanas. Produce indicadores de pobreza multidimensional (no solo monetaria), bienestar subjetivo, empleo, salud, educación, vivienda. Dos series empalmables: Bicentenario (2010-2016) y Agenda para la Equidad (2017-2025).

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Pobreza multidimensional (carencias en derechos) | Anual | 2010–presente | Nacional urbano, con desagregación regional | No solo ingreso: vivienda, salud, educación, empleo |
| Inseguridad alimentaria | Anual | 2010–presente | Nacional urbano | Indicador extremo de malestar material |
| Percepción de insuficiencia de ingresos | Anual | 2010–presente | Nacional urbano | % hogares que perciben que sus ingresos no alcanzan |
| Capacidad de ahorro percibida | Anual | 2010–presente | Nacional urbano | Indicador de bienestar económico subjetivo |
| Malestar psicológico (ansiedad, depresión) | Anual | 2010–presente | Nacional urbano | Dimensión de bienestar subjetivo |
| Estrés económico, social y subjetivo | Anual | 2023–presente | Nacional urbano | Nuevo en la EDSA 2025 |

**Relevancia para el proyecto:** Aporta dimensiones de malestar que los indicadores macro no capturan — en particular, la percepción subjetiva de insuficiencia de ingresos y la inseguridad alimentaria son indicadores de "sufrimiento vivido" más que de "dato macro". La limitación principal es que la periodicidad es anual (no mensual ni trimestral), lo que da solo 1-2 puntos por ventana electoral de 24 meses, y el nivel geográfico es nacional/regional sin desagregación a nivel La Plata. Útil como variable de contexto o de validación, no como input principal del modelo de ventanas.

---

### 13. CEDLAS (Centro de Estudios Distributivos, Laborales y Sociales) — UNLP

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

**Relevancia para el proyecto:** El valor principal del CEDLAS es que produce series empalmadas de indicadores que el INDEC no empalma oficialmente (especialmente para el período 2007-2015). Si se necesita una serie larga y coherente de pobreza o Gini que cubra todo el panel 2001-2025 sin discontinuidades, CEDLAS es la fuente más confiable. Además, al estar en la UNLP, hay acceso institucional directo.

---

### 14. Tipo de cambio paralelo ("dólar blue") — Fuentes no oficiales

**Fuente:** Ámbito Financiero (ambito.com/contenidos/dolar.html), dolarblue.net, series históricas compiladas por investigadores y portales financieros.

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Cotización del dólar paralelo (blue) | Diaria | ~2011–presente (con cobertura más firme desde 2012) | No es dato oficial; no existe fuente única canónica |
| Brecha cambiaria (% diferencia blue vs. oficial) | Diaria | Calculable desde 2011 | Indicador de distorsión cambiaria y desconfianza |

**Relevancia para el proyecto:** La brecha cambiaria es un indicador muy saliente para el electorado argentino, probablemente más que la tasa de interés o las reservas. En períodos de cepo cambiario (2011-2015, 2019-2023), la brecha fue tema central del discurso público y la percepción de "crisis". Limitación: la serie es estimada (no hay cotización oficial de un mercado paralelo); la confiabilidad varía según la fuente. Para el período 2001-2011 (pre-cepo), la brecha era marginal y puede considerarse cero.

---

### 15. Resultado fiscal primario — Secretaría de Hacienda

**Fuente:** Ministerio de Economía, Secretaría de Hacienda. Series disponibles vía datos.gob.ar y Oficina Nacional de Presupuesto (https://www.economia.gob.ar/onp/estadisticas/).

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Nivel geográfico | Observaciones |
|---|---|---|---|---|
| Resultado primario del SPN no financiero | Mensual | 1993–presente | Nacional | Superávit/déficit antes de intereses |
| Resultado financiero del SPN | Mensual | 1993–presente | Nacional | Incluye pago de intereses de deuda |
| Ingresos tributarios nacionales | Mensual | 1993–presente | Nacional | IVA, Ganancias, derechos de exportación, etc. |
| Gasto primario del SPN | Mensual | 1993–presente | Nacional | Jubilaciones, salarios, transferencias, capital |

**Relevancia para el proyecto:** El resultado fiscal es una variable de política económica del oficialismo que el votante puede (o no) percibir. En el contexto argentino reciente, el superávit/déficit fiscal se ha vuelto parte del discurso público, pero históricamente fue una variable técnica con poca penetración en la percepción del votante medio. Su inclusión es relevante como control o como moderador (¿importa el déficit solo cuando es políticamente saliente?), no necesariamente como predictor principal.

---

### 16. INDEC — Índice de Salarios (IS)

**Fuente:** INDEC. https://www.indec.gob.ar/

**Variables extraíbles:**

| Variable | Periodicidad | Cobertura temporal | Observaciones |
|---|---|---|---|
| Índice de Salarios nivel general | Mensual | Oct 2016–presente | Compuesto: privado registrado + público + privado no registrado |
| IS sector privado registrado | Mensual | Oct 2016–presente | Incluye paritarias |
| IS sector público | Mensual | Oct 2016–presente | Salarios estatales |
| IS sector privado no registrado | Mensual | Oct 2016–presente | Única serie oficial de salarios informales |

**Relevancia para el proyecto:** El componente de empleo privado no registrado (informal) del IS es particularmente relevante para capturar la realidad de los sectores más vulnerables, que suelen ser los más afectados por las crisis y los más reactivos electoralmente. Sin embargo, la serie solo existe desde octubre 2016.

---

## PARTE III: FUENTES DE POTENCIAL INTERÉS COMPLEMENTARIO

---

### 17. Datos electorales — Dirección Nacional Electoral / Junta Electoral PBA

**Fuente:** Atlas Electoral de Andy Tow (andy.towsa.com), datos abiertos del Ministerio del Interior (datos.gob.ar), DINE.

**Variables:** Resultado total del Partido de La Plata para intendente, gobernador y presidente (2001-2025). Estas variables ya están parcialmente en el repositorio (`data/distrito/`); lo que falta para el panel temporal es construir la serie de ventanas (delta_v entre elecciones) a nivel agregado de distrito.

---

### 18. Encuesta de Supermercados y Autoservicios Mayoristas — INDEC

**Fuente:** INDEC. Ventas de supermercados (en valores corrientes y constantes). Mensual, desde 2003. Nacional con desagregación por región.

**Relevancia:** Proxy de consumo de los hogares. La caída de ventas en supermercados es un indicador de contracción del consumo privado, muy visible y con periodicidad mensual.

---

### 19. Indicador Sintético de Servicios Públicos (ISSP) — INDEC

**Fuente:** INDEC. Mensual, desde 2004.

**Relevancia:** Incluye telefonía, electricidad, gas, agua, transporte. Puede reflejar el impacto de las políticas de tarifas (quita de subsidios, aumento de servicios) que tienen alto impacto perceptivo en el electorado.

---

### 20. Encuesta Nacional de Gastos de los Hogares (ENGHo) — INDEC

**Fuente:** INDEC. Se realiza cada ~10 años (2004/05, 2012/13, 2017/18). La próxima está en planificación.

**Relevancia limitada:** Periodicidad demasiado baja para el panel de ventanas. Útil solo como referencia de estructura de consumo para contextualizar qué mide el IPC, no como input del modelo.

---

### 21. Censos Nacionales de Población (2001, 2010, 2022) — INDEC

**Fuente:** INDEC. Datos desagregados a nivel de radio censal, fracción, departamento.

**Relevancia limitada para el modelo temporal:** Solo 3 puntos (2001, 2010, 2022). Sin embargo, los datos censales a nivel de radio censal podrían servir para la dimensión espacial del proyecto (análisis secundario por localidad) si se retoma: NBI, condiciones de vivienda, nivel educativo, composición demográfica por localidad.

---

### 22. Índice de Producción Industrial Manufacturero (IPI) — INDEC

**Fuente:** INDEC. Mensual, base 2004=100 (nueva base 2018 también disponible).

**Relevancia:** La Plata tiene un perfil económico particular (capital administrativa, universitaria, con presencia industrial moderada en la periferia). El IPI nacional puede no ser el mejor proxy, pero la actividad industrial es un componente visible del empleo formal en el conurbano.

---

### 23. Índice de Costo de la Construcción (ICC) — INDEC

**Fuente:** INDEC. Mensual, GBA. Desde 1993.

**Relevancia:** La construcción es un sector altamente cíclico en Argentina y un gran empleador de mano de obra no calificada. Su evolución puede capturar una dimensión del malestar laboral en sectores populares que el desempleo formal no registra (mucha informalidad).

---

### 24. Precio del dólar como commodity informacional

**Fuente:** Múltiples (BCRA para oficial, portales financieros para paralelo, MEP, CCL).

**Relevancia:** En Argentina, "el dólar" no es solo un tipo de cambio: es un termómetro político. La evolución del tipo de cambio (oficial, paralelo, MEP, CCL) y especialmente los saltos discretos (devaluaciones) son eventos con alto impacto perceptivo. Podría operacionalizarse como variable dummy (¿hubo devaluación discreta en la ventana?) o como variación acumulada.

---

## PARTE IV: MATRIZ DE COBERTURA TEMPORAL Y PERIODICIDAD

---

| Variable / Fuente | 2001 | 2002-06 | 2007-15 | 2016-25 | Periodicidad | Nivel geográfico más fino |
|---|---|---|---|---|---|---|
| IPC (empalme) | ✓ | ✓ | ⚠ (intervenido) | ✓ | Mensual | GBA / Nacional |
| Desocupación EPH | ✓ (puntual) | ✓ | ⚠ (con reservas) | ✓ | Trimestral | Aglomerado Gran La Plata |
| Pobreza EPH | ✓ (puntual) | ✓ | ⚠ | ✓ | Semestral | Aglomerado Gran La Plata |
| EMAE | ✗ | ✓ (desde 2004) | ⚠ | ✓ | Mensual | Nacional |
| RIPTE | ✓ | ✓ | ✓ | ✓ | Mensual | Nacional |
| Tipo de cambio oficial | ✓ | ✓ | ✓ | ✓ | Diaria | Nacional |
| Brecha cambiaria | ✗ | ✗ | ✓ (desde ~2011) | ✓ | Diaria | Nacional |
| ICG (UTDT) | ✓ (desde nov) | ✓ | ✓ | ✓ | Mensual | Nacional (con desag. regional) |
| ICC (UTDT) | ✓ | ✓ | ✓ | ✓ | Mensual | Nacional (con desag. regional) |
| Resultado fiscal primario | ✓ | ✓ | ✓ | ✓ | Mensual | Nacional |
| Reservas BCRA | ✓ | ✓ | ✓ | ✓ | Diaria | Nacional |
| REM (expectativas) | ✗ | ✗ | ✗ | ✓ (desde jul 2016) | Mensual | Nacional |
| Índice de Salarios | ✗ | ✗ | ✗ | ✓ (desde oct 2016) | Mensual | Nacional |
| OEDE empleo registrado (PBA) | ✓ | ✓ | ✓ | ✓ | Trimestral | Provincial |
| OEDE empleo (La Plata depto.) | ✗ | ✗ | ✗ | ✓ (desde 2019) | Trimestral | Departamental |
| CBA/CBT | ✓ (empalme) | ✓ (empalme) | ⚠ | ✓ (desde abr 2016 limpia) | Mensual | GBA |
| Gini (CEDLAS empalme) | ✓ | ✓ | ✓ (empalmado) | ✓ | Semestral | Aglomerado |
| ODSA-UCA | ✗ | ✓ (desde 2004) | ✓ (desde 2010 con empalme) | ✓ | Anual | Nacional urbano |

**Leyenda:** ✓ = disponible sin reservas; ⚠ = disponible con reservas metodológicas (período de intervención INDEC); ✗ = no disponible.

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

### Variables complementarias (cobertura parcial o periodicidad menor)

9. **EMAE** (desde 2004, mensual) — actividad económica real
10. **Pobreza** (semestral, Gran La Plata) — vía EPH o CEDLAS empalme
11. **Gini** (semestral, empalme CEDLAS) — desigualdad
12. **Brecha cambiaria** (desde ~2011, diaria) — saliente en períodos de cepo
13. **Empleo registrado PBA** (OEDE, trimestral) — mercado laboral formal provincial

### Variables de solo valor exploratorio o para el período reciente

14. **REM expectativas** (desde 2016)
15. **Índice de Salarios con informal** (desde 2016)
16. **OEDE departamental La Plata** (desde 2019)
17. **ODSA-UCA indicadores multidimensionales** (anual, desde 2010)

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

*Documento generado el 27 de agosto de 2026. Todas las URLs verificadas a esa fecha.*
