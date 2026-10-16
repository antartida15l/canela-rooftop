import json
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SesionIn(BaseModel):
    nino_id: UUID
    habilidad: str = Field(pattern=r"^[a-z_]{3,40}$")


class SesionOut(BaseModel):
    id: str
    nino_id: str
    inicio: datetime
    fin: datetime | None
    ajustes: dict
    kpi: dict
    nota: float | None


class EjercicioPublico(BaseModel):
    id: str
    nivel: int
    tipo: str
    enunciado: str
    opciones: list[str]


class RespuestaIn(BaseModel):
    ejercicio_id: UUID
    # Opciones elegidas en cada intento, en orden. La corrección la hace el servidor.
    elecciones: list[int] = Field(min_length=1, max_length=3)
    ms: int = Field(ge=0, le=600_000)

    @field_validator("elecciones")
    @classmethod
    def _indices_validos(cls, v: list[int]) -> list[int]:
        if any(e < 0 or e > 5 for e in v):
            raise ValueError("índice de opción fuera de rango")
        return v


class CierreIn(BaseModel):
    respuestas: list[RespuestaIn] = Field(max_length=100)
    # Pausas, lecturas emocionales e intervenciones. Solo etiquetas, nunca imágenes.
    detalle: dict = Field(default_factory=dict)

    @field_validator("detalle")
    @classmethod
    def _tamano(cls, v: dict) -> dict:
        if len(json.dumps(v)) > 200_000:
            raise ValueError("detalle demasiado grande")
        return v


class CierreOut(BaseModel):
    nota: float | None
    kpi: dict