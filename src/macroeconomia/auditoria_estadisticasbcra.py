"""Auditoría externa contra `estadisticasbcra.com`, una corrida manual (ver
`docs/plan_macroeconomia.md` §1 y §5, punto 5): para cada concepto marcado
`auditable_estadisticasbcra` en `catalogo_series.csv`, compara nuestro dato
crudo de datos.gob.ar (mismo id cacheado que usa `macroeconomia.series`)
contra el de estadisticasbcra.com, en el **mes más reciente que ambas
fuentes tengan en común** -- no en el mes más reciente de nuestra serie,
porque estadisticasbcra.com puede estar más atrasada (ver hallazgo en
`SISTEMATIZACION_VARIABLES_MACRO.md`).

No es parte del pipeline regular de `macroeconomia.series` -- esa fuente
requiere token (registro en `/api/registracion`) y tiene límite de 100
consultas/día, así que esto se corre a mano cuando hace falta reauditar,
no en cada regeneración del CSV. El token nunca se guarda en el repo: se
pasa por `--token` o por la variable de entorno `ESTADISTICASBCRA_TOKEN`.

Uso:
    ESTADISTICASBCRA_TOKEN=... PYTHONPATH=src python -m macroeconomia.auditoria_estadisticasbcra
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests

from constantes import MACRO_CACHE_DATOS_GOB_DIR, MACRO_CATALOGO_SERIES_PATH
from macroeconomia.series import ConceptoCatalogo, _parsear_puntos, cargar_catalogo

BASE_URL = "https://api.estadisticasbcra.com/"


@dataclass(frozen=True)
class ResultadoAuditoria:
    concepto: str
    endpoint: str
    anio_mes: str
    fecha_nuestra: str
    valor_nuestro: float
    fecha_bcra: str
    valor_bcra: float

    @property
    def diferencia_porcentual(self) -> float:
        if self.valor_bcra == 0:
            return float("inf") if self.valor_nuestro != 0 else 0.0
        return (self.valor_nuestro - self.valor_bcra) / self.valor_bcra * 100

    @property
    def coincide(self) -> bool:
        return abs(self.diferencia_porcentual) < 0.5  # tolerancia por redondeo entre fuentes


def _extraer_endpoint(auditable: str) -> str | None:
    """`"si (usd)"` -> `"usd"`; `"si (tasa_leliq aprox.)"` -> `"tasa_leliq"`; `"no"` -> `None`."""
    m = re.match(r"si \(([a-z_]+)", auditable)
    return m.group(1) if m else None


def cargar_conceptos_auditables(path: Path | str) -> list[tuple[ConceptoCatalogo, str]]:
    """`(concepto_catalogo, endpoint_estadisticasbcra)` para cada fila auditable."""
    import csv as _csv

    with Path(path).open(encoding="utf-8", newline="") as f:
        filas_crudas = list(_csv.DictReader(f))
    catalogo = cargar_catalogo(path)
    resultado = []
    for concepto, fila in zip(catalogo, filas_crudas):
        endpoint = _extraer_endpoint(fila["auditable_estadisticasbcra"])
        if endpoint:
            resultado.append((concepto, endpoint))
    return resultado


def cargar_puntos_propios(concepto: ConceptoCatalogo, cache_dir: Path | str) -> list[tuple[date, float]]:
    cache_path = Path(cache_dir) / f"{concepto.id_datos_gob}.json"
    crudo = json.loads(cache_path.read_text(encoding="utf-8"))
    return _parsear_puntos(crudo["data"])


def consultar_estadisticasbcra(endpoint: str, token: str, timeout: float = 30.0) -> list[tuple[date, float]]:
    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers={"Authorization": f"BEARER {token}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return sorted((date.fromisoformat(p["d"]), float(p["v"])) for p in response.json())


def _por_anio_mes(puntos: list[tuple[date, float]]) -> dict[str, tuple[date, float]]:
    """Último punto de cada año-mes (`"2024-08"` -> `(fecha, valor)`)."""
    resultado: dict[str, tuple[date, float]] = {}
    for fecha, valor in puntos:
        resultado[fecha.strftime("%Y-%m")] = (fecha, valor)
    return resultado


# Conceptos donde nuestra fuente guarda un ÍNDICE (nivel) y estadisticasbcra
# guarda directamente la variación % mensual -- no son comparables sin
# transformar antes: se recalcula la variación % mes contra mes anterior a
# partir de nuestro propio índice, y ESO es lo que se compara contra el
# valor de estadisticasbcra (que ya viene en %).
_CONCEPTOS_INDICE_A_VARIACION_MENSUAL = {"ipc_nacional"}


def comparar(
    concepto: ConceptoCatalogo, endpoint: str, puntos_propios: list[tuple[date, float]], puntos_bcra: list[tuple[date, float]]
) -> ResultadoAuditoria | None:
    """Compara en el año-mes más reciente que ambas series tengan en común."""
    propios_por_mes = _por_anio_mes(puntos_propios)
    bcra_por_mes = _por_anio_mes(puntos_bcra)
    meses_comunes = sorted(set(propios_por_mes) & set(bcra_por_mes), reverse=True)

    if concepto.concepto in _CONCEPTOS_INDICE_A_VARIACION_MENSUAL:
        # Solo sirven los meses donde también tengamos el mes anterior, para
        # poder calcular la variación.
        meses_ordenados = sorted(propios_por_mes)
        indice_mes_anterior = {
            meses_ordenados[i]: meses_ordenados[i - 1] for i in range(1, len(meses_ordenados))
        }
        meses_comunes = [m for m in meses_comunes if m in indice_mes_anterior]
        if not meses_comunes:
            return None
        mes = meses_comunes[0]
        fecha_n, valor_actual = propios_por_mes[mes]
        _, valor_anterior = propios_por_mes[indice_mes_anterior[mes]]
        valor_n = (valor_actual / valor_anterior - 1) * 100 if valor_anterior else float("nan")
        fecha_b, valor_b = bcra_por_mes[mes]
        return ResultadoAuditoria(
            f"{concepto.concepto} (variación % m/m, no el índice)", endpoint, mes, fecha_n.isoformat(), valor_n, fecha_b.isoformat(), valor_b
        )

    if not meses_comunes:
        return None
    mes = meses_comunes[0]
    fecha_n, valor_n = propios_por_mes[mes]
    fecha_b, valor_b = bcra_por_mes[mes]
    return ResultadoAuditoria(concepto.concepto, endpoint, mes, fecha_n.isoformat(), valor_n, fecha_b.isoformat(), valor_b)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalogo", default=MACRO_CATALOGO_SERIES_PATH)
    parser.add_argument("--cache-dir", default=MACRO_CACHE_DATOS_GOB_DIR)
    parser.add_argument("--token", default=os.environ.get("ESTADISTICASBCRA_TOKEN"))
    args = parser.parse_args()
    if not args.token:
        raise SystemExit("Falta token: pasar --token o setear ESTADISTICASBCRA_TOKEN")

    resultados: list[ResultadoAuditoria] = []
    for concepto, endpoint in cargar_conceptos_auditables(args.catalogo):
        puntos_propios = cargar_puntos_propios(concepto, args.cache_dir)
        try:
            puntos_bcra = consultar_estadisticasbcra(endpoint, args.token)
        except Exception as exc:
            print(f"{concepto.concepto} ({endpoint}): ERROR consultando estadisticasbcra.com -- {exc}")
            continue
        resultado = comparar(concepto, endpoint, puntos_propios, puntos_bcra)
        if resultado is None:
            print(f"{concepto.concepto} ({endpoint}): sin ningún año-mes en común entre las dos fuentes")
            continue
        resultados.append(resultado)

    print(
        f"\n{'concepto':<32}{'endpoint':<24}{'año-mes':<10}"
        f"{'nuestro (fecha=valor)':<28}{'bcra (fecha=valor)':<28}{'dif %':>8}  resultado"
    )
    for r in resultados:
        nuestro_str = f"{r.fecha_nuestra}={r.valor_nuestro:.4f}"
        bcra_str = f"{r.fecha_bcra}={r.valor_bcra:.4f}"
        estado = "coincide" if r.coincide else "DIFIERE"
        print(f"{r.concepto:<32}{r.endpoint:<24}{r.anio_mes:<10}{nuestro_str:<28}{bcra_str:<28}{r.diferencia_porcentual:>+7.2f}%  {estado}")


if __name__ == "__main__":
    main()
