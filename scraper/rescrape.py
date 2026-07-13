"""
rescrape.py — Rescrapea SOLO las celdas faltantes con pool de 6 hilos.
Preserva existente via INSERT OR IGNORE.
"""
import argparse
import concurrent.futures
import json
import logging
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.scraper import obtener_mesas_por_municipio, buscar_municipio_por_nomenclator
from db.carga import insertar_resultado

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

API_BASE = "https://resultadospreccongreso2026.registraduria.gov.co"
COD_CORP = {"SE": "SENADO", "CA": "CAMARA"}
CORP_API = {"SE": "SE", "CA": "CA"}

session = requests.Session()

def fetch_mesa(municipio, codigo_dane, mesa_info, corporacion):
    cod = CORP_API[corporacion]
    url = f"{API_BASE}/json/ACT/{cod}/{mesa_info['codigo_mesa']}.json"
    for intento in range(3):
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                if intento < 2:
                    time.sleep(2 ** intento)
                    continue
                return None
            return resp.json()
        except Exception:
            if intento < 2:
                time.sleep(2 ** intento)
                continue
            return None
    return None

def process_mesa(municipio, meta, mesa_info, corporacion):
    data = fetch_mesa(municipio, meta["codigo"], mesa_info, corporacion)
    if data is None:
        return 0
    inserted = 0
    for camara in data.get("camaras", []):
        for partido in camara.get("partotabla", []):
            act = partido.get("act", {})
            for candidato in act.get("cantotabla", []):
                nombre = f"{candidato.get('nomcan','')} {candidato.get('apecan','')}".strip()
                votos = int(candidato.get("vot", 0) or 0)
                if insertar_resultado(
                    corporacion=corporacion,
                    municipio=municipio,
                    codigo_dane=meta["codigo"],
                    zona=mesa_info["zona"],
                    codigo_zona=mesa_info["codigo_zona"],
                    puesto=mesa_info["puesto"],
                    codigo_puesto=mesa_info["codigo_puesto"],
                    mesa=mesa_info["mesa"],
                    codigo_mesa=mesa_info["codigo_mesa"],
                    partido=act.get("nompar", str(act.get("codpar",""))),
                    codigo_partido=act.get("codpar",""),
                    candidato=nombre,
                    codigo_candidato=str(candidato.get("codcan","")),
                    votos=votos,
                ):
                    inserted += 1
    return inserted

def rescrape_municipio(args):
    nombre, corporaciones = args
    meta = buscar_municipio_por_nomenclator(nombre)
    if not meta:
        logger.warning("Municipio %s no encontrado", nombre)
        return
    mesas = obtener_mesas_por_municipio(nombre)
    logger.info("Rescrapeando %s (%d mesas, %s)", nombre, len(mesas), corporaciones)
    total = 0
    for corp in corporaciones:
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            for m in mesas:
                futures.append(executor.submit(process_mesa, nombre, meta, m, corp))
            for f in concurrent.futures.as_completed(futures):
                total += f.result()
    logger.info("%s: %d nuevos registros insertados", nombre, total)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--municipios", "-m", nargs="+", default=["Paipa", "Duitama", "Tunja", "Sogamoso"])
    parser.add_argument("--corps", nargs="+", default=["SE"], choices=["SE", "CA"],
                        help="Corporaciones a rescrapear (default: SE)")
    parser.add_argument("--preflight", action="store_true", help="Solo contar")
    args = parser.parse_args()
    if args.preflight:
        total = 0
        for nombre in args.municipios:
            mesas = obtener_mesas_por_municipio(nombre)
            total += len(mesas) * len(args.corps)
        print(f"Preflight: {len(args.municipios)} municipios, {total} solicitudes ({args.corps})")
        return
    for nombre in args.municipios:
        rescrape_municipio((nombre, args.corps))

if __name__ == "__main__":
    main()
