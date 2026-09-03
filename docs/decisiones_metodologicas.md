# Decisiones metodológicas — panel temporal de ventanas electorales

Registro de las decisiones D1-D13 adoptadas en la rama `especializacion`
(ver `docs/especificacion_panel_temporal.md` para el diseño completo). Cada
decisión indica su estado; las marcadas "pendiente" no habilitan su uso en
conclusiones del TFI hasta resolverse.

| ID | Decisión | Estado |
|---|---|---|
| D1 | Pivote de panel espacial (localidad) a panel temporal de ventanas a nivel distrito | **Pendiente de confirmación formal con la dirección del TFI** |
| D2 | Corte temporal inferior en 2001, por disponibilidad conjunta de series económicas e ICG | Adoptada |
| D3 | El bloque largo (t-2 → t) genera features adicionales de la misma observación, no observaciones nuevas — evita pseudo-replicación | Adoptada |
| D4 | Ventanas de largo homogéneo (~24 meses); no se normaliza por duración variable (único desdoblamiento en 2025, de pocos meses) | Adoptada |
| D5 | Similitud definida como unificación de trayectoria intraventana + posición relativa interventana; se descarta el nivel absoluto como criterio principal | Adoptada |
| D6 | Período 2007-2015 (INDEC intervenido): se incluye, se marca con flag `periodo_intervenido`, se hace análisis de sensibilidad. No se excluye a priori | Adoptada |
| D7 | Tres series paralelas por nivel, no panel apilado. Pooling parcial entre niveles queda por resolver empíricamente | Adoptada (pooling abierto) |
| D8 | El panel espacial por localidad se conserva como análisis secundario y para visualización, no se elimina | Adoptada |
| D9 | El conjunto de variables es abierto y extensible. Se declara en `registro_variables.csv`, no en código. `features_ventana.py` opera genéricamente sobre ese registro. Incorporar una variable nueva no requiere refactorizar | Adoptada |
| D10 | `panel_ventanas.csv` mantiene las 31 filas con columna `nivel` (un solo pipeline de construcción), pero la interfaz de carga para modelado (`src/ml_models/cargar_panel.py`) exige `nivel` como parámetro obligatorio en `cargar_panel()`. El apilado de los tres niveles requiere `cargar_panel_apilado(justificacion)`, una función separada que exige justificación explícita. La estructura de datos no compromete la resolución de D7: ambas vías (sin pooling, pooling parcial vía apilado deliberado) siguen disponibles, pero el apilado nunca es la ruta por defecto ni puede ocurrir por accidente | Adoptada |
| D11 | `resultado_distrito.csv`/`voto_partido_distrito.csv` usan siempre la etapa `generales` (primera vuelta), nunca `balotaje` -- misma convención que `analisis.graficos._cargar_circuito`. Para presidente 2015 y 2023, `gana_oficialismo`/`share_oficialismo` describen la primera vuelta en La Plata, no el resultado final de la elección (decidido en balotaje). Verificado empíricamente: en ambos años el resultado de primera vuelta en La Plata coincide con el `agrupacion_ganadora`/`era_oficialismo` ya curado en `oficialismos.csv`, así que esto es consistente con el resto del repo, no una fuente nueva de error | Adoptada |
| D12 | `oficialismo_por_nivel.csv`: `agrupacion_oficialismo` es el titular del Ejecutivo *real* (quién efectivamente gobierna la provincia/nación/municipio), llevado como estado que solo cambia en años con elección ejecutiva -- nunca se deriva de `agrupacion_ganadora` de esa misma fila (eso tautologizaría `gana_oficialismo`). Para `provincial`/`nacional`, `agrupacion_ganadora` de `oficialismos.csv` es el voto *de La Plata*, que puede divergir del resultado real de la provincia/nación (divergencia real encontrada y corregida: gobernador 2019, La Plata votó JUNTOS POR EL CAMBIO pero la provincia eligió a Kicillof/FRENTE DE TODOS) -- el titular se corrige a mano en esos casos puntuales (`_TITULAR_REAL_DIVERGE_DE_VOTO_LA_PLATA`), verificado por conteo real de circuitos, no supuesto. Para `municipal` no aplica (el intendente lo elige La Plata directamente) | Adoptada |
| D13 | Panel trimestral complementario (`panel_trimestral_<nivel>.csv`, Fase 5, paralelo a `panel_ventanas.csv`, no lo reemplaza): N de trimestres por ventana es `round(meses_entre_elecciones / 3)`, variable entre 6 y 10 según la ventana real, nunca fijo en 8 -- ver corrección a D4 abajo | Adoptada |
| D14 | Panel trimestral "bielección" (`panel_bieleccion_trimestral_<nivel>.csv`, `data/tfi_data/panel/t-2/`, paralelo a D13 que pasa a vivir en `data/tfi_data/panel/t-1/`): mismo formato de fila, pero sobre el bloque largo `_vl` de `features_ventana.py` (elección t-2 a t, 4 años/dos elecciones) en vez del bloque corto `_vc`. Ventanas sin `fecha_inicio_vl` (primera transición de cada nivel, D3) se saltean -- 28 ventanas resultantes, no 31 | Adoptada |
| D15 | `oficialismos.csv` se extiende de 2011-2025 a 2001-2025 (`municipal`/`provincial`; `nacional` sigue sin cubrir 2001-2009, mismo criterio que `calendario_electoral.csv`/`oficialismo_por_nivel.csv`, que tampoco lo cubren). `agrupacion_ganadora` sale de `data/tfi_data/elecciones/<año>_<nivel>.csv` (mayor cantidad de votos, excluyendo BLANCO/NULO/VOTANTES_HABILITADOS); `era_oficialismo` no se re-deriva desde cero -- reusa las mismas fuentes ya citadas en `construir_calendario.py` (`_EJECUTIVA_PRE_2011`/`_TITULAR_INICIAL_2001`, resultado de la elección ejecutiva real) y en `construir_resultado_distrito.py` (`ALIAS_LISTA_OFICIALISMO`, relabeling de listas peronistas 2005-2009). Verificado contra `data/tfi_data/resultado_distrito.csv` ya existente: `gana_oficialismo`/`share_oficialismo` de esas 10 filas, calculados hasta ahora por matching de nombre contra `oficialismo_por_nivel.csv`, coinciden exactamente con los valores de `era_oficialismo` cargados acá -- no una fuente nueva de criterio, una curación explícita de uno ya vigente. `continua_renombrada` (2007 provincial, Solá→Scioli) colapsa a `era_oficialismo=true`, mismo tratamiento binario que ya recibía cualquier renombre de frente en 2011-2025 (ej. Bruera 2007→2011, Partido Progreso Social→FPV) | Adoptada |

## Corrección a D4 (2026-09-01)

D4 asumía ventanas de largo homogéneo (~24 meses), con el único
desdoblamiento real en 2025. Verificado contra las 31 filas reales de
`ventanas.csv`: las ventanas municipal/provincial 2001-2011 (desdoblamientos
PBA de ese período, no solo 2025) van de 18 a 30 meses. D4 sigue vigente
como estaba para `panel_ventanas.csv` (que en efecto no normaliza por
duración de ventana, Fase 4) -- la homogeneidad de ~24 meses no es, sin
embargo, un hecho general del calendario electoral. El panel trimestral
(D13) sí normaliza, calculando N de trimestres por ventana real en vez de
asumir 8 fijo.

## Corrección a D12 (2026-09-01)

D12 documenta el mecanismo `_TITULAR_REAL_DIVERGE_DE_VOTO_LA_PLATA` con
un único caso real (gobernador 2019). Se encontró y corrigió un segundo
caso del mismo tipo, faltante hasta esta fecha: **presidente 2023**. La
Plata votó por UNION POR LA PATRIA en primera vuelta (`oficialismos.csv`,
`era_oficialismo=true`), pero Milei/ALIANZA LA LIBERTAD AVANZA ganó la
presidencia real en balotaje. Sin este caso en el diccionario, el titular
nacional no se actualizaba tras 2023 y la fila `2025,nacional` de
`oficialismo_por_nivel.csv` quedaba con `agrupacion_oficialismo=UNION POR
LA PATRIA`, arrastrado por error a `panel_ventanas.csv` y a
`panel_trimestral_nacional.csv` (Fase 5). Corregido agregando
`("nacional", 2023)` al diccionario -- `continuidad_oficialismo` de esa
fila pasa a `ruptura` (el Ejecutivo real sí cambió) y el titular desde
dic-2023 es ALIANZA LA LIBERTAD AVANZA. `gana_oficialismo`/
`share_oficialismo`/`delta_v` de `resultado_distrito.csv` no cambiaron --
ya eran correctos porque salen directo de `oficialismos.csv` curado, no
de `oficialismo_por_nivel.csv`.

## Nota sobre alcance real vs. especificado (auditoría de la rama)

La especificación (`especificacion_panel_temporal.md` §4.3) lista 8
variables económicas en estado `nucleo`. La auditoría inicial de esta rama
y los intentos de adquisición de la Fase 0.5 determinan el estado real de
cada una en `registro_variables.csv` — no se asume `nucleo` por default.
Igual criterio para la cobertura electoral 2001-2009: se documenta el
resultado real de los intentos de adquisición (ver sección "Datos
pendientes de adquisición" del reporte de la rama) en vez de asumir que el
panel alcanza los 31 valores de `delta_v` no nulos que la especificación
proyecta como ideal.
