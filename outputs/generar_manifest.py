#!/usr/bin/env python3
"""
generar_manifest.py — Genera evaluation_manifest.json
Ejecuta validaciones sobre el pipeline electoral.
Incluye validacion de cobertura de mesas (tarea 1.3).
"""
import json
import os
import sqlite3
import subprocess
import sys

# ──────────────── META (EDITAR AQUI) ────────────────
META = {
    "nombre": "CESAR RAMIREZ",
    "email": "cesar.rcely@gmail.com",
    "url_repo": "https://github.com/cdramirezc/ramirez_prueba_utl_2026",
    "fecha": "2026-07-13",
}
# ────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "puestos_2026.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")
OUT_PATH = os.path.join(BASE_DIR, "outputs", "evaluation_manifest.json")
EXAMPLE_PATH = os.path.join(BASE_DIR, "outputs", "evaluation_manifest.example.json")
SCATTER_PATH = os.path.join(BASE_DIR, "viz", "scatter.py")
HEATMAP_PATH = os.path.join(BASE_DIR, "viz", "heatmap.py")
NOM_PATH = os.path.join(BASE_DIR, "nomenclator_temp.json")
COVERAGE_CHECK = []  # stores coverage matrix details

results = {"meta": META, "checks": [], "sql": [], "visualizations": {}, "errors": []}

def check(desc, ok, detail=""):
    results["checks"].append({"desc": desc, "ok": ok, "detail": detail})
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {desc}" + (f" — {detail}" if detail else ""))

def run_sql(name, path, params=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        sql = open(path, encoding="utf-8").read()
        if params:
            c = conn.execute(sql, params)
        else:
            c = conn.execute(sql)
        rows = c.fetchall()
        conn.close()
        print(f"  [SQL OK] {name}: {len(rows)} filas")
        for r in rows[:3]:
            print(f"    {r}")
        results["sql"].append({"name": name, "status": "OK", "rows": len(rows), "sample": [str(r) for r in rows[:3]]})
    except Exception as e:
        print(f"  [SQL ERROR] {name}: {e}")
        results["sql"].append({"name": name, "status": "ERROR", "error": str(e)})

def load_nomenclator():
    """Carga nomenclator y retorna dict municipio -> set de codigos_mesa."""
    if not os.path.exists(NOM_PATH):
        return {}
    with open(NOM_PATH, encoding="utf-8") as f:
        nomdata = json.load(f)
    ambitos = nomdata["amb"][0]["ambitos"]
    idx_map = {e["i"]: e for e in ambitos}
    result = {}
    for nom_upper in ["TUNJA", "PAIPA", "SOGAMOSO", "DUITAMA"]:
        mun = None
        for e in ambitos:
            if e.get("n","").upper().strip() == nom_upper and e.get("l") == 3:
                mun = e; break
        if not mun:
            result[nom_upper] = set()
            continue
        mesas = set()
        for nl_z in mun.get("h", []):
            if nl_z["l"] != 4: continue
            for z_idx in nl_z["p"]:
                z = idx_map.get(z_idx)
                if not z: continue
                for nl_p in z.get("h", []):
                    if nl_p["l"] != 6: continue
                    for p_idx in nl_p["p"]:
                        p = idx_map.get(p_idx)
                        if not p: continue
                        for nm in range(1, p.get("m",0)+1):
                            mesas.add(p["c"] + str(nm).zfill(6))
        result[nom_upper] = mesas
    return result

def main():
    print("=" * 60)
    print("MANIFEST — Evaluacion automatica del pipeline")
    print("=" * 60)

    # ── 0. DB ──
    print("\n--- Base de datos ---")
    db_ok = os.path.exists(DB_PATH)
    check(f"DB existe en {DB_PATH}", db_ok)
    if not db_ok:
        results["errors"].append("DB no encontrada")
        _write()
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT municipio, corporacion, COUNT(*) as cnt
        FROM carga_log
        GROUP BY municipio, corporacion
        ORDER BY municipio, corporacion
    """)
    pairs = [(r[0], r[1], r[2]) for r in c.fetchall()]
    all_nonzero = all(cnt > 0 for _, _, cnt in pairs)
    pair_summary = {f"{m}|{c}": cnt for m, c, cnt in pairs}
    expected = {"DUITAMA|CA", "DUITAMA|SE", "PAIPA|CA", "PAIPA|SE", "SOGAMOSO|CA", "SOGAMOSO|SE", "TUNJA|CA", "TUNJA|SE"}
    missing = expected - set(pair_summary.keys())
    if missing or not all_nonzero:
        detail = f"Faltan o tienen 0 filas: {missing}. Presentes: {pair_summary}"
    else:
        detail = str(pair_summary)
    check(f"Municipios: 8/8 pares (municipio, corporacion) con filas >0", all_nonzero and not missing, detail)

    for t in ["partido", "municipio", "zona", "puesto", "mesa", "candidato", "resultados_votacion"]:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = c.fetchone()[0]
        check(f"Tabla {t}: {cnt} registros", cnt > 0)

    # ── Tarea 1.3: Validacion de cobertura de mesas contra nomenclator ──
    print("\n--- Tarea 1.3: Cobertura de mesas vs Nomenclator ---")
    nom_map = load_nomenclator()
    MUNS = ["DUITAMA", "PAIPA", "SOGAMOSO", "TUNJA"]
    CORPS = ["CA", "SE"]
    all_ok = True
    matrix_lines = []
    header = f"{'MUNICIPIO':<12} {'CORP':<5} {'NOM':<6} {'CARGALOG':<10} {'RES_VOT':<10} {'COBERTURA':<10} {'FILAS':<8}"
    matrix_lines.append(header)
    matrix_lines.append("-" * len(header))

    for nom in MUNS:
        n_set = nom_map.get(nom, set())
        n_total = len(n_set)
        for corp in CORPS:
            c.execute("SELECT COUNT(DISTINCT codigo_mesa), COUNT(*) FROM carga_log WHERE UPPER(municipio)=? AND corporacion=?", (nom, corp))
            ii_mesas, filas_cl = c.fetchone()
            c.execute("""
                SELECT COUNT(DISTINCT me.codigo_mesa), COUNT(*)
                FROM resultados_votacion rv
                JOIN corporacion co ON co.id = rv.corporacion_id
                JOIN municipio m ON m.id = rv.municipio_id
                JOIN mesa me ON me.id = rv.mesa_id
                WHERE UPPER(m.nombre)=? AND co.codigo=?
            """, (nom, corp))
            iii_mesas, filas_rv = c.fetchone()
            pct = round(100.0 * ii_mesas / n_total, 1) if n_total > 0 else 0
            ok = pct >= 95.0
            if not ok:
                all_ok = False
            status = "OK" if ok else "BAJA"
            line = f"{nom:<12} {corp:<5} {n_total:<6} {ii_mesas:<10} {iii_mesas:<10} {pct:<8}% {filas_cl:<8}"
            matrix_lines.append(line)
            coverage_detail = f"{nom}|{corp}: {ii_mesas}/{n_total} = {pct}%"
            check(f"Cobertura {nom}|{corp}: {ii_mesas}/{n_total} mesas ({pct}%)", ok, coverage_detail)
            print(f"    [{status}] {nom} {corp}: {ii_mesas}/{n_total} mesas = {pct}% (umbral 95%)")

    print("\n  Matriz completa de cobertura:")
    for line in matrix_lines:
        print(f"    {line}")

    conn.close()

    # ── SQL ──
    print("\n--- Consultas analiticas ---")
    run_sql("tarea_3_1 - Arrastre Verde", os.path.join(SQL_DIR, "tarea_3_1.sql"), ("57", "5"))
    run_sql("tarea_3_2 - Concentracion >60%", os.path.join(SQL_DIR, "tarea_3_2.sql"))
    run_sql("tarea_3_3 - Atribucion Determinística", os.path.join(SQL_DIR, "tarea_3_3.sql"))

    # ── Visualizaciones ──
    print("\n--- Visualizaciones ---")
    for viz_name, viz_path in [("scatter", SCATTER_PATH), ("heatmap", HEATMAP_PATH)]:
        try:
            out = subprocess.run(
                [sys.executable, viz_path],
                capture_output=True, text=True, timeout=120,
                cwd=BASE_DIR,
                env={**os.environ, "PYTHONPATH": BASE_DIR},
            )
            stdout = out.stdout.strip()
            stderr = out.stderr.strip()
            results["visualizations"][viz_name] = {"stdout": stdout, "stderr": stderr if stderr else "", "returncode": out.returncode}
            if out.returncode == 0 and stdout:
                print(f"  [VIZ OK] {viz_name}: {stdout[:120]}")
            else:
                print(f"  [VIZ FAIL] {viz_name}: rc={out.returncode}, err={stderr[:200]}")
        except Exception as e:
            results["visualizations"][viz_name] = {"error": str(e)}
            print(f"  [VIZ ERROR] {viz_name}: {e}")

    # ── Escribir manifest ──
    _write()

    # ── Generar ejemplo ──
    _write_example()

    print("\n" + "=" * 60)
    ok_count = sum(1 for c in results["checks"] if c["ok"])
    total_count = len(results["checks"])
    print(f"Resumen: {ok_count}/{total_count} checks OK, "
          f"{len(results['sql'])} queries SQL, "
          f"{len(results['visualizations'])} visualizaciones")
    if results["errors"]:
        print(f"ERRORES: {results['errors']}")
    print("=" * 60)

def _write():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nManifest escrito en: {OUT_PATH}")

def _write_example():
    example = {
        "meta": META,
        "checks": [
            {"desc": "DB existe en db/puestos_2026.db", "ok": True, "detail": ""},
            {"desc": "Municipios: 8/8 pares (municipio, corporacion) con filas >0", "ok": True, "detail": "{'DUITAMA|CA': 73626, 'DUITAMA|SE': 75166, 'PAIPA|CA': 24288, 'PAIPA|SE': 50291, 'SOGAMOSO|CA': 76031, 'SOGAMOSO|SE': 1363, 'TUNJA|CA': 39400, 'TUNJA|SE': 141528}"},
            {"desc": "Cobertura DUITAMA|CA: 279/287 mesas (97.2%)", "ok": True, "detail": ""},
            {"desc": "Cobertura DUITAMA|SE: 69/287 mesas (24.0%)", "ok": False, "detail": ""},
            {"desc": "Tabla resultados_votacion: 481688 registros", "ok": True, "detail": ""},
        ],
        "sql": [
            {"name": "tarea_3_1 - Arrastre Verde", "status": "OK", "rows": 55, "sample": ["('DUITAMA', '0700079010001', 'COLEGIO SALESIANO', 0, 320, 0.0)"]},
            {"name": "tarea_3_2 - Concentracion >60%", "status": "OK", "rows": 1919, "sample": ["(1, 'AUDITORIO GUSTAVO M CASTELLANOS COMFABOY', 'ZONA01', 'TUNJA', '92', 'SOLO POR LA LISTA', '0', 'Senado', 59, 59, 100.0)"]},
            {"name": "tarea_3_3 - Atribucion Determinística", "status": "OK", "rows": 5, "sample": ["('YAMIT NOE HURTADO NEIRA', 'Alianza Verde', 2287.64)"]},
        ],
        "visualizations": {
            "scatter": {"stdout": "r=0.872 | pendiente=0.884 | n_mesas=242", "stderr": "", "returncode": 0},
            "heatmap": {"stdout": "Heatmap guardado en: C:/repo/viz/heatmap_municipios.png", "stderr": "", "returncode": 0},
        },
        "errors": [],
    }
    with open(EXAMPLE_PATH, "w", encoding="utf-8") as f:
        json.dump(example, f, indent=2, ensure_ascii=False)
    print(f"Example escrito en: {EXAMPLE_PATH}")

if __name__ == "__main__":
    main()
