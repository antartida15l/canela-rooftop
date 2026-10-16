import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.contenido import service as contenido
from app.modules.ninos import service as ninos
from app.modules.sesiones import calificacion
from app.modules.sesiones.congelar_ajustes import congelar

_SEL = "s.id::text AS id, s.nino_id::text AS nino_id, s.inicio, s.fin, s.ajustes, s.kpi, s.nota"


class NoEncontrada(Exception):
    pass


class SinContenido(Exception):
    pass


class SesionCerrada(Exception):
    pass


class RespuestasInvalidas(Exception):
    pass


def iniciar(db: Session, padre_id: str, nino_id: str, habilidad: str) -> dict:
    nino = ninos.obtener(db, padre_id, nino_id)
    if nino is None:
        raise NoEncontrada()
    if not contenido.hay_contenido(db, habilidad):
        raise SinContenido()
    ajustes = congelar(db, padre_id, nino, habilidad)
    fila = db.execute(
        text("""INSERT INTO sesiones (nino_id, ajustes)
                VALUES (CAST(:n AS uuid), CAST(:a AS jsonb))
                RETURNING id::text AS id, nino_id::text AS nino_id, inicio, fin,
                          ajustes, kpi, nota"""),
        {"n": nino_id, "a": json.dumps(ajustes)},
    ).mappings().one()
    db.commit()
    return dict(fila)


def obtener(db: Session, padre_id: str, sesion_id: str) -> dict | None:
    fila = db.execute(
        text(f"""SELECT {_SEL} FROM sesiones s JOIN ninos n ON n.id = s.nino_id
                 WHERE s.id = CAST(:s AS uuid) AND n.padre_id = CAST(:p AS uuid)"""),
        {"s": sesion_id, "p": padre_id},
    ).mappings().first()
    return dict(fila) if fila else None


def listar(db: Session, padre_id: str, nino_id: str, limite: int = 50) -> list[dict]:
    filas = db.execute(
        text(f"""SELECT {_SEL} FROM sesiones s JOIN ninos n ON n.id = s.nino_id
                 WHERE s.nino_id = CAST(:n AS uuid) AND n.padre_id = CAST(:p AS uuid)
                 ORDER BY s.inicio DESC LIMIT CAST(:l AS int)"""),
        {"n": nino_id, "p": padre_id, "l": limite},
    ).mappings().all()
    return [dict(f) for f in filas]


def _nivel_de(dominio: dict, habilidad: str) -> int:
    try:
        nivel = int(((dominio or {}).get(habilidad) or {}).get("nivel", 1))
    except (TypeError, ValueError):
        nivel = 1
    return min(3, max(1, nivel))


def ejercicios_para(db: Session, padre_id: str, sesion_id: str, cantidad: int) -> list[dict]:
    sesion = obtener(db, padre_id, sesion_id)
    if sesion is None:
        raise NoEncontrada()
    if sesion["fin"] is not None:
        raise SesionCerrada()
    nino = ninos.obtener(db, padre_id, sesion["nino_id"])
    habilidad = sesion["ajustes"]["habilidad"]
    # El módulo de dominio mantendrá el nivel; si no hay ejercicios en él, se baja.
    for nivel in range(_nivel_de(nino["dominio"], habilidad), 0, -1):
        lote = contenido.muestra(db, habilidad, nivel, cantidad)
        if lote:
            return lote
    return []


def cerrar(db: Session, padre_id: str, sesion_id: str,
           respuestas: list[dict], detalle: dict) -> dict:
    s = db.execute(
        text("""SELECT s.ajustes, s.fin,
                       EXTRACT(EPOCH FROM (now() - s.inicio))::int AS duracion
                FROM sesiones s JOIN ninos n ON n.id = s.nino_id
                WHERE s.id = CAST(:s AS uuid) AND n.padre_id = CAST(:p AS uuid)
                FOR UPDATE OF s"""),
        {"s": sesion_id, "p": padre_id},
    ).mappings().first()
    if s is None:
        db.rollback()
        raise NoEncontrada()
    if s["fin"] is not None:
        db.rollback()
        raise SesionCerrada()

    ids = [r["ejercicio_id"] for r in respuestas]
    if len(set(ids)) != len(ids):
        db.rollback()
        raise RespuestasInvalidas("Hay ejercicios repetidos en el lote")

    por_id: dict[str, dict] = {}
    if ids:
        filas = db.execute(
            text("""SELECT id::text AS id, habilidad, nivel, contenido FROM ejercicios
                    WHERE id = ANY(CAST(:ids AS uuid[]))"""),
            {"ids": ids},
        ).mappings().all()
        por_id = {f["id"]: dict(f) for f in filas}

    habilidad = s["ajustes"]["habilidad"]
    items, a_guardar = [], []
    for r in respuestas:
        ej = por_id.get(r["ejercicio_id"])
        if ej is None or ej["habilidad"] != habilidad:
            db.rollback()
            raise RespuestasInvalidas("Ejercicio inexistente o de otra habilidad")
        if any(e >= len(ej["contenido"]["opciones"]) for e in r["elecciones"]):
            db.rollback()
            raise RespuestasInvalidas("Opción fuera de rango para un ejercicio")
        correcta, intentos = calificacion.corregir(ej["contenido"], r["elecciones"])
        items.append((ej["nivel"], correcta, intentos))
        a_guardar.append({"s": sesion_id, "e": r["ejercicio_id"], "c": correcta,
                          "i": intentos, "ms": r["ms"]})

    objetivo = int(s["ajustes"].get("ejercicios_objetivo", calificacion.OBJETIVO_POR_DEFECTO))
    nota, comp = calificacion.calcular_nota(items, objetivo)
    n = len(items)
    kpi = {
        "respondidas": n,
        "correctas": sum(1 for _, ok, _ in items if ok),
        "aciertos_primer_intento": sum(1 for _, ok, i in items if ok and i == 1),
        "ms_promedio": round(sum(r["ms"] for r in respuestas) / n) if n else None,
        "duracion_s": s["duracion"],
        "objetivo": objetivo,
        **comp,
    }

    if a_guardar:
        db.execute(
            text("""INSERT INTO respuestas (sesion_id, ejercicio_id, correcta, intentos, ms)
                    VALUES (CAST(:s AS uuid), CAST(:e AS uuid), :c, :i, :ms)"""),
            a_guardar,
        )
    db.execute(
        text("""UPDATE sesiones SET fin = now(), kpi = CAST(:k AS jsonb),
                       detalle = CAST(:d AS jsonb), nota = CAST(:nota AS numeric)
                WHERE id = CAST(:s AS uuid)"""),
        {"k": json.dumps(kpi), "d": json.dumps(detalle), "nota": nota, "s": sesion_id},
    )
    db.commit()
    return {"nota": nota, "kpi": kpi}