# Extracción del IAELaP (Indicador de Actividad Económica de La Plata)

A diferencia del pipeline electoral y de la EPH, IAELaP **no tiene descarga
masiva** — cada boletín trimestral es un PDF de diseño (imágenes/gráficos),
publicado por el Laboratorio de Desarrollo Sectorial y Territorial (FCE,
UNLP). La extracción es lectura de PDF asistida (tool `Read`, que sí extrae
texto/tablas de estos PDF — a diferencia de `curl`/`WebFetch`, que devuelven
contenido binario no legible), no un cliente HTTP con parseo automático.

## Qué es y qué mide

Índice que combina la variación de actividad económica de todas las ramas
productivas del **Partido de La Plata**, ponderada por su participación en
el Producto Bruto Geográfico (PBG) del partido. Fuentes: encuesta propia del
Laboratorio (sector comercial, y en boletines más recientes también
hoteles/restaurantes/taxis/servicios) + información secundaria de organismos
oficiales; los índices de precios usados para deflactar salen de la
Dirección Nacional de Cuentas Nacionales (INDEC).

**Geografía: Partido de La Plata — no es el mismo universo que "Gran La
Plata" de la EPH** (que suma Berisso y Ensenada).

## Hallazgo importante: la serie retrospectiva se revisa entre boletines

Cada boletín trimestral incluye un gráfico con la serie completa desde
1T2018 hasta el trimestre publicado — pero **el valor de un mismo trimestre
cambia de un boletín a otro**. Confirmado explícitamente por el propio
Laboratorio en el boletín 4T2022: *"A partir de la publicación del 1T 2022
se modificaron las fuentes de información para las ramas Construcción y
Administración Pública, por lo tanto las series de este informe pueden
diferir de las publicadas con anterioridad."*

Verificado con datos reales leyendo 4 boletines de control (1T2019, 2T2020,
4T2022, 1T2025) más el más reciente (4T2025): el valor de 1T2018 aparece
como **2,3%** (boletín 1T2019, tabla "Cuadro 1"), **2,6%** (boletines 2T2020
y 4T2022) y **2,8%** (boletines 1T2025 y 4T2025) — tres valores distintos
para el mismo trimestre, según en qué momento se publicó el boletín que lo
reporta. La revisión más grande encontrada es en 2022: el boletín 4T2022
reportaba 5,9%/5,3%/3,7%/3,4% para los cuatro trimestres de 2022; el boletín
1T2025 (con datos ya revisados) reporta 5,3%/3,9%/1,2%/2,3% para esos mismos
trimestres.

**Regla adoptada para este proyecto**: usar siempre el valor del boletín
**más reciente disponible** para cada trimestre, no el primero publicado.
`data/socioeconomia/iaelap_la_plata.csv` sigue esta regla y deja registrada,
en la columna `boletin_fuente`, de qué boletín salió cada valor.

## Estado de `iaelap_la_plata.csv`

- 1T2018 a 3T2024 (27 trimestres): leído del gráfico del boletín 1T2025
  (junio 2025), que trae los ticks de eje por trimestre individual
  (`IT-18`, `IIT-18`, ...) — más fácil de leer sin ambigüedad que el gráfico
  retrospectivo del boletín 4T2025, que aprieta 32 trimestres sin ese detalle.
  Confianza: alta.
- **4T2024: falta.** El boletín 4T2025 confirma en texto que "a lo largo de
  2024 el índice registró caídas interanuales en los cuatro trimestres", pero
  no se pudo aislar el valor exacto de 4T2024 en esta sesión — se dejó vacío
  en vez de estimarlo.
- 1T2025: **4,2%** (boletín 4T2025, revisado) — el boletín 1T2025 original
  había publicado 3,9% para ese mismo trimestre; se prefirió el valor
  revisado más reciente, según la regla de arriba.
- 2T2025, 3T2025: leídos del gráfico retrospectivo del boletín 4T2025 (32
  trimestres apretados en un solo gráfico) — confianza media, no
  cross-validados contra un segundo boletín.
- 4T2025: **-0,9%**, confirmado dos veces en el boletín 4T2025 (el
  callout destacado y el texto de la portada) — confianza alta.

## Catálogo completo de boletines (URLs confirmadas)

Base: `https://www.econo.unlp.edu.ar`. Fuente: listado de
`https://www.econo.unlp.edu.ar/laboratorio/indicador-de-actividad-economica-la-plata-iaelap-6682`.

| Período | URL (path relativo a la base) |
|---|---|
| Presentación del IAELaP | `/frontend/media/69/17369/9a541b2df7452771b4469b21d3db3b52.pdf` |
| 1T2019 | `/frontend/media/56/17356/bab243a0b73e8a07ea3af69b7c5a0057.pdf` |
| 2T2019 | `/frontend/media/42/18442/041080bf101ce806eb4c758482190ca2.pdf` |
| 3T2019 | `/frontend/media/48/19848/6798b6fecaaab9b546e0c3c5e7bcc599.pdf` |
| 4T2019 y resumen anual | `/frontend/media/3/20403/6be87b2ec9c9c1dda546320fe9d8c137.pdf` |
| 1T2020 | `/frontend/media/82/20482/2b7a3c1ff118dfd04639b913f11878ef.pdf` |
| 2T2020 | `/frontend/media/58/20758/730001ae40e6ae3f73526c06e85cdcba.pdf` |
| 3T2020 | `/frontend/media/92/21592/53da785c86a5b10954dcef590deb32b3.pdf` |
| 4T2020 | `/frontend/media/0/22000/25fbfb3fd5a1d1ad4182364e2b70e648.pdf` |
| Resumen anual 2020 | `/frontend/media/22/22522/c351898c1357dc158093a8bbb3ee8cab.pdf` |
| 1T2021 | `/frontend/media/30/22730/749ad2cbbdcc6d92ba8793368b36af4f.pdf` |
| 2T2021 (informe para prensa) | `/frontend/media/24/23324/512736fe756c6b5022ee0d380d975b77.pdf` |
| 2T2021 (informe completo) | `/frontend/media/25/23325/96a6d030313141afec4d6912981f6b23.pdf` |
| 3T2021 | `/frontend/media/36/24236/738c4bf7ff3b34cba16f58678c6ed97b.pdf` |
| 4T2021 | `/frontend/media/20/24620/93f7d978388d5069e07af451a95b774d.pdf` |
| 1T2022 | `/frontend/media/16/25316/f6e156692a4dff62303342713f90f954.pdf` |
| 2T2022 | `/frontend/media/90/25990/7b6f3f445180e3dd7e882d42f0d8e43e.pdf` |
| 3T2022 | `/frontend/media/27/27027/ded22ea703bef23dcf40321f6415d7d4.pdf` |
| 4T2022 | `/frontend/media/15/27415/4793af1fabb0ee3124c44235627855e4.pdf` |
| 1T2023 | `/frontend/media/19/28119/a794cf43bc056ec95d2bf9c0768a0ba0.pdf` |
| 2T2023 | `/frontend/media/31/28931/cf4a19b79719663d343e4c8230ca2ecf.pdf` |
| 3T2023 | `/frontend/media/58/29758/e88df86856393e08ba6908cb931b93b4.pdf` |
| 4T2023 | `/frontend/media/45/30045/049a417b728be5dbed7a1a97e29f74c8.pdf` |
| 1T2024 | `/frontend/media/53/30653/803985c131421e45a7ad93140419e63c.pdf` |
| 2T2024 | `/frontend/media/1/31301/892bf8a516b737774b67efae0375f121.pdf` |
| 3T2024 | `/frontend/media/87/32387/6432e76ef140010422e4ecf024dc131d.pdf` |
| 4T2024 | `/frontend/media/88/32388/98a533960455dfbfd509795bb1f7fb33.pdf` |
| 1T2025 | `/frontend/media/67/33167/5b9c3ab1901fb7b887ba94b54c1c5a63.pdf` |
| 2T2025 | `/frontend/media/9/33709/9c33c33e778e7ca410624aa8d09de710.pdf` |
| 3T2025 | `/frontend/media/51/34651/815135e20b84fd4e4d45fed1202ae180.pdf` |
| 4T2025 | `/frontend/media/68/34968/85b21e9958fb81a1b12787fa316d2c6a.pdf` |
| 1T2026 | `/frontend/media/9/35609/92b94ae1d008f5cf4422fce0ed61f5e8.pdf` |

## Qué falta si se quiere completar/mejorar el dataset

1. Localizar el valor exacto de 4T2024 (probablemente leyendo el boletín
   4T2024 o 1T2025 con más cuidado, o un boletín posterior que lo repita).
2. Subir la confianza de 2T2025/3T2025 leyendo el boletín 3T2025
   directamente (en vez de leerlos del gráfico retrospectivo apretado del
   4T2025).
3. Si se quiere una serie de niveles del índice (no solo variación %
   interanual), hay que leer el valor `Índice 2018=100` de cada boletín —
   no se relevó en esta pasada, solo la variación %.
4. Ampliar `iaelap_la_plata_ramas.csv` a más trimestres/ramas si hace falta
   para los gráficos de series por rama — hoy solo tiene 4T2025 (trimestral)
   y 2025 (anual).
