import json

from sqlalchemy import text
from sqlalchemy.orm import Session

_COLS = ("id::text AS id, codigo, habilidad, nivel, version, activo, contenido, "
         "revisado_por, revisado_en")


def existe(db: Session, codigo: str) -> bool:
    return db.execute(text("SELECT 1 FROM ejercicios WHERE codigo = :c LIMIT 1"),
                      {"c": codigo}).first() is not None


def crear_borrador(db: Session, codigo: str, habilidad: str, nivel: int,
                   contenido: dict) -> dict:
    """Siempre nace inactivo. Si el código ya existe, crea la versión siguiente."""
    fila = db.execute(
        text(f"""INSERT INTO ejercicios (codigo, habilidad, nivel, contenido, version)
                 SELECT CAST(:c AS text), CAST(:h AS text), CAST(:n AS smallint),
                        CAST(:ct AS jsonb), COALESCE(MAX(version), 0) + 1
                 FROM ejercicios WHERE codigo = CAST(:c AS text)
                 RETURNING {_COLS}"""),
        {"c": codigo, "h": habilidad, "n": nivel, "ct": json.dumps(contenido)},
    ).mappings().one()
    db.commit()
    return dict(fila)


def listar(db: Session, habilidad: str | None, activo: bool | None) -> list[dict]:
    filas = db.execute(
        text(f"""SELECT {_COLS} FROM ejercicios
                 WHERE (CAST(:h AS text) IS NULL OR habilidad = CAST(:h AS text))
                   AND (CAST(:a AS boolean) IS NULL OR activo = CAST(:a AS boolean))
                 ORDER BY codigo, version"""),
        {"h": habilidad, "a": activo},
    ).mappings().all()
    return [dict(f) for f in filas]


def activar(db: Session, ejercicio_id: str, revisor: str) -> dict | None:
    """Activa esta versión y desactiva las demás versiones del mismo código."""
    base = db.execute(
        text("SELECT codigo FROM ejercicios WHERE id = CAST(:id AS uuid) FOR UPDATE"),
        {"id": ejercicio_id},
    ).first()
    if base is None:
        db.rollback()
        return None
    db.execute(
        text("""UPDATE ejercicios SET activo = false
                WHERE codigo = :c AND id <> CAST(:id AS uuid)"""),
        {"c": base[0], "id": ejercicio_id},
    )
    fila = db.execute(
        text(f"""UPDATE ejercicios
                 SET activo = true, revisado_por = :r, revisado_en = now()
                 WHERE id = CAST(:id AS uuid) RETURNING {_COLS}"""),
        {"id": ejercicio_id, "r": revisor},
    ).mappings().one()
    db.commit()
    return dict(fila)


def desactivar(db: Session, ejercicio_id: str) -> dict | None:
    fila = db.execute(
        text(f"""UPDATE ejercicios SET activo = false
                 WHERE id = CAST(:id AS uuid) RETURNING {_COLS}"""),
        {"id": ejercicio_id},
    ).mappings().first()
    db.commit()
    return dict(fila) if fila else None


def hay_contenido(db: Session, habilidad: str) -> bool:
    return db.execute(
        text("SELECT 1 FROM ejercicios WHERE activo AND habilidad = :h LIMIT 1"),
        {"h": habilidad},
    ).first() is not None


def muestra(db: Session, habilidad: str, nivel: int, cantidad: int) -> list[dict]:
    """Ejercicios activos para jugar. Nunca incluye la respuesta correcta."""
    filas = db.execute(
        text("""SELECT id::text AS id, nivel, contenido FROM ejercicios
                WHERE activo AND habilidad = :h AND nivel = CAST(:n AS smallint)
                ORDER BY random() LIMIT CAST(:c AS int)"""),
        {"h": habilidad, "n": nivel, "c": cantidad},
    ).mappings().all()
    return [{"id": f["id"], "nivel": f["nivel"], "tipo": f["contenido"]["tipo"],
             "enunciado": f["contenido"]["enunciado"],
             "opciones": f["contenido"]["opciones"]} for f in filas]