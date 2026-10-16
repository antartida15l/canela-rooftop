from sqlalchemy import text
from sqlalchemy.orm import Session

TIPOS = ("terminos", "camara", "investigacion")

# Subir la versión de un tipo cuando cambie su texto legal (validado por el abogado).
# Todos los usuarios tendrán que aceptar de nuevo ese tipo.
VERSIONES = {
    "terminos": "2026-01",
    "camara": "2026-01",
    "investigacion": "2026-01",
}


def registrar(db: Session, usuario_id: str, tipo: str, aceptado: bool) -> None:
    """Inserta una fila con la versión vigente. No hace commit."""
    db.execute(
        text("""INSERT INTO consentimientos (usuario_id, tipo, version, aceptado)
                VALUES (CAST(:u AS uuid), :t, :v, :a)"""),
        {"u": usuario_id, "t": tipo, "v": VERSIONES[tipo], "a": aceptado},
    )


def cambiar(db: Session, usuario_id: str, tipo: str, aceptado: bool) -> None:
    registrar(db, usuario_id, tipo, aceptado)
    db.commit()


def estado_todos(db: Session, usuario_id: str) -> list[dict]:
    """Última fila de cada tipo, con la vigencia ya calculada."""
    filas = db.execute(
        text("""SELECT DISTINCT ON (tipo) tipo, version, aceptado, fecha
                FROM consentimientos WHERE usuario_id = CAST(:u AS uuid)
                ORDER BY tipo, fecha DESC"""),
        {"u": usuario_id},
    ).mappings().all()
    ultimas = {f["tipo"]: f for f in filas}

    salida = []
    for tipo in TIPOS:
        f = ultimas.get(tipo)
        misma_version = f is not None and f["version"] == VERSIONES[tipo]
        salida.append({
            "tipo": tipo,
            "version_vigente": VERSIONES[tipo],
            "aceptado": bool(f and f["aceptado"] and misma_version),
            "version_aceptada": f["version"] if f else None,
            "fecha": f["fecha"] if f else None,
            "requiere_reaceptacion": bool(f and f["aceptado"] and not misma_version),
        })
    return salida


def consentimiento_vigente(db: Session, usuario_id: str, tipo: str) -> bool:
    f = db.execute(
        text("""SELECT version, aceptado FROM consentimientos
                WHERE usuario_id = CAST(:u AS uuid) AND tipo = :t
                ORDER BY fecha DESC LIMIT 1"""),
        {"u": usuario_id, "t": tipo},
    ).mappings().first()
    return bool(f and f["aceptado"] and f["version"] == VERSIONES[tipo])


def historial(db: Session, usuario_id: str, tipo: str) -> list[dict]:
    filas = db.execute(
        text("""SELECT tipo, version, aceptado, fecha FROM consentimientos
                WHERE usuario_id = CAST(:u AS uuid) AND tipo = :t
                ORDER BY fecha DESC"""),
        {"u": usuario_id, "t": tipo},
    ).mappings().all()
    return [dict(f) for f in filas]