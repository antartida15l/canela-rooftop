from pydantic import BaseModel


class HabilidadOut(BaseModel):
    nivel: int
    dominio: float
    racha: int
    muestras: int


class DominioOut(BaseModel):
    nino_id: str
    habilidades: dict[str, HabilidadOut]