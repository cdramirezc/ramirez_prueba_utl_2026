import json
import logging
import os
import time
from functools import lru_cache

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

NOMENCLATOR_URL = "https://resultadospreccongreso2026.registraduria.gov.co/json/nomenclator.json"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
NOMENCLATOR_CACHE = os.path.join(CACHE_DIR, "nomenclator.json")

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


def _fetch_nomenclator():
    if os.path.exists(NOMENCLATOR_CACHE):
        with open(NOMENCLATOR_CACHE, encoding="utf-8") as f:
            data = json.load(f)
            logger.info("Nomenclator cargado desde cache (%s)", NOMENCLATOR_CACHE)
            return data
    logger.info("Descargando nomenclator desde %s", NOMENCLATOR_URL)
    session = _get_session()
    for intento in range(3):
        try:
            resp = session.get(NOMENCLATOR_URL, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(NOMENCLATOR_CACHE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            logger.info("Nomenclator guardado en cache (%s)", NOMENCLATOR_CACHE)
            return data
        except (requests.RequestException, ValueError) as e:
            logger.error("Error descargando nomenclator (intento %d/3): %s", intento + 1, e)
            if intento < 2:
                time.sleep(2 ** intento)
    raise RuntimeError("No se pudo descargar el nomenclator tras 3 intentos")


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
    for nivel_zonas in mun.get("h", []):
        if nivel_zonas["l"] != 4:
            continue
        for zona_idx in nivel_zonas["p"]:
            zona = idx_map.get(zona_idx)
            if not zona:
                continue
            for nivel_puestos in zona.get("h", []):
                if nivel_puestos["l"] != 6:
                    continue
                for puesto_idx in nivel_puestos["p"]:
                    puesto = idx_map.get(puesto_idx)
                    if not puesto:
                        continue
                    num_mesas = puesto.get("m", 0)
                    for numero_mesa in range(1, num_mesas + 1):
                        codigo_mesa = puesto["c"] + str(numero_mesa).zfill(6)
                        mesas.append({
                            "zona": zona.get("n", ""),
                            "codigo_zona": zona.get("c", ""),
                            "puesto": puesto.get("n", ""),
                            "codigo_puesto": puesto.get("c", ""),
                            "mesa": numero_mesa,
                            "codigo_mesa": codigo_mesa,
                        })
    return mesas
