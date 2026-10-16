from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.security import (
    COOKIE_REFRESH, TokenInvalido, borrar_cookie_refresh, crear_access_token,
    crear_refresh_token, crear_zona_token, decodificar_token, hash_secreto,
    poner_cookie_refresh, verificar_secreto,
)
from app.db import get_db
from app.deps import usuario_actual
from app.modules.cuentas import service
from app.modules.cuentas.schemas import (
    LoginIn, PinIn, PinSetIn, RegistroIn, TokenOut, UsuarioOut,
)
from app.modules.consentimientos import service as consentimientos
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["cuentas"])

_HASH_FALSO = hash_secreto("hash-para-igualar-tiempos")
_CRED_MALAS = HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales incorrectas")


def _emitir(response: Response, u: dict) -> TokenOut:
    poner_cookie_refresh(
        response, crear_refresh_token(u["id"], u["rol"], u["token_version"]))
    return TokenOut(access_token=crear_access_token(u["id"], u["rol"], u["token_version"]))

@router.post("/registro", response_model=TokenOut, status_code=201)
@limiter.limit("5/minute")
def registro(
    request: Request,
    datos: RegistroIn,
    response: Response,
    db: Session = Depends(get_db)
):
    if not datos.acepta_terminos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debes aceptar los términos para registrarte"
        )

    u = service.crear_usuario(db, datos.email, datos.password)

    if u is None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese correo ya está registrado"
        )

    consentimientos.registrar(db, u["id"], "terminos", True)
    db.commit()

    return _emitir(response, u)


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
def login(request: Request, datos: LoginIn, response: Response,
          db: Session = Depends(get_db)):
    u = service.buscar_por_email(db, datos.email)
    if u is None:
        verificar_secreto(_HASH_FALSO, datos.password)
        raise _CRED_MALAS
    if not verificar_secreto(u["pass_hash"], datos.password):
        raise _CRED_MALAS
    return _emitir(response, u)


@router.post("/refresh", response_model=TokenOut)
@limiter.limit("30/minute")
def refresh(request: Request, response: Response,
            nb_refresh: str | None = Cookie(default=None, alias=COOKIE_REFRESH),
            db: Session = Depends(get_db)):
    no_auth = HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión no válida")
    if nb_refresh is None:
        raise no_auth
    try:
        payload = decodificar_token(nb_refresh, "refresh")
    except TokenInvalido:
        raise no_auth
    u = service.buscar_por_id(db, payload["sub"])
    if u is None or u["token_version"] != payload["ver"]:
        raise no_auth
    return _emitir(response, u)  # rota también el refresh


@router.post("/logout", status_code=204)
def logout(response: Response):
    borrar_cookie_refresh(response)


@router.post("/logout-todo", status_code=204)
def logout_todo(response: Response, u: dict = Depends(usuario_actual),
                db: Session = Depends(get_db)):
    service.cerrar_todas_las_sesiones(db, u["id"])
    borrar_cookie_refresh(response)


@router.get("/yo", response_model=UsuarioOut)
def yo(u: dict = Depends(usuario_actual)):
    return UsuarioOut(id=u["id"], email=u["email"], rol=u["rol"])


# ---------- PIN de la zona de padres ----------
@router.put("/pin", status_code=204)
@limiter.limit("10/minute")
def definir_pin(request: Request, datos: PinSetIn, u: dict = Depends(usuario_actual),
                db: Session = Depends(get_db)):
    completo = service.buscar_por_id(db, u["id"])
    if not verificar_secreto(completo["pass_hash"], datos.password):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Contraseña incorrecta")
    service.guardar_pin(db, u["id"], datos.pin)


@router.post("/pin/verificar")
@limiter.limit("20/minute")
def verificar_pin(request: Request, datos: PinIn, u: dict = Depends(usuario_actual),
                  db: Session = Depends(get_db)):
    resultado = service.verificar_pin(db, u["id"], datos.pin)
    if resultado == "ok":
        return {
            "ok": True,
            "zona_token": crear_zona_token(u["id"], u["rol"], u["token_version"]),
            "expira_en_min": get_settings().zona_padres_minutes,
        }    
    if resultado == "bloqueado":
        raise HTTPException(
            status.HTTP_423_LOCKED,
            f"PIN bloqueado por {service.BLOQUEO_PIN_MIN} minutos por demasiados intentos")
    if resultado == "sin_pin":
        raise HTTPException(status.HTTP_409_CONFLICT, "Aún no has definido un PIN")
    raise HTTPException(status.HTTP_403_FORBIDDEN, "PIN incorrecto")