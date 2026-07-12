CREATE TABLE IF NOT EXISTS carga_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corporacion TEXT NOT NULL CHECK(corporacion IN ('SE', 'CA')),
    municipio TEXT NOT NULL,
    codigo_dane_municipio TEXT NOT NULL,
    partido TEXT NOT NULL,
    codigo_partido TEXT NOT NULL,
    candidato TEXT NOT NULL,
    codigo_candidato TEXT NOT NULL,
    votos_obtenidos INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'no procesado',
    UNIQUE(codigo_candidato, codigo_partido, codigo_dane_municipio, corporacion)
);
