#!/usr/bin/env python3
"""
generar_manifest.py — Genera evaluation_manifest.json
Ejecuta validaciones sobre el pipeline electoral.
"""

import json
import os
import sqlite3
import subprocess
import sys

# ──────────────── META (EDITAR AQUÍ) ────────────────
META = {
    "nombre": "CESAR RAMIREZ",
    "email": "cesar.ramirez@ejemplo.com",
    "url_repo": "https://github.com/cesar/ramirez_prueba_utl_2026",
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


def main():
    print("=" * 60)
    print("MANIFEST — Evaluación automática del pipeline")
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

    c.execute("SELECT COUNT(DISTINCT municipio) FROM carga_log")
    total_muns = c.fetchone()[0]
    c.execute("SELECT municipio, COUNT(*) FROM carga_log GROUP BY municipio ORDER BY municipio")
    muns = {r[0]: r[1] for r in c.fetchall()}
    check(f"Municipios: {total_muns}/4", total_muns == 4, str(muns))

    for t in ["partido", "municipio", "zona", "puesto", "mesa", "candidato", "resultados_votacion"]:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = c.fetchone()[0]
        check(f"Tabla {t}: {cnt} registros", cnt > 0)

    conn.close()

    # ── SQL ──
    print("\n--- Consultas analíticas ---")
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
        "meta": {
            "nombre": "NOMBRE APELLIDO",
            "email": "nombre@ejemplo.com",
            "url_repo": "https://github.com/usuario/prueba_utl_2026",
            "fecha": "2026-07-13",
        },
        "checks": [
            {"desc": "DB existe en db/puestos_2026.db", "ok": True, "detail": ""},
            {"desc": "Municipios: 4/4", "ok": True, "detail": "{'DUITAMA': 13632, 'PAIPA': 25683, 'SOGAMOSO': 77394, 'TUNJA': 180928}"},
            {"desc": "Tabla resultados_votacion: ~297637 registros", "ok": True, "detail": ""},
        ],
        "sql": [
            {"name": "tarea_3_1 - Arrastre Verde", "status": "OK", "rows": 34, "sample": ["('TUNJA', '0700001010001', 'AUDITORIO GUSTAVO M CASTELLANOS COMFABOY', 778, 3439, 0.2262)"]},
            {"name": "tarea_3_2 - Concentracion >60%", "status": "OK", "rows": 1919, "sample": ["(1, 'AUDITORIO GUSTAVO M CASTELLANOS COMFABOY', 'ZONA01', 'TUNJA', '92', 'SOLO POR LA LISTA', '0', 'Senado', 59, 59, 100.0)"]},
            {"name": "tarea_3_3 - Atribucion Deterministica", "status": "OK", "rows": 5, "sample": ["('SOLO POR LA LISTA', '92', 6319.0)"]},
        ],
        "visualizations": {
            "scatter": {"stdout": "r=0.846 | pendiente=0.874 | n_mesas=129", "stderr": "", "returncode": 0},
            "heatmap": {"stdout": "Heatmap guardado en: C:/repo/viz/heatmap_municipios.png", "stderr": "", "returncode": 0},
        },
        "errors": [],
    }
    with open(EXAMPLE_PATH, "w", encoding="utf-8") as f:
        json.dump(example, f, indent=2, ensure_ascii=False)
    print(f"Example escrito en: {EXAMPLE_PATH}")


if __name__ == "__main__":
    main()
