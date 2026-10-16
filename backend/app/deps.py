from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import TokenInvalido, decodificar_token
from app.db import get_db

_bearer = HTTPBearer(auto_error=False)
_NO_AUTH = HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")


def usuario_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> dict:
    if cred is None:
        raise _NO_AUTH
    try:
        payload = decodificar_token(cred.credentials, "access")
    except TokenInvalido:
        raise _NO_AUTH
    fila = db.execute(
        text("SELECT id::text AS id, email::text AS email, rol, token_version "
             "FROM usuarios WHERE id = CAST(:id AS uuid)"),
        {"id": payload["sub"]},
    ).mappings().first()
    if fila is None or fila["token_version"] != payload["ver"]:
        raise _NO_AUTH
    return {**fila, "id": str(fila["id"]), "email": str(fila["email"])}


def requiere_rol(*roles: str):
    def _check(u: dict = Depends(usuario_actual)) -> dict:
        if u["rol"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin permiso")
        return u
    return _check


def zona_padres(
    u: dict = Depends(requiere_rol("padre")),
    x_zona_padres: str | None = Header(default=None),
) -> dict:
    """Exige el token que se obtiene al verificar el PIN (header X-Zona-Padres)."""
    err = HTTPException(status.HTTP_403_FORBIDDEN, detail={"codigo": "zona_padres_requerida"})
    if not x_zona_padres:
        raise err
    try:
        p = decodificar_token(x_zona_padres, "zona")
    except TokenInvalido:
        raise err
    if p["sub"] != u["id"] or p["ver"] != u["token_version"]:
        raise err
    return u