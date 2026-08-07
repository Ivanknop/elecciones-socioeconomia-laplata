# Elecciones y Economía en La Plata (para no técnicos)

Este repositorio es un intento de responder a la pregunta sobre cómo se pueden entender
los desplazamientos políticos en una ciudad capital como La Plata. **¿Son las condiciones económicas
y sociales cuasas correlacionadas con los resultados electorales finales? ¿Qué otras variables pueden 
y/o deben incorporarse?**.

El trabajo base recopila datos oficiales electorales y datos socioeconómicos dejando 
por escrito qué tan confiable es cada dato. Todavía no se ha procedido al cruce ni se han recogido otras variables.

## Qué hay hecho hasta ahora

Por ahora existen **dos colecciones de datos separadas**, construidas en
paralelo pero todavía no combinadas entre sí:

1. **Resultados electorales** de La Plata entre 2011 y 2025: quién ganó,
con qué porcentaje, en cada una de las mesas y circuitos de votación de
la ciudad, para las elecciones de Presidente, Gobernador, Intendente,
Diputados, Senadores y Concejales.

2. **Datos socioeconómicos**: información sobre empleo, ingresos y
condiciones de vida, tomada de encuestas oficiales (la Encuesta
Permanente de Hogares) y del Censo Nacional.

Estas dos colecciones **todavía no están unidas**. Es una decisión
deliberada: cruzar datos electorales con datos socioeconómicos requiere
que ambos hablen del mismo pedazo de territorio, y hoy no es así (ver
"vacancias" más abajo). Avanzar de todos modos hubiera producido un cruce
con apariencia prolija pero fundamentos débiles.

## El paso intermedio: agrupar la ciudad en barrios

La unidad más chica en la que hay datos electorales es el "circuito", una
subdivisión administrativa que no coincide con los barrios que la gente
reconoce (Tolosa, City Bell, Los Hornos, etc.). Para que los resultados
electorales se puedan leer en términos de barrios, se está construyendo
una tabla que asigna cada circuito a un barrio.

Esa tabla combina dos fuentes de calidad distinta:

- Un **listado oficial** (una resolución del Ministerio del Interior de
2007) que cubre una porción menor de los circuitos, pero con total
certeza sobre a qué barrio pertenece cada uno.
- Un **listado periodístico** (coberturas del diario El Día tras cada
elección) que cubre casi todos los circuitos restantes, pero sin el
mismo respaldo oficial.

Cada circuito queda marcado con la fuente de la que salió su barrio
asignado, para que cualquiera que use estos datos después sepa qué tan
firme es esa asignación. Es una regla de trabajo que se repite en todo
el proyecto: **cuando hay incertidumbre, se deja documentada en vez de
esconderla o de descartar el dato.**

## Los supuestos sobre los que se está parado

Todo trabajo con datos parte de algunos supuestos. Los principales acá
son:

- **Que los barrios asignados por el diario El Día son razonablemente
correctos**, aunque no tengan el mismo respaldo legal que la resolución
oficial. Esto todavía no fue verificado de manera independiente.

- **Que los datos de empleo e ingresos del "Gran La Plata"** (una región
que la encuesta oficial define y que incluye, además de La Plata, a los
partidos vecinos de Berisso y Ensenada) **son un buen sustituto** de los
datos de La Plata sola, porque la encuesta oficial no releva la ciudad
de forma separada. Esto es una hipótesis pendiente de poner a prueba.

- **Que los límites geográficos de los circuitos electorales no cambiaron
de forma relevante entre 2011 y 2025.** Hay indicios de que un puñado de
circuitos sí tuvo altas, bajas o subdivisiones en ese período, y estos
casos quedan señalados para revisión, no asumidos como error de datos.

## Las vacancias: lo que todavía no existe

- **El cruce electoral-socioeconómico en sí mismo.** Falta resolver antes el problema de
fondo: los datos electorales están armados por circuito (una unidad
chica y numerosa) y los datos socioeconómicos están armados por radio
censal (una unidad distinta, que no coincide exactamente con los
circuitos).

- **La verificación de si Berisso y Ensenada pueden separarse de La
Plata** en los datos de la encuesta oficial. Si se puede, el supuesto
del "Gran La Plata como sustituto" deja de ser necesario. Si no se
puede, hay que decidir qué tan grave es esa limitación para las
conclusiones del proyecto.

- **Un criterio sistemático para clasificar a los partidos políticos**
Hoy esa clasificación existe tanto por ideología como por familia política. 
Pero fue armada caso por caso, sin una regla explícita y uniforme
todavía.

- **La cobertura completa del mapeo circuito-barrio.** Una porción de
los circuitos de la ciudad todavía no tiene barrio asignado con ninguna
de las dos fuentes disponibles.

## Las hipótesis que están a la vista

Estas son las preguntas que el proyecto busca responder una vez que la
base de datos esté firme, no afirmaciones ya comprobadas:

- **¿El barrio explica el voto, o solo lo acompaña?** Es decir, si dos
barrios votan distinto, ¿es porque tienen condiciones económicas
distintas, o esa relación es más débil o más compleja de lo que parece
a primera vista.

- **¿Esa relación cambió con el tiempo?** La Plata atravesó crisis
económicas y varios cambios de gobierno entre 2011 y 2025; una misma
zona pudo haber tenido una relación distinta entre economía y voto en
distintos momentos.

- **¿El "Gran La Plata" es, en la práctica, un buen sustituto de "La
Plata sola"** para estudiar estos temas, o las diferencias entre los
tres partidos (La Plata, Berisso, Ensenada) son demasiado grandes como
para tratarlos como una sola unidad?

--- 
## Vísteme despacio que estoy apurado

El proyecto tiene intención de convertirse en una publicación académica.
Esa meta empuja a un estándar más exigente que "los números cierran": lo
importante no es apurar un resultado, sino poder explicar con precisión
qué se sabe, qué se está suponiendo, y qué queda todavía por resolver
antes de sacar cualquier conclusión sobre la relación entre economía y
voto en La Plata.