import json
import os

RUTA_CODIGOS_DANE = os.path.join(os.path.dirname(__file__), "..", "sample_data", "codigos_dane.json")


def _cargar_codigos_dane():
    with open(RUTA_CODIGOS_DANE, encoding="utf-8") as f:
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
