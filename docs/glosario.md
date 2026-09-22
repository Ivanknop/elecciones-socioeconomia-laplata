# Glosario

Referencia de todos los términos usados a lo largo del repositorio,
organizada en tres categorías: **variables** (columnas de datos: qué
significan, qué miden, cómo se calculan, si son fuente primaria o
cálculo derivado), **modelos de machine learning** (modo de uso general
y uso concreto en este proyecto) y **conceptos teóricos** (definición
académica original, usos en ciencias sociales, bibliografía de
respaldo, y uso concreto en este proyecto).

## Índice

1. [Variables](#variables)
   - [Capa electoral](#capa-electoral)
   - [Capa macroeconómica](#capa-macroeconómica)
   - [Capa socioeconómica](#capa-socioeconómica)
   - [Capa de geolocalización](#capa-de-geolocalización)
   - [Panel temporal (`src/ml_models`)](#panel-temporal-srcml_models)
2. [Modelos de machine learning](#modelos-de-machine-learning)
3. [Conceptos teóricos](#conceptos-teóricos)

---

## Variables

### Capa electoral

#### Resultados crudos (API de Resultados Electorales / `electoral.models`)

##### `circuito_id`
- **Significado:** identificador de un circuito electoral (unidad geográfica de agregación de mesas dentro de una sección electoral).
- **Qué mide:** a qué circuito pertenecen los datos de una fila (electores, votos, mesas).
- **Cómo se calcula:** campo crudo del CSV/JSON oficial de la API de Resultados Electorales; se normaliza (ver `docs/FUNCIONALIDADES.md` §"Totales por circuito") al construir `circuito_<nivel>.json` en el notebook 04.
- **Origen:** Primaria, con normalización — el campo viene de la fuente, pero la clave final (`circuito_id`) puede requerir una corrección puntual documentada en `data/agrupaciones/circuito_id_correspondencias.csv`.

##### `agrupacion` / `nombre_agrupacion` / `nombreAgrupacion`
- **Significado:** nombre del partido, frente o alianza que participa en la elección.
- **Qué mide:** identidad de la fuerza política a la que se le asignan votos.
- **Cómo se calcula:** campo crudo de la API; se normaliza a mayúsculas en el notebook 04 (`agregar_por_circuito`) para que coincida con la clave usada al unir contra `clasificacion_ideologica_agrupaciones.csv`.
- **Origen:** Primaria con normalización de formato en el repo.

##### `id_agrupacion` / `idAgrupacion`
- **Significado:** identificador numérico/string de la agrupación en la API.
- **Qué mide:** clave estable para sumar votos de la misma agrupación entre mesas/circuitos.
- **Cómo se calcula:** campo crudo de `ValorAgrupacion` (`src/electoral/models.py`).
- **Origen:** Primaria.

##### `votos` (agrupación)
- **Significado:** cantidad de votos obtenidos por una agrupación en una mesa/circuito/total.
- **Qué mide:** votos positivos (válidos y asignados a una agrupación).
- **Cómo se calcula:** campo crudo (`votos` en `ValorAgrupacion.from_json`); al totalizar (`electoral.models.totalizar_agrupaciones`) se suma por `id_agrupacion` a través de mesas/circuitos.
- **Origen:** Primaria a nivel mesa/circuito.

##### `votos_porcentaje` / `votosPorcentaje`
- **Significado:** porcentaje que representan los votos de una agrupación sobre el total de esa consulta.
- **Qué mide:** peso relativo de una agrupación.
- **Cómo se calcula:** en la fuente cruda viene calculado por la propia API sobre esa consulta puntual (mesa/circuito); al totalizar en el repo (`totalizar_agrupaciones`) se **recalcula desde cero** sobre el total agregado (`votos / total * 100`), no se hereda del crudo. `totales_por_lista.resultado_total_con_blanco_nulo` lo vuelve a recalcular una tercera vez incluyendo `BLANCO + NULO` en el denominador.
- **Origen:** Primaria a nivel mesa (viene de la API); Derivada (recalculada) en cualquier nivel de agregación superior.

##### `electores` / `cantidadElectores`
- **Significado:** cantidad de personas habilitadas para votar (padrón) en esa mesa/circuito.
- **Qué mide:** tamaño del padrón electoral de esa unidad.
- **Cómo se calcula:** campo crudo de la API (`EstadoRecuento.cantidad_electores`, o `electores` dentro de cada circuito de `circuito_<nivel>.json`).
- **Origen:** Primaria.

##### `positivos`
- **Significado:** total de votos válidos asignados a alguna agrupación en un circuito.
- **Qué mide:** votos que eligieron una fuerza política (excluye blancos, nulos, procedimentales).
- **Cómo se calcula:** dentro de `circuito_<nivel>.json`, es el diccionario `{id_agrupacion: {nombre, votos, campo_ideologico}}` de cada circuito; su suma (`sum(info["votos"] for info in c["positivos"].values())`) es el total de votos positivos de ese circuito. Equivale a `ResultadoElectoral.total_votos_positivos` a nivel mesa.
- **Origen:** Primaria (el desglose por agrupación) / Derivada (la suma total).

##### `votantes` / `cantidadVotantes`
- **Significado:** cantidad de personas que efectivamente votaron (positivos + blancos + nulos + procedimentales).
- **Qué mide:** participación electoral en términos absolutos.
- **Cómo se calcula:** campo crudo de `EstadoRecuento` (API), a nivel mesa/circuito reportado por el escrutinio.
- **Origen:** Primaria.

##### `votos_nulos` / `votosNulos`, `votos_en_blanco` / `votosEnBlanco`, `votos_recurridos_comando_impugnados`
- **Significado:** categorías de voto no positivo — nulo (boleta inválida), en blanco (sobre vacío/sin marcar), y procedimentales (recurridos, de comando, impugnados).
- **Qué mide:** votos emitidos que no se asignan a ninguna agrupación.
- **Cómo se calcula:** campos crudos de `ValoresOtros` (`src/electoral/models.py`); dentro de `circuito_<nivel>.json` viven en el diccionario `otros` de cada circuito (claves `BLANCOS`, `NULOS`, `COMANDO`, `IMPUGNADOS`, `RECURRIDOS`).
- **Origen:** Primaria.

##### `ausentismo`
- **Significado:** personas del padrón que no concurrieron a votar.
- **Qué mide:** no-participación electoral.
- **Cómo se calcula:** `electores - positivos - otros_total` (padrón menos votos positivos menos *todos* los "otros", incluidos los procedimentales — recurridos/impugnados/comando entran en la resta aunque no se grafiquen como categoría propia). Fórmula en `graficos._votos_no_ideologicos`, reusada idéntica en `visualizacion.mapa_interactivo` (ver `CLAUDE.md`).
- **Origen:** Derivada.

##### `etapa`
- **Significado:** instancia electoral: `generales`, `paso` (primarias abiertas simultáneas y obligatorias) o `balotaje` (segunda vuelta).
- **Qué mide:** a qué tipo de consulta pertenecen los datos.
- **Cómo se calcula:** nombre de la subcarpeta bajo `data/distrito/<año>/<nivel>/<etapa>/`; corresponde a `tipo_eleccion` de la API (1=PASO, 2=Generales, 3=Balotaje).
- **Origen:** Primaria (estructural, define qué consulta de la API se pidió).

##### `nivel` / `cargo`
- **Significado:** cargo en disputa — a nivel `data/distrito/` son 6 valores (`presidente`, `gobernador`, `intendente`, `nacional`, `provincial`, `municipal`, estos tres últimos para legislativas); a nivel de análisis temporal (`serie_temporal.py` y módulos que lo importan) se **unifican** en 3 "niveles de gobierno" (`nacional`, `provincial`, `municipal`), cada uno combinando su cargo ejecutivo + legislativo en una sola serie.
- **Qué mide:** a qué nivel de gobierno corresponde la elección.
- **Cómo se calcula:** nombre de carpeta/parámetro; la unificación ejecutivo+legislativo vive en `NIVELES`/`_puntos_del_nivel` (`analisis.serie_temporal`) y el mapeo de nombres inconsistente `"gobernador"` ↔ `"gobernacion"` entre `data/distrito/` y `clasificacion_ideologica_agrupaciones.csv` se resuelve vía `NIVEL_A_NIVEL_CSV` (`totales_por_lista.py`).
- **Origen:** Primaria (estructural) / Derivada (la unificación en 3 niveles).

#### Clasificación ideológica (`data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`)

##### `campo_ideologico`
- **Significado:** posición ideológico-programática de una agrupación **en una elección puntual** (puede cambiar de año a año para la misma agrupación).
- **Qué mide:** ubicación en una escala 1-6, izquierda → derecha radical.
- **Cómo se calcula:** clasificación cargada a mano; clave de unión es `(anio, agrupacion, nivel)`. El archivo es append-only: nunca se sobreescribe una fila existente, solo se agregan agrupaciones nuevas con el campo vacío (aviso, no error silencioso).
- **Origen:** Primaria en el sentido de que es un juicio experto cargado a mano, no calculado de otra fuente; funcionalmente actúa como tabla de referencia (join) para el resto del pipeline.

##### `filiacion_politica`
- **Significado:** familia o identidad partidaria de una agrupación (peronistas, progresistas, liberales, marxistas, nacionalistas, conservadores, peronismo provincial, radicalismo, otros).
- **Qué mide:** genealogía/identidad de largo plazo de un partido, ortogonal a su posición ideológico-programática puntual.
- **Cómo se calcula:** clasificación a mano. **No varía por `anio`/`nivel`** — una agrupación tiene una única `filiacion_politica`.
- **Origen:** Primaria (juicio experto cargado a mano).

##### `vparty_economico`, `vparty_progresismo`, `vparty_populismo`
- **Significado:** posición programática de una agrupación en el espacio del proyecto V-Party (V-Dem Institute) — eje económico izquierda-derecha, eje progresismo social, y grado de discurso populista.
- **Qué mide:** posicionamiento programático comparable internacionalmente, ortogonal tanto a `campo_ideologico` como a `filiacion_politica`.
- **Cómo se calcula:** para partidos con cobertura real de V-Party, viene directo del dataset `data/agrupaciones/v-party/v_party_argentina_2001_2019.csv`; para partidos sin cobertura, se estima con `src/analisis/generar_v_party_propio.py` a partir de una encuesta propia a expertos (`encuesta_partidos_propia.csv`), calibrada a la misma escala. Qué fila viene de qué fuente está documentado en `data/agrupaciones/v-party/README.md`.
- **Origen:** Primaria (V-Party real) o Derivada (estimación propia vía encuesta de expertos).

#### Totales y agregaciones derivadas

##### `resultado_total.csv` — `id_agrupacion`, `agrupacion`, `votos`, `votos_porcentaje`
- **Significado:** una fila por agrupación con el total de votos de todo un (año, nivel[, etapa]) en La Plata.
- **Qué mide:** resultado electoral agregado a nivel distrito completo.
- **Cómo se calcula:** suma de todos los circuitos de `circuito_<nivel>.json` vía `electoral.models.totalizar_agrupaciones` (nunca del JSON agregado crudo de la API, que subestima algunos casos — ver "Anomalía... Presidente 2019").
- **Origen:** Derivada — `src/electoral/totales.py` (`resultado_total_por_agrupacion`/`generar_csv_totales`).

##### `BLANCO + NULO` (fila agregada en `totales_por_lista.py`)
- **Significado:** entrada sintética que trata blanco+nulo como si fuera una "agrupación" más, para poder graficarla/tabularla junto a los partidos.
- **Qué mide:** lo mismo que `blanco_nulo`, pero expresada como fila de una tabla de agrupaciones (con su propio `votos_porcentaje` recalculado sobre el nuevo total).
- **Cómo se calcula:** `totales_por_lista.resultado_total_con_blanco_nulo` parte de `resultado_total_por_agrupacion` y le agrega esta entrada, recalculando `votos_porcentaje` con `totalizar_agrupaciones` (no relee `data/totales/`, que es agnóstico de blanco/nulo a propósito).
- **Origen:** Derivada.

##### `localidad` / `circuito_id -> localidad` (crosswalk)
- **Significado:** a qué localidad (barrio/pueblo) del Partido de La Plata pertenece un circuito electoral.
- **Qué mide:** agregación geográfica intermedia entre circuito y distrito completo.
- **Cómo se calcula:** dos crosswalks posibles — el nearest-neighbor geolocalizado (`data/geolocalizacion/circuitos_por_localidad.csv`, default) o el hand-curated histórico por barrio (`data/geolocalizacion/fuentes_extra/circuito_localidad.csv`, con niveles de cobertura `oficial_confirmada`/`revision_web`/`periodistico_no_oficial`/`oficial_no_agrupable`). `electoral.localidades.agrupar_resultados_por_localidad` es agnóstica de cuál se usa; un circuito no mapeado cae en `SIN_DETERMINAR`, nunca se descarta.
- **Origen:** Derivada (crosswalk construido en el repo, ver skill `laplata-geolocalizacion`).


### Capa macroeconómica

Todas las variables son de grano **nacional** (sin apertura regional/local), 2001-2025, tomadas de `datos.gob.ar` (API Series de Tiempo) salvo excepción indicada. Viven en `data/macroeconomia/series_macro_2001_2025.csv` (mensual) o `series_macro_anuales_2001_2025.csv` (anual). Regla del pipeline: **nunca se repite (forward-fill) un valor** — una celda vacía significa que ese mes/año no tiene publicación propia, no que el valor sea igual al anterior.

#### `tipo_cambio_oficial`
- **Significado:** cotización de referencia del dólar estadounidense fijada oficialmente.
- **Qué mide:** pesos argentinos por dólar, tipo de cambio de referencia (BCRA Comunicación A 3500 en su definición histórica).
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `175.1_DR_ESTANSE_0_0_20`), diaria, normalizada a mensual (último dato del mes) por `macroeconomia/series.py`.
- **Origen:** Primaria.

#### `tipo_cambio_mayorista`
- **Significado:** dólar de referencia del mercado mayorista.
- **Qué mide:** pesos por dólar, Comunicación A 3500.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `175.1_DR_REFE500_0_0_25`), diaria → mensual.
- **Origen:** Primaria.

#### `reservas_internacionales`
- **Significado:** reservas en moneda extranjera del Banco Central.
- **Qué mide:** millones de USD.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `92.1_RID_0_0_32`), mensual.
- **Origen:** Primaria.

#### `base_monetaria`
- **Significado:** dinero en circulación + reservas bancarias en el BCRA.
- **Qué mide:** saldo en pesos.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `331.1_SALDO_BASERIA__15`), mensual.
- **Origen:** Primaria.

#### `tasa_badlar`
- **Significado:** tasa de interés de referencia para depósitos a plazo fijo mayoristas (>$1M).
- **Qué mide:** porcentaje (0-100, ya multiplicada por 100 según metadata de la fuente).
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `89.1_TIB_0_0_20`), mensual.
- **Origen:** Primaria.

#### `tasa_politica_monetaria`
- **Significado:** tasa de referencia de política monetaria del BCRA (aproximada a LELIQ).
- **Qué mide:** porcentaje, ya multiplicado por 100.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `89.1_IR_BCRARIA_0_M_34`), mensual; sin serie homogénea antes de dic-2015.
- **Origen:** Primaria.

#### `ipc_nacional`
- **Significado:** Índice de Precios al Consumidor, nivel nacional.
- **Qué mide:** variación de precios minoristas.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `148.3_INIVELNAL_DICI_M_26`), mensual; no existe medición nacional homogénea antes de dic-2016 (antes solo GBA/provincias sueltas).
- **Origen:** Primaria.

#### `canasta_basica_alimentaria`
- **Significado:** Canasta Básica Alimentaria (CBA), valor monetario del umbral de indigencia.
- **Qué mide:** pesos por adulto equivalente. En rigor es la serie de GBA usada como referencia nacional (no hay CBA nacional homogénea).
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `150.1_CSTA_BARIA_0_D_26`), mensual desde 2016-04.
- **Origen:** Primaria.

#### `canasta_basica_total`
- **Significado:** Canasta Básica Total (CBT), umbral de pobreza.
- **Qué mide:** pesos por adulto equivalente (misma salvedad de cobertura GBA que la CBA).
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `150.1_CSTA_BATAL_0_D_20`), mensual desde 2016-04.
- **Origen:** Primaria.

#### `emae`
- **Significado:** Estimador Mensual de Actividad Económica, proxy de PBI de alta frecuencia.
- **Qué mide:** índice de actividad económica agregada, base 2004=100.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `143.3_NO_PR_2004_A_21`), mensual.
- **Origen:** Primaria.

#### `pbi`
- **Significado:** Producto Bruto Interno.
- **Qué mide:** millones de pesos corrientes, base 2004.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `166.2_PPIB_0_0_3`), trimestral; solo tiene valor el mes de publicación del trimestre, el resto vacío. Termina en 2024-10 (Q4 2024) por rezago de publicación de INDEC.
- **Origen:** Primaria.

#### `tasa_desocupacion`
- **Significado:** tasa de desocupación, población económicamente activa que no tiene empleo y lo busca.
- **Qué mide:** **fracción 0-1** (`0.074` = 7,4%) pese a que la metadata de la fuente dice "Porcentaje" — no está premultiplicada por 100, a diferencia de `tasa_badlar`/`tasa_politica_monetaria`.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `42.3_EPH_PUNTUATAL_0_M_30`), EPH continua total país, trimestral. Hueco real de 2 trimestres (2015-10, 2016-01)
- **Origen:** Primaria.

#### `tasa_empleo`
- **Significado:** proporción de la población total que está ocupada.
- **Qué mide:** fracción 0-1, misma salvedad de unidad y mismo hueco que `tasa_desocupacion`.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `44.2_ECTET_0_T_30`), EPH continua total país, trimestral.
- **Origen:** Primaria.

#### `tasa_actividad`
- **Significado:** proporción de la población total que participa del mercado laboral (ocupada + desocupada buscando trabajo).
- **Qué mide:** fracción 0-1, misma salvedad y mismo hueco que las dos anteriores.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `43.2_ECTAT_0_T_33`), EPH continua total país, trimestral.
- **Origen:** Primaria.

#### `ripte` (`salario_real` en `data/tfi_data/registro_variables.csv`)
- **Significado:** Remuneración Imponible Promedio de los Trabajadores Estables — serie salarial más larga y estable del catálogo.
- **Qué mide:** salario nominal promedio de trabajadores registrados estables. En `registro_variables.csv`, `salario_real` es RIPTE **deflactado por IPC empalmado** (variable derivada distinta del RIPTE nominal).
- **Cómo se calcula:** RIPTE crudo de datos.gob.ar (id `158.1_REPTE_0_0_5`), mensual; `salario_real` = RIPTE ÷ `ipc`, calculado en `src/ml_models/cargar_series_economicas.py`. Desde D33 (`docs/especificaciones/especificacion_empalme_ipc.md`), `ipc` es la serie FACPCE (Res. JG 539/18, continua 1993-2025, sin huecos) -- ya no hereda el hueco 2014-2016 que tenía la fuente anterior de `ipc` (datos.gob.ar, 3 vintages sin rebasar entre sí). Salvedad que sí sigue vigente: para 2001-2016, FACPCE empalma con IPIM (precios **mayoristas**, no de consumidor) -- `salario_real` de esos años queda deflactado por un proxy mayorista, no por inflación al consumidor real (ver nota de `ipc` en `registro_variables.csv` para el detalle).
- **Origen:** `ripte` es Primaria; `salario_real` es Derivada.

#### `indice_salarios_total`
- **Significado:** Índice de Salarios (todos los sectores), INDEC.
- **Qué mide:** índice base octubre 2016=100.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `149.1_TL_INDIIOS_OCTU_0_21`), mensual desde 2016-10.
- **Origen:** Primaria.

#### `indice_salarios_privado_registrado`
- **Significado:** Índice de Salarios del sector privado registrado.
- **Qué mide:** índice base octubre 2016=100.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `149.1_SOR_PRIADO_OCTU_0_25`), mensual desde 2015-10.
- **Origen:** Primaria.

#### `indice_salarios_publico`
- **Significado:** Índice de Salarios del sector público.
- **Qué mide:** índice base octubre 2016=100.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `149.1_SOR_PUBICO_OCTU_0_14`), mensual desde 2015-10.
- **Origen:** Primaria.

#### `comercio_exterior_cobros`
- **Significado:** cobros por exportaciones de bienes (Balance Cambiario BCRA).
- **Qué mide:** millones de USD/mes, base caja (no aduanero).
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `183.1_COBROS_EXPNES_0_M_27`, dataset "por modalidad de pago", total agregado), mensual.
- **Origen:** Primaria.

#### `comercio_exterior_pagos`
- **Significado:** pagos por importaciones de bienes (Balance Cambiario BCRA).
- **Qué mide:** millones de USD/mes, base caja.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `183.1_PAGOS_IMPONES_0_M_26`), mensual.
- **Origen:** Primaria.

#### `gasto_deuda_publica_nivel`
- **Significado:** gasto en servicios de la deuda pública nacional.
- **Qué mide:** millones de pesos, frecuencia **anual** (catálogo separado del resto, ver `catalogo_series_anuales.csv`).
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `451.3_GPN_SERVICICA_0_0_27_85`), anual.
- **Origen:** Primaria.

#### `gasto_deuda_publica_pib`
- **Significado:** gasto en servicios de deuda pública como % del PBI.
- **Qué mide:** porcentaje del PBI, ya multiplicado por 100 (`1.9` = 1,9%), anual.
- **Cómo se calcula:** campo crudo de datos.gob.ar (id `451.4_GPN_SERVICPIB_0_0_31_93`), anual.
- **Origen:** Primaria.

#### `desocupacion` (variable del panel, `data/tfi_data/registro_variables.csv`)
- **Significado:** alias de `tasa_desocupacion` dentro del panel de `src/ml_models/`.
- **Qué mide:** igual que `tasa_desocupacion` (fracción 0-1).
- **Cómo se calcula:** misma serie de datos.gob.ar, cargada vía `cargar_series_economicas.py` para el panel temporal.
- **Origen:** Primaria (re-etiquetada, no recalculada).

### Capa socioeconómica

#### EPH Gran La Plata (`data/socioeconomia/eph_gran_la_plata*.csv`)

Fuente: microdatos trimestrales INDEC, aglomerado Gran La Plata (`AGLOMERADO=2`, incluye Berisso y Ensenada), 2003T3-2025T4 (86/90 trimestres, faltan 2007T3/2015T3/2015T4/2016T1 por falta de publicación de INDEC). Cambio de fuente en 2016 (DBF histórico → bases actuales INDEC): comparaciones año a año solo válidas dentro de cada tramo (2003-2015 vs. 2016-2025).

##### `tasa_actividad` (EPH Gran La Plata)
- **Significado:** proporción de la población que participa del mercado laboral.
- **Qué mide:** porcentaje, calculado sobre `ESTADO` de la EPH.
- **Cómo se calcula:** ocupados + desocupados / población total, ponderado por `PONDERA`, en `src/socioeconomia/eph_client.py`.
- **Origen:** Derivada (agregación de microdato).

##### `tasa_empleo` (EPH Gran La Plata)
- **Significado:** proporción de la población ocupada.
- **Cómo se calcula:** ocupados / población total, ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `tasa_desocupacion` (EPH Gran La Plata)
- **Significado:** proporción de la PEA sin empleo.
- **Cómo se calcula:** desocupados / (ocupados + desocupados), ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `tasa_informalidad`
- **Significado:** proporción de asalariados sin descuento jubilatorio (empleo no registrado).
- **Qué mide:** porcentaje sobre asalariados, no sobre el total de ocupados.
- **Cómo se calcula:** asalariados con `PP07H` (descuento jubilatorio) = "no" / asalariados con `PP07H` válido (1 o 2), calculada en `eph_client.py`.
- **Origen:** Derivada.

##### `ingreso_ocupacion_principal_medio_todos_ocupados` / `_perceptores`
- **Significado:** ingreso monetario medio de la ocupación principal.
- **Qué mide:** pesos corrientes (nominales, sin deflactar). `_todos_ocupados` trata la no respuesta (`P21=-9`) como ingreso 0, ponderado por `PONDERA`; `_perceptores` excluye a quienes no responden y pondera por `PONDIIO` (ponderador específico de INDEC para esta pregunta).
- **Cómo se calcula:** promedio ponderado de `P21` sobre ocupados, `eph_client.py`.
- **Origen:** Derivada.

##### `ingreso_total_individual_medio_todos` / `_perceptores`
- **Significado:** ingreso total individual (todas las fuentes, no solo laboral).
- **Qué mide:** pesos corrientes, mismo criterio de dos estimandos que el ingreso de ocupación principal.
- **Cómo se calcula:** promedio ponderado de `P47T` (ponderado por `PONDII` en `_perceptores`), `eph_client.py`.
- **Origen:** Derivada.

##### `ipcf_medio`
- **Significado:** Ingreso Per Cápita Familiar medio.
- **Qué mide:** pesos corrientes por integrante del hogar.
- **Cómo se calcula:** promedio ponderado de `IPCF` (campo ya calculado por INDEC en la base EPH), `eph_client.py`.
- **Origen:** Primaria (campo de INDEC) agregada/ponderada en el repo.

##### `pct_patron` / `pct_cuentapropia` / `pct_asalariado` / `pct_trabajador_familiar`
- **Significado:** composición de la ocupación por categoría ocupacional.
- **Qué mide:** porcentaje de ocupados en cada categoría de `CAT_OCUP`.
- **Cómo se calcula:** distribución ponderada de `CAT_OCUP`, `eph_client.py`.
- **Origen:** Derivada.

##### `pct_con_obra_social` / `pct_con_aguinaldo` / `pct_con_vacaciones_pagas`
- **Significado:** indicadores de calidad del empleo asalariado.
- **Qué mide:** porcentaje de asalariados con cada beneficio.
- **Cómo se calcula:** de `PP07G1`/`PP07G2`/`PP07G4`, ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `pct_sin_cobertura_salud`
- **Significado:** población sin cobertura de salud ligada al empleo formal (obra social/prepaga/mutual).
- **Qué mide:** porcentaje de la población; no implica ausencia de acceso al sistema público.
- **Cómo se calcula:** de `CH08`, ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `pct_secundario_completo_o_mas`
- **Significado:** nivel educativo alcanzado, población 25+.
- **Qué mide:** porcentaje con secundario completo o más.
- **Cómo se calcula:** de `NIVEL_ED`, ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `tasa_analfabetismo`
- **Significado:** población que no sabe leer ni escribir, 10+ años.
- **Cómo se calcula:** de `CH09`, ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `tasa_asistencia_escolar`
- **Significado:** asistencia escolar, población 5-24 años.
- **Cómo se calcula:** de `CH10`, ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `hacinamiento_medio` / `pct_hacinamiento_bajo` / `_moderado` / `_critico`
- **Significado:** densidad habitacional del hogar.
- **Qué mide:** `hacinamiento_medio` en personas/cuarto; los `pct_*` son la distribución en 3 tramos de gravedad.
- **Cómo se calcula:** `IX_TOT` (personas)/`II1` (cuartos), ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `pct_agua_red_publica`
- **Significado:** acceso a agua de red pública.
- **Cómo se calcula:** de `IV7`, ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `pct_vivienda_propia` / `pct_inquilino`
- **Significado:** régimen de tenencia de la vivienda.
- **Cómo se calcula:** de `II7`, ponderado, `eph_client.py`.
- **Origen:** Derivada.

##### `tamanio_hogar_medio`
- **Significado:** cantidad media de integrantes por hogar.
- **Cómo se calcula:** promedio ponderado de integrantes del hogar, `eph_client.py`.
- **Origen:** Derivada.

##### `pct_hogares_ayuda_social_gobierno` / `_prestamo_bancario` / `_vendio_pertenencias`
- **Significado:** estrategias de subsistencia del hogar en los últimos 3 meses (conceptualmente distintas entre sí, no combinables en un índice).
- **Cómo se calcula:** de `V5`/`V15`/`V17` respectivamente, ponderado, `eph_client.py`. Desde 2023T4 INDEC dividió `V5` en `V5_01/02/03`; se reconstruye client-side una `V5` equivalente.
- **Origen:** Derivada.

##### `*_por_sexo.csv` / `*_por_edad.csv`
- **Significado:** apertura del núcleo laboral (actividad/empleo/desocupación/informalidad/ingreso) por sexo (`CH04`) y por tramo etario (`CH06`: 10-24/25-39/40-59/60+).
- **Cómo se calcula:** mismas fórmulas que las variables EPH del núcleo laboral, filtrando por sexo o tramo antes de agregar, `eph_client.py`.
- **Origen:** Derivada.

#### ICG / ICC (`data/socioeconomia/icg/*.csv`)

##### `icg_la_plata` / `icg_pais`
- **Significado:** Índice de Confianza en el Gobierno (UTDT/Poliarquía).
- **Qué mide:** nivel de confianza ciudadana en el gobierno nacional, encuesta mensual. `icg_pais` se calcula sobre **todos** los casos del mes sin filtrar ciudad (incluye a La Plata) — es un promedio nacional pooleado, no "resto del país".
- **Cómo se calcula:** promedio ponderado por `ponderacion_UTDT` del microdato UTDT, filtrado por ciudad=La Plata para `icg_la_plata`; `src/socioeconomia/icg_construir_series.py`.
- **Origen:** Derivada (agregación de microdato, `icg_cargar.py`/`icg_construir_series.py`).

##### `brecha`
- **Significado:** diferencia entre la confianza local y la nacional.
- **Qué mide:** `icg_la_plata - icg_pais`. Al incluir La Plata en `icg_pais`, la brecha se autocontiene (no es "La Plata vs. resto del país" puro).
- **Cómo se calcula:** resta directa, `icg_construir_series.py`.
- **Origen:** Derivada.

##### `n_la_plata` / `n_pais`
- **Significado:** tamaño de muestra de cada promedio.
- **Qué mide:** cantidad de encuestados en ese mes/celda — se incluye siempre para que quien use el dato juzgue su confiabilidad (no hay umbral de supresión automática).
- **Origen:** Derivada (conteo).

##### Cortes demográficos ICG (`icg_*_por_edad`/`_por_sexo`/`_por_edu`)
- **Significado:** ICG abierto por tramo etario, sexo o nivel educativo agregado (`edu`, 3 niveles — no `educacion`, que tiene 11 categorías finas).
- **Qué mide:** igual que `icg_la_plata`/`icg_pais` pero por subgrupo. País a resolución **mensual**, La Plata a resolución **anual** (decisión deliberada por tamaño de muestra: La Plata tiene N=6-92 por mes, insuficiente para partir en subgrupos).
- **Cómo se calcula:** `icg_construir_series.construir_series_demograficas`.
- **Origen:** Derivada.

#### Censo (radios censales)

##### `B_POB_TOT`/`POB_TOT_P`, `B_VIV_TOT`/`VIV_TOT_P`
- **Significado:** población total y viviendas totales por radio censal (Censo 2010 y 2022 respectivamente, nombres de columna distintos entre años).
- **Qué mide:** conteos absolutos de personas y viviendas.
- **Cómo se calcula:** campo crudo de la cartografía armonizada CONICET (`radios_censales_2010_la_plata.geojson`/`_2022_la_plata.geojson`), ya contado por INDEC.
- **Origen:** Primaria.

##### `circuito_radio_correspondencia.csv` (columnas de cruce)
- **Significado:** crosswalk espacial circuito electoral ↔ radio censal.
- **Qué mide:** proporción de área de cada radio que cae dentro de cada circuito (join ponderado por área, no 1 a 1) — 44-47% de los radios de La Plata quedan repartidos entre más de un circuito.
- **Cómo se calcula:** intersección geométrica de polígonos, `src/geolocalizacion/geo.py`.
- **Origen:** Derivada.

### Capa de geolocalización

Fuente: `data/geolocalizacion/localidades_la_plata.csv` (generado por `src/geolocalizacion/catalogo.py`) y `data/geolocalizacion/circuitos_por_localidad.csv`.

#### `nombre`
- **Significado:** nombre de la localidad/asentamiento censal del Partido de La Plata.
- **Qué mide:** identificador textual del lugar; es el nombre "canónico" del catálogo (nunca se usa el nombre alternativo del Ministerio como salida).
- **Cómo se calcula:** campo crudo de Georef-AR (`GET /api/asentamientos?municipio=060441`).
- **Origen:** Primaria (Georef-AR).

#### `georef_id`
- **Significado:** identificador interno del asentamiento en Georef-AR.
- **Qué mide:** clave de referencia cruzada contra la API de Georef.
- **Cómo se calcula:** campo crudo de Georef-AR.
- **Origen:** Primaria (Georef-AR).

#### `lat`, `lon`
- **Significado:** coordenadas del centroide de la localidad.
- **Qué mide:** ubicación geográfica principal, la que usa `geolocalizacion.mapa` para graficar.
- **Cómo se calcula:** campo crudo de Georef-AR (centroide del asentamiento).
- **Origen:** Primaria (Georef-AR).

#### `uta_2020`, `uta_2010`
- **Significado:** código de Unidad Territorial de Análisis (nomenclador nacional de localidades) según las versiones 2020 y 2010.
- **Qué mide:** identificador administrativo estandarizado de la localidad.
- **Cómo se calcula:** campos crudos de `data/geolocalizacion/fuentes_extra/localidades.csv` (Ministerio de Obras Públicas). En las 35 filas de La Plata, `uta_2010` coincide exactamente con `uta_2020` porque el código no se revisó entre esos años para este municipio (no es un bug ni una duplicación).
- **Origen:** Primaria (Ministerio de Obras Públicas / SNOP).

#### `lat_ministerio`, `lon_ministerio`
- **Significado:** coordenadas del centroide de la localidad según la segunda fuente (Ministerio de Obras Públicas).
- **Qué mide:** ubicación geográfica alternativa, usada solo para contrastar contra `lat`/`lon` de Georef.
- **Cómo se calcula:** campos crudos de `fuentes_extra/localidades.csv`.
- **Origen:** Primaria (Ministerio de Obras Públicas).

#### `delta_metros`
- **Significado:** distancia entre las dos fuentes de coordenadas para la misma localidad.
- **Qué mide:** discrepancia geográfica entre Georef-AR y el Ministerio (mediana 575 m, máximo ~7 km en el catálogo).
- **Cómo se calcula:** distancia haversine entre `(lat, lon)` y `(lat_ministerio, lon_ministerio)`, función `_haversine_metros` en `catalogo.py`; vacío cuando `fuentes = solo_georef`.
- **Origen:** Derivada (`src/geolocalizacion/catalogo.py`).

#### `fuentes`
- **Significado:** qué fuente(s) confirmaron esa localidad.
- **Qué mide:** cobertura del cruce — `"georef+ministerio"` (35 de 36 localidades) o `"solo_georef"` (solo Buchanan).
- **Cómo se calcula:** resultado del match por nombre normalizado (mayúsculas, sin acentos/paréntesis/puntos), con dos alias manuales (`"ISLA MARTIN GARCIA"` ↔ `"Martín García"`, `"BARRIO RUTA SOL"` ↔ `"Ruta Sol"`).
- **Origen:** Derivada (`catalogo.py`).

#### `nota`
- **Significado:** aclaración textual sobre casos especiales (hoy solo el caso `solo_georef` de Buchanan).
- **Qué mide:** N/A, es texto explicativo, no una magnitud.
- **Cómo se calcula:** texto fijo agregado por `catalogo.py` cuando corresponde.
- **Origen:** Derivada (`catalogo.py`).

#### `circuito` (en `circuitos_por_localidad.csv`)
- **Significado:** identificador de circuito electoral, uno de los 68 del Partido de La Plata.
- **Qué mide:** unidad geográfica electoral mínima usada en toda la capa electoral.
- **Cómo se calcula:** campo crudo de la capa electoral (ver `circuito_id` en la capa electoral).
- **Origen:** Primaria.

#### `localidad` (en `circuitos_por_localidad.csv`)
- **Significado:** localidad del catálogo geolocalizado asignada a ese circuito.
- **Qué mide:** a qué localidad pertenece (aproximadamente) cada circuito electoral.
- **Cómo se calcula:** nearest-neighbor entre el centroide del circuito y las 36 localidades de `localidades_la_plata.csv` (no hay polígono por localidad para hacer punto-en-polígono).
- **Origen:** Derivada (crosswalk generado a partir del catálogo de geolocalización; ver `data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md`).

#### `distancia_metros` (en `circuitos_por_localidad.csv`)
- **Significado:** distancia entre el circuito y la localidad asignada.
- **Qué mide:** calidad/confianza de la asignación nearest-neighbor — cuanto mayor, más incierta la asignación.
- **Cómo se calcula:** distancia geográfica circuito↔localidad más cercana.
- **Origen:** Derivada.

### Panel temporal (`src/ml_models`)

Fuente principal: `docs/especificaciones/especificacion_panel_temporal.md` y `docs/decisiones_metodologicas.md` (D1-D19). El panel modela **transiciones electorales** (elección t-1 → t) para tres niveles de gobierno (`municipal`, `provincial`, `nacional`), 2001-2025, cruzadas con series macroeconómicas nacionales.

#### `calendario_electoral.csv`

##### `anio`, `nivel`
- **Significado:** año e instancia de gobierno (`municipal`/`provincial`/`nacional`) de una elección.
- **Qué mide:** identificación de la elección. El "nivel" es político, no formal de cargo (una elección legislativa cuenta para el mismo nivel que una ejecutiva de ese gobierno).
- **Cómo se calcula:** construido a mano en `construir_calendario.py` a partir del calendario electoral real 2001-2025.
- **Origen:** Primaria (curada).

##### `fecha_eleccion`
- **Significado:** fecha exacta de esa elección para ese nivel.
- **Qué mide:** corte temporal preciso, necesario porque 2025 desdobla provincial/municipal de la nacional.
- **Cómo se calcula:** dato histórico curado.
- **Origen:** Primaria (curada).

##### `tipo_eleccion`
- **Significado:** si la elección fue `ejecutiva` (presidente/gobernador/intendente) o `legislativa`.
- **Qué mide:** naturaleza formal del turno electoral, usada para "tipo_eleccion_t"/"tipo_eleccion_t_menos_1" en `ventanas.csv`.
- **Cómo se calcula:** dato curado.
- **Origen:** Primaria (curada).

##### `desdoblada`
- **Significado:** si esa elección de nivel subnacional se votó en fecha separada de la nacional.
- **Qué mide:** booleano de desdoblamiento (2025 es el único caso relevante del período, ver D4; hay más desdoblamientos PBA 2001-2011).
- **Cómo se calcula:** dato curado.
- **Origen:** Primaria (curada).

##### `cargos_en_juego`
- **Significado:** qué cargos se votaban ese día para ese nivel (ej. "diputados provinciales", "concejales").
- **Qué mide:** descripción textual de la oferta electoral formal.
- **Cómo se calcula:** dato curado.
- **Origen:** Primaria (curada).

#### `oficialismo_por_nivel.csv`

##### `agrupacion_oficialismo`
- **Significado:** agrupación que ocupa el Ejecutivo real de ese nivel al momento de la elección.
- **Qué mide:** titularidad del gobierno, base para medir voto económico/responsabilización.
- **Cómo se calcula:** estado que solo cambia en años con elección ejecutiva; **nunca** se deriva de quién ganó esa misma elección (evitaría tautologizar `gana_oficialismo`).
- **Origen:** Derivada (`ml_models.construir_calendario`, curada con `oficialismos.csv`).

##### `campo_ideologico`, `filiacion_politica`, `vparty_economico`, `vparty_progresismo`, `vparty_populismo` (en este archivo)
- **Significado:** clasificación ideológica del oficialismo de turno (mismas columnas que en `clasificacion_ideologica_agrupaciones.csv`, ver capa electoral).
- **Qué mide:** posición ideológica del gobierno en funciones.
- **Cómo se calcula:** join contra `clasificacion_ideologica_agrupaciones.csv` por `(agrupacion_oficialismo, año, nivel)`.
- **Origen:** Derivada (join).

##### `continuidad_oficialismo`
- **Significado:** si el oficialismo de la elección `t` es "la misma fuerza" que en `t-1`.
- **Qué mide:** categoría de continuidad política: `continua` (misma agrupación/etiqueta), `continua_renombrada` (misma fuerza política, etiqueta distinta, ej. provincial 2007: Solá→Scioli), `ruptura` (el oficialismo no compite o se fragmenta, ej. nacional 2023→2025). Estos son los únicos tres valores reales del pipeline — la especificación había previsto una cuarta categoría, `sin_oficialismo`, para la crisis de diciembre de 2001, pero nunca se activa: a nivel nacional la ventana 2001-2003 sí está en el panel desde D31 y da `ruptura` (Alianza→PJ, sin `share_oficialismo` resoluble porque la Alianza no compitió en esa boleta), no una categoría aparte; a nivel provincial/municipal el titular de octubre de 2001 (PARTIDO JUSTICIALISTA en ambos, antes de la crisis) es continuo (Ruckauf→Solá, Alak reelecto).
- **Cómo se calcula:** codificado a mano según el criterio anterior; condiciona si `delta_v` es directamente interpretable.
- **Origen:** Derivada (curada).

#### `ventanas.csv`

##### `id_transicion`
- **Significado:** identificador único de una transición electoral, ej. `municipal_2001_2003`.
- **Qué mide:** clave primaria de la unidad de análisis del panel (la transición, no la elección individual).
- **Cómo se calcula:** `f"{nivel}_{anio_t_menos_1}_{anio_t}"`.
- **Origen:** Derivada.

##### `anio_t`, `anio_t_menos_1`, `anio_t_menos_2`
- **Significado:** año de la elección de llegada (`t`), la anterior (`t-1`) y la previa a esa (`t-2`, si existe).
- **Qué mide:** los tres puntos temporales que definen ventana corta y bloque largo.
- **Cómo se calcula:** derivado del orden cronológico de `calendario_electoral.csv` para ese nivel. `anio_t_menos_2` queda vacío en la primera transición de cada nivel (no hay bloque largo).
- **Origen:** Derivada.

##### `fecha_inicio_vc`, `fecha_fin_vc`
- **Significado:** inicio y fin de la ventana corta (`_vc`), la transición `t-1 → t`.
- **Qué mide:** rango temporal (~24 meses nominales, en la práctica 18-30 meses en años con desdoblamiento PBA) sobre el que se calculan los features intraventana.
- **Cómo se calcula:** `fecha_eleccion(t-1)` y `fecha_eleccion(t)`.
- **Origen:** Derivada.

##### `fecha_inicio_vl`
- **Significado:** inicio del bloque largo (`_vl`), la transición `t-2 → t` (~48 meses).
- **Qué mide:** rango temporal ampliado para features de bloque largo; vacío en la primera transición de cada nivel (D3).
- **Cómo se calcula:** `fecha_eleccion(t-2)` cuando existe.
- **Origen:** Derivada.

##### `tipo_eleccion_t`, `tipo_eleccion_t_menos_1`
- **Significado:** tipo de elección (ejecutiva/legislativa) en cada extremo de la transición.
- **Qué mide:** contexto institucional de la transición.
- **Cómo se calcula:** pass-through de `calendario_electoral.csv`.
- **Origen:** Derivada (join).

#### `panel_ventanas.csv` — familias de features por sufijo

Para cada variable del registro con `paquete_atributos=completo` (las 9
macro -- `icg`, `icc`, `ipc`, `tc_oficial`, `emae`, `desocupacion`,
`salario_real`, `reservas`, `resultado_fiscal` -- y `tasa_informalidad`,
EPH) se calculan, sobre la ventana corta (`_vc`) y el bloque largo (`_vl`),
los siguientes features genéricos (`features_ventana.py`, iterando sobre
`registro_variables.csv`, nunca una lista fija en código). Las variables
con `paquete_atributos=reducido` (las otras 5 EPH: `pct_sin_cobertura_salud`,
`hacinamiento_medio`, `pct_hogares_ayuda_social_gobierno`,
`pct_hogares_prestamo_bancario`, `pct_hogares_vendio_pertenencias`) reciben
solo `<var>_nivel_vc`, `<var>_delta_nivel` y `<var>_cobertura_parcial` --
series de ritmo más lento/estructural que no necesitan el detalle de
trayectoria completo en una ventana de 24 meses (D26):

| Sufijo | Fórmula |
|---|---|
| `<var>_nivel_vc` / `_vl` | media de los valores mensuales de la variable en la ventana |
| `<var>_pendiente_vc` / `_vl` | coeficiente de la regresión lineal de la variable sobre el índice temporal dentro de la ventana |
| `<var>_volatilidad_vc` / `_vl` | desvío estándar de los valores mensuales en la ventana |
| `<var>_final_vc` | media de los últimos 6 meses antes de la elección `t` (solo `_vc` -- `_vl` sería siempre idéntico, `vc`/`vl` comparten `fecha_fin_vc`; retirado, D25) |
| `<var>_acum` | variación acumulada en la ventana (solo si `es_flujo=true`, ej. inflación) |
| `<var>_delta_nivel` | `<var>_nivel_vc(t) − <var>_nivel_vc(t−1)` |
| `<var>_delta_pendiente` | `<var>_pendiente_vc(t) − <var>_pendiente_vc(t−1)` |
| `<var>_cobertura_parcial` | booleano flag: si dentro de la ventana hubo un tramo sin dato real (el feature se calcula igual sobre los meses disponibles, sin imputar) |

Origen de toda la familia: Derivada (`src/ml_models/features_ventana.py`, orquestada por `construir_panel_ventanas.py`).

#### Variables no repetidas de `panel_ventanas.csv` / `elecciones.csv`

##### `delta_v`
- **Significado:** variable dependiente principal del panel.
- **Qué mide:** cambio en el share de voto del oficialismo de ese nivel entre `t-1` y `t`, sobre el total del distrito La Plata.
- **Cómo se calcula:** `share_oficialismo(t) − share_oficialismo(t−1)`.
- **Origen:** Derivada.

##### `gana_oficialismo`, `share_oficialismo`, `agrupacion_oficialismo` (en `elecciones.csv`)
- **Significado:** si el oficialismo ganó esa elección, qué % de votos sacó, y quién es.
- **Qué mide:** resultado electoral del titular del Ejecutivo de ese nivel.
- **Cómo se calcula:** `ml_models.construir_resultado_distrito._entrada_oficialismo`, resuelto por identidad/alias curado (`ALIAS_LISTA_OFICIALISMO`.
- **Origen:** Derivada.

##### `n_fuerzas_viables`
- **Significado:** cantidad de agrupaciones "viables" en esa elección.
- **Qué mide:** fragmentación de la oferta electoral.
- **Cómo se calcula:** cuenta de agrupaciones con `share ≥ 1.5%` sobre `votos_positivos` (piso legal, Ley 26.571 de 2011, aplicado retroactivamente como criterio analítico).
- **Origen:** Derivada.

##### `share_marginal_acumulado`
- **Significado:** proporción del voto que se "pierde" en fuerzas no viables.
- **Qué mide:** suma de `share` de las agrupaciones por debajo del piso de 1.5%.
- **Cómo se calcula:** suma directa.
- **Origen:** Derivada.

##### `share_oposicion_principal`
- **Significado:** fuerza opositora con más votos.
- **Qué mide:** `share` de la fuerza viable no oficialista más votada.
- **Cómo se calcula:** máximo de `share` entre fuerzas viables ≠ oficialismo.
- **Origen:** Derivada.

##### `share_otras_fuerzas_viables`
- **Significado:** resto de fuerzas viables, ni oficialismo ni oposición principal.
- **Qué mide:** cierra la identidad `share_marginal_acumulado + share_oposicion_principal + share_otras_fuerzas_viables + share_oficialismo(si viable) = 100`.
- **Cómo se calcula:** suma de `share` del resto de fuerzas viables.
- **Origen:** Derivada.

##### `dispersion_economico_mu`, `dispersion_progresismo_mu`
- **Significado:** posición ideológica promedio del electorado del distrito en esa elección, en cada eje V-Party.
- **Qué mide:** centro de gravedad ideológico del voto (nunca la ideología del ganador atribuida a todo el distrito — disciplina anti-falacia ecológica del proyecto).
- **Cómo se calcula:** media de `vparty_economico`/`vparty_progresismo` ponderada por share de voto, solo entre fuerzas viables con score V-Party cargado (función `_dispersion_ponderada`).
- **Origen:** Derivada.

##### `dispersion_economico_sigma2`, `dispersion_progresismo_sigma2`
- **Significado:** dispersión (varianza) ideológica del electorado en cada eje.
- **Qué mide:** polarización/fragmentación ideológica del voto, no solo su centro.
- **Cómo se calcula:** varianza ponderada por voto de `vparty_economico`/`vparty_progresismo`, mismas fuerzas que `dispersion_*_mu`.
- **Origen:** Derivada.

##### `dispersion_cobertura_share`
- **Significado:** qué fracción del voto está representada en `dispersion_*_mu/sigma2`.
- **Qué mide:** calidad del dato de dispersión — sin esto, un salto en `dispersion_economico_mu` no se puede distinguir de un cambio en cuánto voto tiene V-Party cargado (D18).
- **Cómo se calcula:** `(votos de fuerzas viables con V-Party cargado) / votos_positivos`, escala 0-100. Vale `0.0` (no vacío) si ninguna fuerza viable tiene score.
- **Origen:** Derivada.

##### `resultado_disponible`
- **Significado:** si la fila de `elecciones.csv` salió del dato de mayor calidad.
- **Qué mide:** `True` si vino de `circuito_<cargo>.json` (agregado real de circuitos); `False` si vino del fallback `elecciones/<año>_<nivel>.csv` (años sin desagregado por circuito, 2001-2009, y 2025 provincial/municipal).
- **Origen:** Derivada.
- **Nota:** existe en `elecciones.csv` (y en `resultado_distrito.csv`, congelado); ya **no** aparece en `panel_ventanas.csv` -- se retiró por D24 al no tener ningún uso crítico (nunca filtraba filas ni condicionaba otro cálculo).

##### `continuidad_oficialismo` (en el panel)
Ver definición en `oficialismo_por_nivel.csv` arriba; se propaga por join.

##### `delta_posicion_ideologica`
- **Significado:** variable dependiente secundaria para H2.
- **Qué mide:** cambio en la posición ideológica ponderada del electorado entre `t-1` y `t` (promedio de scores V-Party ponderado por voto).
- **Cómo se calcula:** `dispersion_economico_mu(t) − dispersion_economico_mu(t−1)` (u homólogo, ver `construir_panel_ventanas.py`).
- **Origen:** Derivada.

##### `delta_dispersion_economico_mu`, `delta_dispersion_progresismo_mu`
- **Significado:** hacia dónde se movió el centro ideológico del electorado.
- **Qué mide:** `dispersion_<eje>_mu(t) − dispersion_<eje>_mu(t−1)`, por eje.
- **Cómo se calcula:** join de `elecciones.csv` en las dos puntas de la transición.
- **Origen:** Derivada.

##### `delta_sigma2_economico`, `delta_sigma2_progresismo`
- **Significado:** cambio en la fragmentación/polarización ideológica del electorado.
- **Qué mide:** `dispersion_<eje>_sigma2(t) − dispersion_<eje>_sigma2(t−1)`; a diferencia de los deltas de `mu`, no se cancela cuando fuerzas de polos opuestos crecen simultáneamente (caso real: LLA/FIT-U 2021).
- **Cómo se calcula:** misma función `calcular_delta_dispersion` que los deltas de `mu`, con parámetro `estadistico="sigma2"`.
- **Origen:** Derivada.

##### `magnitud_desplazamiento_ideologico`
- **Significado:** tamaño total del desplazamiento ideológico del electorado entre dos elecciones.
- **Qué mide:** distancia euclídea del vector de desplazamiento.
- **Cómo se calcula:** `√(delta_dispersion_economico_mu² + delta_dispersion_progresismo_mu²)`.
- **Origen:** Derivada.

##### `cuadrante_desplazamiento`
- **Significado:** dirección del desplazamiento ideológico del electorado.
- **Qué mide:** `derecha`/`izquierda` según el signo de `delta_dispersion_economico_mu`, `progresista`/`conservador` según el signo de `delta_dispersion_progresismo_mu`; `None` si falta algún delta o si alguno es exactamente `0`.
- **Cómo se calcula:** mismo criterio de signo que las etiquetas fijas de `vparty_cuadrantes`/`vparty_localidad`, aplicado al vector de desplazamiento.
- **Origen:** Derivada.

##### `dispersion_cobertura_share_min`
- **Significado:** calidad mínima de dato de dispersión en la transición.
- **Qué mide:** `min(dispersion_cobertura_share(t), dispersion_cobertura_share(t−1))`, para ponderar/filtrar transiciones con baja cobertura V-Party sin fijar un umbral en código.
- **Origen:** Derivada.

##### `participacion_pct` (y `_t`/`_t_menos_1` en el panel)
- **Significado:** porcentaje de votantes habilitados que efectivamente votó (voto válido + blanco/nulo).
- **Qué mide:** participación electoral.
- **Cómo se calcula:** `(votos_positivos + votos_blancos_y_nulos) / votantes_habilitados * 100`.
- **Origen:** Derivada.

##### `participacion_relevante` / `participacion_relevante_t`
- **Significado:** si la participación de esa elección superó un piso de referencia.
- **Qué mide:** booleano `participacion_pct > 79.0` (`PARTICIPACION_BENCHMARK_NACIONAL_PCT`, benchmark externo: promedio nacional 1983-2023, Chequeado 26/10/2025) — la participación real de La Plata 2001-2025 es 75.7%, por debajo del benchmark.
- **Origen:** Derivada.

##### `voto_exit_ausentismo_pct`, `voto_exit_blanco_nulo_pct` (y sus `_t`/`_t_menos_1`)
- **Significado:** las dos formas de "salida" del voto positivo: no ir a votar, o votar en blanco/nulo.
- **Qué mide:** `voto_exit_ausentismo_pct = ausentismo / votantes_habilitados * 100`; `voto_exit_blanco_nulo_pct = votos_blancos_y_nulos / votantes_habilitados * 100`. La suma de ambas (`voto_exit_total_pct`, equivalente a `100 − participacion_pct`) sigue calculándose internamente en `calcular_participacion_voto_exit`, pero ya no se expone como columna `_t`/`_t_menos_1` del panel: era exactamente redundante con estas dos (D22).
- **Cómo se calcula:** `ml_models.construir_elecciones_resumen.calcular_participacion_voto_exit`.
- **Origen:** Derivada.

##### `delta_participacion_pct`, `delta_voto_exit_ausentismo_pct`, `delta_voto_exit_blanco_nulo_pct`
- **Significado:** cambio de participación/ausentismo/voto en blanco-nulo entre `t-1` y `t`, cada uno por separado (D22: ausentismo y blanco/nulo son fenómenos políticamente distintos, ya no se ofrece un delta "total" combinado).
- **Qué mide:** `participacion_pct_t − participacion_pct_t_menos_1` (e idem para cada componente de voto exit).
- **Origen:** Derivada.

##### `votos_blancos_y_nulos`
- **Significado:** blanco y nulo tratados como una sola categoría.
- **Qué mide:** votos que no son positivos pero sí "activos" (no ausentismo). Unificados porque la Ley 5.109 (PBA 2025) elimina la categoría "nulo" (Art. 88), lo que dejaría a 2025 provincial/municipal sin comparación directa si se mantuvieran separados (D19).
- **Cómo se calcula:** `votos_blancos + (votos_nulos or 0)`.
- **Origen:** Derivada.

##### `ausentismo` (en `elecciones.csv`, propagada al panel)
- **Significado:** votantes habilitados que no emitieron voto válido/blanco/nulo.
- **Qué mide:** abstención electoral.
- **Cómo se calcula:** dos fórmulas según disponibilidad de dato: con `circuito_<cargo>.json`, `electores − positivos − otros_total` (excluye categorías `RECURRIDO(S)`/`IMPUGNADO(S)`/`COMANDO` del ausentismo); sin circuito (2001-2009, 2025 provincial/municipal), `votantes_habilitados − votos_positivos − votos_blancos − (votos_nulos or 0)`. Las dos fórmulas no son exactamente equivalentes (ver D17); vacío solo si faltan los insumos base.
- **Origen:** Derivada.

#### `distancias_ideologicas.csv` (D18)

Grano `(nivel, año, agrupación)`, una fila por fuerza viable, sucesor de `distancia_oficialismo_alternativa`.

##### `es_oficialismo`
- **Significado:** si esa fila es la fuerza que gobierna ese nivel.
- **Cómo se calcula:** comparación por **identidad de objeto** contra `_entrada_oficialismo` (nunca por nombre — esto es lo que corrige el bug de `distancia_oficialismo_alternativa`).
- **Origen:** Derivada.

##### `distancia_economico_al_oficialismo`, `distancia_progresismo_al_oficialismo`
- **Significado:** de qué lado y a qué distancia está esa fuerza respecto del oficialismo, en cada eje V-Party.
- **Qué mide:** `score_fuerza − score_oficialismo`, **con signo** (no valor absoluto) — el signo indica de qué lado cae la fuerza.
- **Origen:** Derivada.

##### `distancia_euclidea_al_oficialismo`
- **Significado:** distancia ideológica total entre esa fuerza y el oficialismo.
- **Qué mide:** `√(distancia_economico² + distancia_progresismo²)`. La fila del propio oficialismo tiene las 3 distancias en `0.0` siempre (incluso sin score propio cargado).
- **Origen:** Derivada.

#### Panel trimestral (`data/tfi_data/panel/t-1/`, `t-2/`)

Mismas columnas de `elecciones.csv`/variables núcleo, pero en formato largo por trimestre dentro de cada ventana (D13/D14).

##### `orden`, `tipo_fila`
- **Significado:** posición del trimestre dentro de la ventana y tipo de fila (`trimestre` vs. filas frontera `eleccion_t`/`eleccion_t_menos_1`/`eleccion_t_menos_2`).
- **Qué mide:** estructura del panel largo — las filas frontera son las que llevan las columnas de `elecciones.csv` (D17/D18) para poder graficar el resultado electoral en la misma línea de tiempo que las variables económicas.
- **Origen:** Derivada.

##### `n_meses`
- **Significado:** cantidad de meses reales de esa ventana.
- **Qué mide:** duración real de la transición (varía 18-30 meses, no fija en 24), usada para calcular N de trimestres = `round(meses_entre_elecciones / 3)` (D13, entre 6 y 10 trimestres, nunca fijo en 8).
- **Origen:** Derivada.

##### `<variable núcleo>` (ej. `icg`, `ipc`, `desocupacion`, ... en el panel trimestral)
- **Significado:** valor de esa variable macro en ese trimestre.
- **Qué mide:** nivel trimestral de la serie, para graficar trayectorias económicas (`src/visualizacion/trayectorias_economicas*.py`).
- **Cómo se calcula:** agregación trimestral de la serie mensual de `series_economicas_mensuales.csv`.
- **Origen:** Derivada.

---

## Modelos de machine learning

### Regresión OLS (mínimos cuadrados ordinarios)
- **Modo de uso general:** ajusta una combinación lineal de variables explicativas (`X`) a una variable dependiente continua (`y`) minimizando la suma de errores cuadráticos, sin ningún término de penalización. Es el punto de referencia clásico de la regresión lineal: con `P` variables y `N` observaciones, si `P >= N` el sistema queda subdeterminado (infinitas soluciones con error de entrenamiento ~0), y aunque `P < N` puede sobreajustar si hay variables muy correlacionadas entre sí (multicolinealidad).
- **Uso en este proyecto:** se usa solo como control de validación del Lasso propio en `notebooks/ml/ventana_t-1/01.1_lasso_voto_valido.ipynb` (vía `np.linalg.lstsq`), no como modelo de producción: confirma que con `alpha=0` el Lasso manual converge al mismo régimen degenerado que OLS cuando `P=21 > N-1` (residuo de entrenamiento ~0 en ambos, aunque los coeficientes difieran mucho entre sí por tratarse de un sistema subdeterminado con infinitas soluciones). El panel de este proyecto (`panel_ventanas.csv`, 7 a 12 filas por nivel, ~127 columnas) está estructuralmente en régimen `P >> N`, razón por la cual el proyecto no usa OLS simple como modelo final en ningún nivel.

### Regresión Lasso (regresión lineal con regularización L1) — implementación propia por coordinate descent
- **Modo de uso general:** es una regresión lineal que, además de minimizar el error cuadrático, penaliza la suma de los valores absolutos de los coeficientes (`α·‖β‖₁`). Esa penalización L1 (a diferencia de la L2 de Ridge) tiene la propiedad de llevar coeficientes exactamente a cero, por lo que además de "encoger" las estimaciones actúa como un método de selección automática de variables: con un `α` suficientemente grande, sólo sobreviven (coeficiente ≠ 0) las variables con señal más fuerte. Es especialmente útil cuando hay muchas variables candidatas frente a pocas observaciones (régimen `P` grande, `N` chico) o alta colinealidad entre predictores, escenarios donde OLS es inestable o no identificado.
- **Uso en este proyecto:** predice, según el notebook, `delta_v` (cambio en el porcentaje de votos del oficialismo entre `t-1` y `t`, en `01.1_lasso_voto_valido.ipynb`), `delta_participacion_pct` (cambio en la participación electoral, en `01.2_lasso_voto_ausentismo.ipynb`), `delta_voto_exit_total_pct` (cambio en el "voto exit" ausentismo+blanco/nulo, en `01.3_lasso_voto_exit.ipynb`) y `magnitud_desplazamiento_ideologico` (desplazamiento del electorado en el espacio económico/progresismo V-Party, en `03_desplazamiento_ideologico.ipynb`, hipótesis H2/H3) — todos a partir de `data/tfi_data/panel_ventanas.csv`, con features de trayectoria económica de la ventana corta (`*_vc`: nivel/pendiente/volatilidad/delta de variables como `icg`, `ipc`, `desocupacion`, `tc_oficial`, `reservas`, `salario_real`, `resultado_fiscal`, `emae`, `icc`).

  El motivo declarado para elegir Lasso en vez de OLS es explícito en el propio notebook: el panel tenía muy pocas observaciones por nivel (`municipal: 12`, `provincial: 12`, `nacional: 7` transiciones antes de D31, 12 después, frente a ~20+ columnas candidatas), un régimen `P>>N` donde OLS sin penalizar queda subdeterminado; además hay clusters de colinealidad casi perfecta entre variables (`ipc_*` y `tc_oficial_*`, `r>0.98`), que Lasso maneja mejor que OLS al forzar selección. Antes de ajustar el modelo final se colapsan esos clusters redundantes vía `encontrar_redundantes`/`elegir_representante` (agrupamiento por correlación con umbral, un representante por cluster elegido por menor cantidad de NaN, prioridad teórica y sufijo de la variable), para no dejar que Lasso reparta arbitrariamente el coeficiente entre variables casi idénticas.

  **Selección del hiperparámetro `α` vía LOO-CV manual** (`lasso_loocv_manual`): con tan pocas observaciones no se separa un set de test fijo; en su lugar se hace validación cruzada leave-one-out (dejar una transición afuera, ajustar con el resto, predecir esa transición, repetir para las `N` transiciones) sobre una grilla logarítmica de `α` entre `alpha_max_lasso` (el `α` más chico que anula todos los coeficientes) y una fracción de ese máximo, reportando el `α` de mínimo error (`alpha_min`) y el `α` más grande dentro de un desvío estándar del mínimo (`alpha_1se`, criterio "one standard error" que prioriza modelos más simples/parsimoniosos). El resultado se compara contra `baseline_trivial_loocv` (predecir siempre el promedio de las demás observaciones), el piso mínimo de comparación. Como chequeo adicional de robustez, `estabilidad_seleccion` reajusta el modelo final (mismo `α` ya elegido) sacando una transición a la vez, para ver si la selección de variables depende de un punto influyente puntual o es un patrón sostenido en los datos (leave-one-transition-out).

### Regresión bayesiana jerárquica (modelo lineal con pooling parcial, muestreo MCMC/NUTS)
- **Modo de uso general:** en vez de estimar un único punto óptimo para cada parámetro (como hace OLS/Lasso), el enfoque bayesiano trata a los parámetros como variables aleatorias con una distribución previa (*prior*) que se actualiza con los datos observados para obtener una distribución posterior, de la que se puede leer tanto el valor más probable como la incertidumbre asociada. Un modelo *jerárquico con pooling parcial* permite que cada grupo (acá, cada nivel electoral) tenga su propio coeficiente, pero esos coeficientes de grupo comparten un "hiperprior" común que los acerca entre sí (un punto intermedio entre estimar cada grupo por separado —sin pooling— y forzarlos a ser todos iguales —pooling total—), lo cual ayuda especialmente cuando algunos grupos tienen pocas observaciones. La estimación numérica de la posterior se hace por métodos de cadenas de Markov Monte Carlo (MCMC), en este caso el muestreador NUTS (No-U-Turn Sampler), que evalúa la convergencia con diagnósticos como `r_hat` (cercano a 1 indica que las cadenas convergieron al mismo lugar), `ess_bulk`/`ess_tail` (tamaño de muestra efectivo) y el conteo de "divergencias" (transiciones numéricamente problemáticas del muestreador).
- **Uso en este proyecto:** implementado en `notebooks/ml/ventana_t-1/02_bayes.ipynb` con la librería `pymc` (más `arviz` para los diagnósticos) — ninguna de las dos está en `requirements.txt`, que solo declara `statsmodels`, así que es una dependencia usada puntualmente en ese notebook y no parte del stack declarado del repo. Modela `delta_v` (mismo target que `01.1_lasso_voto_valido.ipynb`) en función de una única variable estandarizada, `icg_pendiente_vc` (elegida por ser la que mostró más señal en el Lasso), con `nivel` (municipal/provincial/nacional) como agrupador jerárquico: `alpha`/`beta` tienen un promedio y una dispersión compartidos entre los tres niveles (`alpha_mu`/`alpha_sigma`, `beta_mu`/`beta_sigma`), con parametrización no-centrada (`beta_nivel = beta_mu + beta_sigma·z_nivel`) para evitar divergencias del muestreador con solo 3 grupos — patrón estándar en modelos jerárquicos bayesianos con pocos grupos. El notebook corre el muestreo con `target_accept=0.95` (3 divergencias en 8000 muestras) y luego con `target_accept=0.99` (0 divergencias), y valida convergencia con `r_hat≈1.00` y `ess` muy por encima de 400 en todos los parámetros. También ajusta, a modo de contraste, una versión **sin pooling** (`modelo_sin_pooling`, un `alpha`/`beta` totalmente independiente por nivel, sin hiperprior compartido) para diagnosticar si el modelo jerárquico da coeficientes parecidos entre niveles (`beta_nivel` similar en los tres) porque el pooling parcial "presta" señal entre niveles, o porque cada nivel ya trae señal propia. Igual que en Lasso, la validación cruzada se hace a mano vía LOO (`loocv_bayesiano_nivel`: para cada punto del nivel, ajusta sin él y predice con la media posterior de `alpha`/`beta`, reportando MSE comparable directo con `baseline_trivial_loocv`).
- **Re-ejecutado tras D31** (extensión de nacional a 2001-2025): `N=10` en nacional (no 12 nominal ni el `N=11` que D31 había estimado -- ver nota de corrección en D31), `N=12` en municipal/provincial. A diferencia de la corrida previa a D31 (con nacional `N=7`), acá Lasso **ya no da 0% de señal en nacional** para `delta_v`: `icg_pendiente_vc` sobrevive con coeficiente positivo y estable (10/10 corridas leave-one-transition-out, valores entre 2.6 y 6.5) al nivel `alpha_min` de `01.1_lasso_voto_valido.ipynb` -- cambia la premisa sobre la que se leía la comparación con el modelo bayesiano, pendiente de revisar la interpretación completa. MSE LOO sin pooling: municipal=83.69, provincial=105.11, nacional=52.46 (baseline trivial nacional=175.34). MSE LOO con pooling parcial: municipal=73.43 (mejora -12.3%), provincial=95.00 (mejora -9.6%), nacional=44.62 (mejora -14.9%) -- la mejora del pooling en nacional ya no es "más del doble" que en los otros dos niveles (hallazgo de la corrida previa a esta extensión), las tres mejoras quedan en un rango más parecido.

### Estandarización (z-score) como paso previo a la regularización
- **Modo de uso general:** no es un modelo en sí sino un preprocesamiento — restar la media y dividir por el desvío estándar de cada variable — necesario en cualquier método que penalice la magnitud de los coeficientes (Lasso/Ridge) o comparta escala entre predictores en un modelo jerárquico, porque sin esa normalización una variable con escala numérica más grande sería penalizada de forma distinta (o dominaría el pooling) solo por su unidad, no por su relevancia real.
- **Uso en este proyecto:** aplicada de forma manual (`estandarizar()` en `src/ml_models/lasso.py`, y su equivalente reimplementado en `03_desplazamiento_ideologico.ipynb`) con `ddof=0`, recalculando medias/desvíos **solo sobre el set de entrenamiento** en cada fold de LOO-CV (nunca sobre el dataset completo antes de partir train/test, para evitar fuga de información del punto dejado afuera) tanto en el Lasso propio como, de forma análoga, en la variable única de `02_bayes.ipynb` (`x_std`, estandarizada sobre el pool completo apilado de los tres niveles antes de correr el modelo jerárquico).

---

## Conceptos teóricos

### Escala ideológica izquierda-derecha (`campo_ideologico`)
- **Definición original:** El eje izquierda-derecha es la síntesis unidimensional más usada en ciencia política para ubicar a partidos y votantes, condensando posiciones sobre redistribución económica, rol del Estado y, según el autor, también clivajes culturales. Su formulación moderna arranca en Anthony Downs (1957), que modela la competencia partidaria como posicionamiento en una recta izquierda-derecha al estilo Hotelling.
- **Usos en ciencias sociales:** Es la variable de posicionamiento más replicada en encuestas de expertos (Chapel Hill Expert Survey, Comparative Manifesto Project, V-Party) y en estudios de opinión pública (autoubicación 1-10), usada para clasificar oferta partidaria, medir polarización y estimar distancia ideológica votante-partido.
- **Bibliografía:** Downs, A. (1957) *An Economic Theory of Democracy*; Budge, Robertson & Hearl (1987) *Ideology, Strategy and Party Change* (origen del Manifesto Project); Bakker et al., series del Chapel Hill Expert Survey (CHES); Huber & Inglehart (1995) sobre el significado cross-nacional de izquierda-derecha.
- **Uso en este proyecto:** Columna `campo_ideologico` en `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`, escala ordinal de 6 valores (`data/agrupaciones/campo_ideologico.csv`: 1=izquierda, 2=centro izquierda, 3=centro, 4=centro derecha, 5=derecha, 6=derecha radical), clasificada a mano por agrupación/año/nivel. Es un join estricto (`KeyError` si falta, ver `CLAUDE.md`) usado en `src/analisis/graficos.py` y toda la capa de gráficos por campo ideológico.

### V-Party (Varieties of Party Identity and Organization, V-Dem Institute)
- **Definición original:** V-Party es un dataset académico del V-Dem Institute (Universidad de Gotemburgo) que codifica, vía panel de expertos país, posiciones programáticas y organizativas de partidos políticos de todo el mundo en múltiples dimensiones (económica, cultural, populismo, clientelismo, etc.), complementando el proyecto V-Dem de calidad democrática.
- **Usos en ciencias sociales:** Se usa para estudios comparados de sistemas de partidos, polarización, populismo y democracia iliberal a nivel global, permitiendo comparar posiciones partidarias entre países y en el tiempo con una metodología común de codificación por expertos.
- **Bibliografía:** Lindberg, S. et al. (2022) *"Codebook Varieties of Party Identity and Organization (V-Party) V2"*, V-Dem Institute; Meijers, M. & Zaslove, A. (2021) *"Measuring Populism in Political Parties: Appraisal of a New Approach"*, Comparative Political Studies (fuente metodológica del índice de populismo que V-Party incorpora); Coppedge, M. et al., proyecto V-Dem (Varieties of Democracy).
- **Uso en este proyecto:** Tres columnas derivadas de V-Party — `vparty_economico` (`v2pariglef`), `vparty_progresismo` (promedio de `v2palgbt`, `v2pawomlab`, `v2paimmig`, `v2parelig`) y `vparty_populismo` (`v2xpa_popul`) — pobladas en `clasificacion_ideologica_agrupaciones.csv` para partidos con cobertura real (2001-2019, ola argentina de V-Party) más una estimación propia calibrada (`v_party_propio.csv`) para partidos sin cobertura. Fuente completa y metodología de join en `data/agrupaciones/v-party/README.md`. Estas tres dimensiones alimentan `analisis.vparty_cuadrantes`/`vparty_localidad`/`vparty_distribucion_tfi`, la pestaña interactiva `distribucion_ideologica_interactiva.py`, y las columnas de dispersión ideológica de `elecciones.csv` (D17) y `distancias_ideologicas.csv` (D18).

### Populismo
- **Definición original:** En ciencia política contemporánea, el populismo se conceptualiza predominantemente en clave ideacional (Mudde) como una ideología delgada (*thin ideology*) que divide a la sociedad en "pueblo puro" vs. "élite corrupta" y sostiene que la política debe expresar la voluntad general del pueblo; enfoques alternativos lo tratan como estrategia política (Weyland) o estilo discursivo/retórico (Hawkins).
- **Usos en ciencias sociales:** Se opera empíricamente mediante análisis de discurso, encuestas de expertos (como V-Party/Global Party Survey) o análisis de manifiestos, para clasificar partidos y medir su grado de retórica antiestablishment y apelación al "pueblo" contra las "élites".
- **Bibliografía:** Mudde, C. (2004) *"The Populist Zeitgeist"*, Government and Opposition; Mudde, C. & Rovira Kaltwasser, C. (2017) *Populism: A Very Short Introduction*; Hawkins, K. (2009) *"Is Chávez Populist?"*, Comparative Political Studies; Weyland, K. (2001) *"Clarifying a Contested Concept: Populism in the Study of Latin American Politics"*.
- **Uso en este proyecto:** Columna `vparty_populismo` (de `v2xpa_popul`, índice V-Party 0-1 basado en el enfoque de Meijers & Zaslove), presente en `clasificacion_ideologica_agrupaciones.csv` y `oficialismos.csv`. Deliberadamente **excluida** de los cuadrantes ideológicos graficados (`vparty_localidad.py`, `vparty_distribucion_tfi.py`) — queda solo como columna de datos disponible, no como eje de encoding visual.

### Filiación política / familia política (party family)
- **Definición original:** El concepto de "familia de partidos" (party family) agrupa partidos de distintos países o momentos históricos que comparten origen genético, ideología transnacional o vínculos organizativos (p.ej. socialdemócratas, democristianos, liberales, comunistas, verdes, radicales de derecha).
- **Usos en ciencias sociales:** Permite comparar partidos entre sistemas de partidos distintos y clasificar oferta electoral por linaje ideológico-organizativo antes que por posición programática puntual en una elección dada.
- **Bibliografía:** Mair, P. & Mudde, C. (1998) *"The Party Family and Its Study"*, Annual Review of Political Science; von Beyme, K. (1985) *Political Parties in Western Democracies* (clasificación clásica de familias partidarias europeas); Gunther, R. & Diamond, L. (2003) *"Species of Political Parties: A New Typology"*, Party Politics.
- **Uso en este proyecto:** Columna `filiacion_politica` en `clasificacion_ideologica_agrupaciones.csv`, con 10 valores propios adaptados al caso argentino (peronistas, peronismo provincial, liberales, marxistas, nacionalistas, progresistas, conservadores, radicalismo, otros, sin_clasificar — ver `data/agrupaciones/tabla_referencia_filiacion_politica.csv`). A diferencia de `campo_ideologico`, es invariante en el tiempo por agrupación (una identidad partidaria, no una posición electoral puntual) — pensada explícitamente para no aplanar genealogías partidarias continuas (ej. FPV/Unidad Ciudadana/Frente de Todos/Unión por la Patria) a una sola posición ideológica (`docs/FUNCIONALIDADES.md`, "Libro de códigos ideológico"). Es también la base del color de cada partido en los gráficos (`colorimetria_familia_politica.csv`).

### Oficialismo / incumbencia (incumbency)
- **Definición original:** "Incumbency" refiere al hecho de ocupar el cargo ejecutivo en el momento de una elección; la literatura de ciencia política electoral estudia sistemáticamente la "ventaja del oficialismo" (incumbency advantage) y, en sentido inverso, el desgaste de gobierno y el castigo retrospectivo al oficialismo.
- **Usos en ciencias sociales:** Se usa como variable de referencia para medir voto de castigo/premio (accountability), continuidad/alternancia, y como línea de base contra la cual se mide la distancia ideológica u electoral de los desafiantes.
- **Bibliografía:** Erikson, R. (1971) *"The Advantage of Incumbency in Congressional Elections"*, Polity; Key, V.O. Jr. (1966) *The Responsible Electorate* (voto retrospectivo, premio/castigo al oficialismo); Fiorina, M. (1981) *Retrospective Voting in American National Elections*.
- **Uso en este proyecto:** `data/agrupaciones/oficialismos.csv` (D15) identifica, por año/nivel, la agrupación ganadora y si esa agrupación **era** oficialismo (`era_oficialismo`) al momento de la elección — corregido a mano para casos de divergencia entre el voto de La Plata y el resultado real provincial/nacional (D12: gobernador 2019, presidente 2023 vía balotaje). `oficialismo_por_nivel.csv` lleva el titular del Ejecutivo como estado que solo cambia en años con elección ejecutiva. Estas tablas alimentan `gana_oficialismo`/`share_oficialismo`/`continuidad_oficialismo`/`agrupacion_oficialismo` en `elecciones.csv` y `panel_ventanas.csv`, y son el punto de referencia de `distancias_ideologicas.csv` (D18): todas las distancias ideológicas de una elección se miden respecto del oficialismo de ese nivel. El titular inicial de cada serie (`_TITULAR_INICIAL_2001` en `construir_calendario.py`) está validado históricamente (D20): octubre de 2001, PARTIDO JUSTICIALISTA gobernaba tanto la provincia (Carlos Ruckauf) como La Plata (Julio Alak) — el nivel nacional de esa fecha era la ALIANZA (Fernando de la Rúa), y desde D31 sí tiene su propia fila en el panel (nacional arranca en 2001, no en 2011).

### Ausentismo electoral / abstención
- **Definición original:** La abstención electoral es la no participación de electores habilitados en una elección; en sistemas de voto obligatorio como el argentino se distingue conceptualmente del voto en blanco/nulo (que sí implica concurrir a votar).
- **Usos en ciencias sociales:** Usada como indicador de desafección política, costo de participación o, en lecturas de "voto económico", como forma pasiva de descontento con el sistema político en su conjunto (a diferencia del castigo activo vía voto opositor).
- **Bibliografía:** Rosenstone, S. y Hansen, J.M. (1993) *Mobilization, Participation, and Democracy in America*; Blais, A. (2000) *To Vote or Not to Vote: The Merits and Limits of Rational Choice Theory* (costo-beneficio de la participación); literatura de participación electoral y voto obligatorio para el caso latinoamericano (Fornos, Power & Garand, 2004).
- **Uso en este proyecto:** Calculado como `electores - positivos - otros_total` para años con `circuito_<cargo>.json` (`analisis.graficos._votos_no_ideologicos`) o como `votantes_habilitados - votos_positivos - votos_blancos - votos_nulos` para años sin circuito (2001-2009, y 2025 provincial/municipal con salvedades legales, ver D17/D19). Graficado siempre en gris neutro junto a `blanco_nulo`, nunca tratado como una opción ideológica más (`docs/FUNCIONALIDADES.md`, "Gráficos"). D19 lo integra en `voto_exit_ausentismo_pct`/`voto_exit_total_pct` junto al voto en blanco/nulo, comparado contra un benchmark externo de participación nacional 1983-2023 (79%, Dirección Nacional Electoral, citado vía Chequeado).

### Voto en blanco / voto nulo (voto de protesta / exit)
- **Definición original:** El voto en blanco expresa participación sin adhesión a ninguna oferta partidaria; el voto nulo (boleta mal emitida o de identidad impugnada) suele leerse como forma de protesta o rechazo activo del sistema de oferta vigente, distinguible de la abstención (no concurrir).
- **Usos en ciencias sociales:** Vinculado a la noción de "exit" de Hirschman (1970) — frente a un producto político insatisfactorio, el elector puede optar por "voz" (voto opositor), "salida" (abstención/voto en blanco) o "lealtad" (voto oficialista) — y usado como proxy de desafección cuando la oferta partidaria no logra representar preferencias.
- **Bibliografía:** Hirschman, A. (1970) *Exit, Voice, and Loyalty*; literatura sobre voto en blanco/nulo como protesta en sistemas de voto obligatorio (Power & Garand, 2007, sobre invalid voting en América Latina); Kang, W.C. (2004) sobre voto nulo como señal de protesta informada.
- **Uso en este proyecto:** `votos_blancos`/`votos_nulos` en `elecciones.csv`, unificados en una sola columna `votos_blancos_y_nulos` (D19) para evitar comparar una distinción que solo existe bajo el régimen legal pre-2025 (la Ley provincial 5.109 elimina la categoría "nulo" en las elecciones bonaerenses 2025). `panel_ventanas.csv`/`panel_trimestral` derivan `voto_exit_blanco_nulo_pct`/`voto_exit_total_pct` (blanco+nulo+ausentismo) como medida agregada de "salida" del sistema de oferta partidaria, en paralelo a `participacion_pct`.

### Voto económico (economic voting) / accountability retrospectiva
- **Definición original:** La teoría del voto económico postula que los electores premian o castigan al oficialismo en función del desempeño económico observado (inflación, desempleo, crecimiento, tipo de cambio), operando como un mecanismo de *accountability* retrospectiva más que de evaluación prospectiva de programas.
- **Usos en ciencias sociales:** Es uno de los marcos explicativos más replicados en estudios electorales comparados, con series temporales agregadas (popularidad de gobierno vs. indicadores macro) y estudios individuales (percepción de la economía como predictor del voto); distingue votación "sociotrópica" (evaluación de la economía nacional) de "egocéntrica" (bienestar económico personal).
- **Bibliografía:** Key, V.O. Jr. (1966) *The Responsible Electorate*; Fiorina, M. (1981) *Retrospective Voting in American National Elections*; Lewis-Beck, M. & Stegmaier, M. (2000) *"Economic Determinants of Electoral Outcomes"*, Annual Review of Political Science; Kramer, G. (1971) *"Short-Term Fluctuations in U.S. Voting Behavior"*, American Political Science Review.
- **Uso en este proyecto:** Es la hipótesis (H1) que motiva todo `src/ml_models/`: el panel de ventanas cruza indicadores macroeconómicos (`icg`, `desocupacion`, `ipc`, `tc_oficial`, `salario_real`, `emae`, `reservas`, `resultado_fiscal`) contra `delta_v`/`gana_oficialismo`/`share_oficialismo` de la elección siguiente. `especificacion_panel_temporal.md` §1.5 sostiene que el pivote a panel temporal (en vez de panel espacial por localidad) da un diseño más fiel a la literatura de voto económico, que trabaja mayoritariamente con series agregadas temporales. Modelado en `notebooks/ml/ventana_t-1/01.1_lasso_voto_valido.ipynb` (y variantes 01.2/01.3) y `02_bayes.ipynb`.

### Desplazamiento ideológico / cuadrante de desplazamiento
- **Definición original:** En la teoría espacial del voto (Downs, 1957), los partidos compiten posicionándose en un espacio ideológico y los votantes eligen la opción más cercana a sus preferencias; el "desplazamiento" del centro de gravedad ideológico del electorado (o de la oferta partidaria) entre dos elecciones sucesivas es una extensión de ese marco para estudiar cambio de sistema de partidos en el tiempo, relacionada también con la idea de realineamiento electoral.
- **Usos en ciencias sociales:** Usado para estudiar polarización, realineamientos y cambios de agenda: se mide comparando la posición (o dispersión) ponderada por voto del electorado/sistema de partidos entre dos momentos, en uno o más ejes programáticos.
- **Bibliografía:** Downs, A. (1957) *An Economic Theory of Democracy*; Enelow, J. & Hinich, M. (1984) *The Spatial Theory of Voting*; literatura de realineamiento electoral (Key, V.O. Jr., 1955, *"A Theory of Critical Elections"*); estudios de polarización de sistemas de partidos con datos de expertos (Dalton, R., 2008, sobre medición de polarización partidaria).
- **Uso en este proyecto:** `magnitud_desplazamiento_ideologico` = distancia euclídea entre `(dispersion_economico_mu, dispersion_progresismo_mu)` de la elección `t` y de `t-1` (`panel_ventanas.csv`, D18); `cuadrante_desplazamiento` clasifica la dirección de ese vector con el mismo criterio de signos que las etiquetas fijas de `vparty_cuadrantes`/`vparty_localidad` (económico positivo=derecha, progresismo positivo=progresista). `delta_sigma2_economico`/`delta_sigma2_progresismo` complementan midiendo cambio de varianza (fragmentación/polarización) en vez de cambio del centro — dos preguntas distintas del mismo fenómeno (ver D18, caso real nacional 2019→2021). Es la variable dependiente central de `notebooks/ml/ventana_t-1/03_desplazamiento_ideologico.ipynb` (H2/H3), explícitamente excluida como predictora de H1/H4.

### Fragmentación del sistema de partidos / fuerzas viables
- **Definición original:** La fragmentación de un sistema de partidos suele medirse con el "Número Efectivo de Partidos" (NEP) de Laakso y Taagepera (1979), un índice basado en el índice de Herfindahl-Hirschman de los shares de voto, que pondera a cada partido por su peso relativo en vez de contarlos por unidad.
- **Usos en ciencias sociales:** Es el estándar de facto en estudios comparados de sistemas de partidos para medir bipartidismo vs. multipartidismo y su relación con reglas electorales, gobernabilidad y polarización.
- **Bibliografía:** Laakso, M. & Taagepera, R. (1979) *"'Effective' Number of Parties: A Measure with Application to West Europe"*, Comparative Political Studies; Sartori, G. (1976) *Parties and Party Systems* (tipología clásica de sistemas de partidos por número y polarización); Lijphart, A. (1994) *Electoral Systems and Party Systems*.
- **Uso en este proyecto:** El repo **no** usa la fórmula NEP de Laakso-Taagepera; en cambio, `ml_models.construir_elecciones_resumen` (D17) define "fuerza viable" con un criterio legal propio — piso de 1.5% de `votos_positivos` (Ley 26.571, 2011, el mismo umbral que exige la ley para participar de la elección general tras las PASO) — y cuenta `n_fuerzas_viables` como el número de agrupaciones que superan ese piso. `share_marginal_acumulado` (voto de fuerzas no viables), `share_oposicion_principal` y `share_otras_fuerzas_viables` completan la identidad `100% = share_oficialismo + share_oposicion_principal + share_otras_fuerzas_viables + share_marginal_acumulado`, verificada en los 34 (nivel, año) reales del período (nunca hubo un sistema estrictamente bipartidista).

### Espacio político bidimensional (eje económico + eje cultural/progresista)
- **Definición original:** Frente al eje único izquierda-derecha, buena parte de la literatura de partidos europea de las últimas décadas usa un espacio de **dos dimensiones** — un eje de redistribución económica (Estado vs. mercado) y un eje cultural/social a veces llamado GAL-TAN (Green-Alternative-Libertarian vs. Traditional-Authoritarian-Nationalist) o postmaterialista — para capturar que partidos con posición económica similar pueden diferir fuertemente en temas como derechos civiles, inmigración o religión.
- **Usos en ciencias sociales:** Usado para ubicar partidos en cuadrantes (ej. izquierda-liberal vs. izquierda-conservadora, derecha-liberal vs. derecha-conservadora) y estudiar la emergencia de partidos verdes, radicales de derecha o populistas que no se explican bien en un solo eje.
- **Bibliografía:** Kitschelt, H. (1994) *The Transformation of European Social Democracy* (origen del eje GAL-TAN); Inglehart, R. (1977) *The Silent Revolution* (eje materialista/postmaterialista); Hooghe, Marks & Wilson (2002) *"Does Left/Right Structure Party Positions on European Integration?"*, Comparative Political Studies (formalización del segundo eje en el Chapel Hill Expert Survey).
- **Uso en este proyecto:** `vparty_economico` (eje económico, `v2pariglef`) y `vparty_progresismo` (eje cultural, promedio de ítems LGBT/mujeres-trabajo/inmigración/religión de V-Party) son los dos ejes graficados en todos los cuadrantes ideológicos del repo (`vparty_cuadrantes.py`, `vparty_localidad.py`, `vparty_distribucion_tfi.py`, la pestaña interactiva `distribucion_ideologica_interactiva.py`), con `vparty_populismo` disponible como dato pero deliberadamente fuera del encoding visual de posición. Es también la base de `dispersion_economico_mu/sigma2` y `dispersion_progresismo_mu/sigma2` en `elecciones.csv` y de las distancias con signo por eje en `distancias_ideologicas.csv`.
