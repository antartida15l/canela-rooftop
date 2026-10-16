from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_rol
from app.modules.contenido import service
from app.modules.contenido.schemas import EjercicioAdminOut, EjercicioIn

router = APIRouter(prefix="/contenido", tags=["contenido"])
solo_admin = requiere_rol("admin")


@router.post("/ejercicios", response_model=EjercicioAdminOut, status_code=201)
def crear(datos: EjercicioIn, u: dict = Depends(solo_admin), db: Session = Depends(get_db)):
    return service.crear_borrador(db, datos.codigo, datos.habilidad, datos.nivel,
                                  datos.contenido.model_dump())


@router.get("/ejercicios", response_model=list[EjercicioAdminOut])
def listar(habilidad: str | None = None, activo: bool | None = None,
           u: dict = Depends(solo_admin), db: Session = Depends(get_db)):
    return service.listar(db, habilidad, activo)


@router.post("/ejercicios/{ejercicio_id}/activar", response_model=EjercicioAdminOut)
def activar(ejercicio_id: UUID, u: dict = Depends(solo_admin), db: Session = Depends(get_db)):
    """El revisor queda registrado con el correo del admin que activa."""
    fila = service.activar(db, str(ejercicio_id), u["email"])
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ejercicio no encontrado")
    return fila


@router.post("/ejercicios/{ejercicio_id}/desactivar", response_model=EjercicioAdminOut)
def desactivar(ejercicio_id: UUID, u: dict = Depends(solo_admin),
               db: Session = Depends(get_db)):
    fila = service.desactivar(db, str(ejercicio_id))
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ejercicio no encontrado")
    return fila