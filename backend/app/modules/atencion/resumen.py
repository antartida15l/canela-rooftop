from collections import Counter

from app.modules.atencion.reglas import EMOCIONES_MALESTAR

UMBRAL_ATENCION_ALTA = 0.5


def resumir(lecturas: list[dict], intervenciones: list[dict], pausas: list[dict]) -> dict | None:
    """Agregados de la sesión. Es lo que se conserva en kpi cuando se purga el detalle."""
    if not lecturas:
        return None
    n = len(lecturas)
    con_atencion = [l["atencion"] for l in lecturas if l.get("atencion") is not None]
    con_emocion = [l["emocion"] for l in lecturas if l.get("emocion")]
    tipos = Counter(i["tipo"] for i in intervenciones)
    return {
        "lecturas": n,
        "atencion_media": round(sum(con_atencion) / len(con_atencion), 3) if con_atencion else None,
        "pct_atencion_alta": (round(sum(1 for a in con_atencion if a >= UMBRAL_ATENCION_ALTA)
                                    / len(con_atencion), 3) if con_atencion else None),
        "pct_sin_rostro": round((n - len(con_atencion)) / n, 3),
        "emociones": ({e: round(c / len(con_emocion), 3)
                       for e, c in Counter(con_emocion).items()} if con_emocion else {}),
        "pct_malestar": (round(sum(1 for e in con_emocion if e in EMOCIONES_MALESTAR)
                               / len(con_emocion), 3) if con_emocion else 0.0),
        "avisos": tipos.get("aviso_suave", 0),
        "pausas_sugeridas": tipos.get("pausa", 0),
        "pausas_realizadas": len(pausas),
    }