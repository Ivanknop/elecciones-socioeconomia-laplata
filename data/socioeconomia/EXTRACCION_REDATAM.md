# Extracción manual de Censo 2010 / 2022 por radio censal (REDATAM)

A diferencia del resto de este proyecto, esto **no es un script que se corre
solo**. REDATAM no tiene un endpoint tipo CSV masivo como
`get_resultados_csv` del cliente electoral — la extracción se hace a mano en
la herramienta web, tabla por tabla. Este documento deja los pasos y
parámetros exactos para que sea reproducible por otra persona, no para que
se automatice.

**Estado**: los pasos de abajo están armados a partir de la documentación
pública de REDATAM y de los parámetros geográficos ya confirmados en este
proyecto (partido de La Plata, códigos de radio) — no se llegaron a ejecutar
clic a clic en esta sesión (sin navegador disponible). Quien los corra por
primera vez debería ajustar el detalle de UI si difiere de lo descripto acá,
y dejar constancia de cualquier ajuste en este mismo archivo.

## Portales y parámetros geográficos

- **Censo 2022**: `https://redatam.indec.gob.ar/binarg/RpWebEngine.exe/Portal?BASE=CPV2022&lang=ESP`
- **Censo 2010**: `https://redatam.indec.gob.ar/argbin/RpWebEngine.exe/PortalAction?BASE=CPV2010B`
- **Partido de La Plata**: provincia Buenos Aires (`PROV=06`), departamento/partido **`441`** — confirmado en esta sesión cruzando el shapefile de circuitos electorales (que trae `departamen="La Plata"`, `indec_d="441"`) contra la cartografía censal armonizada de CONICET (`DEPTO="441"` da 756.074 personas en 2022 y 654.324 en 2010, en línea con la población conocida del partido).
- **Id de radio a reconstruir**: `COD_<censo> = PROV(2) + DEPTO(3) + FRACC(2) + RADIO(2)`, 9 dígitos (ej. `"064417406"` = depto 441, fracción 74, radio 06). Es el mismo id que ya usa `circuito_radio_correspondencia.csv` en la columna `radio_censal_id` — la tabla de salida de este proceso manual tiene que quedar con esa misma clave para poder unirse.

## Pasos generales (repetir para 2010 y para 2022)

1. Entrar al portal REDATAM correspondiente (arriba) y elegir la base de
   Personas/Hogares/Viviendas de radios (no la de resultados provinciales
   agregados).
2. Navegar el árbol geográfico: Buenos Aires → partido `441` (La Plata) →
   todas las fracciones/radios (no filtrar a un subconjunto: se necesitan
   los 849 radios de 2010 / 1.049 de 2022 completos, ver
   `radios_censales_2010_la_plata.geojson` / `_2022_la_plata.geojson` para
   el total esperado).
3. Armar una tabla de frecuencias con **radio censal como fila** (nivel de
   desagregación más chico disponible) y, como columnas, las variables de
   abajo — una tabla por variable/tema, no todas mezcladas, porque REDATAM
   arma cruces de a un tema por vez.
4. Exportar cada tabla a CSV/Excel y anotar, en la primera fila o en un
   archivo aparte, la selección exacta usada (variable, categorías,
   filtros) — es la única documentación de procedencia que va a quedar,
   porque no hay una consulta reproducible por URL como en el pipeline
   electoral.
5. Unir todas las tablas de un mismo censo por `radio_censal_id`
   (reconstruido como PROV+DEPTO+FRACC+RADIO) en un único
   `censo_2010_radio.csv` / `censo_2022_radio.csv`, una fila por radio.

## Variables a extraer (según Nota metodológica §5.4 y H8)

Todas por radio censal, para el partido de La Plata:

| Tema | Qué pedir en REDATAM | Para qué |
|---|---|---|
| País de nacimiento | Personas × país de nacimiento (al menos: Argentina / Venezuela / resto extranjero) | H8 — proporción de nacidos en Venezuela por circuito (vía la correspondencia radio→circuito) |
| Nivel educativo | Personas × nivel educativo alcanzado | Nota §5.4, caracterización estructural |
| Condición de actividad | Personas × condición de actividad (ocupado/desocupado/inactivo, la apertura que dé el censo — más agregada que la EPH) | Nota §5.4; nunca reemplaza a la serie EPH, es un corte estructural |
| Vivienda / hacinamiento | Hogares × calidad de materiales, Personas u Hogares × hacinamiento (personas por cuarto) | Proxy tipo NBI — ver limitación de abajo, no hay un índice NBI que INDEC recalcule igual en los dos censos |
| Totales de referencia | Población total y viviendas totales por radio | Ya vienen en la cartografía de CONICET (`POB_TOT_P`/`VIV_TOT_P` para 2022, `B_POB_TOT` para 2010) — usar para validar cobertura de la extracción manual, no hace falta repetirlos acá |

## Limitaciones a mantener documentadas en el CSV de salida

- **No existe un índice NBI único que INDEC recalcule igual en 2010 y 2022.**
  Si se quiere un índice de privación comparable entre censos, construirlo a
  mano a partir de estos componentes (vivienda, saneamiento, educación,
  subsistencia), con el método explícito por escrito — no inventarlo acá.
- **Los radios cambian de límites entre 2010 y 2022.** No comparar
  `censo_2010_radio.csv` y `censo_2022_radio.csv` fila a fila por
  `radio_censal_id` como si fueran el mismo territorio — el id puede
  referirse a una geometría distinta entre censos (la cartografía
  armonizada de CONICET ya usada en este proyecto para las capas de
  polígonos es la fuente que corrigió esto para el join espacial; a nivel
  de la tabla de atributos extraída de REDATAM no hay corrección
  automática, así que cualquier comparación entre censos tiene que pasar
  por la geometría, no por el id crudo).
