-- Arrastre Verde CA->SE (9 pts)
-- Ratio votos_SE_Verde / votos_CA_Verde por puesto y municipio
-- Homologacion: codpar_CA=5 → codpar_SE=57

WITH votos_se AS (
    SELECT
        m.nombre AS municipio,
        p.codigo_puesto AS codigo_puesto,
        p.nombre AS nombre_puesto,
        SUM(rv.votos) AS votos
    FROM resultados_votacion rv
    JOIN corporacion co ON co.id = rv.corporacion_id
    JOIN partido pa ON pa.id = rv.partido_id
    JOIN municipio m ON m.id = rv.municipio_id
    JOIN mesa me ON me.id = rv.mesa_id
    JOIN puesto p ON p.id = me.puesto_id
    WHERE (pa.nombre_partido = ?1 OR pa.codigo_partido = ?1)
      AND co.codigo = 'SE'
    GROUP BY m.nombre, p.codigo_puesto, p.nombre
),
votos_ca AS (
    SELECT
        m.nombre AS municipio,
        p.codigo_puesto AS codigo_puesto,
        p.nombre AS nombre_puesto,
        SUM(rv.votos) AS votos
    FROM resultados_votacion rv
    JOIN corporacion co ON co.id = rv.corporacion_id
    JOIN partido pa ON pa.id = rv.partido_id
    JOIN municipio m ON m.id = rv.municipio_id
    JOIN mesa me ON me.id = rv.mesa_id
    JOIN puesto p ON p.id = me.puesto_id
    WHERE (pa.nombre_partido = ?2 OR pa.codigo_partido = ?2)
      AND co.codigo = 'CA'
    GROUP BY m.nombre, p.codigo_puesto, p.nombre
),
combinado AS (
    SELECT municipio, codigo_puesto, nombre_puesto, votos AS votos_se, 0 AS votos_ca
    FROM votos_se
    UNION ALL
    SELECT municipio, codigo_puesto, nombre_puesto, 0 AS votos_se, votos AS votos_ca
    FROM votos_ca
)
SELECT
    municipio,
    codigo_puesto,
    MAX(nombre_puesto) AS nombre_puesto,
    MAX(votos_se) AS votos_senado,
    MAX(votos_ca) AS votos_camara,
    CASE
        WHEN MAX(votos_ca) > 0
        THEN ROUND(1.0 * MAX(votos_se) / MAX(votos_ca), 4)
        ELSE NULL
    END AS arrastre
FROM combinado
GROUP BY municipio, codigo_puesto
ORDER BY municipio, codigo_puesto;