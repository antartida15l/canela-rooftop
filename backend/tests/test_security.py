from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import get_settings
from app.core import security as s


def test_hash_y_verificacion():
    h = s.hash_secreto("clave-segura-123")
    assert h.startswith("$argon2id$")
    assert s.verificar_secreto(h, "clave-segura-123")
    assert not s.verificar_secreto(h, "otra")


def test_verificar_con_hash_basura_no_revienta():
    assert not s.verificar_secreto("no-es-un-hash", "x")


@pytest.mark.parametrize("pin,ok", [("1234", True), ("123456", True),
                                    ("123", False), ("1234567", False), ("12a4", False)])
def test_pin(pin, ok):
    assert s.pin_valido(pin) is ok


def test_access_token_ida_y_vuelta():
    t = s.crear_access_token("u-1", "padre", 3)
    p = s.decodificar_token(t, "access")
    assert (p["sub"], p["rol"], p["ver"]) == ("u-1", "padre", 3)


def test_refresh_no_sirve_como_access():
    t = s.crear_refresh_token("u-1", "padre", 0)
    with pytest.raises(s.TokenInvalido):
        s.decodificar_token(t, "access")


def test_token_expirado():
    ahora = datetime.now(timezone.utc)
    t = jwt.encode({"sub": "u", "rol": "padre", "ver": 0, "type": "access",
                    "exp": ahora - timedelta(seconds=1)},
                   get_settings().jwt_secret, algorithm="HS256")
    with pytest.raises(s.TokenInvalido):
        s.decodificar_token(t, "access")


def test_token_con_firma_ajena():
    t = jwt.encode({"sub": "u", "type": "access"}, "otro-secreto-de-32-bytes-o-mas!!", algorithm="HS256")
    with pytest.raises(s.TokenInvalido):
        s.decodificar_token(t, "access")