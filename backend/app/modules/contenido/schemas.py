from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class ContenidoOpcionMultiple(BaseModel):
    tipo: Literal["opcion_multiple"]
    enunciado: str = Field(min_length=1, max_length=500)
    opciones: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        min_length=2, max_length=6)
    correcta: int = Field(ge=0)

    @model_validator(mode="after")
    def _correcta_en_rango(self):
        if self.correcta >= len(self.opciones):
            raise ValueError("'correcta' debe ser un índice de 'opciones'")
        return self


class EjercicioIn(BaseModel):
    codigo: str = Field(pattern=r"^[a-z0-9_-]{3,60}$")
    habilidad: str = Field(pattern=r"^[a-z_]{3,40}$")
    nivel: int = Field(ge=1, le=3)
    contenido: ContenidoOpcionMultiple


class EjercicioAdminOut(BaseModel):
    id: str
    codigo: str
    habilidad: str
    nivel: int
    version: int
    activo: bool
    contenido: dict
    revisado_por: str | None
    revisado_en: datetime | None