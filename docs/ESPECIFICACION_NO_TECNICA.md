# Elecciones y Economía en La Plata (para no técnicos)

Este repositorio es un intento de responder a la pregunta sobre cómo se pueden entender
los desplazamientos políticos en una ciudad capital como La Plata. **¿Son las condiciones económicas
y sociales cuasas correlacionadas con los resultados electorales finales? ¿Qué otras variables pueden 
y/o deben incorporarse?**.

El trabajo base recopila datos oficiales electorales y varias colecciones
de datos de contexto (socioeconómicos, económicos, de confianza en el
gobierno), dejando por escrito qué tan confiable es cada dato. Todavía no
se ha procedido al cruce entre ellas.

## Qué hay hecho hasta ahora

Por ahora existen **varias colecciones de datos separadas**, construidas
en paralelo pero todavía no combinadas entre sí:

1. **Resultados electorales** de La Plata entre 2011 y 2025: quién ganó,
con qué porcentaje, en cada una de las mesas y circuitos de votación de
la ciudad, para las elecciones de Presidente, Gobernador, Intendente,
Diputados, Senadores y Concejales. Sobre esta base también se construyó
una primera clasificación de los partidos —por posición ideológica, por
familia/tradición política, y por un tercer criterio más fino tomado de
un proyecto académico internacional (V-Party)— para poder agrupar
resultados más allá del nombre de lista de cada elección puntual.

2. **Datos socioeconómicos**: información sobre empleo, ingresos y
condiciones de vida, tomada de encuestas oficiales (la Encuesta
Permanente de Hogares) y del Censo Nacional.

3. **Datos económicos nacionales**: inflación, tipo de cambio, deuda
pública, actividad y empleo a nivel país, 2011-2025 — sirven de contexto
temporal (a qué le tocó gobernar cada gestión), no están abiertos por
barrio ni por circuito.

4. **Un índice de confianza en el gobierno** (encuesta nacional
mensual, universidad privada), que permite comparar cómo evolucionó esa
confianza en La Plata contra el resto del país, 2011 en adelante.

5. **Un catálogo geográfico validado** de los barrios/localidades del
partido de La Plata (nombre y ubicación de cada uno), que sirve de base
para agrupar los resultados electorales por barrio (ver siguiente
sección).

Ninguna de estas colecciones **está unida a las demás todavía**. Es una
decisión deliberada: cruzar datos electorales con datos de contexto
requiere que ambos hablen del mismo pedazo de territorio o del mismo
período, y hoy eso solo está resuelto parcialmente (ver "vacancias" más
abajo). Avanzar de todos modos hubiera producido un cruce con apariencia
prolija pero fundamentos débiles. Lo que sí está disponible para
explorar visualmente, sin esperar a ese cruce, son dos mapas/gráficos
interactivos publicados: uno muestra los resultados electorales
circuito por circuito sobre un mapa de la ciudad, y el otro ubica a cada
partido en un plano según su posición económica y su posición en temas
sociales, año por año.

## El paso intermedio: agrupar la ciudad en barrios

La unidad más chica en la que hay datos electorales es el "circuito", una
subdivisión administrativa que no coincide con los barrios que la gente
reconoce (Tolosa, City Bell, Los Hornos, etc.). Para que los resultados
electorales se puedan leer en términos de barrios, existen hoy **dos
formas distintas** de asignar cada circuito a una localidad, con
propósitos distintos:

- Una **tabla derivada de coordenadas geográficas**: un catálogo
  validado de las 36 localidades del partido (cruzando una fuente
  nacional de normalización geográfica contra un listado del Ministerio
  de Obras Públicas) permite calcular, para cada circuito, cuál es la
  localidad geográficamente más cercana. Esta asignación es completa —
  todos los circuitos quedan cubiertos, sin excepción — pero es
  automática: no usa nombres de barrio "de sentido común", sino la
  localidad más próxima según coordenadas.
- Un **listado curado a mano**, que combina dos fuentes de calidad
  distinta: un **listado oficial** (una resolución del Ministerio del
  Interior de 2007) que cubre una porción menor de los circuitos con
  total certeza sobre a qué barrio pertenece cada uno, y un **listado
  periodístico** (coberturas del diario El Día tras cada elección) que
  cubre casi todos los circuitos restantes, pero sin el mismo respaldo
  oficial. Esta es la fuente a usar cuando lo que importa es el nombre
  de barrio tal como lo reconoce la gente, no una coordenada.

Los gráficos y mapas del proyecto usan por defecto la primera (la
derivada de coordenadas, por estar completa); la segunda sigue
disponible para quien específicamente necesite nombres de barrio.
Cada circuito, en ambos casos, queda marcado con la fuente de la que
salió su asignación, para que cualquiera que use estos datos después
sepa qué tan firme es. Es una regla de trabajo que se repite en todo
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

- **Que el promedio nacional del índice de confianza en el gobierno
"incluye" a La Plata**, en vez de compararla contra el resto del país
excluyéndola. Es la misma convención que usa la fuente de esos datos, no
una decisión propia del proyecto, pero significa que la "distancia" entre
La Plata y el país no es una comparación contra un afuera completamente
ajeno: La Plata es, en parte, ese promedio.

## Las vacancias: lo que todavía no existe

- **El cruce entre lo electoral y todo lo demás.** Falta resolver antes
el problema de fondo: los datos electorales están armados por circuito
(una unidad chica y numerosa) y los datos socioeconómicos están armados
por radio censal (una unidad distinta, que no coincide exactamente con
los circuitos); los datos económicos nacionales y el índice de confianza
en el gobierno, además, no tienen ninguna apertura geográfica en sí
mismos — solo se pueden relacionar con lo electoral por fecha, no por
barrio ni por circuito. Ninguno de estos cruces existe todavía.

- **La verificación de si Berisso y Ensenada pueden separarse de La
Plata** en los datos de la encuesta oficial. Si se puede, el supuesto
del "Gran La Plata como sustituto" deja de ser necesario. Si no se
puede, hay que decidir qué tan grave es esa limitación para las
conclusiones del proyecto.

- **Un criterio sistemático para clasificar a los partidos políticos.**
Hoy esa clasificación existe por tres caminos —posición ideológica,
familia/tradición política, y una posición más fina tomada de un
proyecto académico internacional (parcial: cubre bien las elecciones
nacionales de Diputados 2011-2019, y se completó para el resto con una
estimación propia calibrada contra esa misma fuente)— pero las tres se
armaron caso por caso, sin una regla explícita y uniforme todavía. Una
revisión reciente encontró además que, para una porción de los partidos
con esa tercera clasificación, no quedó registrado con precisión de qué
fuente puntual salió cada valor — está identificado, no resuelto
todavía.

- **La cobertura completa del mapeo circuito-barrio con nombres
reconocibles.** El mapeo por coordenadas (ver sección anterior) ya cubre
el 100% de los circuitos; el mapeo curado a mano, que es el que da
nombres de barrio en el sentido cotidiano, todavía tiene una porción de
circuitos sin el mismo nivel de certeza que los demás.

- **El cruce del índice de confianza en el gobierno con cualquier otro
dato del proyecto.** Por ahora es una colección aparte, igual que las
otras — se puede mirar la serie de La Plata contra el país, pero no
está relacionada todavía ni con el voto ni con las condiciones
socioeconómicas.

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

- **¿La confianza en el gobierno se mueve junto con el voto, o por
delante/detrás de él?** Con el índice de confianza ya disponible mes a
mes, queda abierta la pregunta de si La Plata confía más o menos que el
resto del país en los mismos momentos en que su voto se desplaza —y si
esas dos cosas se mueven juntas o de forma independiente.

--- 
## Vísteme despacio que estoy apurado

El proyecto tiene intención de convertirse en una publicación académica.
Esa meta empuja a un estándar más exigente que "los números cierran": lo
importante no es apurar un resultado, sino poder explicar con precisión
qué se sabe, qué se está suponiendo, y qué queda todavía por resolver
antes de sacar cualquier conclusión sobre la relación entre economía y
voto en La Plata.