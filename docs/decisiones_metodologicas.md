# Decisiones metodológicas — panel temporal de ventanas electorales

Registro de las decisiones D1-D13 adoptadas en la rama `especializacion`
(ver `docs/especificaciones/especificacion_panel_temporal.md` para el diseño completo). Cada
decisión indica su estado; las marcadas "pendiente" no habilitan su uso en
conclusiones del TFI hasta resolverse.

| ID | Decisión | Estado |
|---|---|---|
| D1 | Pivote de panel espacial (localidad) a panel temporal de ventanas a nivel distrito | **Pendiente de confirmación formal con la dirección del TFI** |
| D2 | Corte temporal inferior en 2001, por disponibilidad conjunta de series económicas e ICG | Adoptada |
| D3 | El bloque largo (t-2 → t) genera features adicionales de la misma observación, no observaciones nuevas — evita pseudo-replicación | Adoptada |
| D4 | Ventanas de largo homogéneo (~24 meses); no se normaliza por duración variable (único desdoblamiento en 2025, de pocos meses) | Adoptada |
| D5 | Similitud definida como unificación de trayectoria intraventana + posición relativa interventana; se descarta el nivel absoluto como criterio principal | Adoptada |
| D6 | Período 2007-2015 (INDEC intervenido): se incluye, no se excluye a priori. Ver corrección abajo -- ya no se marca con flag | Adoptada (corregida) |
| D7 | Tres series paralelas por nivel, no panel apilado. Pooling parcial entre niveles queda por resolver empíricamente | Adoptada (pooling abierto) |
| D8 | El panel espacial por localidad se conserva como análisis secundario y para visualización, no se elimina | Adoptada |
| D9 | El conjunto de variables es abierto y extensible. Se declara en `registro_variables.csv`, no en código. `features_ventana.py` opera genéricamente sobre ese registro. Incorporar una variable nueva no requiere refactorizar | Adoptada |
| D10 | `panel_ventanas.csv` mantiene las 31 filas con columna `nivel` (un solo pipeline de construcción), pero la interfaz de carga para modelado (`src/ml_models/cargar_panel.py`) exige `nivel` como parámetro obligatorio en `cargar_panel()`. El apilado de los tres niveles requiere `cargar_panel_apilado(justificacion)`, una función separada que exige justificación explícita. La estructura de datos no compromete la resolución de D7: ambas vías (sin pooling, pooling parcial vía apilado deliberado) siguen disponibles, pero el apilado nunca es la ruta por defecto ni puede ocurrir por accidente | Adoptada |
| D11 | `resultado_distrito.csv`/`voto_partido_distrito.csv` usan siempre la etapa `generales` (primera vuelta), nunca `balotaje` -- misma convención que `analisis.graficos._cargar_circuito`. Para presidente 2015 y 2023, `gana_oficialismo`/`share_oficialismo` describen la primera vuelta en La Plata, no el resultado final de la elección (decidido en balotaje). Verificado empíricamente: en ambos años el resultado de primera vuelta en La Plata coincide con el `agrupacion_ganadora`/`era_oficialismo` ya curado en `oficialismos.csv`, así que esto es consistente con el resto del repo, no una fuente nueva de error | Adoptada |
| D12 | `oficialismo_por_nivel.csv`: `agrupacion_oficialismo` es el titular del Ejecutivo *real* (quién efectivamente gobierna la provincia/nación/municipio), llevado como estado que solo cambia en años con elección ejecutiva -- nunca se deriva de `agrupacion_ganadora` de esa misma fila (eso tautologizaría `gana_oficialismo`). Para `provincial`/`nacional`, `agrupacion_ganadora` de `oficialismos.csv` es el voto *de La Plata*, que puede divergir del resultado real de la provincia/nación (divergencia real encontrada y corregida: gobernador 2019, La Plata votó JUNTOS POR EL CAMBIO pero la provincia eligió a Kicillof/FRENTE DE TODOS) -- el titular se corrige a mano en esos casos puntuales (`_TITULAR_REAL_DIVERGE_DE_VOTO_LA_PLATA`), verificado por conteo real de circuitos, no supuesto. Para `municipal` no aplica (el intendente lo elige La Plata directamente) | Adoptada |
| D13 | Panel trimestral complementario (`panel_trimestral_<nivel>.csv`, Fase 5, paralelo a `panel_ventanas.csv`, no lo reemplaza): N de trimestres por ventana es `round(meses_entre_elecciones / 3)`, variable entre 6 y 10 según la ventana real, nunca fijo en 8 -- ver corrección a D4 abajo | Adoptada |
| D14 | Panel trimestral "bielección" (`panel_bieleccion_trimestral_<nivel>.csv`, `data/tfi_data/panel/t-2/`, paralelo a D13 que pasa a vivir en `data/tfi_data/panel/t-1/`): mismo formato de fila, pero sobre el bloque largo `_vl` de `features_ventana.py` (elección t-2 a t, 4 años/dos elecciones) en vez del bloque corto `_vc`. Ventanas sin `fecha_inicio_vl` (primera transición de cada nivel, D3) se saltean -- 28 ventanas resultantes, no 31 | Adoptada |
| D15 | `oficialismos.csv` se extiende de 2011-2025 a 2001-2025 (`municipal`/`provincial`; `nacional` sigue sin cubrir 2001-2009, mismo criterio que `calendario_electoral.csv`/`oficialismo_por_nivel.csv`, que tampoco lo cubren). `agrupacion_ganadora` sale de `data/tfi_data/elecciones/<año>_<nivel>.csv` (mayor cantidad de votos, excluyendo BLANCO/NULO/VOTANTES_HABILITADOS); `era_oficialismo` no se re-deriva desde cero -- reusa las mismas fuentes ya citadas en `construir_calendario.py` (`_EJECUTIVA_PRE_2011`/`_TITULAR_INICIAL_2001`, resultado de la elección ejecutiva real) y en `construir_resultado_distrito.py` (`ALIAS_LISTA_OFICIALISMO`, relabeling de listas peronistas 2005-2009). Verificado contra `data/tfi_data/resultado_distrito.csv` ya existente: `gana_oficialismo`/`share_oficialismo` de esas 10 filas, calculados hasta ahora por matching de nombre contra `oficialismo_por_nivel.csv`, coinciden exactamente con los valores de `era_oficialismo` cargados acá -- no una fuente nueva de criterio, una curación explícita de uno ya vigente. `continua_renombrada` (2007 provincial, Solá→Scioli) colapsa a `era_oficialismo=true`, mismo tratamiento binario que ya recibía cualquier renombre de frente en 2011-2025 (ej. Bruera 2007→2011, Partido Progreso Social→FPV) | Adoptada |
| D16 | Bug de matching de nombre (no hueco de adquisición) en `_resolver_oficialismo`: cuando `era_oficialismo=false` (D15), `share_oficialismo` igual necesita emparejar por nombre contra `_match_oficialismo`, y ese emparejamiento fallaba en silencio para `(2013, nacional/provincial/municipal)` -- boleta real `FRENTE PARA LA VICTORIA`, sin el prefijo "ALIANZA" que sí trae `oficialismo_por_nivel.csv` y que sí aparece en 2011/2015 (`id_agrupacion` 0501 en 2013 vs. 0131 en 2011/2015, alianza registrada distinto ese año) -- y para `(2019, nacional)` -- boleta real `JUNTOS POR EL CAMBIO`, rebranding de Cambiemos para las legislativas de 2019 (mismo `id_agrupacion` 135), mientras `oficialismo_por_nivel.csv` sigue etiquetando esa fila como `ALIANZA CAMBIEMOS`. Corregido agregando las 4 entradas a `ALIAS_LISTA_OFICIALISMO`, mismo mecanismo ya usado para 2005-2009. Auditado el resto de las 34 filas `(año,nivel)` con fila en `oficialismo_por_nivel.csv`: ningún otro caso de `era_oficialismo=false` tiene mismatch de nombre sin resolver (hay mismatches en años con `era_oficialismo=true`, ej. 2011 municipal, 2017/2019/2023/2025 varios niveles, pero esa rama no pasa por `_match_oficialismo` -- usa `ganador.share` directo -- así que no son bugs activos, no se les agrega alias). Afecta tanto `panel_trimestral_<nivel>.csv` (D13, 4 filas frontera) como `panel_bieleccion_trimestral_<nivel>.csv` (D14, 7 filas frontera -- cada año interviene dos veces en el bloque largo, una vez como `eleccion_t` y otra como `eleccion_t_menos_2` de la ventana siguiente) además de `panel_ventanas.csv` (8 `delta_v` que dependían de alguno de los 4 extremos). Verificado fila por fila (no solo conteo de nulos): `gana_oficialismo` no cambió en ninguna fila (ya lo resolvía D15 sin depender del nombre); `share_oficialismo`/`delta_v` cambiaron únicamente en las filas esperadas | Adoptada |
| D17 | `data/tfi_data/elecciones.csv` (grano `nivel`×`anio`, generado por `ml_models.construir_elecciones_resumen`) pasa a ser la fuente de verdad de la estructura de la oferta electoral (fuerzas viables, marginal, oposición principal, dispersión ideológica) y del cruce oficialismo/ausentismo que consume el panel trimestral (D13/D14) -- ver diccionario de columnas en `docs/especificaciones/especificacion_panel_temporal.md`. `resultado_distrito.csv`/`voto_partido_distrito.csv` quedan congelados: siguen en el repo y `construir_resultado_distrito.py` sigue andando si se lo corre a mano, pero ninguna otra pieza del pipeline los lee ni los regenera modificados (mismo patrón "huérfano, no eliminado" ya documentado en `CLAUDE.md` para `vparty_cuadrantes_local`). El pedido original era construir `elecciones.csv` a partir de `voto_partido_distrito.csv`; se usó en cambio `data/tfi_data/elecciones/<año>_<nivel>.csv` (detalle por partido con BLANCO/NULO/VOTANTES_HABILITADOS y V-Party ya sincronizado, ver `construir_elecciones.py`) porque `voto_partido_distrito.csv` no tiene ninguna de esas columnas y reconstruirlas ahí hubiera duplicado lógica ya resuelta y testeada. `ausentismo` usa dos fórmulas no exactamente equivalentes: años con `circuito_<cargo>.json` reusan `electores - positivos - otros_total` (`analisis.graficos._votos_no_ideologicos`), que excluye de "ausente" a categorías `RECURRIDO(S)`/`IMPUGNADO(S)`/`COMANDO`; años sin circuito (2001-2009, 2025 municipal/provincial) restan `votantes_habilitados - votos_positivos - votos_blancos - votos_nulos`, que no puede distinguir esas categorías si existieron -- el `ausentismo` de 2001-2009 podría estar levemente sobreestimado por esto, documentado como limitación, no corregido por falta de desglose real. `votos_nulos`/`ausentismo` quedan vacíos (no en 0) para `2025 provincial`/`2025 municipal`: la fuente de esos dos años (sistema separado de la Junta Electoral bonaerense, ver `docs/adquisicion_datos_especializacion.md` §1.c) no trae fila NULO. El piso de "fuerza viable" es 1.5% de `votos_positivos` (Ley 26.571, 2011) -- mismo denominador que usa `share_oficialismo` en las dos ramas de `_resolver_oficialismo` (`models.totalizar_agrupaciones` y `_voto_partido_desde_tfi`, verificado antes de escribir este módulo, no supuesto). Verificado contra los 34 `(nivel,año)` reales que ninguna elección del período fue bipartidista (entre 5 y 13 fuerzas viables siempre) -- por eso se agrega `share_otras_fuerzas_viables` (no estaba en el pedido original): sin ella, `share_oficialismo + share_oposicion_principal + share_marginal_acumulado` no se acerca a 100 (ej. 2001 provincial: 50.44 sobre 100, un 49.56 real quedaba sin ninguna columna). Con esa cuarta columna la identidad cierra por construcción: `share_marginal_acumulado + share_oposicion_principal + share_otras_fuerzas_viables + share_oficialismo (si el oficialismo es viable) = 100`; si el oficialismo no es viable (share < 1.5%), su share ya está adentro de `share_marginal_acumulado` y no se lo cuenta en `n_fuerzas_viables` (no ocurrió en los 34 casos reales del período, caso cubierto con fixture sintética en `tests/ml_models/test_construir_elecciones_resumen.py`). Dispersión ideológica ponderada por voto (μ, σ²) se calcula por separado para los ejes `vparty_economico` y `vparty_progresismo` (populismo afuera, mismo criterio que `vparty_cuadrantes_local`), solo sobre fuerzas viables y solo con score V-Party cargado (388/557 filas de `clasificacion_ideologica_agrupaciones.csv` a esta fecha) -- vacía si ninguna fuerza viable de esa elección tiene score. Las columnas nuevas se documentan en `docs/especificaciones/especificacion_panel_temporal.md`, no en `registro_variables.csv`: ese registro es para series mensuales/trimestrales externas que alimenta genéricamente `features_ventana.py` (periodicidad_nativa, es_flujo, polaridad), no para atributos estructurales por elección -- forzarlas ahí haría que `features_ventana.py` intentara calcular `_pendiente`/`_volatilidad` sobre un valor puntual por elección, sin sentido. **Extensión posterior**: se agrega `dispersion_cobertura_share` = (suma de votos de fuerzas viables con V-Party cargado) / `votos_positivos`, escala 0-100 (mismo criterio que las columnas `share_*` hermanas) -- sin esta columna, un salto en `dispersion_economico_mu`/`dispersion_progresismo_mu` entre dos elecciones no se puede distinguir de un cambio en qué fracción del voto tiene V-Party cargado; `0.0` (no vacío) si ninguna fuerza viable tiene score, a diferencia de `dispersion_economico_mu`/`sigma2`, que sí quedan vacías en ese caso -- son preguntas distintas ("cuánto sabemos" vs. "qué dice lo que sabemos") | Adoptada |
| D18 | **Auditoría de `distancia_oficialismo_alternativa`** (`panel_ventanas.csv`, calculada en `construir_resultado_distrito.calcular_distancia_oficialismo_alternativa`, invocada desde `construir_panel_ventanas.construir_panel`): mide un solo eje (`vparty_economico` -- `_construir_posiciones` nunca guarda `vparty_progresismo`), contra la fuerza con más votos entre TODAS las agrupaciones con score conocido (sin piso de viabilidad 1.5%), y matchea `of_t["agrupacion_oficialismo"]` (`oficialismo_por_nivel.csv`) **por nombre** contra la boleta real, sin pasar por el curado de `oficialismos.csv`/`ALIAS_LISTA_OFICIALISMO` que sí usa `_entrada_oficialismo` (D15/D16). Verificado contra los datos reales, no supuesto: de 31 filas de `panel_ventanas.csv`, **17 (55%) tienen la columna vacía**, y las 17 son fallo de matching de nombre, no ausencia de score V-Party (confirmado caso por caso con un script ad hoc) -- ej. `oficialismo_por_nivel.csv` dice `FRENTE DE TODOS` para `(2023, nacional)`/`(2023, provincial)` mientras la boleta real dice `UNION POR LA PATRIA`; dice `PARTIDO JUSTICIALISTA` en años donde la boleta real es `ALIANZA FRENTE PARA LA VICTORIA`, etc. **Resolución**: la columna queda en `panel_ventanas.csv` sin tocar, marcada DEPRECADA en el código (comentario en `construir_panel_ventanas.py`) y en la documentación -- no se corrige in-place (sería reimplementar lo que la tabla nueva ya resuelve de raíz) ni se elimina (principio aditivo del repo). Sucedida por **`data/tfi_data/distancias_ideologicas.csv`** (`ml_models.construir_distancias_ideologicas`, grano `nivel×anio×agrupación`, una fila por fuerza viable de cada elección -- no una sola "alternativa" preseleccionada), que resuelve la identidad del oficialismo por **identidad de objeto** contra `_entrada_oficialismo` en vez de por nombre (verificado con los mismos casos reales 2023 nacional/provincial: la fila `es_oficialismo=True` resulta `UNION POR LA PATRIA`, no `FRENTE DE TODOS`, en `tests/ml_models/test_construir_distancias_ideologicas.py::TestCasoRealAuditoria2023`). Distancias por eje (`distancia_economico_al_oficialismo`, `distancia_progresismo_al_oficialismo`) guardadas **con signo** (`score_fuerza − score_oficialismo`, no valor absoluto) -- son las componentes de `distancia_euclidea_al_oficialismo = √(economico² + progresismo²)`, y el signo indica de qué lado del oficialismo cae cada alternativa (relevante para H2/H3). Fila del propio oficialismo: distancias `0.0` siempre, aunque no tenga score propio cargado (distancia de un punto a sí mismo). Si el oficialismo no tiene score V-Party: ninguna distancia de esa elección se puede calcular (sin referencia) -- no ocurrió en los 34 casos reales. `panel_ventanas.csv` suma además `delta_dispersion_economico_mu`/`delta_dispersion_progresismo_mu` (`mu(t) − mu(t−1)` por eje, join contra `elecciones.csv`), `magnitud_desplazamiento_ideologico` (`√(delta_economico² + delta_progresismo²)`) y `cuadrante_desplazamiento` -- criterio de cuadrante: mismo signo que las etiquetas fijas de `analisis.vparty_cuadrantes`/`vparty_cuadrantes_local` (positivo en económico → derecha, positivo en progresismo → progresista), aplicado al **vector de desplazamiento** en vez de al punto absoluto (no existe una función reusable de cuadrantes en esos módulos, solo dibujan las 4 etiquetas como texto fijo); `None` si falta cualquiera de los dos deltas o si alguno es exactamente `0` (cuadrante indefinido, no se fuerza un lado arbitrario). `dispersion_cobertura_share_min` = `min` de la cobertura V-Party en las dos puntas de la transición, agregada para que el notebook de H2/H3 pueda ponderar/filtrar por baja cobertura sin fijar un umbral en código. **Disciplina H1/H4 vs. H2/H3**: estas 4 columnas de desplazamiento son variables dependientes de H2 calculadas con datos de `t` -- nunca predictoras de H1/H4. Confirmado que no hace falta tocar código de `notebooks/ml/01_lasso.ipynb`/`02_bayes.ipynb` para garantizarlo: `01_lasso.ipynb` selecciona features por sufijo (`c.endswith("_vc")`), `02_bayes.ipynb` usa una única variable hardcodeada (`icg_pendiente_vc`) -- ninguna de las 4 columnas nuevas termina en `_vc`/`_vl`, quedan excluidas por construcción. Advertencia dejada en el notebook nuevo (`notebooks/ml/03_desplazamiento_ideologico.ipynb`): si algún día `01_lasso.ipynb` cambia a "todas las columnas menos una blacklist", esas 4 columnas deben agregarse a mano a esa blacklist. **Extensión
posterior**: se agregan `delta_sigma2_economico`/`delta_sigma2_progresismo`
(`dispersion_<eje>_sigma2(t) - dispersion_<eje>_sigma2(t-1)`, mismo join y
misma función `calcular_delta_dispersion` que `delta_dispersion_*_mu`,
ahora con un parámetro `estadistico` -- `"mu"` por default, sin cambiar
comportamiento de los 2 usos existentes). `delta_dispersion_*_mu` mide
hacia dónde se mueve el **centro** de la dispersión ideológica del
electorado y puede cancelarse cuando fuerzas de polos opuestos ganan
votos parecidos entre `t-1` y `t`; `delta_sigma2_*` mide la **varianza**
(fragmentación/polarización) y no cancela ese caso -- son dos preguntas
distintas del mismo fenómeno, ambas necesarias. Caso real que motiva la
distinción (nacional, 2019→2021): `delta_dispersion_economico_mu` = +0.20
(corrimiento moderado del centro) vs. `delta_sigma2_economico` = +0.48
(la varianza creció proporcionalmente más que el centro se movió) --
consistente con que 2021 sumó crecimiento simultáneo de fuerzas en polos
opuestos (LLA a la derecha, FIT-U a la izquierda), un desplazamiento que
`mu` por sí solo subestima. Mismo criterio de exclusión de H1/H4 que las
4 columnas anteriores: son variables dependientes de H2/H3 (fragmentación
en `t`), y por el mismo mecanismo de selección de features (sufijo `_vc`/`_vl`
en `01_lasso.ipynb`, variable única hardcodeada en `02_bayes.ipynb`)
quedan excluidas por construcción, sin tocar esos dos notebooks. Además,
`data/tfi_data/distancias_ideologicas.csv` gana una pestaña interactiva
propia (`src/visualizacion/distancia_por_fuerza.py`, ver
`docs/FUNCIONALIDADES.md`) -- distancia euclídea al oficialismo con signo
(derecha/izquierda según el eje económico) por fuerza viable, año y
nivel; paleta azul/rojo/gris (derecha/izquierda/oficialismo-o-empate)
propia de esa pestaña (no sale de los CSV de
colorimetría, que son para campo ideológico/filiación política absolutos,
no para una distancia relativa al oficialismo) | Adoptada |

## Corrección a D6 (2026-09-06)

La columna booleana `periodo_intervenido` (`series_economicas_mensuales.csv`
y, agregada por trimestre, `panel_trimestral_<nivel>.csv`/
`panel_bieleccion_trimestral_<nivel>.csv`) se elimina: no llegó a
consumirse en ningún análisis de sensibilidad ni en el modelado -- una
columna sin lectores. La mitad de D6 que sigue vigente es la sustantiva:
el período 2007-2015 se incluye igual, sin excluirlo a priori: la reserva
sobre las series oficiales de ese tramo (`ipc`, `desocupacion`,
indirectamente `salario_real`) queda documentada en `nota_metodologica`
de `registro_variables.csv`, no en una columna del panel. Si en algún
momento se retoma el análisis de sensibilidad, la columna se puede volver
a derivar de las fechas (2007-01 a 2015-12) sin depender de este flag.

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

## Nota sobre `trayectorias_economicas*.py` tras D17

`src/visualizacion/trayectorias_economicas.py`/`trayectorias_economicas_bieleccion.py`
infieren qué columnas de `panel_trimestral_<nivel>.csv`/
`panel_bieleccion_trimestral_<nivel>.csv` son variables económicas a
graficar por descarte (`_COLUMNAS_FIJAS`, todo lo que no está en ese
set). Las columnas nuevas que trae D17 a esos dos CSV (`votos_positivos`,
`n_fuerzas_viables`, `dispersion_economico_mu`, etc.) no son variables
económicas y no tienen entrada en `_UNIDADES` -- sin ajustar
`_COLUMNAS_FIJAS` el payload las tomaba como si lo fueran y la pestaña
interactiva rompía (`unidades` vacío para esas columnas). Corregido
importando `ml_models.construir_elecciones_resumen.COLUMNAS_ELECCION_PANEL`
en `_COLUMNAS_FIJAS` de los dos módulos (y del test correspondiente) en
vez de repetir a mano la lista de columnas de `elecciones.csv` una tercera
vez -- mismo criterio D9 de no hardcodear lo que ya está declarado en otro
lado.
