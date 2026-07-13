# ramirez_prueba_utl_2026

## Candidato

## Instalación

1. Clonar el repositorio.
2. Crear un entorno virtual e instalarlo con las dependencias del archivo `requirements.txt`:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

Dependencias principales: `requests`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`.

## Pipeline de ejecución

1. **Scraper** (`scraper/scraper.py`): consulta el nomenclátor de la Registraduría (`core/scraper.py`) para resolver el código DANE del municipio y todas sus mesas, y luego descarga el resultado por mesa (`/json/ACT/{SE|CA}/{codigo_mesa}.json`) para las corporaciones Senado (SE) y Cámara (CA). El nomenclátor se cachea en `outputs/nomenclator.json` para no volver a descargarlo.

   ```bash
   python scraper/scraper.py --municipios Tunja Paipa Sogamoso
   ```

2. **Carga** (`db/carga.py`): cada registro obtenido por el scraper se inserta en la tabla `carga_log` de `carga_log.db` (SQLite), evitando duplicados mediante una restricción `UNIQUE(codigo_candidato, codigo_partido, codigo_mesa, corporacion)`.

3. **ETL** (`db/etl.py`): migra los datos planos de `carga_log` hacia un modelo normalizado (tablas `corporacion`, `partido`, `municipio`, `zona`, `puesto`, `mesa`, `candidato` y `resultados_votacion`).

   ```bash
   python db/etl.py
   ```

4. **Consultas SQL** (carpeta `sql/`): `tarea_3_1.sql`, `tarea_3_2.sql` y `tarea_3_3.sql` corren contra el modelo normalizado.

5. **Visualizaciones** (carpeta `viz/`): `heatmap_municipios.py` y `scatter_ca_se.py` leen `carga_log.db` y generan las imágenes `heatmap_municipios.png` y `scatter_ca_se.png`.

6. **Dashboard** (carpeta `dashboard/`): `index.html` + `app.js` (Plotly y Chart.js) para visualizar los resultados en el navegador.

## API

El proyecto consume la API pública de resultados de la Registraduría Nacional:

- Nomenclátor (departamentos, municipios, zonas, puestos y mesas): `https://resultadospreccongreso2026.registraduria.gov.co/json/nomenclator.json`
- Resultados por mesa y corporación: `https://resultadospreccongreso2026.registraduria.gov.co/json/ACT/{SE|CA}/{codigo_mesa}.json`

Donde `SE` corresponde a Senado y `CA` a Cámara.

## Municipios en la BD

La base de datos (`carga_log.db`) contiene actualmente datos de prueba scrapeados para 3 municipios de Boyacá:

- Tunja
- Paipa
- Sogamoso

## Hallazgos principales

- `carga_log` almacena 281,811 registros crudos (Tunja, Paipa, Sogamoso; Senado y Cámara), de los cuales 217,821 quedan efectivamente vinculados en el modelo normalizado (`resultados_votacion`) tras la migración.
- La opción "SOLO POR LA LISTA" (voto solo por el partido, sin candidato) aparece en 37,758 registros y, al calcular la atribución determinística de votos de Senado (`sql/tarea_3_3.sql`), ocupa los 2 primeros lugares del top 5 (partidos con código `92` y `10`), por delante de cualquier candidato individual.
- Con el criterio de concentración de voto por mesa (`sql/tarea_3_2.sql`, candidato con más del 60% de los votos de su partido en una mesa), se identifican 1,919 combinaciones candidato-mesa que cumplen esa condición.
- El campo `departamento` de la tabla `municipio` queda vacío tras la migración: el script `db/etl.py` no lo puebla al insertar los municipios, aunque el scraper (`core/scraper.py`) sí lo obtiene del nomenclátor.
- En varios registros el nombre del partido (`partido`/`nombre_partido`) corresponde solo al código numérico (p. ej. `"5"`, `"57"`) en lugar de un nombre legible, porque el scraper usa `act.get("nompar", str(act.get("codpar", "")))` y la API no siempre trae `nompar`.

## Bonus implementados

- Visualizaciones exploratorias en `viz/`: heatmap del % de votos por municipio para los 8 principales candidatos a Cámara (`heatmap_municipios.py`) y dispersión Cámara vs. Senado por mesa con regresión OLS y coeficiente de Pearson (`scatter_ca_se.py`).
- Dashboard interactivo en `dashboard/` (HTML + JS con Plotly y Chart.js) con comparativo de votos por municipio, top de candidatos por municipio y ratio de arrastre de Alianza Verde por puesto.
