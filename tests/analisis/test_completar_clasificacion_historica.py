"""Tests de `completar_clasificacion_historica.py`: parseo de
`<año>_<nivel>.csv`, extracción del rango histórico y fusión append-only
-- lógica pura, sin red ni archivos reales. `main()` sin test, mismo
criterio que el resto de `src/analisis/` (ver CLAUDE.md)."""
from analisis.completar_clasificacion_historica import (
    _cargo_de_archivo,
    extraer_clasificacion_historica,
    fusionar_clasificacion,
    leer_clasificacion_de_eleccion,
)


def _escribir_eleccion(tmp_path, nombre, cargo, filas):
    path = tmp_path / nombre
    contenido = [f"# Total de votos, elección general -- La Plata, x (cargo: {cargo})"]
    contenido.append("id_agrupacion,agrupacion,votos,votos_porcentaje,campo_ideologico,filiacion_politica,vparty_economico,vparty_progresismo,vparty_populismo")
    contenido.extend(filas)
    path.write_text("\n".join(contenido) + "\n", encoding="utf-8")
    return path


def test_cargo_de_archivo_extrae_cargo_entre_parentesis(tmp_path):
    path = _escribir_eleccion(tmp_path, "2003_provincial.csv", "gobernador", [])
    assert _cargo_de_archivo(path) == "gobernador"


def test_leer_clasificacion_de_eleccion_excluye_blanco_nulo_votantes(tmp_path):
    path = _escribir_eleccion(
        tmp_path, "2001_municipal.csv", "municipal",
        [
            "0002,PARTIDO JUSTICIALISTA,73601,23.3,3,peronistas,0.544,0.05,0.503",
            "BLANCO,BLANCO,100,1.0,,,,,",
            "NULO,NULO,50,0.5,,,,,",
            "VOTANTES_HABILITADOS,VOTANTES_HABILITADOS,300000,100.0,,,,,",
        ],
    )
    filas = leer_clasificacion_de_eleccion(path)
    assert [f["agrupacion"] for f in filas] == ["PARTIDO JUSTICIALISTA"]


def test_leer_clasificacion_de_eleccion_normaliza_gobernador_a_gobernacion(tmp_path):
    path = _escribir_eleccion(
        tmp_path, "2003_provincial.csv", "gobernador",
        ["0002,PARTIDO JUSTICIALISTA,98136,31.8,3,peronistas,-0.416,0.268,0.658"],
    )
    filas = leer_clasificacion_de_eleccion(path)
    assert filas[0]["anio"] == "2003"
    assert filas[0]["nivel"] == "gobernacion"
    assert filas[0]["campo_ideologico"] == "3"


def test_leer_clasificacion_de_eleccion_conserva_campo_ideologico_vacio(tmp_path):
    path = _escribir_eleccion(
        tmp_path, "2003_provincial.csv", "provincial",
        ["0001,PARTIDO SIN CLASIFICAR,1348,0.4,,,,,"],
    )
    filas = leer_clasificacion_de_eleccion(path)
    assert filas[0]["campo_ideologico"] == ""


def test_extraer_clasificacion_historica_respeta_anio_max(tmp_path):
    _escribir_eleccion(tmp_path, "2009_nacional.csv", "nacional", ["01,PARTIDO A,10,1.0,3,peronistas,,,"])
    _escribir_eleccion(tmp_path, "2011_nacional.csv", "presidente", ["01,PARTIDO A,10,1.0,3,peronistas,,,"])
    filas = extraer_clasificacion_historica(tmp_path, anio_max=2009)
    assert {f["anio"] for f in filas} == {"2009"}


def test_extraer_clasificacion_historica_junta_varios_archivos(tmp_path):
    _escribir_eleccion(tmp_path, "2001_municipal.csv", "municipal", ["01,PARTIDO A,10,1.0,3,peronistas,,,"])
    _escribir_eleccion(tmp_path, "2001_nacional.csv", "nacional", ["01,PARTIDO B,10,1.0,4,liberales,,,"])
    filas = extraer_clasificacion_historica(tmp_path, anio_max=2009)
    assert len(filas) == 2
    assert {f["nivel"] for f in filas} == {"municipal", "nacional"}


def _fila(anio, nivel, agrupacion, campo_ideologico="3", filiacion="peronistas"):
    return {
        "anio": anio, "nivel": nivel, "agrupacion": agrupacion,
        "campo_ideologico": campo_ideologico, "filiacion_politica": filiacion,
        "vparty_economico": "", "vparty_progresismo": "", "vparty_populismo": "",
    }


def test_fusionar_clasificacion_agrega_filas_nuevas():
    existentes = [_fila("2011", "presidente", "PARTIDO A")]
    nuevas = [_fila("2003", "presidente", "PARTIDO B")]
    combinado = fusionar_clasificacion(existentes, nuevas)
    assert len(combinado) == 2
    assert combinado[0]["anio"] == "2003"  # ordenado por año primero


def test_fusionar_clasificacion_nunca_sobreescribe_fila_existente():
    existente = _fila("2011", "presidente", "PARTIDO A", campo_ideologico="3", filiacion="peronistas")
    nueva_misma_clave = _fila("2011", "presidente", "PARTIDO A", campo_ideologico="9", filiacion="otra")
    combinado = fusionar_clasificacion([existente], [nueva_misma_clave])
    assert len(combinado) == 1
    assert combinado[0]["campo_ideologico"] == "3"
    assert combinado[0]["filiacion_politica"] == "peronistas"


def test_fusionar_clasificacion_es_idempotente():
    existentes = [_fila("2011", "presidente", "PARTIDO A")]
    nuevas = [_fila("2003", "presidente", "PARTIDO B")]
    primera = fusionar_clasificacion(existentes, nuevas)
    segunda = fusionar_clasificacion(primera, nuevas)
    assert segunda == primera


def test_fusionar_clasificacion_orden_anio_nivel_agrupacion():
    existentes = []
    nuevas = [
        _fila("2003", "provincial", "PARTIDO Z"),
        _fila("2003", "municipal", "PARTIDO A"),
        _fila("2001", "nacional", "PARTIDO M"),
    ]
    combinado = fusionar_clasificacion(existentes, nuevas)
    orden = [(f["anio"], f["nivel"], f["agrupacion"]) for f in combinado]
    assert orden == sorted(orden, key=lambda t: (int(t[0]), t[1], t[2]))
