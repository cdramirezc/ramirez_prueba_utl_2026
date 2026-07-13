-- ============================================================
-- Schema de puestos_2026.db — Pipeline Electoral Boyacá 2026
-- Generado automáticamente desde sqlite_master
-- ============================================================

-- Catálogo de candidatos único por codigo_candidato + partido_id
CREATE TABLE candidato (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_candidato TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            partido_id INTEGER NOT NULL,
            FOREIGN KEY (partido_id) REFERENCES partido(id),
            UNIQUE(codigo_candidato, partido_id)
        );

-- Tabla plana: datos crudos descargados por el scraper, uno por fila candidato-mesa
CREATE TABLE carga_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corporacion TEXT NOT NULL CHECK(corporacion IN ('SE', 'CA')),
    municipio TEXT NOT NULL,
    codigo_dane_municipio TEXT NOT NULL,
    zona TEXT NOT NULL DEFAULT '',
    codigo_zona TEXT NOT NULL DEFAULT '',
    puesto TEXT NOT NULL DEFAULT '',
    codigo_puesto TEXT NOT NULL DEFAULT '',
    mesa INTEGER NOT NULL DEFAULT 0,
    codigo_mesa TEXT NOT NULL DEFAULT '',
    partido TEXT NOT NULL,
    codigo_partido TEXT NOT NULL,
    candidato TEXT NOT NULL,
    codigo_candidato TEXT NOT NULL,
    votos_obtenidos INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'no procesado',
    UNIQUE(codigo_candidato, codigo_partido, codigo_mesa, corporacion)
);

-- Corporaciones electorales: SE (Senado) y CA (Camara)
CREATE TABLE corporacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE CHECK(codigo IN ('SE', 'CA')),
            nombre TEXT NOT NULL
        );

-- Mesas de votación, pertenecen a un puesto
CREATE TABLE mesa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_mesa TEXT NOT NULL UNIQUE,
            numero_mesa INTEGER NOT NULL,
            puesto_id INTEGER NOT NULL,
            FOREIGN KEY (puesto_id) REFERENCES puesto(id)
        );

-- Municipios con código DANE, incluye departamento
CREATE TABLE municipio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_dane TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            departamento TEXT NOT NULL DEFAULT ''
        );

-- Partidos políticos con código único de la Registraduría
CREATE TABLE partido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_partido TEXT NOT NULL UNIQUE,
            nombre_partido TEXT NOT NULL
        );

-- Puestos de votación, pertenecen a una zona
CREATE TABLE puesto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_puesto TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            zona_id INTEGER NOT NULL,
            FOREIGN KEY (zona_id) REFERENCES zona(id)
        );

-- Hechos: votos por corporacion-partido-candidato-municipio-mesa
CREATE TABLE resultados_votacion (
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

-- Zonas electorales, pertenecen a un municipio
CREATE TABLE zona (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_zona TEXT NOT NULL,
            nombre TEXT NOT NULL DEFAULT '',
            municipio_id INTEGER NOT NULL,
            FOREIGN KEY (municipio_id) REFERENCES municipio(id),
            UNIQUE(codigo_zona, municipio_id)
        );

-- ============================================================
-- Índices explícitos
-- ============================================================

-- Optimiza JOIN candidato → partido en consultas de agrupación por partido
CREATE INDEX idx_candidato_partido ON candidato(partido_id);

-- Optimiza filtro y GROUP BY por candidato (top candidatos, atribución)
CREATE INDEX idx_resultados_candidato ON resultados_votacion(candidato_id);

-- Optimiza filtro por corporacion (SE/CA) en consultas analíticas
CREATE INDEX idx_resultados_corporacion ON resultados_votacion(corporacion_id);

-- Optimiza JOIN resultados → mesa (scatter por mesa, arrastre por puesto)
CREATE INDEX idx_resultados_mesa ON resultados_votacion(mesa_id);

-- Optimiza JOIN y GROUP BY por municipio (dashboard, heatmap)
CREATE INDEX idx_resultados_municipio ON resultados_votacion(municipio_id);

-- Optimiza JOIN y filtro por partido en consultas de arrastre y atribución
CREATE INDEX idx_resultados_partido ON resultados_votacion(partido_id);

