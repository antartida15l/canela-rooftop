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