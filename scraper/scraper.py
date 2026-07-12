import requests

from core.scraper import _cargar_codigos_dane

API_REGISTRADURIA_BASE_URL = "https://resultadospreccongreso2026.registraduria.gov.co"
CORPORACIONES = ("SE", "CA")


def obtener_resultado_municipio(municipios):
    nombres = {m.upper().strip() for m in municipios}
    dane_cache = _cargar_codigos_dane()
    dane_idx = {}
    for depto, info in dane_cache.items():
        for mun, cod in info["municipios"].items():
            dane_idx[mun] = {"departamento": depto, "dane_depto": info["dane"], "dane_municipio": cod}

    resultados = {}

    for corp in CORPORACIONES:
        for nombre in nombres:
            meta = dane_idx.get(nombre)
            if not meta:
                continue

            url = f"{API_REGISTRADURIA_BASE_URL}/json/ACT/{corp}/{meta['dane_municipio']}.json"

            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    continue
                data = resp.json()
            except (requests.RequestException, ValueError):
                continue

            for cam in data.get("camaras", []):
                for mun in cam.get("mapagan", []):
                    nombre_resp = (mun.get("nombre") or "").upper().strip()
                    if nombre_resp != nombre:
                        continue

                    amb = mun.get("amb", "")
                    if nombre not in resultados:
                        resultados[nombre] = {"_meta": meta}

                    if corp not in resultados[nombre]:
                        resultados[nombre][corp] = []

                    partidos = []
                    for partido in cam.get("partotabla", []):
                        act = partido.get("act", {})
                        cantotabla = act.get("cantotabla", [])
                        candidatos = [
                            {
                                "codigo": c.get("codcan"),
                                "nombre_completo": f"{c.get('nomcan', '')} {c.get('apecan', '')}".strip(),
                                "cedula": c.get("cedula"),
                                "votos": c.get("vot"),
                                "porcentaje": c.get("pvot"),
                                "voto_preferente": c.get("pref"),
                            }
                            for c in cantotabla
                        ]
                        partidos.append({
                            "codigo_partido": act.get("codpar"),
                            "votos_partido": act.get("vot"),
                            "porcentaje_partido": act.get("pvot"),
                            "candidatos": candidatos,
                        })

                    resultados[nombre][corp].append({
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

    return resultados
