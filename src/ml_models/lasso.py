import pandas as pd
import numpy as np

from ml_models.cargar_panel import COLUMNAS_METADATA_PANEL, COLUMNAS_OUTCOME_ELECTORAL


def _rechazar_metadata(columnas: list[str]) -> None:
    """Guarda defensiva (D23, ampliada en D27 contra outcome electoral):
    protege a cualquier llamador de `construir_Xy_final`/
    `estabilidad_seleccion`, sin importar cómo haya armado su lista de
    columnas (sufijo, `.select_dtypes`, a mano)."""
    colados = set(columnas) & (set(COLUMNAS_METADATA_PANEL) | set(COLUMNAS_OUTCOME_ELECTORAL))
    if colados:
        raise ValueError(f"columnas de metadata u outcome electoral coladas en el feature set: {sorted(colados)}")


def encontrar_redundantes(corr: pd.DataFrame, umbral: float) -> list[set[str]]:
    """Agrupa columnas en clusters de redundancia transitiva (single-linkage):
    si A-B >= umbral y B-C >= umbral, A/B/C quedan juntas aunque A-C no
    supere el umbral directamente."""
    cols = list(corr.columns)
    adyacencia = {c: set() for c in cols}
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            if abs(corr.loc[a, b]) >= umbral:
                adyacencia[a].add(b)
                adyacencia[b].add(a)

    visit, clusters = set(), []
    for c in cols:
        if c in visit:
            continue
        stack, cluster = [c], set()
        while stack:
            actual = stack.pop()
            if actual in cluster:
                continue
            cluster.add(actual)
            stack.extend(adyacencia[actual] - cluster)
        visit |= cluster
        clusters.append(cluster)
    return clusters


def elegir_representante(cluster: set[str], df: pd.DataFrame | None = None,orden_sufijo: list[str] | None = None, prioridad_teorica: list[str] | None = None,
) -> str:
    """Elige un representante aplicando los criterios
    provistos en orden de prioridad. Los criterios son:
    - df: si se pasa, antepone la columna con menos NaN.
    - orden_sufijo: lista de sufijos en orden de preferencia
      (ej. "_nivel_vc" antes que "_pendiente_vc").
    - prioridad_teorica: lista de prefijos de variable en orden de
      relevancia teórica (ej. "ipc" antes que "reservas").
    """
    def clave(col):
        criterios = []
        if df is not None:
            criterios.append(df[col].isna().sum())
        if orden_sufijo is not None:
            criterios.append(next((i for i, s in enumerate(orden_sufijo) if col.endswith(s)), 99))
        if prioridad_teorica is not None:
            variable = next((v for v in prioridad_teorica if col.startswith(v + "_")), None)
            criterios.append(prioridad_teorica.index(variable) if variable is not None else 99)
        criterios.append(col)
        return tuple(criterios)

    return min(cluster, key=clave)

def columnas_nan(nivel: str, id_transicion: str, columnas: list[str], df: pd.DataFrame = None) -> list[str]:
    """Devuelve las columnas de `columnas` que son NaN para esa fila puntual."""
    df_local = df[nivel]
    fila = df_local[df_local["id_transicion"] == id_transicion]
    if fila.empty:
        raise ValueError(f"no encontré {id_transicion!r} en el panel de {nivel}")
    fila = fila.iloc[0]
    return [c for c in columnas if pd.isna(fila[c])]


def estandarizar(X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    medias = X.mean(axis=0).values
    desvios = X.std(axis=0, ddof=0).values
    # D29: una columna sin varianza en el N completo (D28) puede volverse
    # constante solo dentro de un fold de LOO-CV (ej. emae_cobertura_parcial,
    # True en una única fila) -- desvio=0 ahí implica numerador=0 también, así
    # que el resultado correcto es 0, no NaN por división 0/0.
    desvios_seguros = np.where(desvios == 0, 1.0, desvios)
    X_std = (X.values - medias) / desvios_seguros
    return X_std, medias, desvios_seguros


def soft_threshold(z: float, umbral: float) -> float:
    """Operador proximal de la norma L1: encoge z hacia cero, y lo pone en cero
    exactamente si |z| <= umbral."""
    if z > umbral:
        return z - umbral
    elif z < -umbral:
        return z + umbral
    return 0.0

def construir_Xy_final(nivel: str, columnas: list[str], df,target: str) -> tuple[pd.DataFrame, pd.Series]:
    _rechazar_metadata(columnas)
    df_local = df[nivel]
    X = df_local[columnas].copy()
    y = df_local[target].copy()

    completas = X.notna().all(axis=1) & y.notna()
    n_incompletas = (~completas).sum()
    if n_incompletas:
        print(f"[{nivel}] excluye {n_incompletas} fila(s) por NaN: {df_local.loc[~completas, 'id_transicion'].tolist()}")

    X_final = X.loc[completas].reset_index(drop=True)
    y_final = y.loc[completas].reset_index(drop=True)

    # D28: columnas_candidatas (D27) ya no filtra por sufijo -- una variable
    # bien cubierta (ej. icc/icg/tc_oficial) puede tener cobertura_parcial
    # constante en las filas que sobreviven para un nivel dado. Sin varianza
    # no hay nada que estandarizar (división por 0), y no aporta nada a LASSO.
    constantes = X_final.columns[X_final.std(axis=0, ddof=0) == 0]
    if len(constantes):
        print(f"[{nivel}] excluye columna(s) sin varianza: {list(constantes)}")
        X_final = X_final.drop(columns=constantes)

    # D28: columnas booleanas (ej. X_cobertura_parcial) mezcladas con
    # float64 hacen que X.values sea dtype=object -- se castean a float
    # (True/False -> 1.0/0.0, codificación numérica estándar para LASSO).
    X_final = X_final.astype(float)

    return X_final, y_final


def lasso_coordinate_descent(
    X: np.ndarray, y: np.ndarray, alpha: float, tol: float = 1e-6, max_iter: int = 1000
) -> np.ndarray:
    n, p = X.shape
    beta = np.zeros(p)
    for iteracion in range(max_iter):
        beta_anterior = beta.copy()
        for j in range(p):
            residuo_parcial = y - X @ beta + X[:, j] * beta[j]  
            rho_j = X[:, j] @ residuo_parcial / n
            beta[j] = soft_threshold(rho_j, alpha)

        if np.max(np.abs(beta - beta_anterior)) < tol:
            break

    return beta

def verificar_kkt(X: np.ndarray, y: np.ndarray, beta: np.ndarray, alpha: float, n: int) -> dict:
    gradiente = X.T @ (y - X @ beta) / n  # Xⱼᵀ(y - Xβ)/n para cada j

    activos = beta != 0
    inactivos = ~activos

    # para los activos: gradiente debería ser ~alpha * signo(beta)
    error_activos = np.max(np.abs(gradiente[activos] - alpha * np.sign(beta[activos]))) if activos.any() else 0.0

    # para los inactivos: |gradiente| debería ser <= alpha
    exceso_inactivos = np.max(np.abs(gradiente[inactivos]) - alpha) if inactivos.any() else -np.inf

    return {
        "error_max_en_activos": error_activos,
        "exceso_max_en_inactivos": exceso_inactivos,  
        "n_activos": activos.sum(),
    }

def alpha_max_lasso(X: np.ndarray, y: np.ndarray) -> float:
    """El alpha más chico a partir del cual todos los coeficientes quedan
    en cero (condición KKT en beta=0: |Xⱼᵀy|/n <= alpha para todo j)."""
    n = len(y)
    return np.max(np.abs(X.T @ y)) / n

def lasso_loocv_manual(X_df: pd.DataFrame, y_ser: pd.Series, n_alphas: int = 50, factor_extension: float = 1.0) -> dict:
    n = len(y_ser)
    X_std_full, _, _ = estandarizar(X_df)
    y_full = y_ser.values
    alpha_max = alpha_max_lasso(X_std_full, y_full - y_full.mean()) * factor_extension
    alphas = np.logspace(np.log10(alpha_max * 1e-3), np.log10(alpha_max), n_alphas)

    errores = np.zeros((n, n_alphas))

    for i in range(n):
        idx_train = [k for k in range(n) if k != i]
        X_train_df = X_df.iloc[idx_train]
        y_train = y_ser.iloc[idx_train].values
        X_test_df = X_df.iloc[[i]]
        y_test = y_ser.iloc[i]

        X_train_std, medias_tr, desvios_tr = estandarizar(X_train_df)
        y_train_media = y_train.mean()
        y_train_centrado = y_train - y_train_media
        X_test_std = (X_test_df.values - medias_tr) / desvios_tr

        beta = np.zeros(X_train_std.shape[1])
        for j, alpha in enumerate(alphas[::-1]):  # de mayor a menor -> warm start natural
            beta = lasso_coordinate_descent(X_train_std, y_train_centrado, alpha, tol=1e-6, max_iter=1000)
            pred = y_train_media + X_test_std @ beta
            errores[i, len(alphas) - 1 - j] = (pred[0] - y_test) ** 2

    mean_mse = errores.mean(axis=0)
    se_mse = errores.std(axis=0, ddof=1) / np.sqrt(n)

    idx_min = mean_mse.argmin()
    umbral = mean_mse[idx_min] + se_mse[idx_min]
    alpha_1se = alphas[mean_mse <= umbral].max()

    return {"alphas": alphas, "mean_mse": mean_mse, "se_mse": se_mse, "alpha_min": alphas[idx_min], "alpha_1se": alpha_1se}

def verificar_saturacion(X_df: pd.DataFrame, y_ser: pd.Series, factores: list[float]) -> pd.DataFrame:
    """Corre lasso_loocv_manual con distintos factor_extension y devuelve
    el MSE mínimo y el MSE en el techo de cada corrida -- si ambos se
    estabilizan al ampliar la grilla, la saturación es real, no un límite
    artificial de rango."""
    filas = []
    for factor in factores:
        r = lasso_loocv_manual(X_df, y_ser, factor_extension=factor)
        idx_min = r["mean_mse"].argmin()
        filas.append({
            "factor_extension": factor,
            "techo": r["alphas"][-1],
            "alpha_min": r["alpha_min"],
            "alpha_1se": r["alpha_1se"],
            "mse_min": r["mean_mse"][idx_min],
            "mse_en_techo": r["mean_mse"][-1],
        })
    return pd.DataFrame(filas)

def baseline_trivial_loocv(y_ser: pd.Series) -> float:
    """MSE en LOO de predecir, para cada punto dejado afuera, el promedio
    de los demás -- el piso de comparación: cualquier modelo que no le
    gane a esto no aporta nada."""
    n = len(y_ser)
    errores = []
    for i in range(n):
        pred = np.delete(y_ser.values, i).mean()
        errores.append((pred - y_ser.values[i]) ** 2)
    return np.mean(errores)


def mse_en_alpha(X_df: pd.DataFrame, y_ser: pd.Series, alpha: float) -> float:
    """MSE en LOO de lasso_coordinate_descent para un alpha puntual."""
    n = len(y_ser)
    errores = []
    for i in range(n):
        idx_train = [k for k in range(n) if k != i]
        X_train_df, y_train = X_df.iloc[idx_train], y_ser.iloc[idx_train].values
        X_test_df, y_test = X_df.iloc[[i]], y_ser.iloc[i]

        X_train_std, medias, desvios = estandarizar(X_train_df)
        y_train_media = y_train.mean()
        X_test_std = (X_test_df.values - medias) / desvios

        beta = lasso_coordinate_descent(X_train_std, y_train - y_train_media, alpha)
        pred = y_train_media + X_test_std @ beta
        errores.append((pred[0] - y_test) ** 2)
    return np.mean(errores)


def ajustar_final(X_df: pd.DataFrame, y_ser: pd.Series, alpha: float) -> pd.Series:
    """Ajuste final sobre todos los datos del nivel (ya no hay held-out
    acá) -- coeficientes en la escala estandarizada."""
    X_std, medias, desvios = estandarizar(X_df)
    y_centrado = y_ser.values - y_ser.values.mean()
    beta = lasso_coordinate_descent(X_std, y_centrado, alpha)
    return pd.Series(beta, index=X_df.columns)

def estabilidad_seleccion(
    nivel: str, alpha: float, df: pd.DataFrame, columnas: list, target: str, X_df: pd.DataFrame, y_ser: pd.Series
) -> pd.DataFrame:
    """Reajusta el modelo final (mismo alpha ya elegido por CV) sacando
    una ventana a la vez -- para ver si la selección de variables
    depende de un punto influyente en vez de ser un patrón sostenido.
    X_df/y_ser tienen que ser los mismos (ya filtrados por completas)
    que se usaron para ajustar el modelo con ese alpha."""
    _rechazar_metadata(columnas)
    X_completo = df[columnas]
    y_completo = df[target]
    completas = X_completo.notna().all(axis=1) & y_completo.notna()
    ids = df.loc[completas, "id_transicion"].reset_index(drop=True)

    n = len(y_ser)
    filas = {}
    for i in range(n):
        idx_sub = [k for k in range(n) if k != i]
        beta = ajustar_final(X_df.iloc[idx_sub], y_ser.iloc[idx_sub], alpha)
        filas[f"sin_{ids[i]}"] = beta

    return pd.DataFrame(filas).T