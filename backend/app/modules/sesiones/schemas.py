from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Emocion = Literal["neutral", "feliz", "triste", "enojo", "miedo", "sorpresa", "asco", "desprecio"]


class _Estricto(BaseModel):
    model_config = ConfigDict(extra="forbid")


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


# ---- Detalle: solo etiquetas y números, nunca imágenes ----
class PausaIn(_Estricto):
    inicio_s: int = Field(ge=0, le=14_400)
    duracion_s: int = Field(ge=0, le=3_600)
    motivo: Literal["programada", "solicitada", "sugerida"] = "programada"


class LecturaIn(_Estricto):
    t: int = Field(ge=0, le=14_400)           # segundos desde el inicio de la sesión
    rostro: bool = True
    atencion: float | None = Field(default=None, ge=0, le=1)
    emocion: Emocion | None = None

    @model_validator(mode="after")
    def _coherencia(self):
        if self.rostro and self.atencion is None:
            raise ValueError("con rostro detectado se requiere 'atencion'")
        if not self.rostro and (self.atencion is not None or self.emocion is not None):
            raise ValueError("sin rostro no puede haber atención ni emoción")
        return self


class IntervencionIn(_Estricto):
    t: int = Field(ge=0, le=14_400)
    tipo: Literal["aviso_suave", "pausa"]
    motivo: Literal["atencion_baja", "malestar", "ausente"]


class DetalleIn(_Estricto):
    pausas: list[PausaIn] = Field(default_factory=list, max_length=50)
    lecturas: list[LecturaIn] = Field(default_factory=list, max_length=1_500)
    intervenciones: list[IntervencionIn] = Field(default_factory=list, max_length=100)


class CierreIn(BaseModel):
    respuestas: list[RespuestaIn] = Field(max_length=100)
    detalle: DetalleIn = Field(default_factory=DetalleIn)


class CierreOut(BaseModel):
    nota: float | None
    kpi: dict


class ObservacionOut(BaseModel):
    nivel: Literal["info", "atencion"]
    texto: str