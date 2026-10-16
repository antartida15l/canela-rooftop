from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_rol, zona_padres
from app.modules.ninos import service
from app.modules.ninos.schemas import CondicionOut, NinoIn, NinoOut, NinoUpdate

router = APIRouter(prefix="/ninos", tags=["ninos"])

solo_padres = requiere_rol("padre")
_NO_ENCONTRADO = HTTPException(status.HTTP_404_NOT_FOUND, "Niño no encontrado")


@router.get("", response_model=list[NinoOut])
def listar(u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    return service.listar(db, u["id"])


@router.post("", response_model=NinoOut, status_code=201)
def crear(datos: NinoIn, u: dict = Depends(zona_padres), db: Session = Depends(get_db)):
    return service.crear(db, u["id"], datos.nombre, datos.edad, datos.condicion)


@router.get("/{nino_id}", response_model=NinoOut)
def obtener(nino_id: UUID, u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    nino = service.obtener(db, u["id"], str(nino_id))
    if nino is None:
        raise _NO_ENCONTRADO
    return nino


@router.patch("/{nino_id}", response_model=NinoOut)
def actualizar(nino_id: UUID, datos: NinoUpdate, u: dict = Depends(zona_padres),
               db: Session = Depends(get_db)):
    nino = service.actualizar(db, u["id"], str(nino_id), datos.model_dump(exclude_none=True))
    if nino is None:
        raise _NO_ENCONTRADO
    return nino


@router.get("/{nino_id}/condicion", response_model=CondicionOut)
def ver_condicion(nino_id: UUID, u: dict = Depends(zona_padres),
                  db: Session = Depends(get_db)):
    condicion = service.leer_condicion(db, u["id"], str(nino_id))
    if condicion is None:
        raise _NO_ENCONTRADO
    return CondicionOut(condicion=condicion)


@router.delete("/{nino_id}", status_code=204)
def eliminar(nino_id: UUID, u: dict = Depends(zona_padres), db: Session = Depends(get_db)):
    if not service.eliminar(db, u["id"], str(nino_id)):
        raise _NO_ENCONTRADO