-- Tablas normalizadas para resultados electorales
-- Basado en la estructura actual de carga_log

CREATE TABLE IF NOT EXISTS corporacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE CHECK(codigo IN ('SE', 'CA')),
    nombre TEXT NOT NULL
);

INSERT OR IGNORE INTO corporacion (codigo, nombre) VALUES ('SE', 'Senado');
INSERT OR IGNORE INTO corporacion (codigo, nombre) VALUES ('CA', 'Camara');

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
    votos INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (corporacion_id) REFERENCES corporacion(id),
    FOREIGN KEY (partido_id) REFERENCES partido(id),
    FOREIGN KEY (candidato_id) REFERENCES candidato(id),
    FOREIGN KEY (municipio_id) REFERENCES municipio(id),
    UNIQUE(corporacion_id, candidato_id, partido_id, municipio_id)
);

CREATE INDEX IF NOT EXISTS idx_candidato_partido ON candidato(partido_id);
CREATE INDEX IF NOT EXISTS idx_resultados_corporacion ON resultados_votacion(corporacion_id);
CREATE INDEX IF NOT EXISTS idx_resultados_partido ON resultados_votacion(partido_id);
CREATE INDEX IF NOT EXISTS idx_resultados_candidato ON resultados_votacion(candidato_id);
CREATE INDEX IF NOT EXISTS idx_resultados_municipio ON resultados_votacion(municipio_id);
