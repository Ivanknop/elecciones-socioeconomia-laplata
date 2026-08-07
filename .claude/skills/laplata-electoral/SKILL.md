---
name: laplata-electoral
description: Estructura de datos, convenciones de código y decisiones de diseño del repositorio elecciones-socioeconomia-laplata (electoral + socioeconómico de La Plata 2011-2025, más una capa macroeconómica nacional separada). Usar SIEMPRE al trabajar en este repositorio -- leer o escribir datos electorales/socioeconómicos/macroeconómicos, tocar el crosswalk de localidades, escribir o correr tests, o decidir cómo versionar un cambio. Evita tener que re-explorar la estructura del repo, releer el historial de git o re-derivar reglas ya decididas en cada sesión nueva.
---

# elecciones-socioeconomia-laplata

Repositorio de investigación que cruza resultados electorales con
indicadores socioeconómicos para La Plata, Argentina (2011-2025).
Unidad de análisis: `circuito_id`. `seccionId=63` = La Plata,
`seccionProvincialId=8` = Sección Capital.

Además tiene una tercera capa, `src/macroeconomia/`, de grano
**nacional exclusivamente** (sin `circuito_id`, sin localidad) que da
contexto temporal a las dos anteriores y no comparte nada de lo que sigue
en este archivo -- para esa capa, andá directo a
`docs/plan_macroeconomia.md` y
`data/macroeconomia/SISTEMATIZACION_VARIABLES_MACRO.md`, no hace falta
leer el resto de este skill.

Este archivo es el mapa de arranque. Para el detalle de cada decisión,
andá directo al documento de referencia indicado -- no re-derives nada
de esto leyendo el código o el git log desde cero, ya está resuelto.

**Este archivo puede desactualizarse** si el repo se reorganiza (pasó
con la migración a `data/distrito/` en v3.0.0, que dejó obsoleta la
versión anterior de este mismo skill). Ante cualquier ruta que no
coincida con lo que ves en el filesystem o en `CLAUDE.md`, confiá en el
filesystem/`CLAUDE.md` -- que documenta la estructura vigente con más
detalle -- y avisá para que esto se corrija.

## Antes de escribir código: leé esto, en este orden

1. `data/fuentes_extra/LOCALIDADES_README.md` -- estado de la
   agrupación circuito→localidad, los dos niveles de cobertura y sus
   fuentes.
2. `docs/AUDITORIA_ESTADO.md` -- qué puntos de la auditoría
   metodológica original están resueltos, parciales o abiertos.
3. `docs/nota_metodologica.md` -- el diseño de investigación completo:
   problema, objetivos, sistema de hipótesis con estatus diferenciado
   (exploratorio vs. confirmatorio), y el alcance válido de las
   inferencias con estos datos (cuidado con la falacia ecológica).
4. `CLAUDE.md` (raíz) -- comandos, arquitectura, y la estructura de
   directorios autoritativa (manda por sobre la de este archivo si
   difieren).

Si la tarea es sobre localidades específicamente, con el punto 1
alcanza. No hace falta releer `git log` completo ni re-auditar archivos
que ya están marcados como resueltos en `docs/AUDITORIA_ESTADO.md`.

## Estructura de datos (no listar el directorio para redescubrir esto)

```
data/distrito/<año>/<nivel>/{generales,paso,balotaje}/        # crudo (JSON + CSV oficial)
data/distrito/<año>/<nivel>/<etapa>/circuito_<nivel>.json     # derivado por circuito -- las tres etapas lo tienen, pero paso/balotaje solo donde existió esa instancia (ver notebook 04, secciones 6-7)
data/por_localidad/<año>_<nivel>_<etapa>_localidad.csv        # cuadros por localidad, derivado, NO versionado
data/totales/<nivel>/<año>/resultado_total.csv                # total por agrupación (generales), derivado, NO versionado
data/totales/<nivel>/<año>/<etapa>/resultado_total.csv        # ídem para paso/balotaje, hermana de la ruta de arriba
data/agrupaciones/clasificacion_ideologica_agrupaciones.csv    # clasificación ideológica manual -- append-only
data/agrupaciones/tabla_referencia_filiacion_politica.csv       # fuente de filiacion_politica + confianza/nota de cada valor
data/agrupaciones/circuito_id_correspondencias.csv             # normalización circuito_id entre años
data/fuentes_extra/circuito_localidad.csv                      # crosswalk circuito -> localidad, dos niveles
data/fuentes_extra/LOCALIDADES_README.md                       # estado + qué falta
data/fuentes_extra/AUDITORIA_DISCREPANCIAS.md                  # auditoría oficial vs. periodístico
data/fuentes_extra/resolucion_1990-2007.md                     # fuente legal completa (familia 496/497/503)
data/socioeconomia/circuito_radio_correspondencia.csv           # correspondencia espacial circuito<->radio censal (peso_area)
data/socioeconomia/radios_censales_{2010,2022}_la_plata.geojson
src/electoral/          # cliente API, modelos, parsing, agrupamiento por localidad (localidades.py), totales por agrupación (totales.py)
src/analisis/           # gráficos y cuadros por circuito/nivel/localidad, a partir de circuito_<nivel>.json; totales_por_lista.py grafica data/totales/ + blanco_nulo; comparativo_nivel.py compara Municipio/Provincia/Nación en Markdown
src/socioeconomia/      # EPH, geo, IAELaP
notebooks/               # 01-06, la pipeline real corre acá (ver CLAUDE.md)
graficos/distrito/, graficos/por_localidad/, graficos/socioeconomia/   # salida, mayormente no versionada
tests/
```

`<nivel>` = presidente | gobernador | intendente | nacional | provincial
| municipal, según el año (la nomenclatura cambió entre 2011-2017 y
2019-2025; ver `docs/nota_metodologica.md` sección "Series unen cargos
distintos"). `<etapa>` = generales | paso | balotaje (balotaje solo
Presidente 2015/2023).

## Reglas que no se negocian (violarlas rompe trabajo previo)

- **Nunca se pierde un voto silenciosamente.** Todo circuito sin
  clasificación conocida (localidad, campo ideológico, lo que sea) cae
  en una categoría explícita tipo `SIN_DETERMINAR`, nunca se descarta ni
  se redistribuye. Cualquier función de agregación debe poder probar
  que `suma(salida) == suma(entrada)`. Mismo criterio se usó al separar
  `blanco_nulo` de `otros` en `cuadros_por_localidad.py`: ambas columnas
  quedan explícitas, ninguna absorbe a la otra en silencio. Todo gráfico
  de `src/analisis/` (barras/torta, las tres series temporales,
  `cuadros_anualizados`, y las variantes `por_localidad`) suma además
  `blanco_nulo` y `ausentismo` (`electores` del circuito/nivel menos votos
  válidos, vía `graficos._votos_no_ideologicos`) junto al desglose
  ideológico/de filiación -- ningún gráfico se queda solo con "% de los
  positivos".
- **`clasificacion_ideologica_agrupaciones.csv` (columnas `campo_ideologico`
  y `filiacion_politica`) es append-only.** Nunca se regenera desde cero ni
  se sobreescribe con un script automático -- es curaduría manual. Es un
  único archivo compartido por los notebooks 02 (ejecutivos) y 03
  (legislativos); ninguno de los dos debe tocar esas columnas en filas
  existentes, ni las que agregó el otro notebook. `filiacion_politica` (familia/
  identidad partidaria, no varía por `anio`/`nivel`) se fusionó desde
  `tabla_referencia_filiacion_politica.csv`, que sigue siendo la fuente de
  la justificación (`nota_clasificacion`) y confianza (`confianza_clasificacion`)
  de cada valor -- esas dos columnas deliberadamente no se fusionaron al CSV
  principal.
- **`circuito_id` no es comparable entre años sin normalizar.** Usar
  `circuito_id_correspondencias.csv` (formatos: con cero a la izquierda
  vs. sin, con o sin sufijo de letra) antes de cualquier cruce
  longitudinal.
- **Los crosswalks tienen niveles de cobertura explícitos, y no se
  mezclan sin que el código lo declare.** Ver el patrón en
  `circuito_localidad.csv` (`oficial_confirmada` /
  `oficial_no_agrupable` / `periodistico_no_oficial`, con
  `oficial_confirmada` como default más conservador en
  `agrupar_resultados_por_localidad`). Cualquier crosswalk nuevo que se
  agregue a este repo debería seguir el mismo patrón: columna `fuente`,
  columna `cobertura`, y una función de agregación que reciba
  explícitamente qué niveles usar.
- **No tocar datos para que un número dé mejor.** Si un accuracy,
  cobertura o test da bajo, el resultado es que da bajo -- se documenta,
  no se ajusta el dato de origen para maquillarlo.
- **La correspondencia espacial circuito↔radio censal (Censo) y la capa
  EPH-aglomerado NO se cruzan a nivel circuito.** Decisión tomada
  explícitamente: el desajuste entre las tres mallas (circuito, radio
  censal, localidad) es estructural, no un bug -- documentado con
  evidencia cuantitativa en `docs/AUDITORIA_ESTADO.md`. No reabrir esto sin
  releer esa sección primero.
- **Los CSV/PNG derivados (bajo `data/por_localidad/` y casi todo
  `graficos/`) no se versionan.** Se regeneran en segundos corriendo el
  script correspondiente; no hace falta commitear la salida ni pedir
  permiso para borrarla y regenerarla. Las excepciones son
  `graficos/distrito/serie_temporal/`, `graficos/distrito/totales_por_lista/`
  y `graficos/socioeconomia/eph/` (gráficos EPH -- no los de IAELaP ni el de
  contraste EPH/IAELaP, que siguen sin trackear), que sí están trackeadas -- ver `.gitignore` y
  `CLAUDE.md` antes de asumir cuál es cuál.

## Estilo de código de este repo

- Docstrings, comentarios y mensajes de error en **español**.
- Reportes de resultados como `@dataclass` con propiedades calculadas
  (ver `ReporteCobertura` en `src/electoral/localidades.py`) en vez de
  tuplas sueltas o dicts sin tipo.
- Tests con `pytest`, fixtures chicas, un `assert` por comportamiento,
  nombres de test descriptivos en español
  (`test_circuito_no_agrupable_cae_en_sin_determinar`, no `test_case_3`).
- Trabajo espacial con `geopandas`. Instalación de dependencias con
  `pip install -r requirements.txt` (ver `CLAUDE.md`) -- no asumas un
  flag de instalación distinto sin confirmarlo contra ese archivo.
- Cuando se agregue una fuente nueva (una resolución, un relevamiento
  periodístico, un dataset oficial), documentarla con: nombre de fuente,
  fecha, URL, y qué porción del universo de circuitos cubre -- siguiendo
  el formato ya usado en `LOCALIDADES_README.md`.

## Versionado (SemVer real, no solo la convención previa del repo)

- **MINOR** (x.Y.0): agregado compatible hacia atrás sobre un dominio de
  datos que ya existe -- nuevo crosswalk, nueva agregación, nueva
  columna opcional. Nada existente cambia de esquema, de ruta, ni deja
  de andar con los defaults previos.
- **MAJOR** (X.0.0): nuevo dominio analítico que no existía (ej. el
  salto v1→v2 fue agregar toda la capa socioeconómica desde cero), o
  cualquier cambio que rompe algo que ya se usaba -- incluye mover o
  renombrar rutas de `data/`/`graficos/` que otro script o notebook
  pudiera asumir, no solo cambios de esquema de datos (ej. v3.0.0, la
  reorganización a `data/distrito/`).
- Antes de tagear, confirmar en cuál de las dos categorías cae el
  cambio -- no asumir MAJOR solo porque "se siente grande", pero
  tampoco asumir MINOR solo porque no cambiaron los datos si cambiaron
  las rutas o los defaults de CLI que algo externo pudiera usar.

## Gaps conocidos, para no re-descubrirlos

- Localidad sin **ninguna** fuente (ni oficial ni periodística):
  únicamente el circuito **521**.
- `496E` y `496F` sí tienen fuente oficial (`oficial_confirmada`), pero
  El Día no los cubre -- no confundir "sin etiqueta periodística" con
  "sin fuente".
- Familias de circuitos subdivididos sin resolución equivalente a la
  1990/2007: **504, 505, 508, 509** (solo tienen fuente periodística).
- Discrepancia real conocida entre fuente oficial y periodística:
  **496A** (Villa Elvira vs. Villa Montoro) -- ver
  `AUDITORIA_DISCREPANCIAS.md`.
- El cruce electoral↔socioeconómico completo (H1-H8 de
  `docs/nota_metodologica.md`) todavía no existe. No asumir que sí al leer
  el nombre del repositorio.
- El circuito **508G** (2013, `municipal`/`nacional`/`provincial`) tiene
  más votos emitidos que `electores` registrados -> `ausentismo` negativo
  para ese circuito puntual. Es de la misma familia subdivida sin
  resolución (504/505/508/509) del punto anterior -- ver
  `docs/FUNCIONALIDADES.md`, sección "Anomalía conocida: circuito 508G".
  `graficar_torta` ya lo maneja (avisa en vez de graficar); no es un bug a
  "corregir" ajustando el dato.
- El circuito **493** en Presidente/Gobernador/Intendente 2023 tiene
  `electores=109` con `positivos=0` y `otros=0` (ítem 8.1.5 de
  `docs/AUDITORIA_ESTADO.md`, hueco de telegrama). Su `ausentismo` puntual da
  100% -- no es abstención real, es el mismo hueco de cobertura ya
  documentado, no una fila nueva a investigar.
- **PASO 2013 legislativas** (`nacional`/`provincial`/`municipal`) tienen
  `coincide_con_agregado_json=false`, pero no por votos: `positivos` y
  `otros` suman exactamente igual que el JSON agregado. La diferencia está
  en `mesas`/`electores` -- el CSV de esas tres categorías cubre bastantes
  menos mesas que las que el agregado dice totalizadas (ej. nacional 2013:
  1524 mesas/524.733 electores sumados desde el CSV vs. 2550
  mesas/878.293 electores que informa el agregado), como si al CSV le
  faltaran filas de mesas enteras sin votos para esa categoría puntual.
  Es distinto de la anomalía de Presidente 2019 (ahí el agregado
  subestimaba votos) -- acá los votos están bien, lo que falta es
  cobertura de mesas/electores. No se investigó la causa a fondo todavía;
  no usar `cobertura` de estos tres `circuito_<nivel>.json` de PASO 2013
  para calcular `ausentismo` sin tener esto presente.

## Referencias

- `data/fuentes_extra/resolucion_1990-2007.md` -- fuente legal completa
  (texto + anexo de localidades) para la familia 496/497/503.
- `data/fuentes_extra/AUDITORIA_DISCREPANCIAS.md` -- comparación fila
  por fila entre oficial y periodístico para los 16 circuitos con
  fuente oficial.
- `docs/AUDITORIA_ESTADO.md` -- tabla de estado de cada punto de auditoría,
  con referencia a qué commit lo resolvió.
- `CLAUDE.md` -- comandos, arquitectura, y la estructura de directorios
  que manda si este archivo y la realidad difieren.
