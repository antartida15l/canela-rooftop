import re
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Response

from app.config import get_settings

_hasher = PasswordHasher()  # Argon2id por defecto
_ALG = "HS256"
COOKIE_REFRESH = "nb_refresh"


class TokenInvalido(Exception):
    pass


# ---------- Contraseñas y PIN (Argon2id) ----------
def hash_secreto(texto: str) -> str:
    return _hasher.hash(texto)


def verificar_secreto(hash_guardado: str, texto: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, texto)
    except (VerificationError, InvalidHashError):
        return False


def pin_valido(pin: str) -> bool:
    return re.fullmatch(r"\d{4,6}", pin) is not None


# ---------- JWT ----------
def _crear(sub: str, rol: str, ver: int, tipo: str, vida: timedelta) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"sub": sub, "rol": rol, "ver": ver, "type": tipo,
               "iat": ahora, "exp": ahora + vida}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=_ALG)


def crear_access_token(user_id: str, rol: str, token_version: int) -> str:
    s = get_settings()
    return _crear(user_id, rol, token_version, "access",
                  timedelta(minutes=s.jwt_access_minutes))


def crear_refresh_token(user_id: str, rol: str, token_version: int) -> str:
    s = get_settings()
    return _crear(user_id, rol, token_version, "refresh",
                  timedelta(days=s.jwt_refresh_days))

def crear_zona_token(user_id: str, rol: str, token_version: int) -> str:
    s = get_settings()
    return _crear(user_id, rol, token_version, "zona",
                  timedelta(minutes=s.zona_padres_minutes))

def decodificar_token(token: str, tipo: str) -> dict:
    """Valida firma, expiración y que sea del tipo esperado (access o refresh)."""
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[_ALG])
    except jwt.PyJWTError as e:
        raise TokenInvalido(str(e)) from e
    if payload.get("type") != tipo:
        raise TokenInvalido("tipo de token incorrecto")
    return payload


# ---------- Cookie del refresh ----------
def poner_cookie_refresh(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        COOKIE_REFRESH, token,
        max_age=s.jwt_refresh_days * 86400,
        httponly=True, secure=s.cookie_secure,
        samesite="strict", path="/auth",
    )


def borrar_cookie_refresh(response: Response) -> None:
    response.delete_cookie(COOKIE_REFRESH, path="/auth")