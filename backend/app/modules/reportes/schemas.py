from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NinoReporte(BaseModel):
    nombre: str
    edad: int


class ResumenOut(BaseModel):
    sesiones: int
    minutos: int
    nota_media: float | None
    aciertos_pct: float | None
    tendencia: Literal["mejora", "estable", "baja", "insuficiente"]


class HabilidadReporte(BaseModel):
    habilidad: str
    sesiones: int
    nota_media: float | None
    nivel: int
    dominio: float


class SesionReporte(BaseModel):
    id: str
    inicio: datetime
    habilidad: str
    nota: float | None
    respondidas: int
    correctas: int


class AtencionReporte(BaseModel):
    sesiones_con_camara: int
    atencion_media: float | None
    pct_malestar: float
    avisos: int
    pausas_sugeridas: int


class Recomendacion(BaseModel):
    nivel: Literal["info", "sugerencia"]
    texto: str


class ReporteOut(BaseModel):
    periodo_dias: int
    generado_en: datetime
    alcance: Literal["resumen", "completo"]
    nino: NinoReporte
    resumen: ResumenOut
    habilidades: list[HabilidadReporte]
    sesiones: list[SesionReporte]
    # Solo con alcance "completo"
    atencion: AtencionReporte | None = None
    recomendaciones: list[Recomendacion] | None = None
