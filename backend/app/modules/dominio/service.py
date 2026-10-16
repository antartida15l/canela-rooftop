import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.dominio import estimador


def aplicar_sesion(db: Session, nino_id: str, habilidad: str,
                   items: list[tuple[int, bool, int]]) -> dict:
    """Actualiza el dominio con las respuestas de una sesión. No hace commit:
    lo hace quien cierra la sesión, así nota y dominio se guardan juntos."""
    fila = db.execute(
        text("SELECT dominio FROM ninos WHERE id = CAST(:n AS uuid) FOR UPDATE"),
        {"n": nino_id},
    ).mappings().one()
    todo = dict(fila["dominio"] or {})
    antes = todo.get(habilidad) or estimador.estado_inicial()
    despues, cambios = estimador.actualizar(
        antes, [(nivel, acierto) for nivel, acierto, _ in items])

    if items:
        todo[habilidad] = despues
        db.execute(
            text("UPDATE ninos SET dominio = CAST(:d AS jsonb) WHERE id = CAST(:n AS uuid)"),
            {"d": json.dumps(todo), "n": nino_id},
        )
    return {
        "habilidad": habilidad,
        "nivel_antes": antes["nivel"],
        "nivel_despues": despues["nivel"],
        "dominio": despues["dominio"],
        "racha": despues["racha"],
        "cambios": cambios,
    }


def resumen(dominio: dict) -> dict:
    """Vista para el padre. No expone la ventana de respuestas."""
    return {
        habilidad: {
            "nivel": e.get("nivel", 1),
            "dominio": e.get("dominio", 0.0),
            "racha": e.get("racha", 0),
            "muestras": len(e.get("ventana", [])),
        }
        for habilidad, e in (dominio or {}).items()
    }