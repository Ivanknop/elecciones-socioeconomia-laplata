---
name: laplata-geolocalizacion
description: Estructura de datos y metodología de la capa de geolocalización del repositorio elecciones-socioeconomia-laplata (catálogo validado de las 36 localidades del Partido de La Plata, Georef-AR cruzado contra el Ministerio de Obras Públicas). Usar al trabajar con Georef-AR, data/fuentes_extra/localidades.csv, coordenadas de localidades, o el mapa de localidades. Para convenciones generales del repo ver primero el skill laplata-general; no confundir con el crosswalk circuito↔localidad de laplata-elecciones.
---

# Capa de geolocalización

`src/geolocalizacion/` es un dominio separado: catálogo validado de
localidades (nombre + lat/lon), **sin `circuito_id` todavía**. No
confundir con el crosswalk `circuito_id → nombre de barrio` de
`laplata-elecciones` (`data/fuentes_extra/circuito_localidad.csv` /
`CIRCUITOS_LOCALIDADES.md`) -- son dos capas paralelas que hoy no están
cruzadas entre sí.

Para convenciones que aplican a todo el repo, ver el skill
`laplata-general` primero. Para la metodología completa y los hallazgos
con su justificación, leer directamente `data/geolocalizacion/LOCALIDADES.md`
-- este skill es solo el resumen de arranque.

## Qué es

Cruza dos fuentes oficiales independientes por nombre normalizado:

- **Georef-AR** (`GET /api/asentamientos?municipio=060441`,
  `apis.datos.gob.ar/georef/api/`) -- nombre + centroide de cada
  asentamiento censal (INDEC) del municipio. Nunca trae geometría de
  polígono por localidad; el polígono del partido sí existe pero solo
  en la descarga masiva `v2.0/departamentos.geojson`.
- **Ministerio de Obras Públicas** (`data/fuentes_extra/localidades.csv`,
  exportado a mano de <https://snop-ppo.obraspublicas.gob.ar/localities>,
  filtrado a La Plata, códigos UTA 2010/2020) -- mismo universo,
  coordenadas propias. Es un insumo, no un derivado: no borrar ni tratar
  como redundante aunque el catálogo final ya incluya sus columnas.

## Estructura de datos

```
data/fuentes_extra/localidades.csv                # fuente Ministerio (SNOP), recorte a La Plata -- insumo de catalogo.py
data/geolocalizacion/localidades_la_plata.csv      # catálogo validado, 36 filas, git-tracked -- generado por catalogo.py
data/geolocalizacion/LOCALIDADES.md                 # metodología, esquema de columnas, hallazgos, qué falta
data/geolocalizacion/_cache/                        # respuestas crudas de Georef, NO versionado
src/geolocalizacion/georef_client.py    # fetch+cache de Georef (asentamientos + el feature del polígono del partido)
src/geolocalizacion/catalogo.py         # cruce por nombre (con dos alias manuales), escribe el CSV validado
src/geolocalizacion/mapa.py             # PNG del partido con las 36 localidades -> graficos/geolocalizacion/, NO versionado
```

## Hallazgos, para no re-descubrirlos

- **35 de 36 localidades confirmadas por ambas fuentes.** La única
  excepción es **Buchanan** (solo Georef), incluida igual en el
  catálogo: es una localidad real confirmada manualmente por el equipo
  del proyecto -- la ausencia de segunda fuente queda anotada en `nota`,
  no es motivo para excluirla (mismo criterio de "nunca perder datos
  silenciosamente" que rige el resto del repo).
- **Las coordenadas de las dos fuentes no coinciden**, aunque el nombre
  sí: delta mediana 575 m, máximo 7.034 m (Barrio El Carmen Oeste). No
  es un error de ninguna de las dos -- son vintages/metodologías
  distintas del mismo asentamiento. Importa para cualquier join futuro
  contra `circuito_id`: a escala de circuito urbano, ese margen puede
  cruzar el punto a otro circuito vecino.
- **Martín García** (circuito 493) es un enclave real ~90 km al norte
  del resto del partido, confirmado por ambas fuentes y por el propio
  polígono oficial (que tiene una segunda pieza geométrica separada
  ahí) -- consistente con la nota ya documentada en
  `data/fuentes_extra/AUDITORIA_DISCREPANCIAS.md` sobre el circuito 493
  como "límite incierto" en el crosswalk de `laplata-elecciones`. Dos
  fuentes de geolocalización independientes apuntan a que esa etiqueta
  amerita revisión, sin que esto sea todavía una corrección aplicada.
- `uta_2010` y `uta_2020` coinciden exactamente en las 35 filas de La
  Plata del export del Ministerio -- no es una columna duplicada por
  error, así viene la fuente.

## Qué falta

- Cruzar contra `circuito_id` (join espacial punto-en-polígono o
  nearest-neighbor, análogo al cruce circuito↔radio censal de
  `src/socioeconomia/geo.py`) para poder agrupar resultados electorales
  por localidad geolocalizada en vez del crosswalk por nombre.
- Cruzar contra series censales (INDEC) para ver crecimiento de
  indicadores socioeconómicos por localidad -- el objetivo original que
  motivó este catálogo.

## Referencias

- `data/geolocalizacion/LOCALIDADES.md` -- metodología completa, tabla
  de origen de cada columna, hallazgos con su detalle.
- `CLAUDE.md` -- comandos exactos y arquitectura autoritativa.
