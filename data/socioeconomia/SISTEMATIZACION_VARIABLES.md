# Sistematización de variables socioeconómicas: EPH y Censo

Documento de referencia: qué variables se relevaron de cada fuente, qué
series históricas se pudieron construir realmente, qué dinámicas muestran
esas series (con números calculados sobre los datos ya en el repo, no
estimaciones), y qué puntos fallan o quedan pendientes. No cruza nada con
resultados electorales — sigue sin hacerse, por instrucción explícita.

## 1. EPH Gran La Plata — qué se relevó

Fuente: microdatos trimestrales INDEC, 2011-2025 (`src/socioeconomia/eph_client.py`,
ver su docstring para el detalle de dónde sale cada trimestre). Aglomerado
Gran La Plata (`AGLOMERADO=2`, incluye Berisso y Ensenada) — no hay
apertura por circuito, es un techo estructural de la fuente, no de este
pipeline.

**23 indicadores** en `eph_gran_la_plata.csv` (una fila por trimestre),
agrupables en:

| Dimensión | Variables | Fuente EPH |
|---|---|---|
| Mercado de trabajo | tasa de actividad, empleo, desocupación, informalidad (sobre asalariados con `PP07H` válido, no sobre el total de ocupados -- ver §5) | `ESTADO`, `PP07H`, `CAT_OCUP` |
| Composición ocupacional | % patrón, cuentapropia, asalariado, trab. familiar | `CAT_OCUP` |
| Calidad del empleo asalariado | % con obra social, aguinaldo, vacaciones pagas | `PP07G1/G2/G4` |
| Salud | % sin cobertura (de mecanismos ligados al empleo formal -- no implica ausencia de acceso al sistema público, ver §5) | `CH08` |
| Educación | % secundario completo o más (25+), analfabetismo (10+), asistencia escolar (5-24) | `NIVEL_ED`, `CH09`, `CH10` |
| Vivienda | hacinamiento medio (personas/cuarto) y su distribución (% bajo/moderado/crítico), % agua de red pública, tenencia (% propia, % inquilino), tamaño de hogar medio | `II1`/`IX_TOT`, `IV7`, `II7` |
| Estrategias de subsistencia del hogar (últimos 3 meses) | % recibió ayuda social del gobierno, % pidió préstamo bancario, % vendió pertenencias -- conceptualmente distintas, no combinar en un índice (ver §5) | `V5`, `V15`, `V17` |
| Ingresos | ingreso de la ocupación principal e ingreso total individual, cada uno en dos estimandos (`_todos_ocupados`/`_todos` incluye no-respondentes como 0; `_perceptores` los excluye y pondera con `PONDIIO`/`PONDII`), más IPCF | `P21` (+`PONDIIO`), `P47T` (+`PONDII`), `IPCF` — **nominales, no deflactados** |

Además, **`eph_gran_la_plata_por_sexo.csv`** y **`_por_edad.csv`** abren el
núcleo laboral (actividad/empleo/desocupación/informalidad/ingreso) por
sexo (`CH04`) y por tramo etario (`CH06`: 10-24/25-39/40-59/60+).

## 2. Censo — qué se relevó (y qué no)

Dos capas distintas, con estados de avance muy distintos:

**a) Cartografía + conteos agregados (sí están, ya en el repo):**
`radios_censales_2010_la_plata.geojson` / `_2022_la_plata.geojson`
(cartografía armonizada CONICET) traen, por radio censal, población y
viviendas totales ya contadas por INDEC (`B_POB_TOT`/`B_VIV_TOT` en 2010,
`POB_TOT_P`/`VIV_TOT_P` en 2022) — esto **sí permite una comparación
2010→2022 real**, ver §4. También está `circuito_radio_correspondencia.csv`
(`src/socioeconomia/geo.py`), el cruce espacial circuito↔radio.

**b) Variables temáticas por radio (NO están, extracción manual pendiente):**
país de nacimiento, nivel educativo, condición de actividad,
vivienda/hacinamiento detallado por radio — identificadas y documentadas en
`EXTRACCION_REDATAM.md` (con los parámetros geográficos exactos: partido de
La Plata, `PROV 06`/`DEPTO 441`) pero **nunca extraídas**: REDATAM no tiene
descarga masiva, hay que armar cada tabla a mano en la herramienta web, y
ese paso no se ejecutó. No hay `censo_2010_radio.csv`/`censo_2022_radio.csv`
en el repo.

## 3. Evolución histórica construida — qué series existen realmente

- **EPH: serie trimestral completa, 2011T1-2025T4, 57 de 60 trimestres**
  (solo faltan 2015T3, 2015T4, 2016T1 — INDEC no publicó, no es un hueco de
  este pipeline). Es la única fuente con evolución histórica real y densa.
- **Censo: dos puntos, no una serie** — 2010 y 2022, sin nada en el medio (el
  Censo es decenal). Lo único con "evolución" hoy es población/viviendas
  totales por radio (§2a); las variables temáticas (§2b) no tienen ni
  siquiera esos dos puntos todavía.
- **No hay forma de construir una serie EPH-Censo combinada**: distintos
  grano geográfico (aglomerado vs. radio/circuito) y distinta periodicidad
  (trimestral vs. decenal) — no se intenta forzar acá.

## 4. Dinámicas observadas (calculadas sobre los datos ya en el repo)

### Censo: crecimiento poblacional con subdivisión estadística

La Plata partido, 2010→2022: población 654.324 → 756.074 (**+15,5%**),
viviendas 259.762 → 331.998 (**+27,8%**) — las viviendas crecieron casi el
doble que la población, señal de achicamiento del tamaño medio de hogar
(2,52 personas/vivienda en 2010 → 2,28 en 2022). INDEC subdividió la
cartografía de 849 a 1.049 radios (+23,6%) para mantener el tamaño de radio
manejable (~300 hogares) ante ese crecimiento — coherente con la
densificación observada.

### EPH: cuatro dinámicas estructurales, no solo ruido de coyuntura

**a) Desocupación e informalidad no vuelven al nivel de partida.**
Desocupación anual promedio: 6,3% (2011) → picos en 2019 (9,4%) y 2024
(9,0%), con un valle 2021-2022 (~6%) entre medio — dos crisis distintas, no
una tendencia lineal. Informalidad (recalculada tras corregir el bug del
denominador, ver §5): 25-26% (2011-2013) → 30-38% desde 2017 en adelante
(con un valle puntual en 2020, 26,1%, por la caída de actividad de la
pandemia, no una mejora de calidad del empleo), sin volver nunca al nivel
inicial — más que un pico coyuntural, parece un cambio de piso. **Los
niveles de este párrafo no son comparables con versiones anteriores de
este documento**: el bug corregido subestimaba la tasa en todo el período,
más en los años recientes (más cuentapropismo → más denominador espurio).

**b) Cobertura de salud y hacinamiento empeoran de forma sostenida,
no cíclica.** % sin cobertura de salud: 26,4% (2011) → 33,9% (2025), subida
casi monótona año a año, sin un solo año de reversión sostenida.
Hacinamiento medio: ~1,1 personas/cuarto (2011-2013) → 1,27 (2025). A
diferencia de desocupación/informalidad (que suben y bajan con la
coyuntura), estas dos parecen tendencias estructurales de mediano plazo.

**c) Estrategias de subsistencia del hogar marcan los momentos de crisis
con más precisión que la desocupación sola.** % de hogares que vendió
pertenencias: prácticamente nulo 2015-2016 (0,3-0,9%) → salto a 11,4% en
2019 (la crisis pre-electoral de ese año) → vuelve a subir fuerte 2024-2025
(8,7%→11,7%). % que recurrió a ayuda social del gobierno: 5-8% (2011-2017)
→ duplicado en adelante, con pico en 2020 (15,9%, pandemia) y sostenido
~14-15% desde entonces — no volvió al nivel pre-2018.

**d) Brechas de género: achicamiento y reversión reciente, no una
tendencia única.** La brecha de desocupación mujer-varón, históricamente
favorable a los varones en 2-4 puntos porcentuales (2011-2020), se achicó y
llegó a **invertirse** en 2022 (-1,4pp, varones con más desocupación que
mujeres) y 2024 (-0,9pp), volviendo a +1,7pp en 2025 — no es un cierre
sostenido de la brecha, es una oscilación. El ratio de ingreso mujer/varón
(ocupación principal, estimando solo sobre perceptores — ver §5, recalculado
tras el fix de ingresos): 0,75 (2011) → 0,75 (2021, estable, no en máximo
como se estimaba antes de corregir el bug) → 0,78 (2023) → 0,70 (2025) — la
brecha de ingresos se ensancha en 2025, en la dirección opuesta a lo que
sugeriría solo mirar la brecha de desocupación en el mismo período. **Estos
niveles tampoco son comparables con versiones anteriores de este
documento**: el bug de ingresos corregido en §5 afectaba a varones y
mujeres de forma distinta (no se puede asumir que un sesgo se cancela en
un cociente si el sesgo mismo no es igual entre los dos grupos).

**e) La desocupación juvenil no es solo "más alta" — se mueve distinto.**
El tramo 10-24 años tiene una desocupación 3-5 veces la de 25-39 y 40-59 en
casi todos los años (ej. 2019: 25,7% vs. 8,3% y 5,2%), y sus picos no
siempre coinciden con los de la población general: el pico juvenil más
alto de la serie es 2024 (27,2%), mientras que para el total de la
población 2024 (9,0%) no es tan extremo relativo a 2019 (9,4%) — sugiere
que el ajuste de 2023-2024 golpeó al mercado de trabajo juvenil con más
fuerza relativa que a la población general.

## 5. Puntos que fallan o quedan pendientes

- **Subocupación horaria descartada.** Se intentó calcular desde `INTENSI`
  y dio ~71% de los ocupados subocupados en una prueba real (2T2022) — muy
  por encima de la tasa oficial de INDEC para ese trimestre (~10%). No se
  pudo confirmar la causa (¿cambio de semántica de la variable entre el
  diseño de registro consultado, de 2014, y los datos actuales? ¿falta
  cruzar con otra condición?) — se decidió no publicar el indicador en vez
  de publicar uno probablemente mal. Sigue sin resolverse.
- **Ingresos sin deflactar.** `ingreso_ocupacion_principal_medio_todos_ocupados`/
  `_perceptores`, `ingreso_total_individual_medio_todos`/`_perceptores` e
  `IPCF` medio están en pesos corrientes — con la inflación argentina del
  período, los niveles nominales no dicen nada sobre poder adquisitivo sin
  una serie de IPC, que no está en el repo. El ratio mujer/varón de §4d es
  válido igual (es un cociente dentro del mismo trimestre, la inflación se
  cancela), pero ningún nivel de ingreso en pesos debe leerse como "más" o
  "menos" real sin deflactar primero.
- **Bug de ingreso corregido (`P21`/`PONDIIO`, `P47T`/`PONDII`).** Hasta la
  corrección de esta sesión, `ingreso_ocupacion_principal_medio` promediaba
  `P21` (incluyendo `-9`, código de no respuesta, no ingreso cero) ponderado
  por `PONDERA` en vez de `PONDIIO` (el ponderador que INDEC construye
  específicamente para esta pregunta, corregido por no respuesta) —
  confirmado empíricamente en 2023T4 Gran La Plata: 34% de los ocupados no
  respondía, y el ingreso medio quedaba subestimado. Se expone ahora en dos
  estimandos separados y nombrados explícitamente (`_todos_ocupados`/`_todos`
  trata la no-respuesta como 0; `_perceptores` la excluye y usa
  `PONDIIO`/`PONDII`) para que no se mezclen sin darse cuenta. Mismo bug y
  mismo fix en `ingreso_total_individual_medio` (`P47T`/`PONDII`, ~27% de
  no-respuesta en el mismo trimestre). `PONDIIO` y `PONDII` no existen en
  las bases DBF históricas (2011-2015) — ahí se usa `PONDERA`, igual que ya
  pasaba con `PONDIH`.
- **Bug de informalidad corregido (denominador).** `PP07H` (formal/informal)
  solo se pregunta a asalariados — para patrón/cuentapropia vale `0` ("no
  corresponde"), no nulo. Hasta esta corrección, el denominador de
  `tasa_informalidad` era el total de ocupados (incluía patrón/cuentapropia,
  que nunca podían entrar al numerador), subestimando la tasa con un sesgo
  creciente a medida que crece el cuentapropismo. Ahora el denominador es
  solo asalariados con `PP07H` en {1,2}; un residual de no-respuesta de
  ítem dentro de asalariados (visto en 2011T1 histórico: `PP07H==0` para 2
  casos que sí deberían tener respuesta) también se excluye de numerador y
  denominador — se decide no imputar, no se puede afirmar si son formales
  o informales.
- **Ruido trimestral en un aglomerado chico.** Gran La Plata tiene ~1.100
  viviendas relevadas por trimestre — el movimiento promedio entre
  trimestres consecutivos es del mismo orden de magnitud que el cambio
  total 2011-2025 en varios indicadores (desocupación, cobertura de salud,
  informalidad). Un salto trimestral no se puede leer como cambio real sin
  intervalos de confianza (no calculados en este repo). Recomendación de
  uso: trabajar con promedios anuales o medias móviles de 4 trimestres para
  cualquier lectura de tendencia — esto es responsabilidad de quien
  consume `eph_gran_la_plata.csv`, no un cambio al cálculo trimestral crudo
  (que debe seguir existiendo tal cual, es el insumo de esos promedios).
- **Pendientes año a año solo válidas 2016-2025.** El cambio de fuente de
  2016 (DBF histórico → bases actuales INDEC) es un quiebre metodológico
  real, no solo un cambio de formato — especialmente visible en la serie
  de ingresos (ver el bug de arriba, ya corregido, pero el quiebre de
  fuente en sí sigue estando). Cualquier regresión, pendiente o comparación
  año a año debe partirse en el corte de 2016, nunca calcularse sobre toda
  la serie 2011-2025 de corrido — mezclaría el quiebre de fuente con la
  tendencia real.
- **Cambios de cuestionario a mitad de serie.** Desde 2023T4 INDEC dividió
  la pregunta `V5` (ayuda social del gobierno) en `V5_01/02/03` — se
  reconstruyó una `V5` equivalente (client-side, ver `eph_client.py`), pero
  es la evidencia de que el cuestionario no es 100% estable en el tiempo;
  no se puede descartar que haya otros cambios de este tipo sin documentar
  todavía en variables que no se están usando hoy.
- **Tamaño de muestra en los cortes por sexo/edad.** La EPH está diseñada
  para el aglomerado completo, no para subpoblaciones cruzadas — los cortes
  por tramo etario (sobre todo 60+, con conteos chicos) tienen más ruido
  muestral que el total; el propio diseño de registro de INDEC advierte
  esto explícitamente para subpoblaciones. No se calcularon intervalos de
  confianza ni errores de muestreo en esta pasada.
- **Reservas de INDEC sobre 2007-2015.** INDEC advierte oficialmente que
  las series de ese período deben "considerarse con reservas" (documentado
  en `eph_client.py`) — afecta a 2011-2015 completo dentro de nuestro rango.
- **Censo: la parte temática (§2b) sigue sin existir.** País de nacimiento
  (bloqueante directo para H8 de la Nota metodológica), nivel educativo,
  condición de actividad y vivienda detallada por radio no se extrajeron
  todavía — es el pendiente más grande de toda esta sistematización, y no
  se resuelve con más cómputo, requiere el trabajo manual en REDATAM que
  documenta `EXTRACCION_REDATAM.md`.
- **Radios prorrateados.** Aun cuando exista el Censo temático, el 44-47%
  de los radios de La Plata quedan repartidos entre más de un circuito en
  `circuito_radio_correspondencia.csv` (ya documentado en el README) — toda
  cifra censal futura por circuito hereda esa incertidumbre.
- **IAELaP no entra en este documento** — es una fuente de actividad
  económica (Partido de La Plata), no de condiciones de vida de los
  hogares; su propia sistematización (con el hallazgo de que revisa su
  serie entre boletines) ya está en `EXTRACCION_IAELAP.md`.

## 6. Cortes temporales marcados en los gráficos

`src/socioeconomia/graficos_eph_iaelap.py` marca automáticamente
(`marcar_cortes=True` por default) los cortes metodológicos de la serie
EPH en todos sus gráficos de línea temporal, excepto los de IAELaP (otra
fuente, otro rango temporal — no aplican):

- **Banda gris**: hueco sin dato 2015T3-2016T1 (INDEC no publicó,
  "emergencia estadística") junto con el cambio de fuente/ponderación
  (DBF histórico vía Wayback Machine → bases actuales de INDEC) que ocurre
  justo después — se representan juntos porque son, en la práctica, el
  mismo punto de quiebre en la serie.
- **Línea punteada, 2020**: cambio de operativo EPH (encuesta telefónica
  por la pandemia).
- **Línea punteada, 2023T4** (solo en `graficar_estrategias_subsistencia`,
  vía `incluir_v5=True`): split de la pregunta `V5` en `V5_01/02/03`,
  reconstruida en `eph_client.py`.

En `graficar_contraste_eph_iaelap`, el marcado aplica solo al panel EPH,
nunca al panel IAELaP. Ninguna de estas marcas modifica los datos — son
señales visuales para no leer una ruptura de método como una tendencia real.

## 7. Nota de versión

Esta sesión corrigió dos bugs de cómputo (`ingreso_ocupacion_principal_medio`
y `tasa_informalidad`, más el mismo bug en `ingreso_total_individual_medio`),
cambió el esquema de columnas de `eph_gran_la_plata*.csv` (renombres y
columnas nuevas) y regeneró esos tres CSV versionados con datos 2011-2025
completos (antes el notebook committeado solo cubría 2017-2025 para
`eph_gran_la_plata.csv`, y no generaba `_por_sexo.csv`/`_por_edad.csv` en
absoluto). Siguiendo la convención SemVer de este repo (ver skill
`laplata-electoral`), esto es un cambio **MAJOR**: rompe el esquema de un
CSV versionado que otro código (gráficos, notebooks) ya asumía, no un
agregado compatible hacia atrás.
