"""
5.2 - Scatter CA vs SE por mesa.

Cada punto = una mesa (total de votos CA vs total de votos SE en esa mesa).
Color por municipio. Incluye linea de regresion OLS y r de Pearson anotado.

Salida: viz/scatter_ca_se.png
"""
import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "puestos_2026.db")
OUT_PATH = os.path.join(BASE_DIR, "viz", "scatter_ca_se.png")


def cargar_datos(conn):
    query = """
        SELECT
            me.codigo_mesa AS codigo_mesa,
            m.nombre AS municipio,
            co.codigo AS corporacion,
            SUM(rv.votos) AS votos
        FROM resultados_votacion rv
        JOIN corporacion co ON co.id = rv.corporacion_id
        JOIN municipio m ON m.id = rv.municipio_id
        JOIN mesa me ON me.id = rv.mesa_id
        GROUP BY me.codigo_mesa, m.nombre, co.codigo
    """
    df = pd.read_sql(query, conn)
    pivot = (
        df.pivot_table(
            index=["codigo_mesa", "municipio"], columns="corporacion", values="votos"
        )
        .reset_index()
        .dropna(subset=["CA", "SE"])
    )
    return pivot


def main():
    conn = sqlite3.connect(DB_PATH)
    df = cargar_datos(conn)
    conn.close()

    x = df["CA"].values
    y = df["SE"].values

    # Regresion OLS y correlacion de Pearson
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    fig, ax = plt.subplots(figsize=(9, 7))

    municipios = sorted(df["municipio"].unique())
    palette = dict(zip(municipios, sns.color_palette("tab10", len(municipios))))

    for mun in municipios:
        sub = df[df["municipio"] == mun]
        ax.scatter(
            sub["CA"], sub["SE"], label=mun, color=palette[mun], alpha=0.75, s=45, edgecolor="k", linewidth=0.3
        )

    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, color="black", linestyle="--", linewidth=1.5, label="Regresion OLS")

    ax.annotate(
        f"r de Pearson = {r_value:.3f}\n"
        f"y = {slope:.3f}x + {intercept:.2f}\n"
        f"p-valor = {p_value:.2e}\n"
        f"n = {len(df)} mesas",
        xy=(0.03, 0.97),
        xycoords="axes fraction",
        va="top",
        ha="left",
        fontsize=10,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
    )

    ax.set_xlabel("Votos totales Camara (CA) por mesa")
    ax.set_ylabel("Votos totales Senado (SE) por mesa")
    ax.set_title(
        "Votos CA vs SE por mesa\n(Boyaca - datos de prueba: Tunja, Paipa, Sogamoso)",
        fontsize=12,
    )
    ax.legend(title="Municipio")
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150)
    print(f"r={r_value:.3f} | pendiente={slope:.3f} | n_mesas={len(df)}")


if __name__ == "__main__":
    main()
