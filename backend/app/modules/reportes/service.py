from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.ninos import service as ninos
from app.modules.reportes import calculo


def construir_reporte(db: Session, nino_id: str, dias: int, alcance: str) -> dict | None:
    """OJO: no comprueba permisos. Quien la llame debe haber verificado antes que el padre
    es dueño del niño o que el especialista tiene un acceso vigente."""
    nino = db.execute(
        text("SELECT nombre, edad, dominio FROM ninos WHERE id = CAST(:n AS uuid)"),
        {"n": nino_id},
    ).mappings().first()
    if nino is None:
        return None
    filas = db.execute(
        text("""SELECT s.id::text AS id, s.inicio, s.ajustes->>'habilidad' AS habilidad,
                       s.nota::float AS nota, s.kpi
                FROM sesiones s
                WHERE s.nino_id = CAST(:n AS uuid) AND s.fin IS NOT NULL
                  AND s.inicio >= now() - (:d * INTERVAL '1 day')
                ORDER BY s.inicio ASC"""),
        {"n": nino_id, "d": dias},
    ).mappings().all()
    reporte = calculo.construir(dict(nino), [dict(f) for f in filas], dias, alcance)
    reporte["generado_en"] = datetime.now(timezone.utc)
    return reporte


def reporte_para_padre(db: Session, padre_id: str, nino_id: str, dias: int) -> dict | None:
    if ninos.obtener(db, padre_id, nino_id) is None:
        return None
    return construir_reporte(db, nino_id, dias, "completo")
