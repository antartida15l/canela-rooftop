from sqlalchemy import text

PASS = "clave-larga-123"


def _definir(client, h, pin="1234"):
    return client.put("/auth/pin", json={"pin": pin, "password": PASS}, headers=h)


def _verificar(client, h, pin):
    return client.post("/auth/pin/verificar", json={"pin": pin}, headers=h)


def test_definir_y_verificar_pin(client, registrar):
    h = registrar()
    assert _definir(client, h).status_code == 204
    assert _verificar(client, h, "1234").status_code == 200


def test_definir_pin_pide_contraseña_correcta(client, registrar):
    h = registrar()
    r = client.put("/auth/pin", json={"pin": "1234", "password": "mala-mala-mala"}, headers=h)
    assert r.status_code == 403


def test_pin_formato_invalido(client, registrar):
    h = registrar()
    for malo in ("123", "1234567", "12a4"):
        assert client.put("/auth/pin", json={"pin": malo, "password": PASS}, headers=h).status_code == 422


def test_verificar_sin_pin_definido(client, registrar):
    h = registrar()
    assert _verificar(client, h, "1234").status_code == 409


def test_bloqueo_tras_5_intentos_fallidos(client, registrar):
    h = registrar()
    _definir(client, h)
    for _ in range(4):
        assert _verificar(client, h, "0000").status_code == 403
    assert _verificar(client, h, "0000").status_code == 423      # el 5.º bloquea
    assert _verificar(client, h, "1234").status_code == 423      # ni el PIN correcto pasa


def test_bloqueo_expira(client, registrar, db):
    h = registrar()
    _definir(client, h)
    for _ in range(5):
        _verificar(client, h, "0000")
    db.execute(text("UPDATE usuarios SET pin_bloqueado_hasta = now() - INTERVAL '1 second'"))
    db.commit()
    assert _verificar(client, h, "1234").status_code == 200


def test_acierto_reinicia_el_contador(client, registrar):
    h = registrar()
    _definir(client, h)
    for _ in range(4):
        _verificar(client, h, "0000")
    assert _verificar(client, h, "1234").status_code == 200
    for _ in range(4):
        assert _verificar(client, h, "0000").status_code == 403  # no se bloquea aún