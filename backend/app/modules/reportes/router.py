from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_rol
from app.modules.reportes import service
from app.modules.reportes.schemas import ReporteOut

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/{nino_id}", response_model=ReporteOut)
def reporte(nino_id: UUID, dias: int = Query(30, ge=7, le=365),
            u: dict = Depends(requiere_rol("padre")), db: Session = Depends(get_db)):
    r = service.reporte_para_padre(db, u["id"], str(nino_id), dias)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Niño no encontrado")
    return r
