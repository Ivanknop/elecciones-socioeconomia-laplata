"""Tests de `vparty_distribucion_tfi.py`: carga de un CSV de elección,
descubrimiento de combos y límites de eje -- lógica pura, sin matplotlib."""
from analisis.vparty_distribucion_tfi import cargar_eleccion, combos_disponibles, limites_globales

CABECERA = "# Total de votos, elección general -- La Plata, municipal 2023 (cargo: intendente)\n"
COLUMNAS = "id_agrupacion,agrupacion,votos,votos_porcentaje,campo_ideologico,filiacion_politica,vparty_economico,vparty_progresismo,vparty_populismo\n"


def _escribir_eleccion(path, filas):
    with open(path, "w", encoding="utf-8") as f:
        f.write(CABECERA)
        f.write(COLUMNAS)
        f.writelines(filas)


def test_cargar_eleccion_descarta_blanco_nulo_y_sin_cobertura(tmp_path):
    path = tmp_path / "2023_municipal.csv"
    _escribir_eleccion(path, [
        "0001,PARTIDO A,100,50.0,3,peronistas,-1.0,1.0,0.5\n",
        "0002,PARTIDO SIN VPARTY,50,25.0,4,otros,,,\n",
        "BLANCO,BLANCO,30,15.0,,,,,\n",
        "NULO,NULO,20,10.0,,,,,\n",
    ])
    df = cargar_eleccion(path)
    assert list(df["agrupacion"]) == ["PARTIDO A"]
    assert df.iloc[0]["economico"] == -1.0
    assert df.iloc[0]["progresismo"] == 1.0
    assert df.iloc[0]["populismo"] == 0.5


def test_combos_disponibles_parsea_anio_y_nivel(tmp_path):
    _escribir_eleccion(tmp_path / "2023_municipal.csv", ["0001,PARTIDO A,1,1.0,3,peronistas,-1.0,1.0,0.5\n"])
    _escribir_eleccion(tmp_path / "2019_provincial.csv", ["0001,PARTIDO A,1,1.0,3,peronistas,-1.0,1.0,0.5\n"])
    (tmp_path / "notas.md").write_text("no es un csv de elección", encoding="utf-8")

    combos = combos_disponibles(tmp_path)

    assert [(a, n) for a, n, _ in combos] == [(2019, "provincial"), (2023, "municipal")]


def test_limites_globales_simetricos_respecto_de_cero(tmp_path):
    path = tmp_path / "2023_municipal.csv"
    _escribir_eleccion(path, [
        "0001,PARTIDO A,100,50.0,3,peronistas,-2.0,1.0,0.5\n",
        "0002,PARTIDO B,100,50.0,4,liberales,1.0,-3.0,0.2\n",
    ])
    df = cargar_eleccion(path)

    xlim, ylim = limites_globales([df])

    assert xlim == (-2.6, 2.6)
    assert ylim == (-3.4, 3.4)


def test_limites_globales_sin_datos_devuelve_rango_default():
    assert limites_globales([]) == ((-1.0, 1.0), (-1.0, 1.0))
