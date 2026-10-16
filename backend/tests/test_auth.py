from sqlalchemy import text

from app.core.rate_limit import limiter
from app.core.security import crear_refresh_token

REG = {"email": "padre@test.pe", "password": "clave-larga-123", "acepta_terminos": True}


def test_registro_ok_guarda_consentimiento_y_cookie(client, db):
    r = client.post("/auth/registro", json=REG)
    assert r.status_code == 201
    assert r.json()["access_token"]
    assert "nb_refresh" in r.headers["set-cookie"]
    assert "httponly" in r.headers["set-cookie"].lower()
    fila = db.execute(text("SELECT tipo, aceptado FROM consentimientos")).one()
    assert (fila.tipo, fila.aceptado) == ("terminos", True)


def test_registro_exige_terminos(client):
    r = client.post("/auth/registro", json={**REG, "acepta_terminos": False})
    assert r.status_code == 422


def test_registro_password_corta(client):
    assert client.post("/auth/registro", json={**REG, "password": "corta"}).status_code == 422


def test_registro_email_duplicado_sin_distinguir_mayusculas(client):
    client.post("/auth/registro", json=REG)
    r = client.post("/auth/registro", json={**REG, "email": "PADRE@test.pe"})
    assert r.status_code == 409


def test_login_ok(client):
    client.post("/auth/registro", json=REG)
    r = client.post("/auth/login", json={"email": REG["email"], "password": REG["password"]})
    assert r.status_code == 200 and r.json()["access_token"]


def test_login_error_identico_para_usuario_inexistente_y_clave_mala(client):
    client.post("/auth/registro", json=REG)
    a = client.post("/auth/login", json={"email": REG["email"], "password": "incorrecta-123"})
    b = client.post("/auth/login", json={"email": "nadie@test.pe", "password": "incorrecta-123"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_yo_requiere_token(client, registrar):
    assert client.get("/auth/yo").status_code == 401
    h = registrar()
    r = client.get("/auth/yo", headers=h)
    assert r.status_code == 200 and r.json()["rol"] == "padre"


def test_refresh_con_cookie(client, registrar):
    registrar()
    r = client.post("/auth/refresh")
    assert r.status_code == 200 and r.json()["access_token"]


def test_refresh_sin_cookie(client):
    assert client.post("/auth/refresh").status_code == 401


def test_access_token_no_sirve_como_refresh(client, registrar):
    h = registrar()
    client.cookies.clear()
    client.cookies.set("nb_refresh", h["Authorization"].split()[1], path="/auth")
    assert client.post("/auth/refresh").status_code == 401


def test_logout_todo_invalida_access_y_refresh_anteriores(client, registrar):
    h = registrar()
    refresh_viejo = client.cookies.get("nb_refresh")
    assert client.post("/auth/logout-todo", headers=h).status_code == 204

    assert client.get("/auth/yo", headers=h).status_code == 401  # access viejo muerto
    client.cookies.set("nb_refresh", refresh_viejo, path="/auth")
    assert client.post("/auth/refresh").status_code == 401        # refresh viejo muerto


def test_logout_borra_cookie(client, registrar):
    registrar()
    client.post("/auth/logout")
    assert client.post("/auth/refresh").status_code == 401


def test_rate_limit_en_login(client):
    limiter.enabled = True
    limiter.reset()
    try:
        codigos = [client.post("/auth/login", json={"email": "a@b.pe", "password": "x"}).status_code
                   for _ in range(11)]
        assert codigos[-1] == 429
    finally:
        limiter.enabled = False
        limiter.reset()