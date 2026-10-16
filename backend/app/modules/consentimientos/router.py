from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_rol
from app.modules.consentimientos import service
from app.modules.consentimientos.schemas import CambioIn, ConsentimientoOut, HistorialOut

router = APIRouter(prefix="/consentimientos", tags=["consentimientos"])

Tipo = Literal["terminos", "camara", "investigacion"]
solo_padres = requiere_rol("padre")


@router.get("", response_model=list[ConsentimientoOut])
def listar(u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    return service.estado_todos(db, u["id"])


@router.put("/{tipo}", response_model=list[ConsentimientoOut])
def cambiar(tipo: Tipo, datos: CambioIn, u: dict = Depends(solo_padres),
            db: Session = Depends(get_db)):
    if tipo == "terminos" and not datos.aceptado:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Los términos no se pueden retirar. Para hacerlo, elimina tu cuenta.")
    service.cambiar(db, u["id"], tipo, datos.aceptado)
    return service.estado_todos(db, u["id"])


@router.get("/{tipo}/historial", response_model=list[HistorialOut])
def historial(tipo: Tipo, u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    return service.historial(db, u["id"], tipo)