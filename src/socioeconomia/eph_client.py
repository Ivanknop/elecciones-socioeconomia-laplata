"""Cliente de descarga+caché de microdatos trimestrales de la EPH (INDEC).

## URLs de descarga

Desde el 2do trimestre de 2017 en adelante, INDEC publica los zips con un
patrón regular: `EPH_usu_<trimestre>_Trim_<año>_txt.zip`. Antes de eso usó
nombres irregulares con el trimestre en palabra ("1er_Trim", "2doTrim", sin
convención fija de guión bajo) — `_URLS_IRREGULARES` tiene los que se
confirmaron navegando en esta sesión (2016 T2-T4, 2017 T1).

## 2011-2015: microdatos históricos vía Wayback Machine

INDEC dejó de servir en su propio sitio los trimestres 2011-2015 (el dominio
`www.indec.gov.ar` que los alojaba ya ni resuelve). Se encontraron y
confirmaron en el archivo de Internet (`web.archive.org`), capturados el
2017-10-18, con el nombre `t<trimestre><año 2 dígitos>_dbf.<zip|rar>` (ej.
`t111_dbf.zip` = 1er trimestre de 2011) — un esquema de nombres previo al
`EPH_usu_...` actual, en formato **DBF** (no txt/csv). `_WAYBACK_DBF` tiene
el timestamp de cada trimestre confirmado; `descargar_trimestre_historico` +
`leer_base_historica` los descargan/leen. La extensión no sigue una regla
por año (`_EXTENSION_HISTORICA`): 2011-2013 y el caso puntual de 2014 T2
están en `.zip`; el resto de 2014-2015 está en `.rar` — hace falta el
binario `unar` instalado en el sistema (`apt-get install unar`; no es un
paquete de pip) para extraerlos.

Dentro de estos DBF, la base `Hogar` **no tiene columna `PONDIH`** (se
llama `PONDERA`, igual que en la base individual) — `agregados_gran_la_plata`
ya contempla esto.

Con esto, `data/socioeconomia/eph_gran_la_plata.csv` cubre 2011-2025 casi
completo (57 de 60 trimestres) en un único CSV.

## Huecos conocidos en la serie (no son un bug de este cliente)

- 2015 T3, 2015 T4, 2016 T1: INDEC no publicó la EPH ("emergencia
  estadística") — confirmado además porque no existen `t315`/`t415` en el
  archivo histórico (sí existen `t115`/`t215`, 2015 T1/T2). Son los únicos
  tres trimestres 2011-2025 que faltan en `eph_gran_la_plata.csv`.
- 2007 T3: INDEC no relevó Gran La Plata ese trimestre (no afecta el rango
  2011-2025 de este proyecto, se deja documentado igual).
- 2007-2015: INDEC advierte que esas series deben "considerarse con
  reservas".

Fuente de los tres avisos:
`indec.gob.ar/ftp/cuadros/sociedad/anexo_informe_eph_23_08_16.pdf`.
"""
from __future__ import annotations

import subprocess
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import requests
from dbfread import DBF

AGLOMERADO_GRAN_LA_PLATA = 2

_URL_BASE = "https://www.indec.gob.ar/ftp/cuadros/menusuperior/eph/"
_WAYBACK_URL_BASE = "http://www.indec.gob.ar/ftp/cuadros/menusuperior/eph/"

_URLS_IRREGULARES = {
    (2016, 2): "EPH_usu_2doTrim_2016_txt.zip",
    (2016, 3): "EPH_usu_3erTrim_2016_txt.zip",
    (2016, 4): "EPH_usu_4toTrim_2016_txt.zip",
    (2017, 1): "EPH_usu_1er_trim_2017_txt.zip",  # "trim" en minúscula -- "Trim" (mayúscula) da 404
}

# timestamp de wayback machine (todos capturados 2017-10-18) por (año, trimestre),
# para los .dbf de 2011-2015 -- ver docstring del módulo.
_WAYBACK_DBF = {
    (2011, 1): "20171018105514",
    (2011, 2): "20171018105001",
    (2011, 3): "20171018152650",
    (2011, 4): "20171018160408",
    (2012, 1): "20171018123400",
    (2012, 2): "20171018141654",
    (2012, 3): "20171018131133",
    (2012, 4): "20171018102400",
    (2013, 1): "20171018130429",
    (2013, 2): "20171018134505",
    (2013, 3): "20171018115205",
    (2013, 4): "20171018105846",
    (2014, 1): "20171018104417",
    (2014, 2): "20171018135407",
    (2014, 3): "20171018102630",
    (2014, 4): "20171018131344",
    (2015, 1): "20171018094820",
    (2015, 2): "20171018112910",
}

TRIMESTRES_NO_PUBLICADOS = {(2015, 3), (2015, 4), (2016, 1), (2007, 3)}

# extensión real del archivo dbf capturado en Wayback Machine -- no sigue una
# regla por año: 2014 T2 quedó en .zip mientras T1/T3/T4 del mismo año están
# en .rar (confirmado contra el listado real de archive.org, no una regla inferida).
_EXTENSION_HISTORICA = {
    (2014, 1): "rar",
    (2014, 2): "zip",
    (2014, 3): "rar",
    (2014, 4): "rar",
    (2015, 1): "rar",
    (2015, 2): "rar",
}


class TrimestreNoPublicado(Exception):
    """INDEC no publicó microdatos para este (año, trimestre) — no es un error de descarga."""


class UrlDesconocida(Exception):
    """No hay un patrón de URL confirmado para este (año, trimestre); pasar `url` explícito."""


def _nombre_archivo(anio: int, trimestre: int) -> str:
    if (anio, trimestre) in _URLS_IRREGULARES:
        return _URLS_IRREGULARES[(anio, trimestre)]
    if anio > 2017 or (anio == 2017 and trimestre >= 2):
        return f"EPH_usu_{trimestre}_Trim_{anio}_txt.zip"
    raise UrlDesconocida(
        f"No hay un patrón de URL confirmado para {anio} T{trimestre}. "
        "Pasar `url` explícito a `descargar_trimestre` (ver docstring del módulo)."
    )


def _nombre_archivo_historico(anio: int, trimestre: int) -> str:
    """Nombre del archivo DBF histórico 2011-2015 en Wayback Machine —
    `t<trimestre><año 2 dígitos>_dbf.<zip|rar>`. La extensión no sigue una
    regla por año (ver `_EXTENSION_HISTORICA`): todo 2011-2013 está en zip,
    2014-2015 es rar salvo la excepción confirmada de 2014 T2 (zip).
    """
    yy = anio % 100
    extension = _EXTENSION_HISTORICA.get((anio, trimestre), "zip" if anio <= 2013 else "rar")
    return f"t{trimestre}{yy:02d}_dbf.{extension}"


class EphClient:
    def __init__(
        self, cache_dir: Path | str = "data/socioeconomia/eph_cache", timeout: float = 60.0
    ):
        self.cache_dir = Path(cache_dir)
        self.session = requests.Session()
        self.timeout = timeout

    def descargar_trimestre(
        self, anio: int, trimestre: int, url: str | None = None, force_refresh: bool = False
    ) -> Path:
        """Descarga (o lee de caché) el zip crudo de un trimestre y devuelve su path."""
        if (anio, trimestre) in TRIMESTRES_NO_PUBLICADOS:
            raise TrimestreNoPublicado(
                f"INDEC no publicó la EPH para {anio} T{trimestre} "
                "(emergencia estadística o no relevamiento — ver docstring del módulo)."
            )

        nombre = url.rsplit("/", 1)[-1] if url else _nombre_archivo(anio, trimestre)
        cache_path = self.cache_dir / str(anio) / f"trim{trimestre}" / nombre

        if cache_path.exists() and not force_refresh:
            return cache_path

        descarga_url = url or (_URL_BASE + nombre)
        response = self.session.get(descarga_url, timeout=self.timeout)
        response.raise_for_status()
        if response.headers.get("Content-Type", "").startswith("text/html"):
            raise UrlDesconocida(
                f"{descarga_url} no devolvió un zip (¿nombre de archivo incorrecto "
                "para este trimestre? INDEC devuelve una página HTML en vez de 404)."
            )

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(response.content)
        return cache_path

    def leer_base(self, zip_path: Path, tipo: str) -> pd.DataFrame:
        """Lee la base `individual` u `hogar` de un zip ya descargado. El
        archivo interno de la base individual no siempre se llama igual entre
        trimestres (ej. 4to trim. 2020 lo llamó "personas" en vez de "individual").
        """
        if tipo not in ("individual", "hogar"):
            raise ValueError("tipo debe ser 'individual' u 'hogar'")
        patrones = ("ind", "personas") if tipo == "individual" else ("hog",)
        with zipfile.ZipFile(zip_path) as z:
            nombres = [
                n
                for n in z.namelist()
                if any(p in n.lower() for p in patrones) and n.lower().endswith((".txt", ".csv"))
            ]
            if not nombres:
                raise FileNotFoundError(f"No se encontró la base '{tipo}' dentro de {zip_path}")
            with z.open(nombres[0]) as f:
                return pd.read_csv(f, sep=";", decimal=",", encoding="latin-1", low_memory=False)

    def descargar_trimestre_historico(
        self, anio: int, trimestre: int, force_refresh: bool = False
    ) -> Path:
        """Descarga (o lee de caché) el .zip/.rar con las bases DBF de un
        trimestre 2011-2015, vía Wayback Machine (ver docstring del módulo).
        """
        if (anio, trimestre) in TRIMESTRES_NO_PUBLICADOS:
            raise TrimestreNoPublicado(
                f"INDEC no publicó la EPH para {anio} T{trimestre} (ver docstring del módulo)."
            )
        timestamp = _WAYBACK_DBF.get((anio, trimestre))
        if timestamp is None:
            raise UrlDesconocida(
                f"No hay una captura de Wayback Machine confirmada para {anio} T{trimestre} "
                "(ver _WAYBACK_DBF en el docstring del módulo)."
            )
        nombre = _nombre_archivo_historico(anio, trimestre)
        cache_path = self.cache_dir / str(anio) / f"trim{trimestre}" / nombre

        if cache_path.exists() and not force_refresh:
            return cache_path

        url_wayback = f"http://web.archive.org/web/{timestamp}if_/{_WAYBACK_URL_BASE}{nombre}"
        response = self.session.get(url_wayback, timeout=self.timeout)
        response.raise_for_status()

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(response.content)
        return cache_path

    def leer_base_historica(self, archivo_path: Path, tipo: str) -> pd.DataFrame:
        """Lee la base `individual` u `hogar` de un .zip/.rar histórico
        (2011-2015, formato DBF).
        """
        if tipo not in ("individual", "hogar"):
            raise ValueError("tipo debe ser 'individual' u 'hogar'")
        patron = "individual" if tipo == "individual" else "hogar"
        with tempfile.TemporaryDirectory() as tmp:
            resultado = subprocess.run(
                ["unar", "-quiet", "-output-directory", tmp, str(archivo_path)],
                capture_output=True,
                text=True,
            )
            if resultado.returncode != 0:
                raise RuntimeError(
                    f"unar no pudo extraer {archivo_path} (¿está instalado? "
                    f"'apt-get install unar'): {resultado.stderr}"
                )
            candidatos = [p for p in Path(tmp).rglob("*.dbf") if patron in p.name.lower()]
            if not candidatos:
                raise FileNotFoundError(f"No se encontró la base '{tipo}' dentro de {archivo_path}")
            tabla = DBF(str(candidatos[0]), encoding="latin-1", char_decode_errors="ignore")
            return pd.DataFrame(iter(tabla))


_COLUMNAS_NUMERICAS_INDIVIDUAL = (
    "ESTADO", "CAT_OCUP", "INTENSI", "PP07H", "PP07G1", "PP07G2", "PP07G4",
    "CH04", "CH06", "CH08", "CH09", "CH10", "NIVEL_ED", "P21", "P47T", "PONDERA",
)
_COLUMNAS_NUMERICAS_HOGAR = ("IPCF", "IX_TOT", "II1", "IV7", "II7", "V5", "V15", "V17")


def _numerico(df: pd.DataFrame, columnas: tuple[str, ...]) -> pd.DataFrame:
    """Fuerza a numérico las columnas dadas que estén presentes -- el formato
    (separador decimal, celdas vacías) no es consistente entre trimestres
    publicados por INDEC, no hay que confiar en el dtype que infirió `read_csv`
    ni asumir que todas las columnas existen en todos los esquemas (2011-2015
    DBF vs. 2017+ txt difieren en columnas auxiliares, ver docstring del módulo).
    """
    df = df.copy()
    for columna in columnas:
        if columna in df.columns:
            df[columna] = pd.to_numeric(df[columna], errors="coerce")
    return df


def _peso(serie_condicion: pd.Series, pondera: pd.Series) -> float:
    return pondera[serie_condicion].sum()


def _tasa(numerador: float, denominador: float) -> float | None:
    return numerador / denominador if denominador else None


def _resolver_v5_dividida(hog: pd.DataFrame) -> pd.DataFrame:
    """Desde 2023 T4, INDEC dividió la pregunta V5 (ayuda social del
    gobierno) en `V5_01`/`V5_02`/`V5_03` -- reconstruye una columna `V5`
    (1=Sí/2=No) igual a "Sí" si cualquiera de las tres lo es, para no perder
    continuidad de la serie. No modifica nada si `V5` ya existe tal cual.
    """
    if "V5" in hog.columns:
        return hog
    columnas_v5 = [c for c in ("V5_01", "V5_02", "V5_03") if c in hog.columns]
    if not columnas_v5:
        return hog
    hog = hog.copy()
    partes = [pd.to_numeric(hog[c], errors="coerce") for c in columnas_v5]
    algun_si = pd.concat(partes, axis=1).eq(1).any(axis=1)
    hog["V5"] = algun_si.map({True: 1, False: 2})
    return hog


def _indicadores_laborales_core(ind: pd.DataFrame) -> dict:
    """Actividad/empleo/desocupación/informalidad/ingreso sobre un
    subconjunto de la base individual ya filtrado (aglomerado, y
    opcionalmente sexo/tramo etario). Población de referencia para
    actividad/empleo: `ESTADO` en {1,2,3} (ocupado/desocupado/inactivo,
    excluye menores de 10 y no-respuesta) -- la convención estándar de
    "población de 10 años y más" que usa la propia EPH.
    """
    poblacion = ind[ind["ESTADO"].isin([1, 2, 3])]
    pea = ind[ind["ESTADO"].isin([1, 2])]
    ocupados = ind[ind["ESTADO"] == 1]

    pob_total = poblacion["PONDERA"].sum()
    poblacion_pea = pea["PONDERA"].sum()
    poblacion_ocupada = ocupados["PONDERA"].sum()

    return {
        "tasa_actividad": _tasa(poblacion_pea, pob_total),
        "tasa_empleo": _tasa(poblacion_ocupada, pob_total),
        "tasa_desocupacion": _tasa(_peso(ind["ESTADO"] == 2, ind["PONDERA"]), poblacion_pea),
        # PP07H: 1 = le descuentan jubilación (formal), 2 = no le descuentan (informal).
        "tasa_informalidad": _tasa(
            _peso(ocupados["PP07H"] == 2, ocupados["PONDERA"]), poblacion_ocupada
        ),
        "ingreso_ocupacion_principal_medio": (
            (ocupados["P21"] * ocupados["PONDERA"]).sum() / poblacion_ocupada
            if poblacion_ocupada
            else None
        ),
    }


def agregados_gran_la_plata(individual: pd.DataFrame, hogar: pd.DataFrame) -> dict:
    """Indicadores trimestrales para el aglomerado Gran La Plata (todas las
    personas/hogares, sin desagregar) a partir de las bases individual y
    hogar ya filtradas o completas (se filtra acá por
    `AGLOMERADO_GRAN_LA_PLATA`). Todos los indicadores están ponderados por
    `PONDERA`/`PONDIH`, como exige la EPH al ser una encuesta muestral.
    En las bases históricas (2011-2015, DBF) la base hogar no tiene columna
    `PONDIH` -- usa `PONDERA` en su lugar.

    Además del núcleo laboral (`_indicadores_laborales_core`), agrega:
    composición ocupacional (`CAT_OCUP`), calidad del empleo asalariado
    (`PP07G1/G2/G4`: vacaciones pagas/aguinaldo/obra social), cobertura de
    salud (`CH08`), educación (`NIVEL_ED`, alfabetización, asistencia
    escolar), hacinamiento y tenencia de vivienda, estrategias de
    subsistencia del hogar (`V5`/`V15`/`V17`), e ingreso total individual
    (`P47T`) además de ingreso de la ocupación principal e IPCF. No incluye
    subocupación horaria (`INTENSI`) -- se descartó, ver comentario más abajo.
    """
    ind = individual[individual["AGLOMERADO"] == AGLOMERADO_GRAN_LA_PLATA].copy()
    hog = hogar[hogar["AGLOMERADO"] == AGLOMERADO_GRAN_LA_PLATA].copy()
    hog = _resolver_v5_dividida(hog)
    ind = _numerico(ind, _COLUMNAS_NUMERICAS_INDIVIDUAL)
    columna_pondih = "PONDIH" if "PONDIH" in hog.columns else "PONDERA"
    hog = _numerico(hog, _COLUMNAS_NUMERICAS_HOGAR + (columna_pondih,))

    core = _indicadores_laborales_core(ind)
    poblacion = ind[ind["ESTADO"].isin([1, 2, 3])]
    poblacion_total = poblacion["PONDERA"].sum()
    ocupados = ind[ind["ESTADO"] == 1]
    poblacion_ocupada = ocupados["PONDERA"].sum()
    asalariados = ocupados[ocupados["CAT_OCUP"] == 3]
    poblacion_asalariada = asalariados["PONDERA"].sum()

    # composición ocupacional (CAT_OCUP: 1 patrón, 2 cuentapropia, 3 asalariado, 4 trab. familiar).
    pct_patron = _tasa(_peso(ocupados["CAT_OCUP"] == 1, ocupados["PONDERA"]), poblacion_ocupada)
    pct_cuentapropia = _tasa(_peso(ocupados["CAT_OCUP"] == 2, ocupados["PONDERA"]), poblacion_ocupada)
    pct_asalariado = _tasa(_peso(ocupados["CAT_OCUP"] == 3, ocupados["PONDERA"]), poblacion_ocupada)
    pct_trabajador_familiar = _tasa(_peso(ocupados["CAT_OCUP"] == 4, ocupados["PONDERA"]), poblacion_ocupada)

    # calidad del empleo asalariado.
    pct_con_obra_social = _tasa(_peso(asalariados["PP07G4"] == 1, asalariados["PONDERA"]), poblacion_asalariada)
    pct_con_aguinaldo = _tasa(_peso(asalariados["PP07G2"] == 1, asalariados["PONDERA"]), poblacion_asalariada)
    pct_con_vacaciones_pagas = _tasa(_peso(asalariados["PP07G1"] == 1, asalariados["PONDERA"]), poblacion_asalariada)

    # cobertura de salud (CH08: 4 = no paga ni le descuentan == sin cobertura), toda la población.
    poblacion_ind_total = ind["PONDERA"].sum()
    pct_sin_cobertura_salud = _tasa(_peso(ind["CH08"] == 4, ind["PONDERA"]), poblacion_ind_total)

    # educación: secundario completo o más, en población de 25+ (convención habitual).
    pob25 = ind[ind["CH06"] >= 25]
    pct_secundario_completo_o_mas = _tasa(
        _peso(pob25["NIVEL_ED"].isin([4, 5, 6]), pob25["PONDERA"]), pob25["PONDERA"].sum()
    )
    # alfabetización, población de 10+ (CH09: 2 = no sabe leer/escribir).
    pob10 = ind[ind["CH06"] >= 10]
    tasa_analfabetismo = _tasa(_peso(pob10["CH09"] == 2, pob10["PONDERA"]), pob10["PONDERA"].sum())
    # asistencia escolar, población en edad escolar típica (CH10: 1 = asiste).
    pob_edad_escolar = ind[(ind["CH06"] >= 5) & (ind["CH06"] <= 24)]
    tasa_asistencia_escolar = _tasa(
        _peso(pob_edad_escolar["CH10"] == 1, pob_edad_escolar["PONDERA"]), pob_edad_escolar["PONDERA"].sum()
    )

    # vivienda (a nivel hogar): hacinamiento, agua de red, tenencia.
    hog_con_ambientes = hog[hog["II1"] > 0]
    hacinamiento_medio = (
        ((hog_con_ambientes["IX_TOT"] / hog_con_ambientes["II1"]) * hog_con_ambientes[columna_pondih]).sum()
        / hog_con_ambientes[columna_pondih].sum()
        if hog_con_ambientes[columna_pondih].sum()
        else None
    )
    peso_hogares = hog[columna_pondih].sum()
    pct_agua_red_publica = _tasa(_peso(hog["IV7"] == 1, hog[columna_pondih]), peso_hogares)
    pct_vivienda_propia = _tasa(_peso(hog["II7"].isin([1, 2]), hog[columna_pondih]), peso_hogares)

    # estrategias de subsistencia del hogar, últimos 3 meses.
    pct_hogares_ayuda_social_gobierno = _tasa(_peso(hog["V5"] == 1, hog[columna_pondih]), peso_hogares)
    pct_hogares_prestamo_bancario = _tasa(_peso(hog["V15"] == 1, hog[columna_pondih]), peso_hogares)
    pct_hogares_vendio_pertenencias = _tasa(_peso(hog["V17"] == 1, hog[columna_pondih]), peso_hogares)

    ingreso_total_individual_medio = (
        (poblacion["P47T"] * poblacion["PONDERA"]).sum() / poblacion_total if poblacion_total else None
    )
    ipcf_medio = (
        (hog["IPCF"] * hog[columna_pondih]).sum() / hog[columna_pondih].sum()
        if hog[columna_pondih].sum()
        else None
    )

    return {
        "anio": int(ind["ANO4"].iloc[0]),
        "trimestre": int(ind["TRIMESTRE"].iloc[0]),
        **core,
        "pct_patron": pct_patron,
        "pct_cuentapropia": pct_cuentapropia,
        "pct_asalariado": pct_asalariado,
        "pct_trabajador_familiar": pct_trabajador_familiar,
        "pct_con_obra_social": pct_con_obra_social,
        "pct_con_aguinaldo": pct_con_aguinaldo,
        "pct_con_vacaciones_pagas": pct_con_vacaciones_pagas,
        "pct_sin_cobertura_salud": pct_sin_cobertura_salud,
        "pct_secundario_completo_o_mas": pct_secundario_completo_o_mas,
        "tasa_analfabetismo": tasa_analfabetismo,
        "tasa_asistencia_escolar": tasa_asistencia_escolar,
        "hacinamiento_medio": hacinamiento_medio,
        "pct_agua_red_publica": pct_agua_red_publica,
        "pct_vivienda_propia": pct_vivienda_propia,
        "pct_hogares_ayuda_social_gobierno": pct_hogares_ayuda_social_gobierno,
        "pct_hogares_prestamo_bancario": pct_hogares_prestamo_bancario,
        "pct_hogares_vendio_pertenencias": pct_hogares_vendio_pertenencias,
        "ingreso_total_individual_medio": ingreso_total_individual_medio,
        "ipcf_medio": ipcf_medio,
    }


_TRAMOS_ETARIOS = (
    (10, 24, "10-24"),
    (25, 39, "25-39"),
    (40, 59, "40-59"),
    (60, 130, "60+"),
)

_SEXO_ETIQUETA = {1: "varon", 2: "mujer"}


def agregados_por_sexo(individual: pd.DataFrame) -> list[dict]:
    """Núcleo laboral (`_indicadores_laborales_core`) para Gran La Plata,
    abierto por sexo (`CH04`: 1=varón, 2=mujer). Una fila por (trimestre, sexo).
    """
    ind = individual[individual["AGLOMERADO"] == AGLOMERADO_GRAN_LA_PLATA].copy()
    ind = _numerico(ind, _COLUMNAS_NUMERICAS_INDIVIDUAL)
    anio, trimestre = int(ind["ANO4"].iloc[0]), int(ind["TRIMESTRE"].iloc[0])

    filas = []
    for codigo, etiqueta in _SEXO_ETIQUETA.items():
        sub = ind[ind["CH04"] == codigo]
        filas.append({"anio": anio, "trimestre": trimestre, "sexo": etiqueta, **_indicadores_laborales_core(sub)})
    return filas


def agregados_por_edad(individual: pd.DataFrame) -> list[dict]:
    """Núcleo laboral (`_indicadores_laborales_core`) para Gran La Plata,
    abierto por tramo etario (`CH06`, ver `_TRAMOS_ETARIOS`). Una fila por
    (trimestre, tramo_etario).
    """
    ind = individual[individual["AGLOMERADO"] == AGLOMERADO_GRAN_LA_PLATA].copy()
    ind = _numerico(ind, _COLUMNAS_NUMERICAS_INDIVIDUAL)
    anio, trimestre = int(ind["ANO4"].iloc[0]), int(ind["TRIMESTRE"].iloc[0])

    filas = []
    for edad_min, edad_max, etiqueta in _TRAMOS_ETARIOS:
        sub = ind[(ind["CH06"] >= edad_min) & (ind["CH06"] <= edad_max)]
        filas.append(
            {"anio": anio, "trimestre": trimestre, "tramo_etario": etiqueta, **_indicadores_laborales_core(sub)}
        )
    return filas
