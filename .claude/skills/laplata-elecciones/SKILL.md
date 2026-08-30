---
name: laplata-elecciones
description: Estructura de datos, crosswalks y decisiones de diseño de la capa electoral + socioeconómica del repositorio elecciones-socioeconomia-laplata (resultados electorales de La Plata 2011-2025 cruzados con EPH/IAELaP/Censo). Usar al trabajar con resultados electorales, circuito_id, el crosswalk circuito↔localidad, clasificación ideológica de agrupaciones, o la capa socioeconómica (EPH/IAELaP/radios censales). Para convenciones generales del repo (versionado, estilo de código, estructura de alto nivel) ver primero el skill laplata-general.
---

# Capa electoral + socioeconómica

Repositorio de investigación que cruza resultados electorales con
indicadores socioeconómicos para La Plata, Argentina (2011-2025).
Unidad de análisis: `circuito_id`. `seccionId=63` = La Plata,
`seccionProvincialId=8` = Sección Capital.

Para convenciones que aplican a todo el repo (versionado SemVer, estilo
de código, estructura de alto nivel), ver el skill `laplata-general`
primero — este archivo solo tiene lo específico de esta capa.

**Este archivo puede desactualizarse** si el repo se reorganiza (pasó
con la migración a `data/distrito/` en v3.0.0, que dejó obsoleta la
versión anterior de este mismo skill). Ante cualquier ruta que no
coincida con lo que ves en el filesystem o en `CLAUDE.md`, confiá en el
filesystem/`CLAUDE.md` — que documenta la estructura vigente con más
detalle — y avisá para que esto se corrija.

## Antes de escribir código: leé esto, en este orden

1. `data/geolocalizacion/fuentes_extra/CIRCUITOS_LOCALIDADES.md` -- estado del crosswalk
   histórico circuito→barrio (dos niveles de cobertura y sus fuentes) y su
   relación con el crosswalk geolocalizado que ahora es el default (ver
   nota al principio de ese documento y
   `data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md`).
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
data/agrupaciones/clasificacion_ideologica_agrupaciones.csv    # clasificación ideológica manual -- append-only; también trae vparty_economico/progresismo/populismo opcionales (de qué fuente viene cada fila: SOLO en data/agrupaciones/v-party/README.md)
data/agrupaciones/tabla_referencia_filiacion_politica.csv       # fuente de filiacion_politica + confianza/nota de cada valor
data/agrupaciones/circuito_id_correspondencias.csv             # normalización circuito_id entre años
data/agrupaciones/oficialismos.csv                              # oficialismo por (año, nivel), 2011-2025 -- hand-curated, mismo criterio append-only
data/agrupaciones/v-party/                                      # dataset V-Party + encuesta propia anonimizada + su estimación calibrada (ver README de esa carpeta)
data/geolocalizacion/circuitos_por_localidad.csv                # crosswalk circuito -> localidad geolocalizada, DEFAULT de analisis.cuadros_por_localidad (ver laplata-geolocalizacion)
data/geolocalizacion/fuentes_extra/circuito_localidad.csv                      # crosswalk histórico circuito -> barrio, dos niveles -- ya no es el default, sigue disponible
data/geolocalizacion/fuentes_extra/CIRCUITOS_LOCALIDADES.md                    # estado + qué falta del crosswalk histórico -- no confundir con data/geolocalizacion/LOCALIDADES.md (ver laplata-geolocalizacion)
data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md                  # auditoría oficial vs. periodístico
data/geolocalizacion/fuentes_extra/resolucion_1990-2007.md                     # fuente legal completa (familia 496/497/503)
data/socioeconomia/circuito_radio_correspondencia.csv           # correspondencia espacial circuito<->radio censal (peso_area)
data/socioeconomia/radios_censales_{2010,2022}_la_plata.geojson
src/electoral/          # cliente API, modelos, parsing, agrupamiento por localidad (localidades.py), totales por agrupación (totales.py)
src/analisis/           # gráficos y cuadros por circuito/nivel/localidad, a partir de circuito_<nivel>.json; totales_por_lista.py ya no grafica, solo capa de datos compartida; comparativo_nivel.py compara Municipio/Provincia/Nación en Markdown; vparty_cuadrantes_local.py -- generación de cuadrantes por partido (distrito) DEPRECADA, ver CLAUDE.md; sus funciones de datos (tabla_distrito/tabla_localidades/etc.) siguen activas para visualizacion/
src/visualizacion/      # generadores de HTML interactivo para docs/, sobre datos de este dominio -- ver skill laplata-visualizacion
src/socioeconomia/      # EPH, geo, IAELaP
notebooks/               # 01-06, la pipeline real corre acá (ver CLAUDE.md)
graficos/distrito/, graficos/por_localidad/, graficos/socioeconomia/   # salida, mayormente no versionada
docs/index.html, docs/mapa_electoral_la_plata.html, docs/distribucion_ideologica_la_plata.html   # sitio de GitHub Pages -- los dos gráficos interactivos del repo (Leaflet), git-tracked, viven en docs/ (no graficos/) porque ahí los sirve Pages
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
- **`agrupar_resultados_por_localidad` (en `electoral/localidades.py`) es
  agnóstica de la fuente del crosswalk**: recibe un mapa
  `circuito_id -> localidad` ya resuelto, no el crosswalk crudo. Dos formas
  de construir ese mapa, no intercambiables sin pensarlo: `cargar_circuito_localidad_geo`
  (crosswalk geolocalizado, `data/geolocalizacion/circuitos_por_localidad.csv`,
  sin niveles -- cada circuito tiene una sola fila, **default** de
  `analisis.cuadros_por_localidad`) o `cargar_crosswalk` +
  `mapa_localidad_por_circuito` (crosswalk histórico por nombre de barrio,
  `circuito_localidad.csv`, con niveles de cobertura explícitos
  `oficial_confirmada` / `oficial_no_agrupable` / `revision_web` /
  `periodistico_no_oficial` que no se mezclan sin que el código lo
  declare). Cualquier crosswalk nuevo con niveles debería seguir el mismo
  patrón que este último: columna `fuente`, columna `cobertura`, y una
  función de agregación que reciba explícitamente qué niveles usar.
- **La correspondencia espacial circuito↔radio censal (Censo) y la capa
  EPH-aglomerado NO se cruzan a nivel circuito.** Decisión tomada
  explícitamente: el desajuste entre las tres mallas (circuito, radio
  censal, localidad) es estructural, no un bug -- documentado con
  evidencia cuantitativa en `docs/AUDITORIA_ESTADO.md`. No reabrir esto sin
  releer esa sección primero.
- **Los CSV/PNG derivados de esta capa (bajo `data/por_localidad/` y
  casi todo `graficos/`) no se versionan** salvo el JSON (nunca el PNG):
  `graficos/distrito/serie_temporal/*.json`,
  `graficos/distrito/comparativos_nivel/` (Markdown, no JSON) y
  `graficos/agrupaciones/<año>/<nivel>/*.json` (cuadrantes V-Party, La
  Plata por año/nivel; el scatter nacional en la raíz de `agrupaciones/`
  también) -- ver `.gitignore` y `CLAUDE.md` antes de asumir cuál es cuál.
  El grano localidad (`graficos/por_localidad/`, `graficos/agrupaciones/por_localidad/`)
  se eliminó del todo, código incluido -- ya no existe ningún PNG por
  localidad. **`graficos/agrupaciones/<año>/<nivel>/*.json` está
  congelado, no se regenera**: su generador
  (`vparty_cuadrantes_local.generar_distrito`) quedó deprecado en favor de
  `data/tfi_data/elecciones/<año>_<nivel>.csv`, que trae lo mismo más las
  agrupaciones sin cobertura V-Party y BLANCO/NULO -- ver CLAUDE.md.

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
  documentado, no una fila nueva a investigar. El propio crosswalk lo
  marca como "límite incierto" (cabecera oficial "Isla Martín García") —
  el skill `laplata-geolocalizacion` aporta una segunda señal
  independiente sobre esto.
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
- **(Resuelto)** `analisis.cuadros_por_localidad` rompía con
  `KeyError('')` en 4 combos por `campo_ideologico` vacío/desactualizado:
  2017 nacional/provincial/municipal PASO (`PARTIDO SOCIALISTA`/`FRENTE
  SOCIALISTA Y POPULAR`, ya clasificados en el CSV -- el
  `circuito_<nivel>.json` cacheado solo estaba desactualizado, un re-run
  de notebook 04 lo corrigió) y 2023 gobernador PASO (`FRENTE FEDERAL DE
  ACCION SOLIDARIA DE LA PROVINCIA DE BUENOS AIRES`, genuinamente sin
  clasificar -- se clasificó `campo_ideologico=3` (centro),
  `filiacion_politica=peronismo provincial` (ya estaba así en la fila
  gemela de nivel `intendente`, consistente con "peronismo federal" según
  Ivan), y se volvió a correr notebook 04). Los 44 combos de
  `data/por_localidad/` generan limpio ahora. Si aparece un caso similar
  a futuro (agrupación con `campo_ideologico` vacío bloqueando este
  script), el diagnóstico es: 1) ¿está clasificada en el CSV pero el JSON
  cacheado es viejo? -> re-correr notebook 04 (no hace falta red si el
  CSV/JSON crudo de ese combo ya está en caché). 2) ¿no está clasificada
  en el CSV? -> pedir la clasificación antes de tocar código.

## Referencias

- `data/geolocalizacion/fuentes_extra/resolucion_1990-2007.md` -- fuente legal completa
  (texto + anexo de localidades) para la familia 496/497/503.
- `data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md` -- comparación fila
  por fila entre oficial y periodístico para los 16 circuitos con
  fuente oficial.
- `docs/AUDITORIA_ESTADO.md` -- tabla de estado de cada punto de auditoría,
  con referencia a qué commit lo resolvió.
- `CLAUDE.md` -- comandos, arquitectura, y la estructura de directorios
  que manda si este archivo y la realidad difieren.
