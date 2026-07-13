import argparse
import logging
import os
import sys

import requests

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


def obtener_resultado_municipio(municipios):
    nombres = {m.upper().strip() for m in municipios}
    saltados = 0
    logger.info("Iniciando scraper para %d municipio(s)", len(nombres))

    for nombre in nombres:
        meta = buscar_municipio_por_nomenclator(nombre)
        if not meta:
            logger.warning("Municipio '%s' no encontrado en nomenclator", nombre)
            continue

        mesas = obtener_mesas_por_municipio(nombre)
        logger.info("Municipio '%s' tiene %d mesas", nombre, len(mesas))

        for corporacion in CORPORACIONES:
            cod_corporacion = CODIGO_API_CORPORACION[corporacion]
            logger.info("Procesando corporacion: %s para %s", corporacion, nombre)

            for mesa_info in mesas:
                url = f"{API_REGISTRADURIA_BASE_URL}/json/ACT/{cod_corporacion}/{mesa_info['codigo_mesa']}.json"
                logger.info("Consultando %s - %s - mesa %d: %s", corporacion, nombre, mesa_info["mesa"], url)

                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code != 200:
                        logger.warning("HTTP %d para mesa %s", resp.status_code, mesa_info["codigo_mesa"])
                        continue
                    data = resp.json()
                except requests.RequestException as e:
                    logger.error("Error de conexion mesa %s: %s", mesa_info["codigo_mesa"], e)
                    continue
                except ValueError as e:
                    logger.error("Error decodificando JSON mesa %s: %s", mesa_info["codigo_mesa"], e)
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

    logger.info("Scraper finalizado. Total registros saltados (duplicados): %d", saltados)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de resultados electorales por mesa")
    parser.add_argument(
        "--municipios", "-m",
        nargs="+",
        default=["Tunja"],
        help="Uno o más municipios a consultar (ej: --municipios Tunja Bogota Medellin)",
    )
    args = parser.parse_args()
    obtener_resultado_municipio(args.municipios)
