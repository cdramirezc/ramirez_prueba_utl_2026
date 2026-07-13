import sqlite3
import os
import logging
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "puestos_2026.db")

# Mapa partido: codigo -> nombre legible
PARTIDO_NOMBRES = {
    "1": "Partido 1", "2": "Partido Conservador Colombiano", "3": "Partido Cambio Radical",
    "5": "Partido Verde", "6": "ASI", "9": "Partido 9", "10": "Centro Democrático",
    "11": "Partido 11", "17": "Dignidad & Compromiso", "18": "Partido 18",
    "33": "Partido 33", "34": "Partido 34", "39": "Partido 39", "40": "Partido 40",
    "43": "Partido 43", "44": "Partido 44", "55": "Partido 55", "57": "Alianza Verde",
    "87": "Partido 87", "92": "Pacto Histórico", "170": "Partido 170",
    "188": "Partido 188", "234": "Partido 234", "237": "Partido 237",
    "252": "Partido 252", "285": "Partido 285", "300": "Frente por la Vida",
    "306": "Partido 306", "347": "Partido 347",
}

# Mapa departamento por codigo_dane (primeros 2 digitos = depto)
# Obtenido de core/scraper.py via nomenclator
_DEPTO_CACHE = None


def _cargar_departamentos():
    global _DEPTO_CACHE
    if _DEPTO_CACHE is not None:
        return _DEPTO_CACHE
    try:
        from core.scraper import _cargar_codigos_internos
        codigos = _cargar_codigos_internos()
        _DEPTO_CACHE = {}
        for nombre, info in codigos.items():
            _DEPTO_CACHE[nombre.upper()] = info.get("departamento", "")
    except Exception:
        _DEPTO_CACHE = {}
    return _DEPTO_CACHE


def _nombre_partido(codigo, nombre_original):
    nombre_limpio = nombre_original.strip()
    if nombre_limpio.isdigit() and nombre_limpio in PARTIDO_NOMBRES:
        return PARTIDO_NOMBRES[nombre_limpio]
    if nombre_limpio.isdigit():
        return f"Partido {nombre_limpio}"
    return nombre_limpio


def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM carga_log")
    total_carga = c.fetchone()[0]
    logger.info("Total registros en carga_log: %d", total_carga)

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

    # Partidos con nombres legibles
    c.execute("""
        INSERT OR IGNORE INTO partido (codigo_partido, nombre_partido)
        SELECT DISTINCT codigo_partido, partido FROM carga_log
    """)
    partidos_migrados = c.execute("SELECT COUNT(*) FROM partido").fetchone()[0]
    c.execute("SELECT codigo_partido, nombre_partido FROM partido")
    for codigo, nombre in c.fetchall():
        nombre_nuevo = _nombre_partido(codigo, nombre)
        if nombre_nuevo != nombre:
            c.execute("UPDATE partido SET nombre_partido=? WHERE codigo_partido=?", (nombre_nuevo, codigo))
    conn.commit()
    logger.info("Partidos migrados: %d (nuevos) | omitidos: 0 | nombres resueltos", partidos_migrados)

    # Municipios con departamento desde nomenclator
    deptos = _cargar_departamentos()
    c.execute("""
        INSERT OR IGNORE INTO municipio (codigo_dane, nombre)
        SELECT DISTINCT codigo_dane_municipio, municipio FROM carga_log
    """)
    muns_migrados = c.execute("SELECT COUNT(*) FROM municipio").fetchone()[0]
    for row in c.execute("SELECT id, nombre, codigo_dane FROM municipio WHERE departamento=''").fetchall():
        mid, mnombre, codigo = row
        depto = deptos.get(mnombre.upper(), "")
        if depto:
            c.execute("UPDATE municipio SET departamento=? WHERE id=?", (depto, mid))
    conn.commit()
    logger.info("Municipios migrados: %d (nuevos) | omitidos: 0 | departamento poblado desde nomenclator", muns_migrados)

    c.execute("""
        INSERT OR IGNORE INTO zona (codigo_zona, nombre, municipio_id)
        SELECT DISTINCT cl.codigo_zona, cl.zona, m.id
        FROM carga_log cl
        JOIN municipio m ON m.codigo_dane = cl.codigo_dane_municipio
        WHERE cl.codigo_zona != ''
    """)
    logger.info("Zonas migradas: %d (nuevas)", c.execute("SELECT COUNT(*) FROM zona").fetchone()[0])

    c.execute("""
        INSERT OR IGNORE INTO puesto (codigo_puesto, nombre, zona_id)
        SELECT DISTINCT cl.codigo_puesto, cl.puesto, z.id
        FROM carga_log cl
        JOIN zona z ON z.codigo_zona = cl.codigo_zona
        WHERE cl.codigo_puesto != ''
    """)
    logger.info("Puestos migrados: %d (nuevos)", c.execute("SELECT COUNT(*) FROM puesto").fetchone()[0])

    c.execute("""
        INSERT OR IGNORE INTO mesa (codigo_mesa, numero_mesa, puesto_id)
        SELECT DISTINCT cl.codigo_mesa, cl.mesa, p.id
        FROM carga_log cl
        JOIN puesto p ON p.codigo_puesto = cl.codigo_puesto
        WHERE cl.codigo_mesa != ''
    """)
    logger.info("Mesas migradas: %d (nuevas)", c.execute("SELECT COUNT(*) FROM mesa").fetchone()[0])

    c.execute("""
        INSERT OR IGNORE INTO candidato (codigo_candidato, nombre_completo, partido_id)
        SELECT DISTINCT c.codigo_candidato, c.candidato, p.id
        FROM carga_log c
        JOIN partido p ON p.codigo_partido = c.codigo_partido
    """)
    logger.info("Candidatos migrados: %d (nuevos)", c.execute("SELECT COUNT(*) FROM candidato").fetchone()[0])

    c.execute("""
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
    resultados = c.execute("SELECT COUNT(*) FROM resultados_votacion").fetchone()[0]
    excedentes = resultados - total_carga if resultados > total_carga else 0
    omitidos = total_carga - resultados if total_carga > resultados else 0
    if excedentes > 0:
        logger.info("Resultados migrados: %d | carga_log: %d | excedentes por JOIN: %d (verificar duplicados en mesa)", resultados, total_carga, excedentes)
    else:
        logger.info("Resultados migrados: %d (insertados) | omitidos (sin match): %d", resultados, omitidos)

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()
    logger.info("Migracion completada exitosamente.")


if __name__ == "__main__":
    migrate()
