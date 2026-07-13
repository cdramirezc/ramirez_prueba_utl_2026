import argparse
import logging
import os
import sys
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scraper import buscar_municipio_por_nomenclator, obtener_mesas_por_municipio
from db.carga import insertar_resultado

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

API_REGISTRADURIA_BASE_URL = "https://resultadospreccongreso2026.registraduria.gov.co"
CORPORACIONES = ("SENADO", "CAMARA")
CODIGO_API_CORPORACION = {"SENADO": "SE", "CAMARA": "CA"}

_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
    return _session


def obtener_resultado_municipio(municipios, preflight=False):
    nombres = {m.upper().strip() for m in municipios}
    saltados = 0
    logger.info("Iniciando scraper para %d municipio(s)", len(nombres))
    session = _get_session()

    for nombre in nombres:
        meta = buscar_municipio_por_nomenclator(nombre)
        if not meta:
            logger.warning("Municipio '%s' no encontrado en nomenclator", nombre)
            continue

        mesas = obtener_mesas_por_municipio(nombre)
        logger.info("Municipio '%s' tiene %d mesas", nombre, len(mesas))

        if preflight:
            total_solicitudes = len(mesas) * len(CORPORACIONES)
            logger.info("[PREFLIGHT] %s: %d mesas, %d solicitudes totales (SENADO + CAMARA)", nombre, len(mesas), total_solicitudes)
            continue

        for corporacion in CORPORACIONES:
            cod_corporacion = CODIGO_API_CORPORACION[corporacion]
            logger.info("Procesando corporacion: %s para %s", corporacion, nombre)

            for mesa_info in mesas:
                url = f"{API_REGISTRADURIA_BASE_URL}/json/ACT/{cod_corporacion}/{mesa_info['codigo_mesa']}.json"
                logger.info("Consultando %s - %s - mesa %d: %s", corporacion, nombre, mesa_info["mesa"], url)

                data = None
                for intento in range(3):
                    try:
                        resp = session.get(url, timeout=10)
                        if resp.status_code != 200:
                            logger.warning("HTTP %d para mesa %s (intento %d/3)", resp.status_code, mesa_info["codigo_mesa"], intento + 1)
                            if intento < 2:
                                time.sleep(2 ** intento)
                                continue
                            break
                        data = resp.json()
                        break
                    except (requests.RequestException, ValueError) as e:
                        logger.error("Error en mesa %s (intento %d/3): %s", mesa_info["codigo_mesa"], intento + 1, e)
                        if intento < 2:
                            time.sleep(2 ** intento)
                            continue
                        break

                if data is None:
                    continue

                for camara in data.get("camaras", []):
                    for partido in camara.get("partotabla", []):
                        act = partido.get("act", {})
                        candidatos_tabla = act.get("cantotabla", [])
                        nombre_partido = act.get("nompar", str(act.get("codpar", "")))
                        codigo_partido = act.get("codpar", "")

                        for candidato in candidatos_tabla:
                            nombre_completo = f"{candidato.get('nomcan', '')} {candidato.get('apecan', '')}".strip()
                            votos = int(candidato.get("vot", 0) or 0)
                            if not insertar_resultado(
                                corporacion=cod_corporacion,
                                municipio=nombre,
                                codigo_dane=meta["codigo"],
                                zona=mesa_info["zona"],
                                codigo_zona=mesa_info["codigo_zona"],
                                puesto=mesa_info["puesto"],
                                codigo_puesto=mesa_info["codigo_puesto"],
                                mesa=mesa_info["mesa"],
                                codigo_mesa=mesa_info["codigo_mesa"],
                                partido=nombre_partido,
                                codigo_partido=codigo_partido,
                                candidato=nombre_completo,
                                codigo_candidato=str(candidato.get("codcan", "")),
                                votos=votos,
                            ):
                                saltados += 1

    if not preflight:
        logger.info("Scraper finalizado. Total registros saltados (duplicados): %d", saltados)


def main():
    parser = argparse.ArgumentParser(description="Scraper de resultados electorales por mesa")
    parser.add_argument(
        "--municipios", "-m",
        nargs="+",
        default=["Paipa", "Duitama", "Tunja", "Sogamoso"],
        help="Uno o más municipios a consultar (ej: --municipios Tunja Paipa)",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Muestra conteo de mesas y solicitudes sin descargar datos",
    )
    args = parser.parse_args()
    obtener_resultado_municipio(args.municipios, preflight=args.preflight)


if __name__ == "__main__":
    main()
