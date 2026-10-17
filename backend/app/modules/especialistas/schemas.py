from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AccesoIn(BaseModel):
    nino_id: UUID
    email: EmailStr
    alcance: Literal["resumen", "completo"]
    # Máximo 90 días; también lo impone la base de datos.
    dias: int = Field(default=30, ge=1, le=90)


class AccesoOut(BaseModel):
    id: str
    nino_id: str
    especialista_email: str
    alcance: Literal["resumen", "completo"]
    creado_en: datetime
    expira_en: datetime
    revocado_en: datetime | None
    estado: Literal["vigente", "expirado", "revocado"]


class AuditoriaOut(BaseModel):
    id: int
    accion: Literal["otorgado", "revocado", "consultado"]
    alcance: Literal["resumen", "completo"] | None
    especialista_email: str
    fecha: datetime


class NinoCompartidoOut(BaseModel):
    nino_id: str
    nombre: str
    edad: int
    alcance: Literal["resumen", "completo"]
    expira_en: datetime
