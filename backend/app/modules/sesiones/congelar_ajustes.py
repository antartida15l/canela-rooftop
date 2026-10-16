from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.consentimientos.service import consentimiento_vigente
from app.modules.sesiones.calificacion import OBJETIVO_POR_DEFECTO
from app.modules.atencion.reglas import PARAMS as PARAMS_ATENCION

def congelar(db: Session, padre_id: str, nino: dict, habilidad: str) -> dict:
    """Copia los ajustes del perfil y el estado de la cámara. No incluye el código del
    perfil ni la condición: lo que ve la aplicación del niño no debe delatarla."""
    fila = db.execute(
        text("SELECT ajustes FROM perfiles_apoyo WHERE codigo = :c"),
        {"c": nino["perfil"]},
    ).mappings().one()
    ajustes = dict(fila["ajustes"])
    ajustes.setdefault("ejercicios_objetivo", OBJETIVO_POR_DEFECTO)
    ajustes["habilidad"] = habilidad
    ajustes["camara"] = consentimiento_vigente(db, padre_id, "camara")
    ajustes["congelado_en"] = datetime.now(timezone.utc).isoformat()
    ajustes["atencion"] = dict(PARAMS_ATENCION)
    return ajustes