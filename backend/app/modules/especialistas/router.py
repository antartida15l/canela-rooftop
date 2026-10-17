from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_rol, zona_padres
from app.modules.especialistas import service
from app.modules.especialistas.schemas import (
    AccesoIn, AccesoOut, AuditoriaOut, NinoCompartidoOut,
)
from app.modules.reportes.schemas import ReporteOut

# ---------------- Padres: dan, ven y quitan accesos ----------------
router = APIRouter(prefix="/accesos", tags=["especialistas"])
solo_padres = requiere_rol("padre")


@router.post("", response_model=AccesoOut, status_code=201)
def otorgar(datos: AccesoIn, u: dict = Depends(zona_padres), db: Session = Depends(get_db)):
    try:
        return service.otorgar(db, u["id"], str(datos.nino_id), datos.email, datos.alcance, datos.dias)
    except service.NoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Niño no encontrado")
    except service.EspecialistaNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            "No hay un especialista registrado con ese correo")
    except service.AccesoVigenteExiste:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Ese especialista ya tiene un acceso vigente. Revócalo primero para cambiarlo")


@router.get("", response_model=list[AccesoOut])
def listar(nino_id: UUID, u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    return service.listar_accesos(db, u["id"], str(nino_id))


@router.get("/auditoria", response_model=list[AuditoriaOut])
def auditoria(nino_id: UUID, u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    return service.auditoria(db, u["id"], str(nino_id))


@router.delete("/{acceso_id}", status_code=204)
def revocar(acceso_id: UUID, u: dict = Depends(zona_padres), db: Session = Depends(get_db)):
    try:
        service.revocar(db, u["id"], str(acceso_id))
    except service.NoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Acceso no encontrado o ya revocado")


# ---------------- Especialistas: solo lectura ----------------
router_especialista = APIRouter(prefix="/especialista", tags=["especialista"])
solo_especialistas = requiere_rol("especialista")


@router_especialista.get("/ninos", response_model=list[NinoCompartidoOut])
def ninos(u: dict = Depends(solo_especialistas), db: Session = Depends(get_db)):
    return service.ninos_compartidos(db, u["id"])


@router_especialista.get("/ninos/{nino_id}/reporte", response_model=ReporteOut)
def reporte(nino_id: UUID, dias: int = Query(30, ge=7, le=365),
            u: dict = Depends(solo_especialistas), db: Session = Depends(get_db)):
    r = service.reporte_como_especialista(db, u, str(nino_id), dias)
    if r is None:
        # 404 tanto si no existe como si no hay acceso: no se revela cuál de los dos
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontrado")
    return r
