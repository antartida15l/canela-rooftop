from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings

# Hipótesis de diseño, no diagnóstico: la condición declarada solo elige un perfil
# interno de ajustes. Lo que no esté aquí usa el perfil base.
PERFIL_POR_CONDICION = {
    "tdah": "tdah",
    "tea": "tea",
    "dislexia": "dislexia",
    "discalculia": "discalculia",
}

_COLS = "id::text AS id, nombre, edad, perfil, dominio, creado_en"


def perfil_para(condicion: str) -> str:
    return PERFIL_POR_CONDICION.get(condicion, "general")


def _clave() -> str:
    return get_settings().condicion_key


def crear(db: Session, padre_id: str, nombre: str, edad: int, condicion: str) -> dict:
    fila = db.execute(
        text(f"""INSERT INTO ninos (padre_id, nombre, edad, condicion_cifrada, perfil)
                 VALUES (CAST(:p AS uuid), :n, :e,
                         pgp_sym_encrypt(CAST(:c AS text), CAST(:k AS text)), :perfil)
                 RETURNING {_COLS}"""),
        {"p": padre_id, "n": nombre, "e": edad, "c": condicion,
         "k": _clave(), "perfil": perfil_para(condicion)},
    ).mappings().one()
    db.commit()
    return dict(fila)


def listar(db: Session, padre_id: str) -> list[dict]:
    filas = db.execute(
        text(f"""SELECT {_COLS} FROM ninos
                 WHERE padre_id = CAST(:p AS uuid) ORDER BY creado_en"""),
        {"p": padre_id},
    ).mappings().all()
    return [dict(f) for f in filas]


def obtener(db: Session, padre_id: str, nino_id: str) -> dict | None:
    fila = db.execute(
        text(f"""SELECT {_COLS} FROM ninos
                 WHERE id = CAST(:id AS uuid) AND padre_id = CAST(:p AS uuid)"""),
        {"id": nino_id, "p": padre_id},
    ).mappings().first()
    return dict(fila) if fila else None


def actualizar(db: Session, padre_id: str, nino_id: str, datos: dict) -> dict | None:
    condicion = datos.get("condicion")
    fila = db.execute(
        text(f"""UPDATE ninos SET
                   nombre = COALESCE(CAST(:n AS text), nombre),
                   edad   = COALESCE(CAST(:e AS smallint), edad),
                   condicion_cifrada = CASE WHEN CAST(:c AS text) IS NULL
                        THEN condicion_cifrada
                        ELSE pgp_sym_encrypt(CAST(:c AS text), CAST(:k AS text)) END,
                   perfil = COALESCE(CAST(:perfil AS text), perfil)
                 WHERE id = CAST(:id AS uuid) AND padre_id = CAST(:p AS uuid)
                 RETURNING {_COLS}"""),
        {"id": nino_id, "p": padre_id, "n": datos.get("nombre"), "e": datos.get("edad"),
         "c": condicion, "k": _clave(),
         "perfil": perfil_para(condicion) if condicion else None},
    ).mappings().first()
    db.commit()
    return dict(fila) if fila else None


def leer_condicion(db: Session, padre_id: str, nino_id: str) -> str | None:
    fila = db.execute(
        text("""SELECT pgp_sym_decrypt(condicion_cifrada, CAST(:k AS text)) AS condicion
                FROM ninos
                WHERE id = CAST(:id AS uuid) AND padre_id = CAST(:p AS uuid)"""),
        {"id": nino_id, "p": padre_id, "k": _clave()},
    ).mappings().first()
    return fila["condicion"] if fila else None


def eliminar(db: Session, padre_id: str, nino_id: str) -> bool:
    """Borrado definitivo. Las sesiones y respuestas caen en cascada."""
    fila = db.execute(
        text("""DELETE FROM ninos
                WHERE id = CAST(:id AS uuid) AND padre_id = CAST(:p AS uuid)
                RETURNING id"""),
        {"id": nino_id, "p": padre_id},
    ).first()
    db.commit()
    return fila is not None