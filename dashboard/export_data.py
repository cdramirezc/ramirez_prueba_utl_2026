#!/usr/bin/env python3
"""
export_data.py — Exporta datos de db/puestos_2026.db a dashboard/data.json
y regenera el bloque embebido de datos en dashboard/index.html
"""

import json
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "puestos_2026.db")
DATA_JSON_PATH = os.path.join(BASE_DIR, "dashboard", "data.json")
HTML_PATH = os.path.join(BASE_DIR, "dashboard", "index.html")


def export_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Total votos SE por municipio
    c.execute("""
        SELECT UPPER(m.nombre) AS municipio, SUM(rv.votos) AS votos
        FROM resultados_votacion rv
        JOIN corporacion co ON co.id = rv.corporacion_id
        JOIN municipio m ON m.id = rv.municipio_id
        WHERE co.codigo = 'SE'
        GROUP BY m.nombre
        ORDER BY m.nombre
    """)
    total_municipios = {r["municipio"]: r["votos"] for r in c.fetchall()}

    # Top 10 candidatos CA por municipio + partido líder SE
    municipios_sorted = sorted(total_municipios.keys())
    top10 = {}
    lider_partido = {}

    for mun in municipios_sorted:
        c.execute("""
            SELECT ca.nombre_completo AS nombre, p.codigo_partido AS codpar, SUM(rv.votos) AS votos
            FROM resultados_votacion rv
            JOIN corporacion co ON co.id = rv.corporacion_id
            JOIN candidato ca ON ca.id = rv.candidato_id
            JOIN partido p ON p.id = ca.partido_id
            JOIN municipio m ON m.id = rv.municipio_id
            WHERE UPPER(m.nombre) = ? AND co.codigo = 'CA' AND ca.nombre_completo != 'SOLO POR LA LISTA'
            GROUP BY ca.nombre_completo, p.codigo_partido
            ORDER BY SUM(rv.votos) DESC
            LIMIT 10
        """, (mun,))
        top10[mun] = [{"nombre": r["nombre"], "codpar": r["codpar"], "votos": r["votos"]} for r in c.fetchall()]

        c.execute("""
            SELECT p.codigo_partido AS codpar, SUM(rv.votos) AS votos
            FROM resultados_votacion rv
            JOIN corporacion co ON co.id = rv.corporacion_id
            JOIN partido p ON p.id = rv.partido_id
            JOIN municipio m ON m.id = rv.municipio_id
            WHERE UPPER(m.nombre) = ? AND co.codigo = 'SE'
            GROUP BY p.codigo_partido
            ORDER BY SUM(rv.votos) DESC
            LIMIT 1
        """, (mun,))
        row = c.fetchone()
        lider_partido[mun] = {"codpar": row["codpar"], "votos": row["votos"]} if row else {"codpar": "", "votos": 0}

    # Arrastre Verde por municipio y puesto
    arrastre = {}
    for mun in municipios_sorted:
        c.execute("""
            SELECT p.nombre AS puesto,
                   SUM(CASE WHEN pa.codigo_partido = '57' THEN rv.votos ELSE 0 END) AS verde,
                   SUM(rv.votos) AS total
            FROM resultados_votacion rv
            JOIN corporacion co ON co.id = rv.corporacion_id
            JOIN partido pa ON pa.id = rv.partido_id
            JOIN municipio m ON m.id = rv.municipio_id
            JOIN mesa me ON me.id = rv.mesa_id
            JOIN puesto p ON p.id = me.puesto_id
            WHERE UPPER(m.nombre) = ? AND co.codigo = 'SE'
            GROUP BY p.nombre
            HAVING total > 0
            ORDER BY p.nombre
        """, (mun,))
        rows = c.fetchall()
        arrastre[mun] = [
            {"puesto": r["puesto"], "verde": r["verde"], "total": r["total"], "ratio": round(r["verde"] / r["total"], 4)}
            for r in rows
        ]

    conn.close()

    data = {
        "total_municipios": total_municipios,
        "top10": top10,
        "lider_partido": lider_partido,
        "arrastre": arrastre,
    }

    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Regenerar HTML embebido
    _regenerar_html(data)

    print(f"data.json escrito en: {DATA_JSON_PATH}")
    print(f"Datos exportados para {len(total_municipios)} municipios")
    return data


def _regenerar_html(data):
    if not os.path.exists(HTML_PATH):
        print(f"Advertencia: {HTML_PATH} no encontrado, saltando regeneración HTML")
        return

    html = open(HTML_PATH, encoding="utf-8").read()
    data_js_str = "var DATA = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n"

    # Replace block using brace-counting: find "var DATA =" and matching "};"
    start = html.find("var DATA =")
    if start >= 0:
        depth = 0
        i = start
        while i < len(html):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 2  # include ";\n"?
                    j = i + 1
                    while j < len(html) and html[j] in "; \t\r\n":
                        j += 1
                    end = j
                    break
            i += 1
        else:
            print("No se pudo encontrar el cierre del bloque DATA, usando regex fallback")
            import re
            html = re.sub(r'var DATA\s*=\s*\{.*?\};', data_js_str, html, flags=re.DOTALL)
            return
        html = html[:start] + data_js_str + html[end:]
    else:
        html = html.replace(
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>',
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>\n    <script>\n' + data_js_str + "\n    </script>",
        )

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML actualizado con datos embebidos: {HTML_PATH}")


if __name__ == "__main__":
    export_data()
