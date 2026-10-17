import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.reportes import service as reportes

_ACCESO_SEL = """a.id::text AS id, a.nino_id::text AS nino_id,
        u.email::text AS especialista_email, a.alcance, a.creado_en, a.expira_en, a.revocado_en,
        CASE WHEN a.revocado_en IS NOT NULL THEN 'revocado'
             WHEN a.expira_en <= now() THEN 'expirado'
             ELSE 'vigente' END AS estado"""


class NoEncontrado(Exception):
    pass


class EspecialistaNoEncontrado(Exception):
    pass


class AccesoVigenteExiste(Exception):
    pass


def _auditar(db: Session, nino_id: str, acceso_id: str | None, especialista_id: str,
             especialista_email: str, actor_id: str, accion: str, alcance: str | None,
             detalle: dict | None = None) -> None:
    db.execute(
        text("""INSERT INTO auditoria_accesos
                  (nino_id, acceso_id, especialista_id, especialista_email, actor_id,
                   accion, alcance, detalle)
                VALUES (CAST(:n AS uuid), CAST(:a AS uuid), CAST(:e AS uuid), :em,
                        CAST(:ac AS uuid), :ax, :al, CAST(:d AS jsonb))"""),
        {"n": nino_id, "a": acceso_id, "e": especialista_id, "em": especialista_email,
         "ac": actor_id, "ax": accion, "al": alcance, "d": json.dumps(detalle or {})},
    )


# ---------- Lado del padre ----------
def otorgar(db: Session, padre_id: str, nino_id: str, email: str, alcance: str, dias: int) -> dict:
    nino = db.execute(
        text("SELECT id FROM ninos WHERE id = CAST(:n AS uuid) AND padre_id = CAST(:p AS uuid) "
             "FOR UPDATE"),
        {"n": nino_id, "p": padre_id},
    ).first()
    if nino is None:
        db.rollback()
        raise NoEncontrado()
    esp = db.execute(
        text("SELECT id::text AS id, email::text AS email FROM usuarios "
             "WHERE email = :e AND rol = 'especialista'"),
        {"e": email},
    ).mappings().first()
    if esp is None:
        db.rollback()
        raise EspecialistaNoEncontrado()
    vigente = db.execute(
        text("""SELECT 1 FROM accesos_especialista
                WHERE nino_id = CAST(:n AS uuid) AND especialista_id = CAST(:e AS uuid)
                  AND revocado_en IS NULL AND expira_en > now()"""),
        {"n": nino_id, "e": esp["id"]},
    ).first()
    if vigente:
        db.rollback()
        raise AccesoVigenteExiste()

    acceso_id = db.execute(
        text("""INSERT INTO accesos_especialista (nino_id, especialista_id, alcance, expira_en)
                VALUES (CAST(:n AS uuid), CAST(:e AS uuid), :al, now() + (:d * INTERVAL '1 day'))
                RETURNING id::text"""),
        {"n": nino_id, "e": esp["id"], "al": alcance, "d": dias},
    ).scalar_one()
    _auditar(db, nino_id, acceso_id, esp["id"], esp["email"], padre_id, "otorgado", alcance,
             {"dias": dias})
    db.commit()
    return obtener_acceso(db, padre_id, acceso_id)


def obtener_acceso(db: Session, padre_id: str, acceso_id: str) -> dict | None:
    fila = db.execute(
        text(f"""SELECT {_ACCESO_SEL}
                 FROM accesos_especialista a
                 JOIN ninos n ON n.id = a.nino_id
                 JOIN usuarios u ON u.id = a.especialista_id
                 WHERE a.id = CAST(:a AS uuid) AND n.padre_id = CAST(:p AS uuid)"""),
        {"a": acceso_id, "p": padre_id},
    ).mappings().first()
    return dict(fila) if fila else None


def listar_accesos(db: Session, padre_id: str, nino_id: str) -> list[dict]:
    filas = db.execute(
        text(f"""SELECT {_ACCESO_SEL}
                 FROM accesos_especialista a
                 JOIN ninos n ON n.id = a.nino_id
                 JOIN usuarios u ON u.id = a.especialista_id
                 WHERE a.nino_id = CAST(:n AS uuid) AND n.padre_id = CAST(:p AS uuid)
                 ORDER BY a.creado_en DESC"""),
        {"n": nino_id, "p": padre_id},
    ).mappings().all()
    return [dict(f) for f in filas]


def revocar(db: Session, padre_id: str, acceso_id: str) -> None:
    fila = db.execute(
        text("""UPDATE accesos_especialista a SET revocado_en = now()
                FROM ninos n
                WHERE a.id = CAST(:a AS uuid) AND n.id = a.nino_id
                  AND n.padre_id = CAST(:p AS uuid) AND a.revocado_en IS NULL
                RETURNING a.nino_id::text AS nino_id, a.especialista_id::text AS especialista_id,
                          a.alcance"""),
        {"a": acceso_id, "p": padre_id},
    ).mappings().first()
    if fila is None:
        db.rollback()
        raise NoEncontrado()
    email = db.execute(
        text("SELECT email::text FROM usuarios WHERE id = CAST(:e AS uuid)"),
        {"e": fila["especialista_id"]},
    ).scalar_one()
    _auditar(db, fila["nino_id"], acceso_id, fila["especialista_id"], email, padre_id,
             "revocado", fila["alcance"])
    db.commit()


def auditoria(db: Session, padre_id: str, nino_id: str, limite: int = 200) -> list[dict]:
    filas = db.execute(
        text("""SELECT au.id, au.accion, au.alcance, au.especialista_email::text AS especialista_email,
                       au.fecha
                FROM auditoria_accesos au JOIN ninos n ON n.id = au.nino_id
                WHERE au.nino_id = CAST(:n AS uuid) AND n.padre_id = CAST(:p AS uuid)
                ORDER BY au.fecha DESC, au.id DESC LIMIT CAST(:l AS int)"""),
        {"n": nino_id, "p": padre_id, "l": limite},
    ).mappings().all()
    return [dict(f) for f in filas]


# ---------- Lado del especialista (solo lectura) ----------
def alcance_vigente(db: Session, especialista_id: str, nino_id: str) -> str | None:
    return db.execute(
        text("""SELECT alcance FROM accesos_especialista
                WHERE nino_id = CAST(:n AS uuid) AND especialista_id = CAST(:e AS uuid)
                  AND revocado_en IS NULL AND expira_en > now()
                ORDER BY creado_en DESC LIMIT 1"""),
        {"n": nino_id, "e": especialista_id},
    ).scalar_one_or_none()


def ninos_compartidos(db: Session, especialista_id: str) -> list[dict]:
    filas = db.execute(
        text("""SELECT n.id::text AS nino_id, n.nombre, n.edad, a.alcance, a.expira_en
                FROM accesos_especialista a JOIN ninos n ON n.id = a.nino_id
                WHERE a.especialista_id = CAST(:e AS uuid)
                  AND a.revocado_en IS NULL AND a.expira_en > now()
                ORDER BY n.nombre"""),
        {"e": especialista_id},
    ).mappings().all()
    return [dict(f) for f in filas]


def reporte_como_especialista(db: Session, especialista: dict, nino_id: str, dias: int) -> dict | None:
    """Devuelve None si no hay un acceso vigente. Cada consulta queda auditada."""
    alcance = alcance_vigente(db, especialista["id"], nino_id)
    if alcance is None:
        return None
    reporte = reportes.construir_reporte(db, nino_id, dias, alcance)
    if reporte is None:
        return None
    _auditar(db, nino_id, None, especialista["id"], especialista["email"], especialista["id"],
             "consultado", alcance, {"dias": dias})
    db.commit()
    return reporte
