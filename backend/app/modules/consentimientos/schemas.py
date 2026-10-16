from datetime import datetime

from pydantic import BaseModel


class ConsentimientoOut(BaseModel):
    tipo: str
    version_vigente: str
    aceptado: bool                  # aceptado Y en la versión vigente
    version_aceptada: str | None
    fecha: datetime | None
    requiere_reaceptacion: bool


class CambioIn(BaseModel):
    aceptado: bool


class HistorialOut(BaseModel):
    tipo: str
    version: str
    aceptado: bool
    fecha: datetime