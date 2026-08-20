# Crosswalk circuito electoral → localidad geolocalizada

## Qué es esto

`data/geolocalizacion/circuitos_por_localidad.csv` asigna a cada uno de
los 68 circuitos electorales del Partido de La Plata
(`data/socioeconomia/circuitos_electorales_la_plata.geojson`) una
localidad del catálogo validado
(`data/geolocalizacion/localidades_la_plata.csv`, 36 filas, ver
`LOCALIDADES.md`). Resuelve el punto 1 de "Qué falta" de ese documento.

Lo arma `src/geolocalizacion/circuitos_por_localidad.py`:

```bash
PYTHONPATH=src python -m geolocalizacion.circuitos_por_localidad
```

Columnas: `circuito` (id canónico, `socioeconomia.geo.canonicalizar_circuito_id`),
`localidad` (nombre tal como aparece en `localidades_la_plata.csv`),
`distancia_metros` (ver metodología).

## Por qué nearest-neighbor y no punto-en-polígono

`localidades_la_plata.csv` no trae polígono por localidad — cada fila es
un solo punto (centroide/asentamiento censal). Punto-en-polígono solo
podría decir, para el puñado de circuitos que efectivamente contienen
ese punto, a qué localidad pertenecen; no dice nada de los otros ~40
circuitos que no contienen ningún punto de localidad. La asignación acá
es entonces: centroide de cada circuito (reproyectado a la UTM estimada
de la capa de circuitos, mismo criterio que
`socioeconomia.geo.calcular_correspondencia`, para que la distancia
salga en metros) contra el punto de localidad más cercano
(`geopandas.sjoin_nearest`). Cada circuito queda con **exactamente una**
localidad — nunca `SIN_DETERMINAR`, porque el nearest-neighbor siempre
encuentra un punto más cercano que otro.

`distancia_metros` es la distancia de ese match — se conserva en la
salida, no se descarta, mismo criterio que `delta_metros` en
`localidades_la_plata.csv` o `peso_area`/`match_limpio` en
`circuito_radio_correspondencia.csv`: el número que sostiene la
asignación queda visible, no implícito.

## Resultado

| | |
|---|---|
| Circuitos asignados | 68 / 68 |
| Localidades utilizadas (al menos un circuito) | 26 / 36 |
| Distancia media del match | ~1.652 m |
| Distancia máxima del match | ~8.064 m (circuito **498** → Esquina Negra) |

**10 localidades no quedan como la más cercana de ningún circuito**:
Barrio El Carmen Oeste, Barrio Gambier, Barrio Las Malvinas, Country
Club El Rodeo, José Hernández, La Providencia, Ringuelet, Ruta Sol,
Transradio, Villa Parque Sicardi. No es un error ni una localidad mal
geolocalizada — es la consecuencia esperada de tener más circuitos (68)
que localidades (36) con un solo punto de referencia cada una: esas diez
comparten zona urbana con otra localidad cuyo punto queda más cerca del
centroide de cualquier circuito de alrededor. Quedan igual en
`localidades_la_plata.csv` (nunca se borran del catálogo), simplemente
no encabezan ningún circuito en este crosswalk puntual.

**La distancia máxima (circuito 498, ~8 km) es un circuito real, no un
bug.** Es el circuito más grande del partido (~208 km², rural, ver el
resto en el rango 20-90 km² contra <1 km² de los circuitos del casco
urbano) — su centroide cae en una zona sin ninguna localidad cerca, así
que la distancia grande es correcta, no se recorta ni se reasigna a
mano.

## El caso circuito 493 / Martín García

El nearest-neighbor asigna el circuito **493** a **Martín García**
(distancia ~689 m — de las más chicas del archivo, pese a que Martín
García está a ~90 km del resto del partido). Esto **confirma** el
hallazgo de `LOCALIDADES.md` ("Hallazgo lateral: el circuito 493 y la
Isla Martín García"): dos fuentes de geolocalización independientes
(Georef + Ministerio, y ahora el propio polígono del circuito
electoral) apuntan a que la etiqueta `MELCHOR_ROMERO` que le da el
crosswalk periodístico (`data/geolocalizacion/fuentes_extra/circuito_localidad.csv`,
`eldia_2025_barrio_por_barrio`) está mal — no se corrige ese archivo acá
porque es hand-curated (ver skill `laplata-elecciones`), pero cualquier
reconstrucción de la capa de localidades que priorice
`localidades_la_plata.csv` (como esta) hereda la etiqueta correcta.

## Qué no resuelve esto

- No reemplaza `data/geolocalizacion/fuentes_extra/circuito_localidad.csv` (crosswalk
  por nombre de barrio, otra fuente, otra metodología, otro objetivo:
  cobertura histórica 1990-2007 + relevamiento periodístico 2025) — son
  dos crosswalks paralelos con criterios y universos de localidad
  distintos (36 acá vs. los nombres de barrio del otro archivo), no se
  fusionan.
- El margen de error de 1-7 km entre las coordenadas de Georef y el
  Ministerio para una misma localidad (ver `LOCALIDADES.md`) sigue
  afectando la precisión cerca de los límites de circuito — este
  crosswalk usa `lat`/`lon` (Georef), no `lat_ministerio`/`lon_ministerio`,
  misma fuente "principal" que ya usa `geolocalizacion.mapa`.
