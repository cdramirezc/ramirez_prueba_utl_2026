import argparse
import logging
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scraper import buscar_municipio_por_nomenclator
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
    resultados = {}
    saltados = 0
    logger.info("Iniciando scraper para %d municipio(s)", len(nombres))

    for corporacion in CORPORACIONES:
        logger.info("Procesando corporacion: %s", corporacion)
        for nombre in nombres:
            meta = buscar_municipio_por_nomenclator(nombre)
            if not meta:
                logger.warning("Municipio '%s' no encontrado en nomenclator", nombre)
                continue

            cod_corporacion = CODIGO_API_CORPORACION[corporacion]
            url = f"{API_REGISTRADURIA_BASE_URL}/json/ACT/{cod_corporacion}/{meta['codigo']}.json"
            logger.info("Consultando %s - %s: %s", corporacion, nombre, url)

            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    logger.warning("HTTP %d para %s - %s", resp.status_code, corporacion, nombre)
                    continue
                data = resp.json()
                logger.info("Respuesta OK para %s - %s", corporacion, nombre)
            except requests.RequestException as e:
                logger.error("Error de conexion para %s - %s: %s", corporacion, nombre, e)
                continue
            except ValueError as e:
                logger.error("Error decodificando JSON para %s - %s: %s", corporacion, nombre, e)
                continue

            for cam in data.get("camaras", []):
                for mun in cam.get("mapagan", []):
                    nombre_resp = (mun.get("nombre") or "").upper().strip()
                    if nombre_resp != nombre:
                        continue

                    amb = mun.get("amb", "")
                    if nombre not in resultados:
                        resultados[nombre] = {"_meta": meta}

                    if corporacion not in resultados[nombre]:
                        resultados[nombre][corporacion] = []

                    partidos = []
                    for partido in cam.get("partotabla", []):
                        act = partido.get("act", {})
                        cantotabla = act.get("cantotabla", [])

                        nombre_partido = act.get("nompar", str(act.get("codpar", "")))
                        codigo_partido = act.get("codpar", "")

                        candidatos = []
                        for c in cantotabla:
                            nombre_completo = f"{c.get('nomcan', '')} {c.get('apecan', '')}".strip()
                            candidato_data = {
                                "codigo": c.get("codcan"),
                                "nombre_completo": nombre_completo,
                                "cedula": c.get("cedula"),
                                "votos": c.get("vot"),
                                "porcentaje": c.get("pvot"),
                                "voto_preferente": c.get("pref"),
                            }
                            candidatos.append(candidato_data)

                            votos = int(c.get("vot", 0) or 0)
                            if not insertar_resultado(
                                corporacion=cod_corporacion,
                                municipio=nombre,
                                codigo_dane=meta["codigo"],
                                partido=nombre_partido,
                                codigo_partido=codigo_partido,
                                candidato=nombre_completo,
                                codigo_candidato=str(c.get("codcan", "")),
                                votos=votos,
                            ):
                                saltados += 1

                        partidos.append({
                            "codigo_partido": codigo_partido,
                            "votos_partido": act.get("vot"),
                            "porcentaje_partido": act.get("pvot"),
                            "candidatos": candidatos,
                        })

                    resultados[nombre][corporacion].append({
                        "codigo": amb,
                        "nombre": mun.get("nombre"),
                        "camara": cam.get("cam"),
                        "totales_municipio": {
                            "votantes": mun.get("votant"),
                            "porcentaje_votacion": mun.get("pvotant"),
                            "votos_candidatos": mun.get("votcan"),
                            "mesas_escrutadas": mun.get("mesesc"),
                            "porcentaje_mesas": mun.get("pmesesc"),
                        },
                        "partido_ganador": {
                            "codigo": mun.get("codpar"),
                            "votos": mun.get("vot"),
                            "porcentaje": mun.get("pvot"),
                        },
                        "partidos": partidos,
                    })

    logger.info("Scraper finalizado. %d municipio(s) procesado(s)", len(resultados))
    logger.info("Total registros saltados (duplicados): %d", saltados)
    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de resultados electorales")
    parser.add_argument(
        "--municipios", "-m",
        nargs="+",
        default=["Tunja"],
        help="Uno o más municipios a consultar (ej: --municipios Tunja Bogota Medellin)",
    )
    args = parser.parse_args()
    resultados = obtener_resultado_municipio(args.municipios)
    print(resultados)
