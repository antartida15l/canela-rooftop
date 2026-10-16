from fastapi import Depends, FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.db import get_db
from app.modules.cuentas.router import router as cuentas_router
from app.modules.consentimientos.router import router as consentimientos_router
from app.modules.ninos.router import router as ninos_router
from app.modules.contenido.router import router as contenido_router
from app.modules.sesiones.router import router as sesiones_router


app = FastAPI(title="NeuroBridge API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(cuentas_router)
app.include_router(cuentas_router)
app.include_router(consentimientos_router)
app.include_router(ninos_router)
app.include_router(contenido_router)
app.include_router(sesiones_router)

@app.get("/salud")
def salud(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"estado": "ok"}