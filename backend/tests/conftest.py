import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

_env = dotenv_values(Path(__file__).resolve().parents[2] / ".env")
if "DATABASE_URL_TEST" not in _env:
    raise RuntimeError("Falta DATABASE_URL_TEST en el .env de la raíz")
os.environ["DATABASE_URL"] = _env["DATABASE_URL_TEST"]  # nunca tocar la base de desarrollo

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.rate_limit import limiter  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402

limiter.enabled = False


@pytest.fixture(autouse=True)
def limpiar_bd():
    with SessionLocal() as db:
        db.execute(text("TRUNCATE usuarios CASCADE"))
        db.execute(text("TRUNCATE usuarios, ejercicios CASCADE"))
        db.commit()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    with SessionLocal() as s:
        yield s


@pytest.fixture
def registrar(client):
    def _registrar(email="padre@test.pe", password="clave-larga-123"):
        r = client.post("/auth/registro", json={
            "email": email, "password": password, "acepta_terminos": True})
        assert r.status_code == 201, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _registrar

@pytest.fixture
def con_zona(client):
    """Define el PIN, lo verifica y devuelve headers con el token de zona de padres."""
    def _zona(headers, pin="1234", password="clave-larga-123"):
        client.put("/auth/pin", json={"pin": pin, "password": password}, headers=headers)
        r = client.post("/auth/pin/verificar", json={"pin": pin}, headers=headers)
        assert r.status_code == 200, r.text
        return {**headers, "X-Zona-Padres": r.json()["zona_token"]}
    return _zona

@pytest.fixture
def nino_de(client, con_zona):
    def _nino(headers, nombre="Luis", condicion="ninguna"):
        r = client.post("/ninos", json={"nombre": nombre, "edad": 8, "condicion": condicion},
                        headers=con_zona(headers))
        assert r.status_code == 201, r.text
        return r.json()["id"]
    return _nino


EJERCICIOS_BASE = [
    ("suma-1", "matematica_suma", 1, "2 + 3 = ?", ["4", "5", "6"], 1),
    ("suma-2", "matematica_suma", 1, "1 + 1 = ?", ["2", "3", "4"], 0),
    ("suma-3", "matematica_suma", 1, "4 + 4 = ?", ["6", "7", "8"], 2),
    ("lectura-1", "lectura_vocales", 1, "¿Cuál es una vocal?", ["b", "a", "z"], 1),
]


@pytest.fixture
def contenido_activo(client, registrar, db):
    """Crea un admin y deja 3 ejercicios de suma y 1 de lectura, activos y revisados."""
    h = registrar("admin@test.pe")
    db.execute(text("UPDATE usuarios SET rol = 'admin' WHERE email = 'admin@test.pe'"))
    db.commit()
    ids = {}
    for codigo, hab, nivel, enunciado, opciones, correcta in EJERCICIOS_BASE:
        r = client.post("/contenido/ejercicios", headers=h, json={
            "codigo": codigo, "habilidad": hab, "nivel": nivel,
            "contenido": {"tipo": "opcion_multiple", "enunciado": enunciado,
                          "opciones": opciones, "correcta": correcta}})
        assert r.status_code == 201, r.text
        eid = r.json()["id"]
        assert client.post(f"/contenido/ejercicios/{eid}/activar", headers=h).status_code == 200
        ids[codigo] = {"id": eid, "correcta": correcta}
    return {"admin": h, "ids": ids}


@pytest.fixture
def objetivo_3(db):
    """La sesión espera 3 ejercicios (en el catálogo viene de ajustes del perfil)."""
    db.execute(text("UPDATE perfiles_apoyo SET ajustes = ajustes || "
                    "jsonb_build_object('ejercicios_objetivo', 3) WHERE codigo = 'general'"))
    db.commit()
    yield
    db.execute(text("UPDATE perfiles_apoyo SET ajustes = ajustes - 'ejercicios_objetivo' "
                    "WHERE codigo = 'general'"))
    db.commit()


@pytest.fixture
def especialista_de(registrar, db):
    """Crea una cuenta y la convierte en especialista (en producción lo hace un administrador)."""
    def _crear(email="doc@test.pe"):
        h = registrar(email)
        db.execute(text("UPDATE usuarios SET rol = 'especialista' WHERE email = :e"), {"e": email})
        db.commit()
        return h
    return _crear
