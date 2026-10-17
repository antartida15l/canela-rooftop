from app.modules.especialistas.router import router as accesos_router
from app.modules.especialistas.router import router_especialista
from app.modules.reportes.router import router as reportes_router
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
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
from app.modules.dominio.router import router as dominio_router

app = FastAPI(title="NeuroBridge API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Zona-Padres"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(cuentas_router)
app.include_router(cuentas_router)
app.include_router(consentimientos_router)
app.include_router(ninos_router)
app.include_router(contenido_router)
app.include_router(sesiones_router)
app.include_router(dominio_router)
app.include_router(reportes_router)
app.include_router(accesos_router)
app.include_router(router_especialista)

@app.get("/salud")
def salud(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"estado": "ok"}