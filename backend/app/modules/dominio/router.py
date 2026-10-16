from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_rol
from app.modules.dominio import service
from app.modules.dominio.schemas import DominioOut
from app.modules.ninos import service as ninos

router = APIRouter(prefix="/dominio", tags=["dominio"])


@router.get("/{nino_id}", response_model=DominioOut)
def ver(nino_id: UUID, u: dict = Depends(requiere_rol("padre")), db: Session = Depends(get_db)):
    nino = ninos.obtener(db, u["id"], str(nino_id))
    if nino is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Niño no encontrado")
    return {"nino_id": nino["id"], "habilidades": service.resumen(nino["dominio"])}