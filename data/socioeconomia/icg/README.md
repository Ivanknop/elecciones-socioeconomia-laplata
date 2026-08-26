# ICG (Índice de Confianza en el Gobierno) — UTDT, Escuela de Gobierno

## Qué es este archivo

`Base_histórica_2001-presente-ICG.dta` es el microdato histórico del
Índice de Confianza en el Gobierno que produce la Escuela de Gobierno de
la Universidad Torcuato Di Tella (UTDT) — encuesta telefónica mensual,
~46 ciudades del país, `ICG` en escala 0-5 más variables demográficas
(`sexo`/`edad`/`edu`) y de ponderación (`ponderacion_UTDT`).

**Ni el `.dta` ni el libro de códigos se distribuyen en este repo.** La
UTDT lo entrega bajo pedido (no hay endpoint público, a diferencia de
EPH/BCRA/datos.gob.ar, que sí tienen cliente propio en `src/`) — para
conseguirlo, contactar a la Escuela de Gobierno UTDT. `.gitignore` excluye
explícitamente `data/socioeconomia/icg/*.dta` y `*.pdf`.

## Cómo colocarlo

Para que `PYTHONPATH=src python -m socioeconomia.icg_exportar_csv`
(constante `ICG_RAW_PATH` en `src/constantes.py`) lo encuentre, debe
llamarse exactamente:

```
data/socioeconomia/icg/Base_histórica_2001-presente-ICG.dta
```

(nombre original con guiones bajos en vez de espacios — si el archivo
que te entregan trae espacios, renombralo antes de colocarlo.)

## Libro de códigos

`Codebook_ICG.pdf` (edición 2023, UTDT) documenta las 33 columnas del
`.dta` — colocarlo también en esta carpeta (mismo criterio que el `.dta`,
tampoco se trackea) para tenerlo a mano localmente. **Ojo**: dice que la
cobertura llega hasta oct-2022, pero el `.dta` real que se usó para
construir el pipeline llegaba hasta 2026-08 — el PDF quedó desactualizado
respecto de las entregas más recientes de la UTDT; la cobertura real la
determina el `.dta` que tengas acá, no el PDF. Detalle de decisiones
metodológicas (asimetría de resolución país/La Plata, ausencia de
variable de ingreso, etc.) en `data/socioeconomia/ICG.md`, no acá — este
README es solo sobre el insumo crudo.
