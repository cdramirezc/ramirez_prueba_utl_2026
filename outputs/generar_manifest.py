import json


def validar_conteos_municipio(datos_municipio):
    """
    Valida los conteos de mesas y filas extraídas de los datos de un municipio.

    Args:
        datos_municipio (dict): Diccionario con la estructura devuelta por
                                obtener_resultado_municipio() para un municipio.

    Returns:
        dict: Con llaves 'valido' (bool) y 'errores' (list[str]).
    """
    errores = []

    mesas_por_corporacion = {}

    for corporacion in ("SENADO", "CAMARA"):
        entries = datos_municipio.get(corporacion, [])
        if not entries:
            continue

        for i, entry in enumerate(entries):
            totales = entry.get("totales_municipio", {})
            mesas = totales.get("mesas_escrutadas")
            pct_mesas = totales.get("porcentaje_mesas")

            if mesas is None:
                errores.append(f"{corporacion}[{i}]: falta 'mesas_escrutadas'")
            else:
                try:
                    mesas = int(mesas)
                    if mesas < 0:
                        errores.append(f"{corporacion}[{i}]: 'mesas_escrutadas' negativo ({mesas})")
                except (ValueError, TypeError):
                        errores.append(f"{corporacion}[{i}]: 'mesas_escrutadas' no es un número ({mesas})")

            if pct_mesas is not None:
                try:
                    pct_mesas = float(pct_mesas)
                    if not (0 <= pct_mesas <= 100):
                        errores.append(f"{corporacion}[{i}]: 'porcentaje_mesas' fuera de rango 0-100 ({pct_mesas})")
                except (ValueError, TypeError):
                        errores.append(f"{corporacion}[{i}]: 'porcentaje_mesas' no es un número ({pct_mesas})")

            partidos = entry.get("partidos", [])
            total_candidatos = 0
            for j, partido in enumerate(partidos):
                candidatos = partido.get("candidatos", [])
                total_candidatos += len(candidatos)
                for k, cand in enumerate(candidatos):
                    if cand.get("votos") is None and cand.get("codigo") is not None:
                        errores.append(
                            f"{corporacion}[{i}].partidos[{j}].candidatos[{k}]: "
                            "candidato sin votos"
                        )

            mesas_por_corporacion.setdefault(corporacion, []).append({
                "indice": i,
                "mesas": mesas,
                "total_partidos": len(partidos),
                "total_candidatos": total_candidatos,
            })

    corporaciones_con_datos = [c for c in ("SENADO", "CAMARA") if datos_municipio.get(c)]
    if len(corporaciones_con_datos) >= 2:
        for corporacion_a, corporacion_b in [("SENADO", "CAMARA")]:
            entries_a = mesas_por_corporacion.get(corporacion_a, [])
            entries_b = mesas_por_corporacion.get(corporacion_b, [])
            if entries_a and entries_b:
                for ea in entries_a:
                    for eb in entries_b:
                        if ea["mesas"] is not None and eb["mesas"] is not None and ea["mesas"] != eb["mesas"]:
                            errores.append(
                                f"Inconsistencia en mesas_escrutadas: "
                                f"{corporacion_a}[{ea['indice']}]={ea['mesas']} vs "
                                f"{corporacion_b}[{eb['indice']}]={eb['mesas']}"
                            )

    for corporacion, items in mesas_por_corporacion.items():
        for item in items:
            if item["total_partidos"] == 0:
                errores.append(f"{corporacion}[{item['indice']}]: no se extrajeron partidos")
            if item["total_candidatos"] == 0:
                errores.append(f"{corporacion}[{item['indice']}]: no se extrajeron candidatos")

    return {"valido": len(errores) == 0, "errores": errores}
