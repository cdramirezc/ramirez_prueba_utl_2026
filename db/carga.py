import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "carga_log.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def insertar_resultado(corporacion, municipio, codigo_dane, zona, codigo_zona, puesto, codigo_puesto, mesa, codigo_mesa, partido, codigo_partido, candidato, codigo_candidato, votos):
    sql = """
        INSERT OR IGNORE INTO carga_log
            (corporacion, municipio, codigo_dane_municipio, zona, codigo_zona, puesto, codigo_puesto, mesa, codigo_mesa, partido, codigo_partido, candidato, codigo_candidato, votos_obtenidos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        conn = get_connection()
        cursor = conn.execute(sql, (corporacion, municipio, codigo_dane, zona, codigo_zona, puesto, codigo_puesto, mesa, codigo_mesa, partido, codigo_partido, candidato, codigo_candidato, votos))
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            logger.info("Saltado (duplicado): %s | %s | %s | %s | %s | mesa %d", corporacion, municipio, candidato, partido, codigo_mesa, mesa)
            return False
        logger.info("Insertado: %s | %s | mesa %d | %s | %s | %s votos", corporacion, municipio, mesa, candidato, partido, votos)
        return True
    except Exception as e:
        logger.error("Error insertando candidato '%s' en mesa %s: %s", candidato, codigo_mesa, e)
        return False
