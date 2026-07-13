# ramirez_prueba_utl_2026

## Candidato

| Campo | Valor |
|-------|-------|
| Nombre | CESAR RAMIREZ |
| Email | cesar.rcely@gmail.com |
| Repo | https://github.com/cdramirezc/ramirez_prueba_utl_2026 |
| Fecha | 2026-07-13 |

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Dependencias: `requests`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`.

## Pipeline de ejecución

```bash
python scraper/scraper.py --municipios Tunja Paipa Sogamoso Duitama
python db/etl.py
python dashboard/export_data.py
python viz/heatmap.py
python viz/scatter.py
python outputs/generar_manifest.py
```

El scraper descarga resultados por mesa y corporacion (`/json/ACT/{SE|CA}/{codigo_mesa}.json`) insertando en `carga_log` con `INSERT OR IGNORE`. El ETL migra a modelo normalizado (`resultados_votacion`, `mesa`, `puesto`, `zona`, `municipio`, `partido`, `candidato`, `corporacion`). Las consultas SQL en `sql/` responden a las tareas analíticas. Las visualizaciones y el dashboard se regeneran desde `export_data.py`.

## API desde el código real

Endpoint de resultados: `https://resultadospreccongreso2026.registraduria.gov.co/json/ACT/{SE|CA}/{codigo_mesa}.json`

El nomenclátor (departamentos, municipios, zonas, puestos, mesas) se descarga de `https://resultadospreccongreso2026.registraduria.gov.co/json/nomenclator.json` y se cachea en `outputs/nomenclator.json`.

Campos del JSON de respuesta por mesa (8+):

| Campo | Ruta | Significado |
|-------|------|-------------|
| `codpar` | `camaras[].partotabla[].act.codpar` | Código numérico del partido (ej. `"57"` = Alianza Verde) |
| `nompar` | `camaras[].partotabla[].act.nompar` | Nombre del partido (puede omitirse) |
| `cantotabla[]` | `camaras[].partotabla[].act.cantotabla` | Arreglo de candidatos del partido |
| `codcan` | `cantotabla[].codcan` | Código del candidato |
| `nomcan` | `cantotabla[].nomcan` | Nombre del candidato |
| `apecan` | `cantotabla[].apecan` | Apellido del candidato |
| `vot` | `cantotabla[].vot` | Votos obtenidos por el candidato en esa mesa |
| `camaras[].i` | `camaras[].i` | Índice de cámara (0=Nacional/SE, 1=Territorial/CA) |

Cabeceras HTTP: `User-Agent` por defecto de `requests`, sin autenticación. La API es pública.

El scraper (`core/scraper.py`) resuelve el código DANE y la lista completa de mesas recorriendo el árbol del nomenclátor (departamento `l=2` → municipio `l=3` → zona `l=4` → puesto `l=6` → mesas por `puesto.m`). Cada código de mesa se construye como `codigo_puesto + str(numero).zfill(6)`.

## Municipios en la BD

Cuatro municipios de Boyacá (Duitama, Paipa, Sogamoso, Tunja). Matriz final de cobertura (mesas en nomenclátor / carga_log / resultados_votacion):

| Municipio | Corp | NOM | carga_log | res_vot | Cobertura | Filas |
|-----------|------|-----|-----------|---------|-----------|-------|
| DUITAMA | CA | 287 | 279 | 279 | 97.2% | 73.626 |
| DUITAMA | SE | 287 | 69 | 69 | 24.0% | 75.166 |
| PAIPA | CA | 95 | 92 | 92 | 96.8% | 24.288 |
| PAIPA | SE | 95 | 49 | 49 | 51.6% | 50.291 |
| SOGAMOSO | CA | 301 | 288 | 288 | 95.7% | 76.031 |
| SOGAMOSO | SE | 301 | 2 | 2 | 0.7% | 1.363 |
| TUNJA | CA | 424 | 150 | 150 | 35.4% | 39.400 |
| TUNJA | SE | 424 | 130 | 130 | 30.7% | 141.528 |

**Total**: 1.107 mesas en nomenclátor, 817 en modelo, 481.688 filas en `resultados_votacion`.

## Hallazgos principales

**Correlación CA-SE**: `r=0.872 | pendiente=0.884 | n_mesas=242`. La pendiente menor a 1 indica que por cada voto adicional en Cámara se obtienen ~0.88 votos en Senado, consistente con el mayor número de listas en Senado que dispersan el voto. El n subió de 197 a 242 tras rescatar 47 mesas SE de Paipa.

**Atribución determinística (tarea 3.3)** — Los 3 primeros del top 5 son candidatos de Alianza Verde (homologación CA codpar 5 → SE codpar 57) porque el partido acumula 9.270 votos SE en los 4 municipios, los cuales se reponderan según la fracción de cada candidato en Cámara. "SOLO POR LA LISTA" se excluye del lado CA porque no representa un candidato individual sino voto de lista sin preferencia nominal. Top 5:

1. YAMIT NOE HURTADO NEIRA (Alianza Verde) — 2.950,26
2. JAIME RAUL SALAMANCA TORRES (Alianza Verde) — 2.299,51
3. RAMIRO BARRAGAN ADAME (Alianza Verde) — 2.066,60
4. HECTOR DAVID CHAPARRO CHAPARRO (Conservador) — 1.953,87
5. EDUAR ALEXIS TRIANA RINCON (Centro Democrático) — 1.621,62

**Arrastre Verde (tarea 3.1)** — Alianza Verde lidera el voto SE en PAIPA (2.169 votos, 3 puestos con ratios 0.31, 0.27, 0.24). En TUNJA tiene 7 puestos con ratios entre 0.12 y 0.24; Pacto Histórico lidera (6.225 votos). En DUITAMA el líder es Pacto Histórico (3.539); Verde tiene 5 puestos con ratios 0.14-0.19. En SOGAMOSO SE solo hay 2 mesas (cobertura 0.7%), insuficiente para arrastre.

**Episodio de cobertura** — La pasada SE original se ejecutó sin reintentos, dejando huecos silenciosos detectados mediante dos heurísticas: (1) densidad anómala: TUNJA presentaba 180.928 filas / 155 mesas ≈ 1.167 (vs. ~260 esperado), señal de que filas de mesas faltantes se concentraban en las pocas mesas scrapeadas; (2) validación contra nomenclátor: la cobertura real era 155/424 = 36%. El rescate con pool de 6 hilos recuperó 47 mesas SE de Paipa (pasando de 2 a 49), subiendo la cobertura SE de Paipa de 2% a 52%. [TODO: el autor debe detallar aquí cómo verificó que las 47 mesas recuperadas pertenecen a puestos no cubiertos originalmente y cómo validó la consistencia de votos contra las mesas CA existentes.]

## Bonus implementados

- **Preflight** (`scraper/scraper.py --preflight`): cuenta mesas y solicitudes totales por municipio sin descargar, útil para estimar tiempo antes de lanzar el scrape masivo.
- **Índices justificados** (`db/schema.sql`): 6 índices en `resultados_votacion` (corporacion_id, partido_id, candidato_id, municipio_id, mesa_id) y 1 en `candidato(partido_id)`, cada uno con comentario explicando la consulta que optimiza.
- **Explicación del bonus de 3.3** incrustada en `sql/tarea_3_3.sql` (líneas 92-97): detalla por qué el top CA no coincide con el top de atribución (un partido con lista SE fuerte infla la atribución de sus candidatos CA).
- **Dark mode** en `dashboard/index.html` (CSS `[data-theme="dark"]` + botón toggle, 31 variables CSS para cards, fondos, textos y bordes).
- **Exportación CSV** en dashboard (`exportCSV()`): descarga el top 10 del municipio seleccionado como archivo CSV codificado UTF-8 BOM.

[TODO: LINK RELEASE]
