"""Tests de `cobertura_clasificacion.py`: lectura de votos/clasificación,
cálculo de cobertura, resumen por (año, nivel) y top-N -- lógica pura,
sin red ni archivos reales. `main()`/`generar_reporte_markdown` (formato
de texto) sin test, mismo criterio que el resto de `src/` (ver CLAUDE.md)."""
import csv

from auditoria_interna.cobertura_clasificacion import (
    calcular_cobertura,
    calcular_delta,
    calcular_totales_globales,
    leer_clasificacion,
    leer_ultima_entrada_log,
    leer_votos_reales,
    registrar_corrida,
    resumen_por_anio_nivel,
    top_n_partidos_a_clasificar,
)


def _escribir_eleccion(tmp_path, nombre, cargo, filas):
    path = tmp_path / nombre
    contenido = [f"# Total de votos, elección general -- La Plata, x (cargo: {cargo})"]
    contenido.append("id_agrupacion,agrupacion,votos,votos_porcentaje,campo_ideologico,filiacion_politica,vparty_economico,vparty_progresismo,vparty_populismo")
    contenido.extend(filas)
    path.write_text("\n".join(contenido) + "\n", encoding="utf-8")
    return path


def _escribir_clasificacion(tmp_path, filas):
    path = tmp_path / "clasificacion.csv"
    columnas = ["anio", "agrupacion", "nivel", "campo_ideologico", "filiacion_politica", "vparty_economico", "vparty_progresismo", "vparty_populismo"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)
    return path


def test_leer_votos_reales_excluye_blanco_nulo_votantes(tmp_path):
    _escribir_eleccion(
        tmp_path, "2011_nacional.csv", "presidente",
        [
            "01,PARTIDO A,1000,50.0,,,,,",
            "BLANCO,BLANCO,100,5.0,,,,,",
            "NULO,NULO,50,2.5,,,,,",
            "VOTANTES_HABILITADOS,VOTANTES_HABILITADOS,300000,100.0,,,,,",
        ],
    )
    votos = leer_votos_reales(tmp_path)
    assert len(votos) == 1
    assert votos[0] == {"anio": 2011, "nivel": "presidente", "agrupacion": "PARTIDO A", "votos": 1000}


def test_leer_votos_reales_normaliza_gobernador_a_gobernacion(tmp_path):
    _escribir_eleccion(tmp_path, "2003_provincial.csv", "gobernador", ["01,PARTIDO A,500,10.0,,,,,"])
    votos = leer_votos_reales(tmp_path)
    assert votos[0]["nivel"] == "gobernacion"


def _fila_clasif(anio, nivel, agrupacion, campo_ideologico="", filiacion_politica="", vparty_economico=""):
    return {
        "anio": anio, "nivel": nivel, "agrupacion": agrupacion,
        "campo_ideologico": campo_ideologico, "filiacion_politica": filiacion_politica,
        "vparty_economico": vparty_economico, "vparty_progresismo": "", "vparty_populismo": "",
    }


def test_leer_clasificacion_indexa_por_anio_nivel_agrupacion(tmp_path):
    path = _escribir_clasificacion(tmp_path, [_fila_clasif("2011", "presidente", "PARTIDO A", "3", "peronistas", "0.1")])
    clasificacion = leer_clasificacion(path)
    assert ("2011", "presidente", "PARTIDO A") in clasificacion
    assert clasificacion[("2011", "presidente", "PARTIDO A")]["campo_ideologico"] == "3"


def test_calcular_cobertura_marca_dimensiones_faltantes():
    votos = [{"anio": 2011, "nivel": "presidente", "agrupacion": "PARTIDO A", "votos": 1000}]
    clasificacion = {("2011", "presidente", "PARTIDO A"): _fila_clasif("2011", "presidente", "PARTIDO A", "3", "peronistas", "")}
    filas = calcular_cobertura(votos, clasificacion)
    assert filas[0]["faltantes"] == ["vparty_economico"]


def test_calcular_cobertura_sin_fila_de_clasificacion_marca_todo_faltante():
    votos = [{"anio": 2001, "nivel": "municipal", "agrupacion": "PARTIDO DESCONOCIDO", "votos": 500}]
    filas = calcular_cobertura(votos, {})
    assert set(filas[0]["faltantes"]) == {"campo_ideologico", "filiacion_politica", "vparty_economico"}


def test_calcular_cobertura_totalmente_clasificado_no_tiene_faltantes():
    votos = [{"anio": 2011, "nivel": "presidente", "agrupacion": "PARTIDO A", "votos": 1000}]
    clasificacion = {("2011", "presidente", "PARTIDO A"): _fila_clasif("2011", "presidente", "PARTIDO A", "3", "peronistas", "0.5")}
    filas = calcular_cobertura(votos, clasificacion)
    assert filas[0]["faltantes"] == []


def test_resumen_por_anio_nivel_suma_votos_faltantes():
    filas = [
        {"anio": 2011, "nivel": "presidente", "agrupacion": "A", "votos": 1000, "faltantes": ["campo_ideologico"]},
        {"anio": 2011, "nivel": "presidente", "agrupacion": "B", "votos": 500, "faltantes": []},
        {"anio": 2013, "nivel": "nacional", "agrupacion": "C", "votos": 200, "faltantes": ["vparty_economico"]},
    ]
    resumen = resumen_por_anio_nivel(filas)
    fila_2011 = next(r for r in resumen if r["anio"] == 2011)
    assert fila_2011["total_votos"] == 1500
    assert fila_2011["campo_ideologico"] == 1000
    assert fila_2011["filiacion_politica"] == 0
    assert fila_2011["vparty_economico"] == 0


def test_resumen_por_anio_nivel_ordenado_anio_nivel():
    filas = [
        {"anio": 2013, "nivel": "provincial", "agrupacion": "A", "votos": 1, "faltantes": []},
        {"anio": 2011, "nivel": "presidente", "agrupacion": "B", "votos": 1, "faltantes": []},
        {"anio": 2011, "nivel": "gobernacion", "agrupacion": "C", "votos": 1, "faltantes": []},
    ]
    resumen = resumen_por_anio_nivel(filas)
    claves = [(r["anio"], r["nivel"]) for r in resumen]
    assert claves == [(2011, "gobernacion"), (2011, "presidente"), (2013, "provincial")]


def test_top_n_partidos_a_clasificar_ordena_por_votos_desc():
    filas = [
        {"anio": 2011, "nivel": "presidente", "agrupacion": "CHICO", "votos": 100, "faltantes": ["campo_ideologico"]},
        {"anio": 2011, "nivel": "presidente", "agrupacion": "GRANDE", "votos": 9000, "faltantes": ["vparty_economico"]},
        {"anio": 2013, "nivel": "nacional", "agrupacion": "CLASIFICADO", "votos": 5000, "faltantes": []},
    ]
    top = top_n_partidos_a_clasificar(filas, n=5)
    assert [r["agrupacion"] for r in top] == ["GRANDE", "CHICO"]
    assert "CLASIFICADO" not in [r["agrupacion"] for r in top]


def test_top_n_partidos_a_clasificar_suma_apariciones_del_mismo_partido():
    filas = [
        {"anio": 2011, "nivel": "presidente", "agrupacion": "PARTIDO A", "votos": 100, "faltantes": ["campo_ideologico"]},
        {"anio": 2013, "nivel": "nacional", "agrupacion": "PARTIDO A", "votos": 200, "faltantes": ["campo_ideologico", "filiacion_politica"]},
    ]
    top = top_n_partidos_a_clasificar(filas, n=5)
    assert len(top) == 1
    assert top[0]["votos_sin_clasificar"] == 300
    assert top[0]["apariciones_sin_clasificar"] == 2
    assert top[0]["faltantes"] == {"campo_ideologico", "filiacion_politica"}
    assert top[0]["anios"] == [2011, 2013]


def test_top_n_partidos_a_clasificar_anios_ordenados_sin_repetir():
    filas = [
        {"anio": 2015, "nivel": "provincial", "agrupacion": "PARTIDO A", "votos": 50, "faltantes": ["vparty_economico"]},
        {"anio": 2011, "nivel": "presidente", "agrupacion": "PARTIDO A", "votos": 100, "faltantes": ["campo_ideologico"]},
        {"anio": 2011, "nivel": "gobernacion", "agrupacion": "PARTIDO A", "votos": 10, "faltantes": ["campo_ideologico"]},
    ]
    top = top_n_partidos_a_clasificar(filas, n=5)
    assert top[0]["anios"] == [2011, 2015]


def test_resumen_por_anio_nivel_calcula_porcentajes():
    filas = [
        {"anio": 2011, "nivel": "presidente", "agrupacion": "A", "votos": 750, "faltantes": ["campo_ideologico"]},
        {"anio": 2011, "nivel": "presidente", "agrupacion": "B", "votos": 250, "faltantes": []},
    ]
    resumen = resumen_por_anio_nivel(filas)
    fila = resumen[0]
    assert fila["campo_ideologico_pct"] == 75.0
    assert fila["filiacion_politica_pct"] == 0.0
    assert fila["vparty_economico_pct"] == 0.0


def test_resumen_por_anio_nivel_porcentaje_cero_si_no_hay_votos():
    resumen = resumen_por_anio_nivel([])
    assert resumen == []


def test_calcular_totales_globales_suma_todos_los_anio_nivel():
    resumen = [
        {"anio": 2011, "nivel": "presidente", "total_votos": 1000, "campo_ideologico": 100, "filiacion_politica": 50, "vparty_economico": 200},
        {"anio": 2013, "nivel": "nacional", "total_votos": 500, "campo_ideologico": 0, "filiacion_politica": 0, "vparty_economico": 100},
    ]
    totales = calcular_totales_globales(resumen)
    assert totales == {"total_votos": 1500, "campo_ideologico": 100, "filiacion_politica": 50, "vparty_economico": 300}


def test_leer_ultima_entrada_log_none_si_no_existe(tmp_path):
    assert leer_ultima_entrada_log(tmp_path / "no_existe.csv") is None


def test_registrar_corrida_crea_encabezado_en_primera_corrida(tmp_path):
    log_path = tmp_path / "log.csv"
    totales = {"total_votos": 1000, "campo_ideologico": 100, "filiacion_politica": 50, "vparty_economico": 200}
    delta = {"total_votos": 0, "campo_ideologico": 0, "filiacion_politica": 0, "vparty_economico": 0}
    registrar_corrida(log_path, "2026-01-01T00:00:00+00:00", totales, delta)
    ultima = leer_ultima_entrada_log(log_path)
    assert ultima["timestamp"] == "2026-01-01T00:00:00+00:00"
    assert ultima["total_votos"] == "1000"
    assert ultima["sin_campo_ideologico"] == "100"


def test_registrar_corrida_se_acumula_no_sobreescribe(tmp_path):
    log_path = tmp_path / "log.csv"
    totales = {"total_votos": 1000, "campo_ideologico": 100, "filiacion_politica": 50, "vparty_economico": 200}
    delta = {"total_votos": 0, "campo_ideologico": 0, "filiacion_politica": 0, "vparty_economico": 0}
    registrar_corrida(log_path, "t1", totales, delta)
    registrar_corrida(log_path, "t2", totales, delta)
    with log_path.open(encoding="utf-8") as f:
        filas = f.read().strip().split("\n")
    assert len(filas) == 3  # encabezado + 2 corridas
    assert leer_ultima_entrada_log(log_path)["timestamp"] == "t2"


def test_calcular_delta_sin_corrida_anterior_es_cero():
    totales = {"total_votos": 1000, "campo_ideologico": 100, "filiacion_politica": 50, "vparty_economico": 200}
    delta = calcular_delta(totales, None)
    assert delta == {"total_votos": 0, "campo_ideologico": 0, "filiacion_politica": 0, "vparty_economico": 0}


def test_calcular_delta_contra_entrada_previa():
    totales = {"total_votos": 1200, "campo_ideologico": 80, "filiacion_politica": 50, "vparty_economico": 250}
    anterior = {"total_votos": "1000", "sin_campo_ideologico": "100", "sin_filiacion_politica": "50", "sin_vparty_economico": "200"}
    delta = calcular_delta(totales, anterior)
    assert delta == {"total_votos": 200, "campo_ideologico": -20, "filiacion_politica": 0, "vparty_economico": 50}


def test_top_n_partidos_a_clasificar_respeta_limite_n():
    filas = [
        {"anio": 2011, "nivel": "presidente", "agrupacion": f"PARTIDO {i}", "votos": i, "faltantes": ["campo_ideologico"]}
        for i in range(1, 11)
    ]
    top = top_n_partidos_a_clasificar(filas, n=3)
    assert len(top) == 3
    assert [r["agrupacion"] for r in top] == ["PARTIDO 10", "PARTIDO 9", "PARTIDO 8"]
