MAX_INTENTOS = 3
PESO_ACIERTOS = 0.85
PESO_PROGRESO = 0.15
OBJETIVO_POR_DEFECTO = 10


def corregir(contenido: dict, elecciones: list[int]) -> tuple[bool, int]:
    """Devuelve (acertó, intentos). Cuenta hasta el primer acierto, máximo 3 intentos."""
    usadas = elecciones[:MAX_INTENTOS]
    for i, eleccion in enumerate(usadas, start=1):
        if eleccion == contenido["correcta"]:
            return True, i
    return False, len(usadas)


def credito(correcta: bool, intentos: int) -> float:
    if not correcta:
        return 0.0
    return max(0.4, 1 - 0.3 * (intentos - 1))


def calcular_nota(items: list[tuple[int, bool, int]], objetivo: int) -> tuple[float | None, dict]:
    """items = [(nivel, correcta, intentos)]. Sin respuestas no hay nota."""
    if not items:
        return None, {"precision_ponderada": None, "progreso": 0.0}
    peso_total = sum(nivel for nivel, _, _ in items)
    precision = sum(nivel * credito(ok, intentos) for nivel, ok, intentos in items) / peso_total
    progreso = min(1.0, len(items) / max(1, objetivo))
    nota = round(20 * (PESO_ACIERTOS * precision + PESO_PROGRESO * progreso), 2)
    return nota, {"precision_ponderada": round(precision, 4), "progreso": round(progreso, 4)}