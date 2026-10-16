from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_rol
from app.modules.sesiones import service
from app.modules.sesiones.schemas import (
    CierreIn, CierreOut, EjercicioPublico, SesionIn, SesionOut,ObservacionOut,
)
from app.modules.atencion import observaciones as obs
from app.modules.ninos import service as ninos

from app.modules.sesiones.schemas import VerificarIn, VerificarOut

router = APIRouter(prefix="/sesiones", tags=["sesiones"])
solo_padres = requiere_rol("padre")
_404 = HTTPException(status.HTTP_404_NOT_FOUND, "No encontrado")


@router.post("", response_model=SesionOut, status_code=201)
def iniciar(datos: SesionIn, u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    try:
        return service.iniciar(db, u["id"], str(datos.nino_id), datos.habilidad)
    except service.NoEncontrada:
        raise _404
    except service.SinContenido:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Aún no hay ejercicios activos para esa habilidad")


@router.get("", response_model=list[SesionOut])
def historial(nino_id: UUID, u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    return service.listar(db, u["id"], str(nino_id))


@router.get("/{sesion_id}", response_model=SesionOut)
def obtener(sesion_id: UUID, u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    sesion = service.obtener(db, u["id"], str(sesion_id))
    if sesion is None:
        raise _404
    return sesion


@router.get("/{sesion_id}/ejercicios", response_model=list[EjercicioPublico])
def ejercicios(sesion_id: UUID, cantidad: int = Query(5, ge=1, le=20),
               u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    try:
        return service.ejercicios_para(db, u["id"], str(sesion_id), cantidad)
    except service.NoEncontrada:
        raise _404
    except service.SesionCerrada:
        raise HTTPException(status.HTTP_409_CONFLICT, "La sesión ya fue cerrada")


@router.post("/{sesion_id}/cerrar", response_model=CierreOut)
def cerrar(sesion_id: UUID, datos: CierreIn, u: dict = Depends(solo_padres),
           db: Session = Depends(get_db)):
    respuestas = [{"ejercicio_id": str(r.ejercicio_id), "elecciones": r.elecciones, "ms": r.ms}
                  for r in datos.respuestas]
    try:
            return service.cerrar(db, u["id"], str(sesion_id), respuestas, datos.detalle.model_dump())
    except service.NoEncontrada:
        raise _404
    except service.SesionCerrada:
        raise HTTPException(status.HTTP_409_CONFLICT, "La sesión ya fue cerrada")
    except service.RespuestasInvalidas as e:
        raise HTTPException(422, str(e))

@router.get("/{sesion_id}/observaciones", response_model=list[ObservacionOut])
def observaciones(sesion_id: UUID, u: dict = Depends(solo_padres),
                  db: Session = Depends(get_db)):
    sesion = service.obtener(db, u["id"], str(sesion_id))
    if sesion is None:
        raise _404
    nino = ninos.obtener(db, u["id"], sesion["nino_id"])
    return obs.generar(nino["nombre"], sesion["kpi"].get("atencion"))


@router.post("/{sesion_id}/ejercicios/{ejercicio_id}/verificar", response_model=VerificarOut)
def verificar(sesion_id: UUID, ejercicio_id: UUID, datos: VerificarIn,
              u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    try:
        return {"correcta": service.verificar(db, u["id"], str(sesion_id), str(ejercicio_id),
                                              datos.eleccion)}
    except service.NoEncontrada:
        raise _404
    except service.SesionCerrada:
        raise HTTPException(status.HTTP_409_CONFLICT, "La sesión ya fue cerrada")
    except service.RespuestasInvalidas as e:
        raise HTTPException(422, str(e))
