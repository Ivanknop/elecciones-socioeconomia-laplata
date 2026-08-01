# Auditoría de discrepancias — `oficial_confirmada` vs. `periodistico_no_oficial`

## Alcance

Esta auditoría cubre **exclusivamente los 16 circuitos** de la Resolución
1990/2007 (14 agrupables + 503/503A no agrupables). Para esos 16, y solo esos
16, existe una fuente oficial con el detalle de códigos de localidad INDEC
contra la cual contrastar la etiqueta de El Día. **No dice nada sobre los 52
circuitos restantes del partido** (68 en total según el dataset de
resultados): para esos no hay ninguna fuente oficial equivalente, así que su
etiqueta de `periodistico_no_oficial` en `circuito_localidad.csv` queda sin
auditar y debe tratarse con la confiabilidad "fuente periodística" que ya
indica su columna `cobertura` — ver `LOCALIDADES_README.md`.

De los 16 circuitos, **2 (496E y 496F) no tienen etiqueta de El Día en
absoluto** (el relevamiento de El Día no los cubre), así que no hay nada que
comparar para ellos: quedan marcados como `sin_dato_periodistico`, no como
una categoría de acuerdo/desacuerdo.

Ver también, al final de este documento, un hallazgo adicional sobre el
circuito 493 (`MELCHOR_ROMERO`) — está fuera de este alcance formal de 16
circuitos (493 no es parte de la Resolución 1990/2007), pero se documenta
igual porque apareció durante la revisión de pertinencia del cuadro de
votos por localidad y es el mismo tipo de problema: confiabilidad de una
etiqueta de localidad.

## Metodología

Para cada uno de los 16 circuitos se reconstruyó, a partir de
`resolucion_1990-2007.md` → sección "LISTADO DE LOCALIDADES", la lista
completa de códigos de localidad INDEC (columna "Cod. Loc." + "Descripción
localidad") que la resolución asigna a ese circuito — no solo el nombre que
aparece en el encabezado de cada subsección del Anexo I (p.ej. "Circuito 496
— Villa Elvira (Parte)"), sino cada fila de su tabla.

La etiqueta de `periodistico_no_oficial` en `circuito_localidad.csv` se
comparó contra esa lista completa (no solo contra el encabezado) y se
clasificó en:

- **coincidencia_exacta**: la etiqueta de El Día coincide con la descripción
  que encabeza la subsección del circuito en el Anexo I (la localidad
  "madre"/dominante).
- **sub_localidad_valida**: la etiqueta de El Día no es la descripción que
  encabeza el circuito, pero sí figura textualmente como uno de los códigos
  de localidad listados **dentro de la tabla de ese mismo circuito**.
- **discrepancia_real**: la etiqueta de El Día no aparece en ningún código de
  localidad de ese circuito según la resolución (puede aparecer en la tabla
  de un circuito *vecino*, lo cual se señala explícitamente cuando ocurre).

### Decisiones de interpretación

1. **Normalización de nombres.** La resolución usa abreviaturas ("B°" =
   Barrio, "V°" = Villa, "Cod. Loc." con tildes) y sufijos como "(PARTE)" o
   "(CTEL. 5°)"; El Día usa mayúsculas sin tilde y `_` como separador, y a
   veces antepone "BARRIO_" a un nombre que en la resolución aparece sin ese
   prefijo (p.ej. "AEROPUERTO" en la resolución vs. `BARRIO_AEROPUERTO` en El
   Día). Se tratan como equivalentes tras normalizar (mayúsculas, sin
   tildes/abreviaturas, ignorando el prefijo "BARRIO_"/"B°"/"V°" y los
   sufijos "(PARTE)"/"(CTEL. 5°)"). Esto afecta el resultado de 496B.
2. **496A — reclasificación respecto de `LOCALIDADES_README.md`.** El README
   describe a 496A como "el único caso que parece ser una discrepancia real,
   no solo de granularidad". Al reconstruir la tabla completa del Anexo I
   para 496A, el primer código listado es justamente `1QW — VILLA MONTORO
   (PARTE)`. Es decir: **Villa Montoro sí figura textualmente dentro de la
   propia tabla de 496A** (no domina el circuito — el encabezado y la
   mayoría del resto de sus códigos son "Villa Elvira (Parte)" — pero está
   ahí). Bajo la definición estricta de esta auditoría (¿aparece la etiqueta
   de El Día en algún código de *ese* circuito?), 496A es **`sub_localidad_valida`**,
   no `discrepancia_real`. Se preserva la observación del README de que no es
   la localidad dominante — por eso se documenta con una nota aparte en vez
   de tratarlo como una coincidencia exacta más — pero formalmente no cumple
   la definición de "no aparece en ningún código", así que no entra en la
   lista de discrepancias reales de abajo.
3. **Asentamientos posteriores a 2007 (RENABAP).** Varias etiquetas de El Día
   para la familia 497 (497C `RENABAP_46_EL_TRIUNFO`, 497E `BARRIO_RENABAP`)
   refieren al Registro Nacional de Barrios Populares, creado en 2016 — no
   puede haber coincidencia con una resolución de 2007 casi por definición.
   Se clasifican igualmente como `discrepancia_real` (no aparecen en la
   tabla), pero la causa más probable no es un error de El Día sino
   crecimiento urbano/asentamientos informales posteriores a la fuente
   oficial.
4. **Circuitos sin localidad dominante (503, 503A).** Estos dos circuitos
   no tienen una única localidad que domine por superficie o cantidad de
   códigos: la resolución les asigna varios (503: Gorina, City Bell, Los
   Porteños, Melchor Romero; 503A: Hernández, La Josefa, La Granja Norte,
   Melchor Romero, Gonnet). No existe entonces una "descripción del
   circuito" contra la cual buscar `coincidencia_exacta` para la etiqueta
   de El Día; solo se evaluó si esa etiqueta aparece como alguno de sus
   códigos internos (`sub_localidad_valida`) o no (`discrepancia_real`) —
   eso da `discrepancia_real` para ambos (ABASTO y GORINA no figuran en
   sus tablas respectivas), y sigue siendo así.

   **Actualización posterior, no relacionada con la comparación de
   arriba**: por decisión explícita de Ivan, `circuito_localidad.csv`
   clasifica igual a 503 y 503A como `oficial_confirmada` → `MELCHOR_ROMERO`,
   porque "Melchor Romero (Parte)" figura textualmente en la tabla oficial
   de ambos — el calificador "(Parte)" no invalida esa mención, y no hace
   falta que sea la única o la dominante para tomarla como base de
   clasificación. Esto **no cambia** el resultado de la comparación de
   arriba (El Día siguió diciendo ABASTO/GORINA, que siguen sin figurar en
   esas tablas — `discrepancia_real` es correcto como descripción de esa
   comparación puntual); lo que cambia es que ahora `oficial_confirmada`
   prevalece sobre `periodistico_no_oficial` para estos dos circuitos, así
   que se agrupan en `MELCHOR_ROMERO` en vez de no agruparse. Ver el
   hallazgo sobre el circuito 493 más abajo para el detalle completo de
   esta decisión y sus consecuencias.

## Tabla completa — los 16 circuitos

| Circuito | Cobertura oficial | Descripción/códigos oficiales (Anexo I) | Etiqueta El Día | Categoría |
|---|---|---|---|---|
| 496 | oficial_confirmada | **VILLA ELVIRA (PARTE)** (1QX, dominante) + V° Vieyra, B° Jardín, V° Ponzatti, B° Monasterio, B° 19 de Febrero, U.P.C.N., B° Circunvalación, B° 8 de Marzo | VILLA_ELVIRA | **coincidencia_exacta** |
| 496A | oficial_confirmada | VILLA ELVIRA (PARTE) (dominante, 1219) + **VILLA MONTORO (PARTE) (1QW)**, Villa Alba, El Palígüe, Lomas de Copello, Arroyo El Pescado, B° La Hermosura | VILLA_MONTORO | **sub_localidad_valida** (ver decisión de interpretación #2) |
| 496B | oficial_confirmada | VILLA ELVIRA (PARTE) (dominante, 1220) + **AEROPUERTO (4DG)**, Villa Montoro (Parte), B° Floresta, B° Frison | BARRIO_AEROPUERTO | **sub_localidad_valida** (normalización "BARRIO_" ~ sin prefijo, decisión #1) |
| 496C | oficial_confirmada | **SAN LORENZO (PARTE)** (dominante, 005) + Villa Lenci (Parte), El Aeródromo, B° Altos de San Lorenzo | ARANA | **discrepancia_real** — Arana (1QS) no está en la tabla de 496C; está en la de **496E** |
| 496D | oficial_confirmada | **SAN LORENZO (PARTE)** (dominante, 004) + Elizalde (Sec. 5°), Villa Lenci (Parte), B° Cementerio, B° U.O.M., B° U.P.C.N., B° F.O.E.C.Y.T., Puente de Fierro | IGNACIO_CORREAS | **discrepancia_real** — I. Correas (1QT) no está en la tabla de 496D; está en la de **496F** |
| 496E | oficial_confirmada | VILLA ELVIRA (PARTE) (dominante, 1221) + Arana, Villa Garibaldi, Villa San Antonio, Sicardi Parque, B° San Carlos | *(sin dato)* | **sin_dato_periodistico** — El Día no cubre este circuito |
| 496F | oficial_confirmada | VILLA ELVIRA (PARTE) (dominante, 1222) + I. Correas | *(sin dato)* | **sin_dato_periodistico** — El Día no cubre este circuito |
| 497 | oficial_confirmada | **LOS HORNOS** (único código, 1R9) | LOS_HORNOS | **coincidencia_exacta** |
| 497A | oficial_confirmada | LOS HORNOS (PARTE) (dominante, 1246) + **POBLET (CTEL. 5°) (1RD)**, L. Olmos (Parte) | POBLET | **sub_localidad_valida** |
| 497B | oficial_confirmada | **LOS HORNOS** (único código, 4VB) | LOS_HORNOS | **coincidencia_exacta** |
| 497C | oficial_confirmada | **LOS HORNOS** (único código, 4VC) | RENABAP_46_EL_TRIUNFO | **discrepancia_real** — ver decisión de interpretación #3 |
| 497D | oficial_confirmada | **LOS HORNOS** (único código, 4VD) | EL_RETIRO | **discrepancia_real** — "El Retiro" no figura en ningún código de 497D |
| 497E | oficial_confirmada | **LOS HORNOS** (único código, 4VE) | BARRIO_RENABAP | **discrepancia_real** — ver decisión de interpretación #3 |
| 497F | oficial_confirmada | LOS HORNOS (4VF) + Olmos (Parte) (4XL) | EL_RETIRO | **discrepancia_real** — "El Retiro" no figura en ningún código de 497F |
| 503 | oficial_confirmada (antes `oficial_no_agrupable`, ver decisión #4) | Sin dominante: Gorina (Parte), City Bell (Parte), Los Porteños, **Melchor Romero (Parte)** | ABASTO | **discrepancia_real** vs. El Día — "Abasto" no figura en ningún código de 503; se agrupa igual en `MELCHOR_ROMERO` porque oficial prevalece (ver decisión #4) |
| 503A | oficial_confirmada (antes `oficial_no_agrupable`, ver decisión #4) | Sin dominante: Hernández (Parte), La Josefa, La Granja Norte (Parte), **Melchor Romero (Parte)**, Gonnet (Parte) | GORINA | **discrepancia_real** vs. El Día — Gorina no figura en la tabla de 503A (figura en la de **503**); se agrupa igual en `MELCHOR_ROMERO` porque oficial prevalece (ver decisión #4) |

### Resumen

De los 16 circuitos, 14 tienen etiqueta de El Día para comparar (496E y 496F
no). De esos 14: **3 coincidencia_exacta** (496, 497, 497B), **3
sub_localidad_valida** (496A, 496B, 497A), **8 discrepancia_real** (496C,
496D, 497C, 497D, 497E, 497F, 503, 503A).

Esto es más discrepante de lo que sugiere `LOCALIDADES_README.md`, que
describe la situación general como "no es una contradicción sino una
diferencia de resolución" con "el único caso que parece ser una discrepancia
real" siendo 496A. La auditoría completa (tabla por tabla, no solo el
encabezado) muestra lo contrario: 496A en realidad *sí* está cubierto
(`sub_localidad_valida`), mientras que **más de la mitad de los circuitos
comparables (8 de 14) caen en `discrepancia_real`** bajo la definición
estricta de esta tarea.

Nota sobre 503 y 503A: que sigan clasificados `discrepancia_real` en esta
tabla es sobre la comparación puntual con la etiqueta de El Día (ABASTO y
GORINA, respectivamente) — no significa que estén sin agrupar en
`circuito_localidad.csv`. Por decisión explícita de Ivan (ver decisión de
interpretación #4), ambos se agrupan igual en `MELCHOR_ROMERO` vía
`oficial_confirmada`, que prevalece sobre la etiqueta periodística
discrepante.

## Circuitos en `discrepancia_real` — detalle por fuente

| Circuito | Dice la Resolución 1990/2007 | Dice El Día |
|---|---|---|
| 496C | San Lorenzo (Parte) [dominante]; también Villa Lenci (Parte), El Aeródromo, B° Altos de San Lorenzo. **Arana no está en esta tabla** (está en la de 496E). | ARANA |
| 496D | San Lorenzo (Parte) [dominante]; también Elizalde (Sec. 5°), Villa Lenci (Parte), B° Cementerio, B° U.O.M., B° U.P.C.N., B° F.O.E.C.Y.T., Puente de Fierro. **I. Correas no está en esta tabla** (está en la de 496F). | IGNACIO_CORREAS |
| 497C | Los Hornos (único código listado). | RENABAP_46_EL_TRIUNFO |
| 497D | Los Hornos (único código listado). | EL_RETIRO |
| 497E | Los Hornos (único código listado). | BARRIO_RENABAP |
| 497F | Los Hornos; Olmos (Parte). | EL_RETIRO |
| 503 | Sin dominante — Gorina (Parte), City Bell (Parte), Los Porteños, Melchor Romero (Parte). | ABASTO |
| 503A | Sin dominante — Hernández (Parte), La Josefa, La Granja Norte (Parte), Melchor Romero (Parte), Gonnet (Parte). **Gorina no está en esta tabla** (está en la de 503). | GORINA |

Tres de estos ocho (496C, 496D, 503A) son casos donde la etiqueta de El Día
sí existe como código oficial de localidad, pero en la tabla del circuito
**vecino**, no en la del circuito etiquetado — un patrón distinto del "no
existe en ninguna fuente oficial" de los otros cinco (497C, 497D, 497E, 497F,
503), y que probablemente refleje que el área urbana real de esas
localidades desborda el límite catastral del circuito tal como lo fijó la
resolución de 2007.

## Hallazgo adicional (fuera del alcance de los 16 circuitos): circuito 493 / `MELCHOR_ROMERO`

Apareció durante la revisión de pertinencia del cuadro de votos por
localidad (Tarea 2), no durante esta auditoría de los 16 circuitos de la
Resolución 1990/2007 — el circuito 493 no es uno de ellos, no tiene fuente
`oficial_confirmada`, y por lo tanto no hay nada oficial contra lo cual
auditar su etiqueta de El Día como en el resto de este documento. Se
documenta acá igual porque es el mismo tipo de problema (confiabilidad de
una etiqueta de localidad) y porque involucra fuentes ya versionadas en el
propio repositorio, no una fuente externa nueva.

**Lo que dice `circuito_localidad.csv`**: una única fila para 493,
`493,MELCHOR_ROMERO,eldia_2025_barrio_por_barrio,periodistico_no_oficial` —
periodística, sin contraparte oficial.

**Lo que dice el propio `README.md` del repositorio sobre este mismo
circuito** (no una fuente externa, sino documentación ya existente en el
proyecto, escrita antes de que existiera este crosswalk):

- línea 199: 493 es uno de los tres circuitos (junto con 496F y 504C) que
  "no es común a todos los años procesados... no es un problema de formato
  sino de altas/bajas/subdivisiones reales de circuito, y requiere revisión
  manual de límites".
- línea 349: 493 queda señalado explícitamente como circuito de **"límite
  incierto"** en la capa de circuitos electorales descargada por el
  proyecto (`mapa2.electoral.gob.ar`).

Y `LOCALIDADES_README.md` (línea 102), citando el catálogo oficial de datos
abiertos de la Provincia, agrega que la `cabecera` catastral de 493 es
**"Isla Martín García"** — no Melchor Romero. Ninguna de las dos cosas
prueba por sí sola que la etiqueta de El Día esté mal (la `cabecera`
catastral no tiene por qué coincidir con dónde vive la mayoría del padrón
de un circuito de límite incierto, que bien podría combinar la isla
deshabitada con población continental cercana a Melchor Romero), pero sí
bajan la confianza de esta etiqueta muy por debajo de la de cualquiera de
los 16 circuitos de la Resolución: acá no hay ninguna fuente
administrativa, ni siquiera indirecta, con la que contrastar.

**Resuelto (actualización posterior a este hallazgo)**: la primera versión
de este documento señalaba una ironía real — "Melchor Romero" tiene
presencia oficial en la Resolución 1990/2007, como "Melchor Romero (Parte)"
en los códigos internos de **503 y 503A** (ver tabla más arriba), pero esos
dos circuitos estaban marcados `oficial_no_agrupable` y nunca se
agrupaban, así que los votos de la Melchor Romero *real*, documentada
oficialmente, quedaban siempre en `SIN_DETERMINAR`, mientras que la fila
`MELCHOR_ROMERO` de los cuadros se armaba solo con el circuito 493 —
probablemente Isla Martín García, no Melchor Romero.

Ivan revisó este hallazgo y decidió corregirlo en la fuente: si la
resolución oficial nombra "Melchor Romero" en la tabla de un circuito —
con o sin el calificador "(Parte)", sea o no la única localidad listada —
eso es base suficiente para clasificarlo como tal. `circuito_localidad.csv`
se actualizó: 503 y 503A pasaron de `oficial_no_agrupable` a
`oficial_confirmada` → `MELCHOR_ROMERO` (ver decisión de interpretación #4
más arriba). Con esto, la fila `MELCHOR_ROMERO` de los cuadros por
localidad ahora combina **tres circuitos**: 493 (periodístico, identidad
dudosa — ver arriba), 503 y 503A (oficial, ahora agrupados). La cobertura
oficial subió de 14/68 a 16/68 circuitos (~30,6% de los votos en
Intendente 2023, antes ~27,5%), y `SIN_DETERMINAR` bajó a un único
circuito estructural: **521** (sin ninguna fila en el crosswalk). Ver
`LOCALIDADES_README.md` para el detalle completo de la decisión.

**Hueco de datos en el circuito 493 (2023, no en otros años) — sigue
existiendo, ya no se nota a simple vista**: en Gobernador, Intendente y
Presidente 2023, el circuito 493 tiene `electores=109` pero **cero** votos,
tanto en `positivos` como en `otros` — ni un blanco, ni un nulo, nada. En
los demás años del dataset (2011-2021, 2025) el mismo circuito reporta
entre 55 y 83 votos positivos y entre 1 y 18 en `otros`, un patrón normal
para un circuito de ~100-120 electores. Esto no lo introduce el cuadro por
localidad — está así en el `circuito_<nivel>.json` de origen — y sigue sin
diagnóstico causal (podría ser un telegrama de escrutinio provisorio no
cargado al momento de la consulta a la API, dado lo remoto del circuito,
pero es una hipótesis, no algo confirmado). Antes de la reclasificación de
503/503A esto se veía directo en la fila `MELCHOR_ROMERO` (quedaba en
cero); ahora que esa fila combina los tres circuitos, el hueco de 493
queda **diluido** por los votos reales de 503 y 503A y ya no es visible
mirando solo el total de la fila — verificado: `MELCHOR_ROMERO` da 13.158
votos en Gobernador 2023, 13.151 en Intendente, 12.422 en Presidente (3
circuitos cada uno), nada de eso en cero. Quien necesite aislar el hueco de
493 tiene que desagregar por circuito, no alcanza con leer el cuadro por
localidad.

**Conclusión**: la fila `MELCHOR_ROMERO` de los cuadros por localidad
combina votos de confiabilidad muy distinta: 503 y 503A (fuente oficial,
Resolución 1990/2007, aunque sin ser la única localidad de esos circuitos
— ver decisión de interpretación #4) y 493 (sin fuente oficial, con
etiqueta periodística de identidad dudosa — ver arriba — y con un hueco de
datos real en 2023). El grueso del volumen de la fila viene de 503/503A
(493 es un circuito chico, ~100-120 electores, contra miles en 503/503A),
así que la fila en su conjunto es razonablemente confiable pese al ruido
de 493 — pero cualquier análisis que necesite aislar específicamente el
circuito 493 (por su identidad dudosa o por el hueco de 2023) tiene que
trabajar por circuito, no por esta fila agregada.
