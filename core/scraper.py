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
    deptos_map = {}
    for entry in ambito.get("ambitos", []):
        if entry.get("l") == 2:
            deptos_map[entry["i"]] = entry["n"]

    result = {}
    for entry in ambito.get("ambitos", []):
        if entry.get("l") != 3:
            continue
        nombre = entry.get("n", "").upper().strip()
        codigo = entry.get("c", "")
        padre = entry.get("p", [{}])[0].get("p", [None])[0]
        departamento = deptos_map.get(padre, "")
        result[nombre] = {
            "codigo": codigo,
            "departamento": departamento,
            "nomenclator_idx": entry.get("i"),
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


def obtener_mesas_por_municipio(nombre_municipio):
    data = _fetch_nomenclator()
    ambitos = data["amb"][0]["ambitos"]
    idx_map = {e["i"]: e for e in ambitos}

    mun = None
    for e in ambitos:
        if e.get("n", "").upper().strip() == nombre_municipio.upper().strip() and e.get("l") == 3:
            mun = e
            break
    if not mun:
        return []

    mesas = []
    for h in mun.get("h", []):
        if h["l"] == 4:
            for zi in h["p"]:
                zona = idx_map.get(zi)
                if not zona:
                    continue
                for h2 in zona.get("h", []):
                    if h2["l"] == 6:
                        for pi in h2["p"]:
                            puesto = idx_map.get(pi)
                            if not puesto:
                                continue
                            num_mesas = puesto.get("m", 0)
                            for m in range(1, num_mesas + 1):
                                codigo_mesa = puesto["c"] + str(m).zfill(6)
                                mesas.append({
                                    "zona": zona.get("n", ""),
                                    "codigo_zona": zona.get("c", ""),
                                    "puesto": puesto.get("n", ""),
                                    "codigo_puesto": puesto.get("c", ""),
                                    "mesa": m,
                                    "codigo_mesa": codigo_mesa,
                                })
    return mesas
