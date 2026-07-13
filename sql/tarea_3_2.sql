WITH
total_partido_mesa AS (
    SELECT
        rv.mesa_id,
        rv.partido_id,
        rv.corporacion_id,
        SUM(rv.votos) AS total_votos_partido
    FROM resultados_votacion rv
    GROUP BY rv.mesa_id, rv.partido_id, rv.corporacion_id
),
candidato_mesa AS (
    SELECT
        rv.mesa_id,
        rv.partido_id,
        rv.corporacion_id,
        rv.candidato_id,
        rv.votos AS votos_candidato,
        tpm.total_votos_partido,
        ROUND(CAST(rv.votos AS REAL) / tpm.total_votos_partido * 100, 2) AS porcentaje
    FROM resultados_votacion rv
    INNER JOIN total_partido_mesa tpm
        ON tpm.mesa_id = rv.mesa_id
        AND tpm.partido_id = rv.partido_id
        AND tpm.corporacion_id = rv.corporacion_id
    WHERE tpm.total_votos_partido > 0
)
SELECT
    cm.mesa_id,
    m.codigo_mesa,
    m.numero_mesa,
    pu.nombre AS puesto,
    z.nombre AS zona,
    mun.nombre AS municipio,
    mun.departamento,
    p.nombre_partido,
    p.codigo_partido,
    c.nombre_completo AS candidato,
    c.codigo_candidato,
    co.nombre AS corporacion,
    cm.votos_candidato,
    cm.total_votos_partido,
    cm.porcentaje
FROM candidato_mesa cm
INNER JOIN candidato c ON c.id = cm.candidato_id
INNER JOIN partido p ON p.id = cm.partido_id
INNER JOIN corporacion co ON co.id = cm.corporacion_id
INNER JOIN mesa m ON m.id = cm.mesa_id
INNER JOIN puesto pu ON pu.id = m.puesto_id
INNER JOIN zona z ON z.id = pu.zona_id
INNER JOIN municipio mun ON mun.id = z.municipio_id
WHERE cm.porcentaje > 60
ORDER BY cm.porcentaje DESC;