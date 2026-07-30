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
| Mercado de trabajo | tasa de actividad, empleo, desocupación, informalidad | `ESTADO`, `PP07H` |
| Composición ocupacional | % patrón, cuentapropia, asalariado, trab. familiar | `CAT_OCUP` |
| Calidad del empleo asalariado | % con obra social, aguinaldo, vacaciones pagas | `PP07G1/G2/G4` |
| Salud | % sin cobertura | `CH08` |
| Educación | % secundario completo o más (25+), analfabetismo (10+), asistencia escolar (5-24) | `NIVEL_ED`, `CH09`, `CH10` |
| Vivienda | hacinamiento (personas/cuarto), % agua de red pública, % vivienda propia | `II1`/`IX_TOT`, `IV7`, `II7` |
| Estrategias de subsistencia del hogar (últimos 3 meses) | % recibió ayuda social del gobierno, % pidió préstamo bancario, % vendió pertenencias | `V5`, `V15`, `V17` |
| Ingresos | ingreso medio de la ocupación principal, ingreso total individual, IPCF | `P21`, `P47T`, `IPCF` — **nominales, no deflactados** |

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
una tendencia lineal. Informalidad: 20-21% (2011-2013) → estable en el
rango 25-30% desde 2016 en adelante, sin volver nunca al nivel inicial —
más que un pico coyuntural, parece un cambio de piso.

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
sostenido de la brecha, es una oscilación. El ratio de ingreso
mujer/varón (ocupación principal) mejoró de 0,75 (2011) a un máximo de 0,88
(2021), pero se **revirtió con fuerza** después: 0,84 (2023) → 0,72 (2025) —
la brecha de ingresos volvió a ensancharse en los últimos años, en la
dirección opuesta a lo que sugeriría solo mirar la brecha de desocupación
en el mismo período.

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
- **Ingresos sin deflactar.** `ingreso_ocupacion_principal_medio`, `P47T`
  medio e `IPCF` medio están en pesos corrientes — con la inflación
  argentina del período, los niveles nominales de la tabla de §3 arriba
  (ej. $2.833 en 2011T1 vs. $638.453 en 2025T4) no dicen nada sobre poder
  adquisitivo sin una serie de IPC, que no está en el repo. El ratio
  mujer/varón de §4d es válido igual (es un cociente dentro del mismo
  trimestre, la inflación se cancela), pero ningún nivel de ingreso en
  pesos debe leerse como "más" o "menos" real sin deflactar primero.
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
