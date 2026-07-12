import json
import logging
import os
from functools import lru_cache

import requests

logger = logging.getLogger(__name__)

NOMENCLATOR_URL = "https://resultadospreccongreso2026.registraduria.gov.co/json/nomenclator.json"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
NOMENCLATOR_CACHE = os.path.join(CACHE_DIR, "nomenclator.json")


def _fetch_nomenclator():
    if os.path.exists(NOMENCLATOR_CACHE):
        with open(NOMENCLATOR_CACHE, encoding="utf-8") as f:
            data = json.load(f)
            logger.info("Nomenclator cargado desde cache (%s)", NOMENCLATOR_CACHE)
            return data
    logger.info("Descargando nomenclator desde %s", NOMENCLATOR_URL)
    resp = requests.get(NOMENCLATOR_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(NOMENCLATOR_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    logger.info("Nomenclator guardado en cache (%s)", NOMENCLATOR_CACHE)
    return data


@lru_cache(maxsize=1)
def _cargar_codigos_internos():
    data = _fetch_nomenclator()
    ambitos = data.get("amb", [])
    ambito = next((a for a in ambitos if a.get("elec") == 1), ambitos[0])
    municipios = [e for e in data.get("elec", [])]
    deptos_map = {}
    for entry in ambito.get("ambitos", []):
        if entry.get("l") == 2:
            deptos_map[entry["i"]] = entry["n"]

    result = {}
    for entry in data.get("elec", []):
        sigla = entry.get("sigla")
        for ambito in ambitos:
            if ambito.get("elec") != entry.get("elec"):
                continue
            for a in ambito.get("ambitos", []):
                if a.get("l") != 3:
                    continue
                nombre = a.get("n", "").upper().strip()
                codigo = a.get("c", "")
                padre = a.get("p", [{}])[0].get("p", [None])[0]
                departamento = deptos_map.get(padre, "")
                result[nombre] = {
                    "codigo": codigo,
                    "departamento": departamento,
                    "nomenclator_idx": a.get("i"),
                }
    return result


def _cargar_codigos_dane():
    ruta = os.path.join(os.path.dirname(__file__), "..", "sample_data", "codigos_dane.json")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def buscar_municipio(nombre):
    data = _cargar_codigos_dane()
    nombre = nombre.upper().strip()
    for depto, info in data.items():
        if nombre in info["municipios"]:
            return {
                "nombre": nombre,
                "departamento": depto,
                "dane_depto": info["dane"],
                "dane_municipio": info["municipios"][nombre],
            }
    return None


def buscar_municipio_por_nomenclator(nombre):
    codigos = _cargar_codigos_internos()
    nombre = nombre.upper().strip()
    info = codigos.get(nombre)
    if info:
        return info
    for key, val in codigos.items():
        if nombre in key or key in nombre:
            return val
    return None
