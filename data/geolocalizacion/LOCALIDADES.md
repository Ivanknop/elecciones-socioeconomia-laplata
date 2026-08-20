# Catálogo de localidades geolocalizadas — Partido de La Plata


## Qué es esto

`data/geolocalizacion/localidades_la_plata.csv` es el catálogo validado
de las 36 localidades del Partido de La Plata, construido cruzando dos
fuentes oficiales independientes por nombre:

1. **Georef-AR** (`GET /api/asentamientos?municipio=060441`,
   <https://apis.datos.gob.ar/georef/api/>) — la API de normalización
   geográfica de datos.gob.ar. Devuelve nombre + centroide (punto) de
   cada asentamiento censal (INDEC) dentro del municipio; nunca
   geometría de polígono por localidad (el polígono del partido sí está
   disponible, pero solo en la descarga masiva, ver más abajo).
2. **Ministerio de Obras Públicas** (`data/geolocalizacion/fuentes_extra/localidades.csv`)
   — exportado a mano desde <https://snop-ppo.obraspublicas.gob.ar/localities>
   (Sistema Nacional de Obras Públicas), filtrando por Municipio = LA
   PLATA, el 09/08/2026. Trae `Nombre`, `Código UTA 2020`,
   `Código UTA 2010`, `Latitud`, `Longitud`, `Municipio`, `Departamento`,
   `Provincia` — las ocho columnas que usa `catalogo.py`. La descarga
   original (formato Excel, país completo, 13.521 filas) trae además
   `Superficie en km²`, `Población`, `Densidad Poblacional hab/km²` y
   referencias a capas OWS — **todas vacías para las 35 filas de La
   Plata** en esta exportación, así que no se copiaron al CSV filtrado.
   Esa descarga original queda en
   `data/geolocalizacion/fuentes_extra/Listado de Localidades - 09-08-2026.xlsx`,
   **no versionada** (`.gitignore`) por ser un dump nacional de ~1 MB
   casi todo irrelevante para este repo — el CSV filtrado sí lo está,
   mismo criterio que el resto de `data/geolocalizacion/fuentes_extra/`.

Lo arma `src/geolocalizacion/catalogo.py`:

```bash
PYTHONPATH=src python -m geolocalizacion.catalogo
```

## Metodología del cruce

Cada asentamiento de Georef se busca por nombre normalizado (mayúsculas,
sin acentos, sin paréntesis/puntos) en el listado del Ministerio. Dos
alias manuales cubren los únicos dos casos donde el nombre difiere en
sustancia, no solo en formato: `"ISLA MARTIN GARCIA"` (Ministerio) ↔
`"Martín García"` (Georef), y `"BARRIO RUTA SOL"` ↔ `"Ruta Sol"` (ver
`_ALIAS_MINISTERIO_A_GEOREF` en `catalogo.py`).

Georef devuelve dos filas para el mismo lugar cuando una localidad
censal tiene un asentamiento puntual homónimo (ej. "La Plata" aparece
como `06441030`, la localidad censal contenedora, y como `0644103015`,
el asentamiento puntual) — se descarta la de id más corto y se conserva
la más específica; ver `_deduplicar_asentamientos`.

## De dónde sale cada columna de `localidades_la_plata.csv`

Ninguna columna es "del catálogo" en abstracto — cada una viene de una
sola fuente concreta, o se calcula a partir de las otras:

| Columna | Origen | Qué es |
|---|---|---|
| `nombre` | Georef-AR | nombre del asentamiento tal como lo devuelve la API — es el nombre "canónico" de este catálogo; el nombre del Ministerio puede diferir en forma (ver los dos alias arriba) pero nunca se usa como nombre de salida |
| `georef_id` | Georef-AR | id interno del asentamiento en Georef |
| `lat`, `lon` | Georef-AR | centroide del asentamiento según Georef — son las coordenadas "principales" que usa `geolocalizacion.mapa` para graficar |
| `uta_2020` | Ministerio de Obras Públicas | columna `Código UTA 2020` de `data/geolocalizacion/fuentes_extra/localidades.csv` |
| `uta_2010` | Ministerio de Obras Públicas | columna `Código UTA 2010` de la misma fuente. **En las 35 filas de La Plata coincide exactamente con `uta_2020`** — no es un bug de este script ni una columna duplicada por error, así viene la fuente (el código no se revisó entre 2010 y 2020 para este municipio) |
| `lat_ministerio`, `lon_ministerio` | Ministerio de Obras Públicas | centroide de esa localidad según el Ministerio — ver la sección de deltas más abajo para por qué casi nunca coincide con `lat`/`lon` |
| `delta_metros` | calculado (`catalogo.py`, `_haversine_metros`) | distancia entre `(lat, lon)` y `(lat_ministerio, lon_ministerio)`; vacío cuando `fuentes=solo_georef` (no hay con qué comparar) |
| `fuentes` | calculado | `"georef+ministerio"` o `"solo_georef"`, según si hubo match por nombre |
| `nota` | calculado | explica el caso `solo_georef` (hoy solo Buchanan); vacía en el resto |

Las cuatro columnas `uta_2020`/`uta_2010`/`lat_ministerio`/`lon_ministerio`
quedan vacías en la única fila `solo_georef` — no se rellenan con el dato
de Georef para "completar la fila", porque mezclaría fuentes en la misma
celda sin dejarlo explícito.

## Resultado: 36 localidades, 35 confirmadas por las dos fuentes

| | |
|---|---|
| Total de localidades en el catálogo | 36 |
| Confirmadas por Georef **y** Ministerio (incluyendo alias) | 35 |
| Solo Georef (sin fila equivalente en el Ministerio) | 1 — **Buchanan** |
| Δ de coordenadas entre ambas fuentes, mediana | 575 m |
| Δ de coordenadas entre ambas fuentes, máximo | 7.034 m (Barrio El Carmen Oeste) |
| Localidades a menos de 100 m entre ambas fuentes | 4 de 35 |

**Buchanan se incluye igual, con una sola fuente.** No tiene fila en el
listado del Ministerio.

### Los deltas de coordenadas importan para lo que viene después

Que dos fuentes oficiales nombren el mismo lugar no significa que den
el mismo punto. La mediana de 575 m y el máximo de 7 km **no son un
error de ninguna de las dos** (Georef hereda de BAHRA/IGN; el Ministerio usa sus
propios códigos UTA 2010/2020) — pero importan en la práctica: a escala
de circuito electoral urbano, 1-7 km puede cruzar el centroide de una
localidad hacia otro circuito vecino. Cualquier join espacial futuro
contra `circuito_id` (ver "Qué falta") tiene que decidir explícitamente
qué fuente de coordenadas usar, o promediarlas con ese margen de error
en mente — no asumir que cualquiera de las dos es "la" ubicación exacta.

### Hallazgo lateral: el circuito 493 y la Isla Martín García

Georef y el Ministerio coinciden en que "Martín García" es un enclave
real a ~90 km al norte del cuerpo continental del partido (lat -34.19°
vs. -34.85° a -35.08° del resto) — consistente con que el polígono
oficial del partido (ver abajo) tiene efectivamente una segunda pieza
geométrica separada ahí (Isla Martín García, Río de la Plata). El
crosswalk `circuito_localidad.csv`, en cambio, etiqueta el circuito
`493` como `MELCHOR_ROMERO` (localidad continental) usando solo la
fuente periodística de El Día — consistente con la nota ya documentada
en `data/geolocalizacion/fuentes_extra/AUDITORIA_DISCREPANCIAS.md` sobre 493 como
"límite incierto". Dos fuentes de geolocalización independientes
apuntan en la misma dirección: esa etiqueta amerita revisión cuando se
haga el cruce circuito↔localidad geolocalizada.

## El polígono del partido

`GET /api/v2.0/departamentos.geojson` (descarga masiva, no consultable
por filtros — la consulta en vivo `/api/departamentos?id=...` solo trae
el centroide, nunca el polígono) trae la geometría completa de
Argentina; `geolocalizacion.georef_client.GeorefClient.get_departamento_geometria("06441")`
la descarga una vez y cachea solo el feature de La Plata en
`data/geolocalizacion/_cache/` (no versionado, se re-descarga solo si
falta o con `--force-refresh`).

## El mapa

```bash
PYTHONPATH=src python -m geolocalizacion.mapa
```

## Cruce contra `circuito_id`

Ver `CIRCUITOS_POR_LOCALIDAD.md` — `data/geolocalizacion/circuitos_por_localidad.csv`
asigna a cada uno de los 68 circuitos electorales la localidad de este
catálogo más cercana (nearest-neighbor, no hay polígono por localidad
para hacer punto-en-polígono).

## Qué falta

Esto es geolocalización pura — nombre + punto, sin indicadores. Un cruce
queda para después, explícitamente fuera de alcance de este catálogo por
ahora:

1. **Cruzar contra series censales** (INDEC) para poder ver crecimiento
   de indicadores socioeconómicos por localidad a lo largo del tiempo —
   el objetivo original que motivó armar este catálogo. Ninguna de las
   dos fuentes usadas acá trae esos indicadores todavía (`Población` y
   `Superficie en km²` del export del Ministerio están vacíos para las
   35 filas de La Plata en esta exportación).
