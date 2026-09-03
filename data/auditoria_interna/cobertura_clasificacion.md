# Cobertura de clasificación de agrupaciones

Votos reales de `data/tfi_data/elecciones/` (2001-2025) cruzados contra `data/agrupaciones/clasificacion_ideologica_agrupaciones.csv`. Generado por `PYTHONPATH=src python -m auditoria_interna.cobertura_clasificacion` -- este reporte no versiona historial, se sobreescribe en cada corrida; el historial de corridas (totales + variación, sin desglose) vive en `cobertura_clasificacion_log.csv`, que sí se acumula.

**Última corrida**: 2026-09-03T22:51:27+00:00 -- 12.409.698 votos totales (+0 vs. corrida anterior), 85.930 sin campo ideológico (-12.513), 85.930 sin filiación política (-12.513), 121.063 sin V-Party (-17.024).

## Votos sin clasificar por año y nivel

| Año | Nivel | Votos totales | Sin campo ideológico | % | Sin filiación política | % | Sin V-Party | % |
|---|---|---|---|---|---|---|---|---|
| 2001 | municipal | 230.541 | 11.760 | 5.1% | 11.760 | 5.1% | 13.304 | 5.8% |
| 2001 | provincial | 229.230 | 11.339 | 4.9% | 11.339 | 4.9% | 12.826 | 5.6% |
| 2003 | gobernacion | 250.900 | 5.935 | 2.4% | 5.935 | 2.4% | 8.813 | 3.5% |
| 2003 | intendente | 277.168 | 10.082 | 3.6% | 10.082 | 3.6% | 10.975 | 4.0% |
| 2005 | municipal | 295.146 | 11.927 | 4.0% | 11.927 | 4.0% | 14.368 | 4.9% |
| 2005 | provincial | 295.971 | 9.549 | 3.2% | 9.549 | 3.2% | 11.202 | 3.8% |
| 2007 | gobernacion | 318.387 | 3.278 | 1.0% | 3.278 | 1.0% | 3.278 | 1.0% |
| 2007 | intendente | 321.163 | 2.856 | 0.9% | 2.856 | 0.9% | 2.856 | 0.9% |
| 2009 | municipal | 324.824 | 5.955 | 1.8% | 5.955 | 1.8% | 8.551 | 2.6% |
| 2009 | provincial | 327.372 | 4.668 | 1.4% | 4.668 | 1.4% | 7.049 | 2.2% |
| 2011 | gobernacion | 330.831 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2011 | intendente | 352.284 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2011 | presidente | 354.798 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2013 | municipal | 393.422 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2013 | nacional | 380.688 | 0 | 0.0% | 0 | 0.0% | 4.698 | 1.2% |
| 2013 | provincial | 384.591 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2015 | gobernacion | 395.874 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2015 | intendente | 392.483 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2015 | presidente | 398.598 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2017 | municipal | 419.518 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2017 | nacional | 401.476 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2017 | provincial | 419.947 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2019 | gobernacion | 426.157 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2019 | intendente | 421.486 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2019 | presidente | 418.164 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2021 | municipal | 397.277 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2021 | nacional | 390.422 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2021 | provincial | 397.358 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2023 | gobernacion | 428.598 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2023 | intendente | 423.261 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2023 | presidente | 428.907 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% |
| 2025 | municipal | 395.040 | 3.962 | 1.0% | 3.962 | 1.0% | 7.254 | 1.8% |
| 2025 | nacional | 393.871 | 0 | 0.0% | 0 | 0.0% | 4.653 | 1.2% |
| 2025 | provincial | 393.945 | 4.619 | 1.2% | 4.619 | 1.2% | 11.236 | 2.9% |

## Top 5 agrupaciones a clasificar

Ordenadas por votos totales afectados por al menos una clasificación faltante, sumando todas sus apariciones (año, nivel).

| # | Agrupación | Votos sin clasificar | Apariciones sin clasificar | Año(s) | Falta |
|---|---|---|---|---|---|
| 1 | FRENTE VECINALISTA PROVINCIAL | 10.842 | 2 | 2001 | campo ideológico, filiación política, V-Party |
| 2 | ALIANZA POTENCIA | 9.575 | 3 | 2025 | V-Party |
| 3 | CONFEDERACION VECINAL | 9.429 | 2 | 2005 | campo ideológico, filiación política, V-Party |
| 4 | PARTIDO PROYECTO POPULAR | 6.340 | 2 | 2005 | campo ideológico, filiación política, V-Party |
| 5 | VAMOS | 5.195 | 2 | 2007 | campo ideológico, filiación política, V-Party |
