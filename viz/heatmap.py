"""
5.1 - Heatmap: top 8 candidatos CA x municipios, valores = % del total de votos
CA de cada municipio.

Salida: viz/heatmap_municipios.png

Nota: la base de datos actual solo contiene datos scrapeados (de prueba) para
3 municipios de Boyaca (TUNJA, PAIPA, SOGAMOSO). No se dispone de un cuarto
municipio con datos reales, por lo que el heatmap se genera con los
municipios disponibles.
"""
import os
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "puestos_2026.db")
OUT_PATH = os.path.join(BASE_DIR, "viz", "heatmap_municipios.png")


def cargar_datos(conn):
    query = """
        SELECT
            ca.nombre_completo AS candidato,
            m.nombre AS municipio,
            SUM(rv.votos) AS votos
        FROM resultados_votacion rv
        JOIN corporacion co ON co.id = rv.corporacion_id
        JOIN candidato ca ON ca.id = rv.candidato_id
        JOIN municipio m ON m.id = rv.municipio_id
        WHERE co.codigo = 'CA'
          AND ca.nombre_completo != 'SOLO POR LA LISTA'
        GROUP BY ca.nombre_completo, m.nombre
    """
    return pd.read_sql(query, conn)


def main():
    conn = sqlite3.connect(DB_PATH)
    df = cargar_datos(conn)
    conn.close()

    # Top 8 candidatos por total de votos CA (sumando todos los municipios)
    top8 = (
        df.groupby("candidato")["votos"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .index
    )

    df_top = df[df["candidato"].isin(top8)]

    # Tabla pivote: filas = candidatos, columnas = municipios, valores = votos
    pivot_votos = df_top.pivot(index="candidato", columns="municipio", values="votos").fillna(0)
    pivot_votos = pivot_votos.reindex(top8)

    # Total de votos CA por municipio (todos los candidatos, incluyendo SOLO POR LA LISTA)
    conn = sqlite3.connect(DB_PATH)
    totales_reales = pd.read_sql(
        """
        SELECT m.nombre AS municipio, SUM(rv.votos) AS votos
        FROM resultados_votacion rv
        JOIN corporacion co ON co.id = rv.corporacion_id
        JOIN municipio m ON m.id = rv.municipio_id
        WHERE co.codigo = 'CA'
        GROUP BY m.nombre
        """,
        conn,
    ).set_index("municipio")["votos"]
    conn.close()

    # % del total de votos CA de cada municipio
    pivot_pct = pivot_votos.div(totales_reales, axis=1) * 100

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        pivot_pct,
        annot=True,
        fmt=".2f",
        cmap="YlOrRd",
        cbar_kws={"label": "% del total de votos CA del municipio"},
        linewidths=0.5,
        linecolor="white",
        ax=ax,
    )
    ax.set_title(
        "Top 8 candidatos a Camara (CA) - % de votos por municipio\n"
        "(Boyaca - Tunja, Paipa, Sogamoso, Duitama)",
        fontsize=12,
    )
    ax.set_xlabel("Municipio")
    ax.set_ylabel("Candidato")
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150)
    print(f"Heatmap guardado en: {OUT_PATH}")


if __name__ == "__main__":
    main()
