AVISO_LEGAL = (
    "Estas observaciones son orientativas: las genera un sistema automático a partir de "
    "señales simples (orientación de la cabeza y expresión facial) y no constituyen una "
    "evaluación ni un diagnóstico. Ante cualquier duda, consulta con un especialista."
)


def _pct(x: float) -> int:
    return int(round(x * 100))


def generar(nombre: str, resumen: dict | None) -> list[dict]:
    if not resumen:
        return []
    obs: list[dict] = []
    media = resumen.get("atencion_media")

    if resumen.get("pct_sin_rostro", 0) > 0.3:
        obs.append({"nivel": "atencion", "texto": (
            f"Durante el {_pct(resumen['pct_sin_rostro'])} % de la sesión la cámara no detectó "
            f"el rostro de {nombre}. Puede deberse a la posición, a la iluminación o a que "
            f"miró hacia otro lado.")})

    if media is not None and media < 0.4:
        obs.append({"nivel": "atencion", "texto": (
            f"La orientación de la cabeza de {nombre} indicó atención baja durante buena parte "
            f"de la sesión. Esta señal es aproximada y puede no reflejar su concentración real.")})

    if resumen.get("pct_malestar", 0) > 0.25:
        obs.append({"nivel": "atencion", "texto": (
            f"Se observaron expresiones asociadas a malestar en el "
            f"{_pct(resumen['pct_malestar'])} % de las lecturas. Podría ayudar probar sesiones "
            f"más cortas o con pausas más frecuentes.")})

    sugerencias = resumen.get("avisos", 0) + resumen.get("pausas_sugeridas", 0)
    if sugerencias >= 3:
        obs.append({"nivel": "atencion", "texto": (
            f"El sistema sugirió {sugerencias} avisos o pausas durante la sesión.")})

    if (media is not None and media >= 0.7 and resumen.get("pct_malestar", 0) < 0.1
            and resumen.get("pct_sin_rostro", 0) < 0.2):
        obs.append({"nivel": "info", "texto": (
            f"La sesión de {nombre} transcurrió con buena orientación de atención y sin "
            f"señales marcadas de malestar.")})

    obs.append({"nivel": "info", "texto": AVISO_LEGAL})
    return obs