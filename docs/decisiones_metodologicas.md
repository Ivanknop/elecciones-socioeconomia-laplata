# Decisiones metodológicas — panel temporal de ventanas electorales

Registro de las decisiones D1-D10 adoptadas en la rama `especializacion`
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
