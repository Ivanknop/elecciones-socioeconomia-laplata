#!/usr/bin/env python3
"""
generar_v_party_propio.py

Genera v_party_propio.csv a partir de encuesta_partidos_propia.csv (encuesta de
posicionamiento ideológico de fuerzas políticas -- versión anonimizada de la
exportación cruda de Google Forms: cada fila trae un ID secuencial en vez de
Marca temporal/Email/Nombre/Descripción, para poder referenciar la fila real
del formulario -- fuera de este repo -- sin exponer datos personales).

Pipeline:
  1. Parsear la encuesta: por cada experto x partido, promediar A1-A4 (económico,
     con polaridad INVERTIDA: 4 - promedio, para que alto = derecha/mercado,
     igual que vparty_economico), B1-B4 (progresismo) y C1-C2 (populismo).
  2. VALIDACIÓN: para los partidos que tienen equivalente real en V-Party
     (ver MAPEO_VPARTY más abajo), comparar cada experto contra el valor real
     en unidades z (estandarizando cada experto sobre sus propias 12
     respuestas, y vparty sobre la distribución completa del archivo de
     referencia). Se listan las distancias para revisión manual; el script NO
     excluye expertos automáticamente, salvo que se pasen explícitamente por
     --excluir.
  3. AGREGACIÓN: mediana de todos los expertos (no excluidos) por partido y
     dimensión.
  4. CALIBRACIÓN: regresión lineal simple (mediana_experto -> valor real
     vparty) ajustada sobre los partidos con match real, aplicada a los
     partidos sin match para llevarlos a la escala real de V-Party. Se avisa
     si alguna estimación cae fuera del rango observado en la referencia
     (extrapolación).
  5. SALIDA: v_party_propio.csv con partido,vparty_economico,vparty_progresismo,
     vparty_populismo. Para partidos con match real se usa el valor real de
     V-Party (no el estimado); para el resto, la estimación calibrada.

Uso:
  python3 generar_v_party_propio.py \
      --encuesta encuesta_partidos_propia.csv \
      --referencia clasificacion_ideologica_agrupaciones.csv \
      --salida v_party_propio.csv \
      [--reporte reporte_validacion_vparty.md] \
      [--excluir "3,7"]

"""

import argparse
import csv
import statistics as st
import sys

PARTIDOS = [
    "Frente de Izquierda",
    "La Libertad Avanza",
    "Proyecto Sur",
    "Coalicion Civica",
    "Principios y Valores",
    "PRO",
    "Union Civica Radical",
    "Frente Renovador",
    "Frente para la Victoria",
    "Patria Grande",
    "Partido Justicialista",
    "Encuentro Republicano Federal",
]

N_COLS_METADATA = 1   # ID (anonimizado; mapea a la fila real en el export crudo)
N_COLS_BLOQUE = 12    # A1-A4, B1-B4, C1-C2, D1, D2
N_COLS_FINAL = 1      # Comentarios adicionales

MAPEO_VPARTY = {
    "Coalicion Civica": [
        "COALICION CIVICA ARI",
        "COALICIÓN CÍVICA - AFIRMACIÓN PARA UNA REPÚBLICA IGUALITARIA ARI",
        "COALICIÓN CÍVICA - A.R.I.",
    ],
    "PRO": [
        "ALIANZA CAMBIEMOS",
        "CAMBIEMOS BUENOS AIRES",
        "JUNTOS POR EL CAMBIO",
        "JUNTOS",
    ],
    "Frente Renovador": ["FRENTE RENOVADOR"],
    "Frente para la Victoria": [
        "ALIANZA FRENTE PARA LA VICTORIA",
        "FRENTE PARA LA VICTORIA",
    ],
    "Partido Justicialista": ["FRENTE JUSTICIALISTA"],
}

# Partidos que ya tienen su clasificación vparty resuelta por otra vía (fuera
# de este script) y por lo tanto no deben remapearse/joinearse a partir de
# este archivo, aunque acá salgan como "estimado_expertos" (sin match real en
# MAPEO_VPARTY). Se marcan igual que los de fuente="real": con "#" delante
# del nombre en la salida.
NO_MAPEAR_ADICIONALES = {"Union Civica Radical"}

DIMENSIONES = ["econ", "prog", "pop"]


# ---------------------------------------------------------------------------
# 1. PARSEO DE LA ENCUESTA
# ---------------------------------------------------------------------------

def cargar_encuesta(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header, data = rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]

    n_cols_esperadas = N_COLS_METADATA + N_COLS_BLOQUE * len(PARTIDOS) + N_COLS_FINAL
    if len(header) != n_cols_esperadas:
        sys.exit(
            f"ERROR: la encuesta tiene {len(header)} columnas, se esperaban "
            f"{n_cols_esperadas} para {len(PARTIDOS)} partidos. Revisá si "
            f"cambió la cantidad de partidos y actualizá PARTIDOS en el script."
        )

    survey = {}
    expertos_orden = []
    for r in data:
        id_experto = r[0].strip()
        if id_experto not in expertos_orden:
            expertos_orden.append(id_experto)
        for i, partido in enumerate(PARTIDOS):
            start = N_COLS_METADATA + i * N_COLS_BLOQUE
            bloque = r[start:start + N_COLS_BLOQUE]
            try:
                vals = [float(x) for x in bloque[:11]]
            except ValueError:
                sys.exit(
                    f"ERROR: no pude convertir a número las respuestas del "
                    f"experto '{id_experto}' para '{partido}'. Revisá filas "
                    f"incompletas en la encuesta."
                )
            econ = 4 - st.mean(vals[0:4])  # polaridad invertida (aprobado)
            prog = st.mean(vals[4:8])
            pop = st.mean(vals[8:10])
            survey[(id_experto, partido)] = {"econ": econ, "prog": prog, "pop": pop}

    return survey, expertos_orden


# ---------------------------------------------------------------------------
# 2. REFERENCIA V-PARTY REAL
# ---------------------------------------------------------------------------

def cargar_referencia(path):
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("vparty_economico")]
    if not rows:
        sys.exit(f"ERROR: no encontré filas con vparty_economico en {path}")
    return rows


def targets_vparty(ref_rows):
    targets = {}
    for partido, nombres_agrupacion in MAPEO_VPARTY.items():
        matched = [r for r in ref_rows if r["agrupacion"] in nombres_agrupacion]
        if not matched:
            print(f"AVISO: sin filas de referencia para '{partido}' "
                  f"({nombres_agrupacion}); se excluye de la validación/calibración.")
            continue
        targets[partido] = {
            "econ": st.mean(float(r["vparty_economico"]) for r in matched),
            "prog": st.mean(float(r["vparty_progresismo"]) for r in matched),
            "pop": st.mean(float(r["vparty_populismo"]) for r in matched),
            "n_filas": len(matched),
        }
    return targets


def rangos_vparty(ref_rows):
    return {
        dim: (
            min(float(r[f"vparty_{col}"]) for r in ref_rows),
            max(float(r[f"vparty_{col}"]) for r in ref_rows),
        )
        for dim, col in zip(DIMENSIONES, ["economico", "progresismo", "populismo"])
    }


# ---------------------------------------------------------------------------
# 3. VALIDACIÓN POR EXPERTO (distancia z contra vparty real)
# ---------------------------------------------------------------------------

def validar_expertos(survey, expertos, targets, ref_rows, log):
    if not targets:
        log.append("No hay partidos con match real disponible: no se puede validar.")
        return {}

    medias_vp = {
        dim: st.mean(float(r[f"vparty_{col}"]) for r in ref_rows)
        for dim, col in zip(DIMENSIONES, ["economico", "progresismo", "populismo"])
    }
    sd_vp = {
        dim: st.pstdev(float(r[f"vparty_{col}"]) for r in ref_rows)
        for dim, col in zip(DIMENSIONES, ["economico", "progresismo", "populismo"])
    }

    log.append("\n## Validación por experto (distancia z contra V-Party real)\n")
    log.append(f"Partidos usados para validar: {', '.join(targets)} (n={len(targets)})\n")
    log.append("| Experto | dist_econ | dist_prog | dist_pop | dist_total |")
    log.append("|---|---|---|---|---|")

    distancias = {}
    for e in expertos:
        e_econ = [survey[(e, p)]["econ"] for p in PARTIDOS]
        e_prog = [survey[(e, p)]["prog"] for p in PARTIDOS]
        e_pop = [survey[(e, p)]["pop"] for p in PARTIDOS]
        m = {"econ": st.mean(e_econ), "prog": st.mean(e_prog), "pop": st.mean(e_pop)}
        sd = {
            "econ": st.pstdev(e_econ) or 1e-9,
            "prog": st.pstdev(e_prog) or 1e-9,
            "pop": st.pstdev(e_pop) or 1e-9,
        }
        dist_por_dim = {d: [] for d in DIMENSIONES}
        for partido, t in targets.items():
            s = survey[(e, partido)]
            for dim in DIMENSIONES:
                z_e = (s[dim] - m[dim]) / sd[dim]
                z_v = (t[dim] - medias_vp[dim]) / (sd_vp[dim] or 1e-9)
                dist_por_dim[dim].append(abs(z_e - z_v))
        medias_dim = {d: st.mean(dist_por_dim[d]) for d in DIMENSIONES}
        total = st.mean(medias_dim.values())
        distancias[e] = total
        log.append(
            f"| {e} | {medias_dim['econ']:.3f} | {medias_dim['prog']:.3f} "
            f"| {medias_dim['pop']:.3f} | {total:.3f} |"
        )

    if len(distancias) >= 3:
        vals = list(distancias.values())
        umbral = st.mean(vals) + 1.5 * (st.pstdev(vals) or 1e-9)
        outliers = [e for e, d in distancias.items() if d > umbral]
        if outliers:
            log.append(
                f"\n**Posibles outliers (distancia > media + 1.5 sd = {umbral:.3f}):** "
                + ", ".join(outliers)
                + " — revisar manualmente, no se excluyen automáticamente."
            )

    return distancias


# ---------------------------------------------------------------------------
# 4. AGREGACIÓN (mediana) + CALIBRACIÓN (regresión lineal)
# ---------------------------------------------------------------------------

def mediana_por_partido(survey, expertos):
    medianas = {}
    for p in PARTIDOS:
        medianas[p] = {
            dim: st.median(survey[(e, p)][dim] for e in expertos) for dim in DIMENSIONES
        }
    return medianas


def ols(xs, ys):
    n = len(xs)
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0 or n < 2:
        return my, 0.0, float("nan")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    yhat = [a + b * x for x in xs]
    ss_res = sum((y - yh) ** 2 for y, yh in zip(ys, yhat))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return a, b, r2


def calibrar(medianas, targets, ref_rows, log):
    if len(targets) < 3:
        log.append(
            "\n**AVISO:** menos de 3 partidos con match real disponibles; "
            "la calibración no es confiable. Revisar MAPEO_VPARTY."
        )
    calib = {}
    log.append("\n## Calibración (mediana experto -> escala V-Party real)\n")
    log.append(f"n = {len(targets)} partidos validados\n")
    log.append("| Dimensión | Ecuación | R² (in-sample) |")
    log.append("|---|---|---|")
    for dim in DIMENSIONES:
        xs = [medianas[p][dim] for p in targets]
        ys = [targets[p][dim] for p in targets]
        a, b, r2 = ols(xs, ys)
        calib[dim] = (a, b)
        r2_str = f"{r2:.3f}" if r2 == r2 else "n/d"
        log.append(f"| {dim} | y = {a:.3f} + {b:.3f}·x | {r2_str} |")

    rangos = rangos_vparty(ref_rows)
    return calib, rangos


def estimar(medianas, calib):
    estimaciones = {}
    for p in PARTIDOS:
        estimaciones[p] = {
            dim: calib[dim][0] + calib[dim][1] * medianas[p][dim] for dim in DIMENSIONES
        }
    return estimaciones


# ---------------------------------------------------------------------------
# 5. SALIDA
# ---------------------------------------------------------------------------

def escribir_salida(path, targets, estimaciones, rangos, log):
    log.append("\n## Resultado final por partido\n")
    log.append("| Partido | econ | prog | pop | fuente | extrapola |")
    log.append("|---|---|---|---|---|---|")

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["partido", "vparty_economico", "vparty_progresismo", "vparty_populismo"])
        for p in PARTIDOS:
            if p in targets:
                vals = targets[p]
                fuente = "real"
            else:
                vals = estimaciones[p]
                fuente = "estimado_expertos"
            extrapola = []
            for dim, col in zip(DIMENSIONES, ["econ", "prog", "pop"]):
                lo, hi = rangos[dim]
                if vals[dim] < lo or vals[dim] > hi:
                    extrapola.append(dim)
            # partidos con fuente="real" (match en MAPEO_VPARTY) o incluidos a
            # mano en NO_MAPEAR_ADICIONALES ya tienen su vparty resuelto por
            # otra vía: se marcan con "#" para que no se vuelvan a
            # mapear/joinear desde este archivo en pasos subsiguientes.
            nombre_salida = f"#{p}" if fuente == "real" or p in NO_MAPEAR_ADICIONALES else p
            w.writerow([nombre_salida, f"{vals['econ']:.3f}", f"{vals['prog']:.3f}", f"{vals['pop']:.3f}"])
            log.append(
                f"| {nombre_salida} | {vals['econ']:.3f} | {vals['prog']:.3f} | {vals['pop']:.3f} "
                f"| {fuente} | {', '.join(extrapola) if extrapola else '-'} |"
            )


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--encuesta", default="encuesta_partidos_propia.csv")
    ap.add_argument("--referencia", default="clasificacion_ideologica_agrupaciones.csv")
    ap.add_argument("--salida", default="v_party_propio.csv")
    ap.add_argument("--reporte", default="reporte_validacion_vparty.md")
    ap.add_argument("--excluir", default="", help="IDs de expertos a excluir, separados por coma")
    args = ap.parse_args()

    excluidos = {n.strip() for n in args.excluir.split(",") if n.strip()}

    survey, expertos = cargar_encuesta(args.encuesta)
    expertos_usados = [e for e in expertos if e not in excluidos]

    log = [f"# Reporte de generación de {args.salida}\n"]
    log.append(f"Expertos en la encuesta: {len(expertos)} — usados: {len(expertos_usados)}")
    if excluidos:
        log.append(f"Excluidos manualmente: {', '.join(sorted(excluidos, key=lambda x: (len(x), x)))}")

    ref_rows = cargar_referencia(args.referencia)
    targets = targets_vparty(ref_rows)

    validar_expertos(survey, expertos_usados, targets, ref_rows, log)
    medianas = mediana_por_partido(survey, expertos_usados)
    calib, rangos = calibrar(medianas, targets, ref_rows, log)
    estimaciones = estimar(medianas, calib)
    escribir_salida(args.salida, targets, estimaciones, rangos, log)

    with open(args.reporte, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")

    print(f"OK: {args.salida} generado ({len(PARTIDOS)} partidos).")
    print(f"Reporte de validación: {args.reporte}")


if __name__ == "__main__":
    main()
