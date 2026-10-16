from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import usuario_actual
from app.modules.consentimientos import service


def requiere_consentimiento(tipo: str):
    """Dependencia que bloquea con 403 si no hay consentimiento vigente de ese tipo."""
    def _check(u: dict = Depends(usuario_actual), db: Session = Depends(get_db)) -> dict:
        if not service.consentimiento_vigente(db, u["id"], tipo):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={"codigo": "consentimiento_requerido", "tipo": tipo},
            )
        return u
    return _check