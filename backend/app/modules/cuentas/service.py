from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_secreto, verificar_secreto

MAX_INTENTOS_PIN = 5
BLOQUEO_PIN_MIN = 15


def buscar_por_email(db: Session, email: str) -> dict | None:
    fila = db.execute(
        text("""SELECT id::text AS id, email::text AS email, pass_hash, rol, token_version
                FROM usuarios WHERE email = :e"""),
        {"e": email},
    ).mappings().first()
    return dict(fila) if fila else None


def buscar_por_id(db: Session, usuario_id: str) -> dict | None:
    fila = db.execute(
        text("""SELECT id::text AS id, email::text AS email, pass_hash, rol, token_version
                FROM usuarios WHERE id = CAST(:u AS uuid)"""),
        {"u": usuario_id},
    ).mappings().first()
    return dict(fila) if fila else None


def crear_usuario(db: Session, email: str, password: str) -> dict | None:
    """Devuelve None si el email ya existe."""
    fila = db.execute(
        text("""INSERT INTO usuarios (email, pass_hash, rol)
                VALUES (:e, :p, 'padre')
                ON CONFLICT (email) DO NOTHING
                RETURNING id::text AS id, email::text AS email, rol, token_version"""),
        {"e": email, "p": hash_secreto(password)},
    ).mappings().first()
    return dict(fila) if fila else None

def cerrar_todas_las_sesiones(db: Session, usuario_id: str) -> None:
    db.execute(
        text("UPDATE usuarios SET token_version = token_version + 1 WHERE id = CAST(:u AS uuid)"),
        {"u": usuario_id},
    )
    db.commit()


# ---------- PIN de la zona de padres ----------
def guardar_pin(db: Session, usuario_id: str, pin: str) -> None:
    db.execute(
        text("""UPDATE usuarios SET pin_hash = :h, pin_intentos = 0, pin_bloqueado_hasta = NULL
                WHERE id = CAST(:u AS uuid)"""),
        {"h": hash_secreto(pin), "u": usuario_id},
    )
    db.commit()


def verificar_pin(db: Session, usuario_id: str, pin: str) -> str:
    """Devuelve: 'ok' | 'incorrecto' | 'bloqueado' | 'sin_pin'."""
    f = db.execute(
        text("""SELECT pin_hash, pin_intentos,
                       COALESCE(pin_bloqueado_hasta > now(), false) AS bloqueado
                FROM usuarios WHERE id = CAST(:u AS uuid) FOR UPDATE"""),
        {"u": usuario_id},
    ).mappings().first()

    if f is None or f["pin_hash"] is None:
        db.rollback()
        return "sin_pin"
    if f["bloqueado"]:
        db.rollback()
        return "bloqueado"

    if verificar_secreto(f["pin_hash"], pin):
        db.execute(text("""UPDATE usuarios SET pin_intentos = 0, pin_bloqueado_hasta = NULL
                           WHERE id = CAST(:u AS uuid)"""), {"u": usuario_id})
        db.commit()
        return "ok"

    intentos = f["pin_intentos"] + 1
    if intentos >= MAX_INTENTOS_PIN:
        db.execute(
            text("""UPDATE usuarios
                    SET pin_intentos = 0, pin_bloqueado_hasta = now() + (:m * INTERVAL '1 minute')
                    WHERE id = CAST(:u AS uuid)"""),
            {"m": BLOQUEO_PIN_MIN, "u": usuario_id},
        )
        db.commit()
        return "bloqueado"

    db.execute(text("UPDATE usuarios SET pin_intentos = :i WHERE id = CAST(:u AS uuid)"),
               {"i": intentos, "u": usuario_id})
    db.commit()
    return "incorrecto"