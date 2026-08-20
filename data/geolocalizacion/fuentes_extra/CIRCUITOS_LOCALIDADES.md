# Agrupación de circuitos electorales por localidad — estado

> **No confundir con `data/geolocalizacion/LOCALIDADES.md`.** Este
> documento es sobre el crosswalk histórico `circuito_id → nombre de
> barrio` (resolución 1990/2007 + relevamiento periodístico de El Día),
> que no tiene coordenadas ni geometría. El catálogo de localidades
> geolocalizadas (georef + Ministerio de Obras Públicas, con lat/lon
> validadas) es otro archivo, `data/geolocalizacion/localidades_la_plata.csv`
> -- este `fuentes_extra/` vive anidado dentro de `data/geolocalizacion/`
> por conveniencia de organización, no porque este crosswalk histórico
> sea parte de ese dominio (sigue siendo del dominio electoral, ver skill
> `laplata-elecciones`).
>
> **Ya no es la fuente que usa `analisis.cuadros_por_localidad` por
> defecto.** Desde la reconstrucción del flujo por localidad sobre la
> capa de geolocalización, `data/por_localidad/` se genera por defecto
> contra `data/geolocalizacion/circuitos_por_localidad.csv` (crosswalk
> derivado, nearest-neighbor circuito↔localidad geolocalizada, ver
> `data/geolocalizacion/CIRCUITOS_POR_LOCALIDAD.md`), no contra
> `circuito_localidad.csv`. Este documento y el crosswalk que describe
> siguen vigentes y sin cambios -- quedan como fuente para quien
> específicamente quiera nombre de barrio en vez de localidad oficial del
> Ministerio, o quiera reproducir resultados previos a la reconstrucción.

## Qué es esto

`circuito_localidad.csv` es el crosswalk histórico que permite agrupar
los resultados electorales (hoy solo disponibles por `circuito_id`) en
localidades/barrios de La Plata (Villa Elvira, Los Hornos, San Lorenzo,
etc.). Lo usa `src/electoral/localidades.py`, vía `cargar_crosswalk` +
`mapa_localidad_por_circuito`.

## Tres niveles de cobertura, que nunca se mezclan sin pedirlo explícitamente

| Nivel | Circuitos | Fuente | Confiabilidad |
|---|---|---|---|
| `oficial_confirmada` | 16/68 | Resolución 1990/2007 (Min. del Interior) | Norma legal — 14 con localidad dominante única, 2 (503, 503A) con varias localidades listadas y sin dominante pero clasificados igual (ver nota más abajo) |
| `revision_web` | 6/68 | Diario *El Día*, relevamiento "barrio por barrio" de las elecciones de octubre 2025, con la etiqueta de localidad recontrastada contra fuentes adicionales en la web | Fuente periodística, no administrativa, pero con una revisión adicional sobre la etiqueta cruda |
| `periodistico_no_oficial` | 59/68 | Diario *El Día*, relevamiento "barrio por barrio" de las elecciones de octubre 2025, sin esa revisión adicional | Fuente periodística, no administrativa |

`mapa_localidad_por_circuito` usa por default `oficial_confirmada` +
`revision_web` (20 circuitos, ~39,2% de los votos en el ejemplo de
Intendente 2023). Para ampliar a 67/68 circuitos (~99,4% de los votos),
hay que pedir además el nivel periodístico explícitamente:

```python
from electoral.localidades import (
    NIVEL_OFICIAL, NIVEL_PERIODISTICO, NIVEL_REVISION_WEB,
    agrupar_resultados_por_localidad, cargar_crosswalk, mapa_localidad_por_circuito,
)

crosswalk = cargar_crosswalk("data/geolocalizacion/fuentes_extra/circuito_localidad.csv")
mapa = mapa_localidad_por_circuito(
    crosswalk, niveles_cobertura=[NIVEL_OFICIAL, NIVEL_REVISION_WEB, NIVEL_PERIODISTICO],
)
agrupado, reporte = agrupar_resultados_por_localidad(resultados, mapa)
```

(`agrupar_resultados_por_localidad` en sí es agnóstica de la fuente --
recibe el mapa `circuito_id -> localidad` ya resuelto, sea de acá o de
`cargar_circuito_localidad_geo`, el default de
`analisis.cuadros_por_localidad`.)

Queda sin ninguna fuente, ni siquiera periodística: **521** (único
circuito sin ninguna fila en el crosswalk).

### La discrepancia 496A: Villa Elvira vs. Villa Montoro

En la mayoría de los circuitos donde ambos niveles coinciden en existir,
lo que pasa no es una contradicción sino una diferencia de resolución: la
fuente oficial agrupa a nivel de la localidad "madre" (Villa Elvira, Los
Hornos), mientras El Día da el sub-barrio popular específico dentro de
esa misma zona (ej. 496C oficial=SAN_LORENZO, El Día=ARANA -- Arana es,
según el propio anexo de 1990/2007, una de las localidades que integran
San Lorenzo).

El único caso que parece ser una discrepancia real, no solo de
granularidad, es **496A**: la fuente oficial lo asigna a VILLA_ELVIRA,
El Día lo llama directamente VILLA_MONTORO. El propio anexo de 1990/2007
ya mostraba a Villa Montoro como una de las localidades *internas* de
496A, sin indicar que fuera la dominante -- es posible que haya crecido
en peso relativo entre 2007 y 2025, o que El Día haya usado el nombre más
reconocible en vez del oficial. Se puede auditar con
`circuitos_con_discrepancia(crosswalk)`.

Cuando se piden varios niveles, `agrupar_resultados_por_localidad` hace
prevalecer siempre `oficial_confirmada` sobre `revision_web`, y
`revision_web` sobre `periodistico_no_oficial`, para cualquier circuito
con fila en más de un nivel.

## Cobertura con `oficial_confirmada` únicamente: 16 de 68 circuitos (23,5%), ~30,3% de los votos

La única fuente oficial con el detalle circuito → localidad que se pudo
conseguir hasta ahora es la **Resolución 1990/2007** del Ministerio del
Interior (BO 24/8/2007), que subdividió los circuitos 496, 497 y 503, y
publicó como anexo un listado de localidades por cada circuito y
sub-circuito resultante. Esa resolución cubre una sola "sección" del
partido (dice explícitamente "SECCIÓN 63 — LA PLATA", con "Total de
localidades en la sección: 60") — no el partido completo, que tiene 68
circuitos según el propio dataset de resultados y según el registro
oficial de circuitos electorales de la provincia.

Fuente: <https://servicios.infoleg.gob.ar/infolegInternet/anexos/130000-134999/131626/norma.htm>

### Filas del crosswalk

| circuito_id | localidad | cobertura |
|---|---|---|
| 496, 496A, 496B, 496E, 496F | VILLA_ELVIRA | oficial_confirmada |
| 496C, 496D | SAN_LORENZO | oficial_confirmada |
| 497, 497A–497F | LOS_HORNOS | oficial_confirmada |
| 503, 503A | MELCHOR_ROMERO | oficial_confirmada |

**503 y 503A — decisión explícita sobre el criterio de clasificación
(actualizada, ver `AUDITORIA_DISCREPANCIAS.md`).** El anexo de la
resolución muestra que cada uno contiene fragmentos de varias localidades
distintas sin que ninguna domine claramente por superficie o cantidad de
códigos (503: partes de Gorina, City Bell, Los Porteños y **Melchor
Romero**; 503A: partes de Hernández, La Josefa, La Granja Norte,
**Melchor Romero** y Gonnet). La primera versión de este crosswalk los
marcó `oficial_no_agrupable` por eso — para no elegir arbitrariamente una
localidad entre varias sin criterio. Decisión posterior de Ivan: el mero
hecho de que "Melchor Romero (Parte)" figure textualmente en la tabla
oficial de ambos circuitos —el calificador "(Parte)" no la invalida, y no
hace falta que sea la única o la mayoritaria— es base suficiente para
clasificarlos como `oficial_confirmada` → `MELCHOR_ROMERO`, en vez de
dejarlos sin agrupar. Con este criterio no hace falta ningún reparto por
área (el problema que sí sigue sin resolverse para el cruce
circuito↔radio censal, ver `docs/AUDITORIA_ESTADO.md`): alcanza con que el
nombre de la localidad aparezca en la tabla del circuito. Hoy no quedan
circuitos marcados `oficial_no_agrupable` en el crosswalk (el nivel
sigue existiendo en el código por si aparece un caso futuro sin ninguna
localidad reconocible en su tabla), y las etiquetas periodísticas que
tenían 503 (`ABASTO`) y 503A (`GORINA`) quedan documentadas igual en
`AUDITORIA_DISCREPANCIAS.md`, aunque ya no determinan el agrupamiento.

### Los 52 circuitos restantes: sin determinar (a nivel `oficial_confirmada`)

No hay, hasta ahora, una fuente oficial equivalente para el resto del
partido. Se probaron y descartaron estas vías:

- **Portal oficial de resultados** (`resultados.eleccionesbonaerenses.gba.gob.ar`),
  que sí permite filtrar por localidad (usa una división interna de 24
  localidades, confirmada por cobertura periodística de las elecciones de
  septiembre de 2025) — pero bloquea acceso automatizado (`robots.txt`).
- **Catálogo de datos abiertos de la Provincia**
  (`catalogo.datos.gba.gob.ar/dataset/circuitos-electorales`) — el CSV
  oficial de circuitos solo tiene el campo `cabecera` a nivel de
  municipio, y para La Plata ese campo vale "La Plata" en el 100% de los
  circuitos salvo el 493 (Isla Martín García). No sirve para diferenciar
  barrios dentro del partido.

## Qué falta

Con la incorporación del relevamiento de El Día, la prioridad cambia: ya
no es "conseguir cobertura" (67/68 está cubierto) sino **subir de nivel
lo que hoy solo tiene fuente periodística**, en orden de esfuerzo. Dentro
de las familias 504, 505, 508 y 509, una revisión adicional contra
fuentes web ya subió a `revision_web` los circuitos 504, 508D, 508F y
508G; quedan en `periodistico_no_oficial` sin esa revisión: 504A, 505,
505A, 505B, 508, 508A, 508B, 508C, 508E, 509 y 509A.

1. **Buscar resoluciones equivalentes a la 1990/2007** para esos
   circuitos, que también están subdivididos y hoy solo tienen la
   etiqueta de El Día (con o sin la revisión web adicional). No se
   encontraron en la búsqueda inicial en InfoLEG/Boletín Oficial -- puede
   que estén en expedientes de la Cámara Nacional Electoral posteriores a
   la Acordada 49/2020, que no se indexan igual que las resoluciones
   ministeriales más viejas.
2. **Pedir por Ley de Acceso a la Información** el listado completo y su
   metodología a la Junta Electoral de la Provincia (son quienes operan
   la app con las 24 localidades que usó El Día como base) o a la Cámara
   Nacional Electoral -- esto serviría también para cubrir **521**, el
   único circuito sin ninguna fuente, y para confirmar la identidad real
   del circuito 493 (ver `AUDITORIA_DISCREPANCIAS.md`: hoy solo tiene
   etiqueta periodística `MELCHOR_ROMERO`, pero `docs/FUNCIONALIDADES.md`
   (ex-`README.md`) lo señala como circuito de "límite incierto" con
   cabecera oficial "Isla Martín García").
3. **Contrastar contra la nota de 0221.com.ar** (24 localidades oficiales
   de la Junta Electoral, ver enlace más abajo) para verificar si el
   relevamiento de El Día usa exactamente esas 24 categorías o las
   subdivide más.

### Fuente de los niveles `periodistico_no_oficial` y `revision_web`

Ambos niveles parten del mismo artículo -- `revision_web` es el
subconjunto de filas de ese relevamiento cuya etiqueta de localidad se
recontrastó además contra fuentes adicionales en la web, no una fuente
distinta.

El Día. "Elecciones 2025.- Resultados: barrio por barrio, cómo se votó en
La Plata." 27 de octubre de 2025.
<https://www.eldia.com/nota/2025-10-27-0-8-0-elecciones-2025---resultados-barrio-por-barrio-como-se-voto-en-la-plata-politica-y-economia>

Cobertura relacionada, con la cifra de 24 localidades oficiales de la
Junta Electoral: 0221.com.ar, "El mapa de las elecciones en La Plata:
barrio por barrio y circuito por circuito, así votó la ciudad", 9/9/2025.
<https://www.0221.com.ar/la-plata/el-mapa-las-elecciones-la-plata-barrio-barrio-y-circuito-circuito-asi-voto-la-ciudad-n115675>

## Cómo se usa

```python
from electoral.localidades import agrupar_resultados_por_localidad, cargar_crosswalk

crosswalk = cargar_crosswalk("data/geolocalizacion/fuentes_extra/circuito_localidad.csv")
agrupado, reporte = agrupar_resultados_por_localidad(resultados_por_circuito, crosswalk)

print(reporte)  # SIEMPRE revisar esto antes de interpretar `agrupado`
```

`agrupado` va a incluir una fila `SIN_DETERMINAR` con todo lo que no pudo
agruparse. Nunca se descarta un voto: `agrupado["votos"].sum()` es
siempre igual a la suma total de los resultados de entrada. El
`ReporteCobertura` indica qué porcentaje de circuitos y de votos quedó
efectivamente agrupado, para que cualquier análisis posterior pueda
decidir si esa cobertura alcanza.
