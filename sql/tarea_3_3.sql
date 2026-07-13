-- Atribución Determinística (8 pts)
-- Top 5 candidatos por atribución SE consolidada
--
-- Fórmula: A_ij = (votos_cand / votos_partido) * votos_SE_partido
--
-- Donde:
--   SE = Sección Electoral (municipio)
--   votos_cand       = total votos del candidato i en Senado
--   votos_partido    = total votos del partido j en Senado
--   votos_SE_partido = votos del partido j en la SE (municipio) específica
--
-- La atribución total del candidato es la suma de A_ij en todas las SE.

WITH votos_candidato AS (
    SELECT
        c.id AS candidato_id,
        c.nombre_completo AS candidato,
        p.id AS partido_id,
        p.nombre_partido AS partido,
        SUM(rv.votos) AS total_votos
    FROM resultados_votacion rv
    JOIN candidato c ON c.id = rv.candidato_id
    JOIN partido p ON p.id = c.partido_id
    JOIN corporacion co ON co.id = rv.corporacion_id
    WHERE co.codigo = 'SE'
    GROUP BY c.id, c.nombre_completo, p.id, p.nombre_partido
),
votos_partido AS (
    SELECT
        p.id AS partido_id,
        p.nombre_partido AS partido,
        SUM(rv.votos) AS total_votos
    FROM resultados_votacion rv
    JOIN partido p ON p.id = rv.partido_id
    JOIN corporacion co ON co.id = rv.corporacion_id
    WHERE co.codigo = 'SE'
    GROUP BY p.id, p.nombre_partido
),
votos_partido_se AS (
    SELECT
        p.id AS partido_id,
        m.id AS seccion_id,
        m.nombre AS seccion,
        SUM(rv.votos) AS votos_se
    FROM resultados_votacion rv
    JOIN partido p ON p.id = rv.partido_id
    JOIN municipio m ON m.id = rv.municipio_id
    JOIN corporacion co ON co.id = rv.corporacion_id
    WHERE co.codigo = 'SE'
    GROUP BY p.id, m.id, m.nombre
),
atribucion AS (
    SELECT
        vc.candidato_id,
        vc.candidato,
        vc.partido,
        vps.seccion,
        ROUND(1.0 * vc.total_votos / vp.total_votos * vps.votos_se, 2) AS atribucion
    FROM votos_candidato vc
    JOIN votos_partido vp ON vc.partido_id = vp.partido_id
    JOIN votos_partido_se vps ON vc.partido_id = vps.partido_id
)
SELECT
    candidato,
    partido,
    ROUND(SUM(atribucion), 2) AS atribucion_total
FROM atribucion
GROUP BY candidato_id, candidato, partido
ORDER BY atribucion_total DESC
LIMIT 5;