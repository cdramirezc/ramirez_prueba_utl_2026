import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "carga_log.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS corporacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE CHECK(codigo IN ('SE', 'CA')),
            nombre TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS partido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_partido TEXT NOT NULL UNIQUE,
            nombre_partido TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS municipio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_dane TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            departamento TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS zona (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_zona TEXT NOT NULL,
            nombre TEXT NOT NULL DEFAULT '',
            municipio_id INTEGER NOT NULL,
            FOREIGN KEY (municipio_id) REFERENCES municipio(id),
            UNIQUE(codigo_zona, municipio_id)
        );

        CREATE TABLE IF NOT EXISTS puesto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_puesto TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            zona_id INTEGER NOT NULL,
            FOREIGN KEY (zona_id) REFERENCES zona(id)
        );

        CREATE TABLE IF NOT EXISTS mesa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_mesa TEXT NOT NULL UNIQUE,
            numero_mesa INTEGER NOT NULL,
            puesto_id INTEGER NOT NULL,
            FOREIGN KEY (puesto_id) REFERENCES puesto(id)
        );

        CREATE TABLE IF NOT EXISTS candidato (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_candidato TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            partido_id INTEGER NOT NULL,
            FOREIGN KEY (partido_id) REFERENCES partido(id),
            UNIQUE(codigo_candidato, partido_id)
        );

        CREATE TABLE IF NOT EXISTS resultados_votacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corporacion_id INTEGER NOT NULL,
            partido_id INTEGER NOT NULL,
            candidato_id INTEGER NOT NULL,
            municipio_id INTEGER NOT NULL,
            mesa_id INTEGER NOT NULL,
            votos INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (corporacion_id) REFERENCES corporacion(id),
            FOREIGN KEY (partido_id) REFERENCES partido(id),
            FOREIGN KEY (candidato_id) REFERENCES candidato(id),
            FOREIGN KEY (municipio_id) REFERENCES municipio(id),
            FOREIGN KEY (mesa_id) REFERENCES mesa(id),
            UNIQUE(corporacion_id, candidato_id, partido_id, mesa_id)
        );

        CREATE INDEX IF NOT EXISTS idx_candidato_partido ON candidato(partido_id);
        CREATE INDEX IF NOT EXISTS idx_resultados_corporacion ON resultados_votacion(corporacion_id);
        CREATE INDEX IF NOT EXISTS idx_resultados_partido ON resultados_votacion(partido_id);
        CREATE INDEX IF NOT EXISTS idx_resultados_candidato ON resultados_votacion(candidato_id);
        CREATE INDEX IF NOT EXISTS idx_resultados_municipio ON resultados_votacion(municipio_id);
        CREATE INDEX IF NOT EXISTS idx_resultados_mesa ON resultados_votacion(mesa_id);
    """)

    conn.executescript("""
        INSERT OR IGNORE INTO corporacion (codigo, nombre) VALUES ('SE', 'Senado');
        INSERT OR IGNORE INTO corporacion (codigo, nombre) VALUES ('CA', 'Camara');
    """)
    conn.commit()

    conn.execute("""
        INSERT OR IGNORE INTO partido (codigo_partido, nombre_partido)
        SELECT DISTINCT codigo_partido, partido FROM carga_log
    """)
    logger.info("Partidos migrados: %d", conn.execute("SELECT COUNT(*) FROM partido").fetchone()[0])

    conn.execute("""
        INSERT OR IGNORE INTO municipio (codigo_dane, nombre)
        SELECT DISTINCT codigo_dane_municipio, municipio FROM carga_log
    """)
    logger.info("Municipios migrados: %d", conn.execute("SELECT COUNT(*) FROM municipio").fetchone()[0])

    conn.execute("""
        INSERT OR IGNORE INTO zona (codigo_zona, nombre, municipio_id)
        SELECT DISTINCT cl.codigo_zona, cl.zona, m.id
        FROM carga_log cl
        JOIN municipio m ON m.codigo_dane = cl.codigo_dane_municipio
        WHERE cl.codigo_zona != ''
    """)
    logger.info("Zonas migradas: %d", conn.execute("SELECT COUNT(*) FROM zona").fetchone()[0])

    conn.execute("""
        INSERT OR IGNORE INTO puesto (codigo_puesto, nombre, zona_id)
        SELECT DISTINCT cl.codigo_puesto, cl.puesto, z.id
        FROM carga_log cl
        JOIN zona z ON z.codigo_zona = cl.codigo_zona
        WHERE cl.codigo_puesto != ''
    """)
    logger.info("Puestos migrados: %d", conn.execute("SELECT COUNT(*) FROM puesto").fetchone()[0])

    conn.execute("""
        INSERT OR IGNORE INTO mesa (codigo_mesa, numero_mesa, puesto_id)
        SELECT DISTINCT cl.codigo_mesa, cl.mesa, p.id
        FROM carga_log cl
        JOIN puesto p ON p.codigo_puesto = cl.codigo_puesto
        WHERE cl.codigo_mesa != ''
    """)
    logger.info("Mesas migradas: %d", conn.execute("SELECT COUNT(*) FROM mesa").fetchone()[0])

    conn.execute("""
        INSERT OR IGNORE INTO candidato (codigo_candidato, nombre_completo, partido_id)
        SELECT DISTINCT c.codigo_candidato, c.candidato, p.id
        FROM carga_log c
        JOIN partido p ON p.codigo_partido = c.codigo_partido
    """)
    logger.info("Candidatos migrados: %d", conn.execute("SELECT COUNT(*) FROM candidato").fetchone()[0])

    conn.execute("""
        INSERT OR IGNORE INTO resultados_votacion (corporacion_id, partido_id, candidato_id, municipio_id, mesa_id, votos)
        SELECT
            co.id,
            p.id,
            ca.id,
            m.id,
            me.id,
            cl.votos_obtenidos
        FROM carga_log cl
        JOIN corporacion co ON co.codigo = cl.corporacion
        JOIN partido p ON p.codigo_partido = cl.codigo_partido
        JOIN candidato ca ON ca.codigo_candidato = cl.codigo_candidato AND ca.partido_id = p.id
        JOIN municipio m ON m.codigo_dane = cl.codigo_dane_municipio
        JOIN mesa me ON me.codigo_mesa = cl.codigo_mesa
    """)
    logger.info("Resultados migrados: %d", conn.execute("SELECT COUNT(*) FROM resultados_votacion").fetchone()[0])

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()
    logger.info("Migracion completada exitosamente.")


if __name__ == "__main__":
    migrate()
