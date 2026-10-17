"""Cálculo puro del reporte: sin base de datos, fácil de probar.
Los textos y umbrales de las recomendaciones son HIPÓTESIS DE DISEÑO: deben ser revisados
por un psicopedagogo antes de abrir al público. Se redactan como observaciones, no como
diagnósticos."""
from collections import defaultdict
from statistics import mean

AVISO_REPORTE = (
    "Este reporte es orientativo: lo genera un sistema automático a partir del desempeño en "
    "los ejercicios y, si hubo permiso de cámara, de señales simples de atención. No es una "
    "evaluación ni un diagnóstico. Ante cualquier duda, consulta con un especialista."
)

UMBRAL_TENDENCIA = 1.0        # puntos de nota entre la primera y la segunda mitad del período
SESIONES_MIN_POR_SEMANA = 2
NOTA_BAJA = 10
NOTA_ALTA = 15
ATENCION_BAJA = 0.4
MALESTAR_ALTO = 0.25


def _media(valores: list[float], decimales: int = 2) -> float | None:
    return round(mean(valores), decimales) if valores else None


def tendencia(notas: list[float]) -> str:
    """notas en orden cronológico."""
    if len(notas) < 4:
        return "insuficiente"
    mitad = len(notas) // 2
    diferencia = mean(notas[mitad:]) - mean(notas[:mitad])
    if diferencia >= UMBRAL_TENDENCIA:
        return "mejora"
    if diferencia <= -UMBRAL_TENDENCIA:
        return "baja"
    return "estable"


def _resumen(sesiones: list[dict]) -> dict:
    notas = [s["nota"] for s in sesiones if s["nota"] is not None]
    respondidas = sum(s["kpi"].get("respondidas", 0) for s in sesiones)
    correctas = sum(s["kpi"].get("correctas", 0) for s in sesiones)
    return {
        "sesiones": len(sesiones),
        "minutos": round(sum(s["kpi"].get("duracion_s", 0) for s in sesiones) / 60),
        "nota_media": _media(notas),
        "aciertos_pct": round(correctas / respondidas, 3) if respondidas else None,
        "tendencia": tendencia(notas),
    }


def _habilidades(sesiones: list[dict], dominio: dict) -> list[dict]:
    por_habilidad: dict[str, list[dict]] = defaultdict(list)
    for s in sesiones:
        por_habilidad[s["habilidad"]].append(s)
    nombres = list(por_habilidad) + [h for h in (dominio or {}) if h not in por_habilidad]
    salida = []
    for h in nombres:
        ss = por_habilidad.get(h, [])
        d = (dominio or {}).get(h) or {}
        salida.append({
            "habilidad": h,
            "sesiones": len(ss),
            "nota_media": _media([s["nota"] for s in ss if s["nota"] is not None]),
            "nivel": d.get("nivel", 1),
            "dominio": d.get("dominio", 0.0),
        })
    return salida


def _atencion(sesiones: list[dict]) -> dict | None:
    con = [s["kpi"]["atencion"] for s in sesiones if s["kpi"].get("atencion")]
    if not con:
        return None
    con_media = [a for a in con if a.get("atencion_media") is not None]
    peso = sum(a["lecturas"] for a in con_media)
    peso_total = sum(a["lecturas"] for a in con)
    return {
        "sesiones_con_camara": len(con),
        "atencion_media": (round(sum(a["atencion_media"] * a["lecturas"] for a in con_media) / peso, 3)
                           if peso else None),
        "pct_malestar": (round(sum(a.get("pct_malestar", 0) * a["lecturas"] for a in con) / peso_total, 3)
                         if peso_total else 0.0),
        "avisos": sum(a.get("avisos", 0) for a in con),
        "pausas_sugeridas": sum(a.get("pausas_sugeridas", 0) for a in con),
    }


def recomendar(nombre: str, dias: int, resumen: dict, habilidades: list[dict],
               atencion: dict | None) -> list[dict]:
    r: list[dict] = []

    def sugerencia(t): r.append({"nivel": "sugerencia", "texto": t})
    def info(t): r.append({"nivel": "info", "texto": t})

    n = resumen["sesiones"]
    if n == 0:
        sugerencia(f"Aún no hay sesiones en los últimos {dias} días. Empezar con sesiones cortas "
                   f"y regulares suele ser un buen punto de partida.")
        info(AVISO_REPORTE)
        return r

    if n / (dias / 7) < SESIONES_MIN_POR_SEMANA:
        sugerencia(f"Se registraron {n} {'sesión' if n == 1 else 'sesiones'} en {dias} días. "
                   f"Practicar con regularidad, en sesiones breves, suele ayudar más que sesiones "
                   f"largas y espaciadas.")

    if resumen["tendencia"] == "mejora":
        info(f"Las notas muestran una mejora a lo largo del período. Reconocer el esfuerzo de "
             f"{nombre} puede ayudar a mantener la motivación.")
    elif resumen["tendencia"] == "baja":
        sugerencia(f"Las notas bajaron en la segunda parte del período. Puede ayudar repasar "
                   f"ejercicios más sencillos y acompañar a {nombre} en algunas sesiones.")

    media = resumen["nota_media"]
    if media is not None and n >= 3:
        if media < NOTA_BAJA:
            sugerencia(f"El promedio de notas fue bajo ({media} de 20). Acompañar la sesión y "
                       f"reforzar con ejercicios más sencillos podría ayudar.")
        elif media >= NOTA_ALTA:
            info(f"El desempeño fue bueno de forma sostenida (promedio {media} de 20).")

    for h in habilidades:
        if h["nivel"] >= 3 and h["dominio"] >= 0.8:
            info(f"En {h['habilidad'].replace('_', ' ')} el dominio es alto en el nivel máximo; "
                 f"podría ser un buen momento para explorar otra habilidad.")

    if atencion:
        if atencion["atencion_media"] is not None and atencion["atencion_media"] < ATENCION_BAJA:
            sugerencia(f"La orientación de la cabeza indicó atención baja en promedio. Es una señal "
                       f"aproximada, pero podría ayudar probar sesiones más cortas con pausas.")
        if atencion["pct_malestar"] > MALESTAR_ALTO:
            sugerencia(f"Se observaron expresiones asociadas a malestar en el "
                       f"{int(round(atencion['pct_malestar'] * 100))} % de las lecturas. Conviene "
                       f"observar en qué momentos ocurre y considerar más pausas.")

    info(AVISO_REPORTE)
    return r


def construir(nino: dict, sesiones: list[dict], dias: int, alcance: str) -> dict:
    """sesiones: [{id, inicio, habilidad, nota, kpi}] en orden cronológico ascendente."""
    resumen = _resumen(sesiones)
    habilidades = _habilidades(sesiones, nino.get("dominio") or {})
    reporte = {
        "periodo_dias": dias,
        "alcance": alcance,
        "nino": {"nombre": nino["nombre"], "edad": nino["edad"]},
        "resumen": resumen,
        "habilidades": habilidades,
        "sesiones": [
            {"id": s["id"], "inicio": s["inicio"], "habilidad": s["habilidad"], "nota": s["nota"],
             "respondidas": s["kpi"].get("respondidas", 0), "correctas": s["kpi"].get("correctas", 0)}
            for s in reversed(sesiones)
        ][:50],
        "atencion": None,
        "recomendaciones": None,
    }
    if alcance == "completo":
        reporte["atencion"] = _atencion(sesiones)
        reporte["recomendaciones"] = recomendar(
            nino["nombre"], dias, resumen, habilidades, reporte["atencion"])
    return reporte
