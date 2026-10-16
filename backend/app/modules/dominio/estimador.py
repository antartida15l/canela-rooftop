VENTANA = 10
UMBRAL_SUBIDA = 0.65
RACHA_SUBE = 2
RACHA_BAJA = -2
MIN_MUESTRAS = 5
NIVEL_MIN, NIVEL_MAX = 1, 3


def estado_inicial() -> dict:
    return {"nivel": NIVEL_MIN, "dominio": 0.0, "racha": 0, "ventana": []}


def _siguiente_nivel(e: dict) -> int:
    nivel = e["nivel"]
    if e["racha"] <= RACHA_BAJA and nivel > NIVEL_MIN:
        return nivel - 1
    if (e["racha"] >= RACHA_SUBE and e["dominio"] > UMBRAL_SUBIDA
            and len(e["ventana"]) >= MIN_MUESTRAS and nivel < NIVEL_MAX):
        return nivel + 1
    return nivel


def actualizar(estado: dict, resultados: list[tuple[int, bool]]) -> tuple[dict, list[dict]]:
    """resultados = [(nivel_del_ejercicio, acertó)] en el orden en que se respondieron.
    Devuelve (estado_nuevo, cambios_de_nivel). No modifica el estado recibido."""
    e = {
        "nivel": min(NIVEL_MAX, max(NIVEL_MIN, int(estado.get("nivel", NIVEL_MIN)))),
        "dominio": float(estado.get("dominio", 0.0)),
        "racha": int(estado.get("racha", 0)),
        "ventana": list(estado.get("ventana", [])),
    }
    cambios: list[dict] = []

    for nivel_ejercicio, acierto in resultados:
        if nivel_ejercicio != e["nivel"]:
            continue
        e["ventana"] = (e["ventana"] + [1 if acierto else 0])[-VENTANA:]
        if acierto:
            e["racha"] = e["racha"] + 1 if e["racha"] > 0 else 1
        else:
            e["racha"] = e["racha"] - 1 if e["racha"] < 0 else -1
        e["dominio"] = round(sum(e["ventana"]) / len(e["ventana"]), 4)

        nuevo = _siguiente_nivel(e)
        if nuevo != e["nivel"]:
            cambios.append({"de": e["nivel"], "a": nuevo,
                            "motivo": "subida" if nuevo > e["nivel"] else "bajada"})
            e.update(nivel=nuevo, racha=0, ventana=[], dominio=0.0)
    return e, cambios