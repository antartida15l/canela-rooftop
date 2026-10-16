from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Condicion = Literal["tdah", "tea", "dislexia", "discalculia",
                    "ninguna", "otra", "prefiero_no_decir"]


class NinoIn(BaseModel):
    nombre: Nombre
    edad: int = Field(ge=3, le=18)
    condicion: Condicion = "ninguna"


class NinoUpdate(BaseModel):
    nombre: Nombre | None = None
    edad: int | None = Field(default=None, ge=3, le=18)
    condicion: Condicion | None = None

    @model_validator(mode="after")
    def _algo_que_cambiar(self):
        if self.nombre is None and self.edad is None and self.condicion is None:
            raise ValueError("Indica al menos un campo para actualizar")
        return self


class NinoOut(BaseModel):
    id: str
    nombre: str
    edad: int
    perfil: str
    dominio: dict
    creado_en: datetime


class CondicionOut(BaseModel):
    condicion: str