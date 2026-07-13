-- Atribución Determinística (8 pts)
-- Top 5 candidatos por atribución CA → SE
--
-- Fórmula: A_ij = (votos_cand_CA / votos_partido_CA) × votos_SE_partido_homologado
--
-- Donde:
--   CA = Cámara de Representantes
--   SE = Senado (voto consolidado en los 4 municipios)
--   Homologación: los códigos de partido difieren entre CA y SE para la misma
--     colectividad (por ej. Alianza Verde usa codpar 57 en SE pero "Partido Verde"
--     codpar 5 en CA para Boyacá). El mapa incluye:
--       5  → 57  (Partido Verde / Alianza Verde)
--       87 → 92  (Partido 87 / Pacto Histórico)
--       2  → 2   (Conservador, identidad)
--       10 → 10  (Centro Democrático, identidad)
--       11 → 11  (identidad)
--       ... los demás CA-only generan atribución 0 (sin voto SE homologable)
--   "SOLO POR LA LISTA" se excluye del lado CA porque no representa un
--     candidato individual — son votos de lista sin preferencia nominal.
--
-- La atribución total del candidato es: (su fracción del partido en CA)
-- multiplicada por el voto consolidado del partido homologado en SE.

WITH homologacion AS (
    -- CA→SE: mapeo de códigos de partido
    SELECT '5' AS ca_codpar, '57' AS se_codpar, 'Alianza Verde' AS se_partido
    UNION ALL SELECT '87', '92', 'Pacto Histórico'
    -- Códigos compartidos (identidad)
    UNION ALL SELECT '2', '2', 'Partido Conservador Colombiano'
    UNION ALL SELECT '10', '10', 'Centro Democrático'
    UNION ALL SELECT '11', '11', 'Partido 11'
    UNION ALL SELECT '188', '188', 'Partido 188'
    UNION ALL SELECT '237', '237', 'Partido 237'
    UNION ALL SELECT '252', '252', 'Partido 252'
    UNION ALL SELECT '306', '306', 'Partido 306'
    UNION ALL SELECT '347', '347', 'Partido 347'
),
-- Votos por candidato en Cámara (CA), excluyendo SOLO POR LA LISTA
cand_ca AS (
    SELECT
        ca.id AS candidato_id,
        ca.nombre_completo AS candidato,
        p.codigo_partido AS ca_codpar,
        SUM(rv.votos) AS total_votos
    FROM resultados_votacion rv
    JOIN candidato ca ON ca.id = rv.candidato_id
    JOIN partido p ON p.id = ca.partido_id
    JOIN corporacion co ON co.id = rv.corporacion_id
    WHERE co.codigo = 'CA'
      AND ca.nombre_completo != 'SOLO POR LA LISTA'
    GROUP BY ca.id, ca.nombre_completo, p.codigo_partido
),
-- Total por partido en Cámara (CA)
partido_ca AS (
    SELECT
        p.codigo_partido AS ca_codpar,
        SUM(rv.votos) AS total_votos
    FROM resultados_votacion rv
    JOIN partido p ON p.id = rv.partido_id
    JOIN corporacion co ON co.id = rv.corporacion_id
    WHERE co.codigo = 'CA'
    GROUP BY p.codigo_partido
),
-- Votos por partido en Senado (SE), consolidado en los 4 municipios
partido_se AS (
    SELECT
        p.codigo_partido AS se_codpar,
        p.nombre_partido,
        SUM(rv.votos) AS total_votos
    FROM resultados_votacion rv
    JOIN partido p ON p.id = rv.partido_id
    JOIN corporacion co ON co.id = rv.corporacion_id
    WHERE co.codigo = 'SE'
    GROUP BY p.codigo_partido
)
SELECT
    cc.candidato,
    COALESCE(h.se_partido, ps.nombre_partido, 'Sin homologación SE') AS partido,
    ROUND(
        1.0 * cc.total_votos / pc.total_votos
        * COALESCE(ps.total_votos, 0),
        2
    ) AS atribucion
FROM cand_ca cc
JOIN partido_ca pc ON cc.ca_codpar = pc.ca_codpar
LEFT JOIN homologacion h ON cc.ca_codpar = h.ca_codpar
LEFT JOIN partido_se ps ON COALESCE(h.se_codpar, cc.ca_codpar) = ps.se_codpar
WHERE pc.total_votos > 0
ORDER BY atribucion DESC
LIMIT 5;

-- Bonus (+2): Por qué el top CA no coincide con el top de atribución.
-- Un partido con lista SE fuerte (ej. Alianza Verde, 7188 votos SE)
-- infla la atribución de sus candidatos CA medianos aunque su cuota
-- CA individual sea modesta. A la inversa, un candidato CA muy votado
-- de un partido con poco arrastre SE (ej. Partido 121 con 0 votos SE
-- homologables) obtendrá atribución nula, quedando fuera del top 5.
