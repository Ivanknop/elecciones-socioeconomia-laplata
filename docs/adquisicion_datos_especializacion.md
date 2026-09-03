# Adquisición de datos — Fase 0.5 de `especializacion`

Registro de los intentos reales de adquisición de datos exigidos por el
protocolo (buscar en el repo → intentar la fuente real → escalar solo si
requiere navegación manual/login/formato no parseable). Cada ítem indica
qué se intentó, con qué resultado, y la fuente exacta.

## 1.b — IPC empalmado 2001-2025: ÉXITO

La API de series de tiempo de datos.gob.ar (`apis.datos.gob.ar/series/api/series/`,
la misma que ya usa `macroeconomia.datos_gob_client.DatosGobClient`) tiene
tres series oficiales de INDEC encadenables por vintage metodológico,
verificadas con pedidos reales (valores numéricos confirmados, no solo
metadata):

| Tramo | `id_datos_gob` | Cobertura real | Periodicidad |
|---|---|---|---|
| Empalme histórico (bases 1943/1960/1974/1988/1999, a abril 2008=100) | `178.1_NL_GENERAL_0_0_13` | 1943-01 → 2008-04 | mensual |
| Base abril 2008=100 | `97.2_ING_2008_M_17` | 1993-01 → 2013-12 | mensual |
| Base diciembre 2016=100 | ya en `data/macroeconomia/catalogo_series.csv` (`ipc_nacional`) | 2016-12 → presente | mensual |

**Hueco real, no una falla de búsqueda:** 2014-01 a fines de 2016 no tiene
serie nacional mensual oficial publicada en ninguna fuente encontrada —
período de transición metodológica post-intervención INDEC, coincide con
el final de la ventana ya marcada `periodo_intervenido` (D6). Se declara
como tramo faltante explícito, no se imputa.

## 1.d — ICC (Índice de Confianza del Consumidor, UTDT): ÉXITO

Misma API de series de datos.gob.ar. Serie `380.3_ICC_NACIONNAL_0_T_12`
("Índice de Confianza del Consumidor"), **2001-03 → 2026-08, mensual**,
valores reales confirmados por pedido directo. No hizo falta scrapear la
página de UTDT ni colocar un archivo manual.

## 1.e — Resultado fiscal primario: ÉXITO

Misma API. Tres series de "Esquema Ahorro - Inversión - Financiamiento.
Sector Público Nacional. Base Caja" (Secretaría de Hacienda), encadenables:

| Tramo | `id_datos_gob` | Cobertura real | Periodicidad |
|---|---|---|---|
| Metodología 1993-2006 | `379.4_RESULTADO_006__36_27` | 1993-01 → 2006-10 | trimestral |
| Metodología 2007-2014 | `379.5_RESULTADO_014__36_68` | 2007-01 → 2014-10 | a confirmar en Fase 3 |
| Metodología 2015-presente | `379.9_RESULTADO_017__31_73` | 2015-01 → 2026-06 | a confirmar en Fase 3 |

Cubre 2001-2025 casi por completo, con posibles micro-huecos en los
empalmes de vintage (se verifican y flaguean en Fase 3, no se interpolan
sin marcar).

## 1.a — Resultados electorales 2001-2009: ÉXITO PARCIAL — requiere escalar

**Confirmado por pedido real a la API oficial** (`resultados.mininterior.gob.ar`):
con los mismos parámetros que devuelven datos reales para 2011
(`categoriaId=7` intendente, `distritoId=2`, `seccionId=63`), los años 2001,
2003 y 2009 devuelven `mesasTotalizadas:0` y listas vacías. **La API de este
repositorio no tiene datos electorales pre-2011**, no es una limitación del
caché.

**Conseguido (identidad y continuidad del oficialismo, no share de voto):**
- Fuente: artículo de 0221.com.ar que cita a la Junta Electoral de la
  Provincia de Buenos Aires como fuente de los registros históricos de
  intendente de La Plata 1983-2023 (`0221.com.ar/la-plata/desde-el-83-la-fecha-...-n82889`).
  Confirma: Alak (PJ) intendente 1991-2007 (electo 1991/1995/1999/2003);
  Bruera (Partido Progreso Social, luego PJ/FpV) gana 2007 y 2011; Garro
  (Cambiemos/JxC) gana 2015 y 2019; Alak (UxP) recupera en 2023.
- Fuente: mirror en GitHub `PoliticaArgentina/data_warehouse`
  (`electorAr/data/escrutinios_definitivos/pba_gober_gral2003.csv` y
  `pba_gober_gral2007.csv`, scrapeados del Atlas Electoral de Andy Tow):
  confirman ganador de gobernación PBA — Solá (Justicialista) 2003, Scioli
  (Frente Para La Victoria) 2007.

Esto permite completar `oficialismo_por_nivel.csv` 2001-2009 con identidad
+ `continuidad_oficialismo` real y citado.

**No conseguido — requiere escalar:** el detalle de voto por lista **a
nivel Partido de La Plata específicamente** (necesario para
`voto_partido_distrito.csv`/`resultado_distrito.csv`/`delta_v`) para
intendente, concejales, gobernador (recorte La Plata) y diputados
provinciales, en 2001/2003/2005/2007/2009. Se intentó:
1. API oficial: vacía (confirmado).
2. Mirror de GitHub: los archivos `pba_gober_gral*.csv` solo tienen
   **totales provinciales**, sin desagregación por partido/localidad —
   estructuralmente insuficientes para este uso. Tampoco existe ningún
   archivo de intendente/concejales (nivel municipal) en todo el
   repositorio — no se compila a ese nivel.
3. Sitio original del Atlas Electoral de Andy Tow (`andytow.com`): responde
   `HTTP 401` (login requerido), confirmado por pedido directo — no
   accesible programáticamente.

**Qué se necesita, en qué formato:** escrutinio definitivo por lista y por
circuito/localidad del Partido de La Plata para intendente y concejales
(2001, 2003, 2005, 2007, 2009) y para gobernador y diputados provinciales
recortado a La Plata (mismos años). La Junta Electoral de la Provincia de
Buenos Aires (`juntaelectoral.gba.gov.ar`) es la fuente primaria más
probable para el archivo histórico; un CSV o planilla con
`año,categoria,circuito_o_localidad,lista,votos` sería directamente
compatible con el pipeline existente.

**Impacto:** hasta que se consiga, las transiciones municipal/provincial
2001→2003, 2003→2005, 2005→2007, 2007→2009 y 2009→2011 quedan con
`resultado_disponible=false` en `resultado_distrito.csv`/`panel_ventanas.csv`
(sin el detalle por circuito, `participacion` exacta y `votos_blanco` con la
fórmula de ausentismo real siguen sin poder derivarse).

**Actualización:** el detalle de voto por lista a nivel Partido de La Plata
sí se consiguió después (sesión "Agrega elecciones 2001-2009 y 2025
municipal/provincial...", `data/tfi_data/elecciones/<año>_<nivel>.csv`, uno
por (año,nivel) 2001-2009) -- `resultado_disponible` sigue en `false` (no
hay circuito), pero `ml_models.construir_resultado_distrito` ya cae a ese
CSV para completar `votos_validos`/`votos_blanco` y, vía
`construir_voto_partido_distrito`, también `gana_oficialismo`/
`share_oficialismo`/`delta_v` (emparejando por nombre contra
`oficialismo_por_nivel.csv`, con `ALIAS_LISTA_OFICIALISMO` citado para los
años de relabeling de frentes: 2005 municipal/provincial, 2007 provincial,
2009 municipal/provincial). Solo `participacion` exacta sigue bloqueada
(depende del padrón real por circuito, no solo del total por lista).

## 1.c — 2025 municipal/provincial: requiere escalar (fuente distinta, no un re-run)

**Corrección a la expectativa original del plan:** no es simplemente
"correr los notebooks 01→04 de nuevo". Confirmado por pedido real a la API
oficial (`categoriaId=7` y `categoriaId=10`, año 2025): vacío. La elección
2025 de la Provincia de Buenos Aires (municipal + provincial) se desdobló
en fecha propia y corrió **por el sistema separado de la Junta Electoral
bonaerense** (`resultados.eleccionesbonaerenses.gba.gob.ar`), no por la API
federal de Ministerio del Interior que usa `src/electoral/client.py`.

Cerrar este gap requiere un cliente HTTP nuevo contra una API distinta —
trabajo de `src/electoral/`, fuera del alcance de `src/ml_models/` en esta
rama (que solo lee `data/distrito/` existente, no agrega fuentes nuevas de
resultados electorales crudos). Se escala como tarea aparte, con la URL del
portal correcto.

## Resumen de estado para `registro_variables.csv` (Fase 3)

| Variable | Estado tras Fase 0.5 |
|---|---|
| `icg`, `desocupacion`, `tc_oficial`, `reservas`, `emae` | `nucleo`/`complementaria` — ya en el repo, sin cambios |
| `ipc` | `nucleo` — datos reales 2001-2013 + 2016-2025, hueco 2014-2016 flagueado |
| `icc` | `nucleo` — datos reales 2001-2025 |
| `resultado_fiscal` | `nucleo` — datos reales 2001-2025 (posibles micro-huecos en empalmes, a verificar) |
| `salario_real` | `nucleo` — depende de `ipc`, cobertura ahora casi completa salvo el mismo hueco 2014-2016 |
| `pobreza`, `gini`, `brecha_cambiaria`, `empleo_registrado_pba` | `exploratoria` — no se intentó adquisición nueva en esta ronda (prioridad menor, fuera de los 5 ítems priorizados); pendiente de una Fase 0.5 futura |
