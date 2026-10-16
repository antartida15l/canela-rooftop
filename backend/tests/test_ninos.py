from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import text

from app.config import get_settings


def _crear(client, zona, **kw):
    datos = {"nombre": "Luis", "edad": 8, "condicion": "tdah", **kw}
    return client.post("/ninos", json=datos, headers=zona)


def test_crear_asigna_perfil_y_no_expone_la_condicion(client, registrar, con_zona):
    r = _crear(client, con_zona(registrar()))
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["perfil"] == "tdah"
    assert "condicion" not in cuerpo and "condicion_cifrada" not in cuerpo


@pytest.mark.parametrize("condicion,perfil", [
    ("tdah", "tdah"), ("tea", "tea"), ("dislexia", "dislexia"),
    ("discalculia", "discalculia"), ("ninguna", "general"),
    ("otra", "general"), ("prefiero_no_decir", "general"),
])
def test_perfil_segun_condicion_declarada(client, registrar, con_zona, condicion, perfil):
    r = _crear(client, con_zona(registrar()), condicion=condicion)
    assert r.json()["perfil"] == perfil


def test_condicion_va_cifrada_en_la_base(client, registrar, con_zona, db):
    z = con_zona(registrar())
    nino = _crear(client, z, condicion="discalculia").json()

    crudo = db.execute(text("SELECT condicion_cifrada FROM ninos")).scalar_one()
    assert b"discalculia" not in bytes(crudo)
    assert client.get(f"/ninos/{nino['id']}/condicion", headers=z).json() == {
        "condicion": "discalculia"}

    # Con otra clave no se puede descifrar
    with pytest.raises(Exception):
        db.execute(text("SELECT pgp_sym_decrypt(condicion_cifrada, 'clave-equivocada') FROM ninos"))


def test_sin_zona_de_padres_no_se_puede_crear_editar_borrar_ni_ver_condicion(
        client, registrar, con_zona):
    h = registrar()
    z = con_zona(h)
    nid = _crear(client, z).json()["id"]

    for resp in (
        client.post("/ninos", json={"nombre": "X", "edad": 8}, headers=h),
        client.patch(f"/ninos/{nid}", json={"nombre": "X"}, headers=h),
        client.get(f"/ninos/{nid}/condicion", headers=h),
        client.delete(f"/ninos/{nid}", headers=h),
    ):
        assert resp.status_code == 403
        assert resp.json()["detail"]["codigo"] == "zona_padres_requerida"

    # Listar y ver nombre/edad/perfil sí funciona con la sesión normal (pantalla del niño)
    assert client.get("/ninos", headers=h).status_code == 200
    assert client.get(f"/ninos/{nid}", headers=h).status_code == 200


def test_token_de_zona_expirado(client, registrar, con_zona):
    h = registrar()
    con_zona(h)
    uid = client.get("/auth/yo", headers=h).json()["id"]
    vencido = jwt.encode(
        {"sub": uid, "rol": "padre", "ver": 0, "type": "zona",
         "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        get_settings().jwt_secret, algorithm="HS256")
    r = client.post("/ninos", json={"nombre": "X", "edad": 8},
                    headers={**h, "X-Zona-Padres": vencido})
    assert r.status_code == 403


def test_tokens_no_son_intercambiables(client, registrar, con_zona):
    h = registrar()
    z = con_zona(h)
    # zona como Bearer: no vale como access
    r = client.get("/ninos", headers={"Authorization": f"Bearer {z['X-Zona-Padres']}"})
    assert r.status_code == 401
    # access como zona: no vale como zona
    r = client.post("/ninos", json={"nombre": "X", "edad": 8},
                    headers={**h, "X-Zona-Padres": h["Authorization"].split()[1]})
    assert r.status_code == 403


def test_logout_todo_invalida_la_zona_de_padres(client, registrar, con_zona):
    h = registrar()
    z = con_zona(h)
    client.post("/auth/logout-todo", headers=h)
    h2 = {"Authorization": "Bearer " + client.post(
        "/auth/login", json={"email": "padre@test.pe", "password": "clave-larga-123"}
    ).json()["access_token"]}
    r = client.post("/ninos", json={"nombre": "X", "edad": 8},
                    headers={**h2, "X-Zona-Padres": z["X-Zona-Padres"]})
    assert r.status_code == 403


@pytest.mark.parametrize("cuerpo", [
    {"nombre": "Luis", "edad": 2},
    {"nombre": "Luis", "edad": 19},
    {"nombre": "   ", "edad": 8},
    {"nombre": "", "edad": 8},
    {"nombre": "Luis", "edad": 8, "condicion": "inventada"},
])
def test_validaciones(client, registrar, con_zona, cuerpo):
    assert client.post("/ninos", json=cuerpo, headers=con_zona(registrar())).status_code == 422


def test_actualizar_condicion_cambia_el_perfil(client, registrar, con_zona):
    z = con_zona(registrar())
    nino = _crear(client, z, condicion="tdah").json()
    r = client.patch(f"/ninos/{nino['id']}", json={"condicion": "dislexia"}, headers=z)
    assert r.status_code == 200 and r.json()["perfil"] == "dislexia"
    assert client.get(f"/ninos/{nino['id']}/condicion", headers=z).json() == {
        "condicion": "dislexia"}


def test_actualizar_nombre_conserva_lo_demas(client, registrar, con_zona):
    z = con_zona(registrar())
    nino = _crear(client, z, condicion="tea").json()
    r = client.patch(f"/ninos/{nino['id']}", json={"nombre": "  Mateo "}, headers=z).json()
    assert (r["nombre"], r["edad"], r["perfil"]) == ("Mateo", 8, "tea")
    assert client.get(f"/ninos/{nino['id']}/condicion", headers=z).json() == {"condicion": "tea"}


def test_actualizar_sin_campos(client, registrar, con_zona):
    z = con_zona(registrar())
    nid = _crear(client, z).json()["id"]
    assert client.patch(f"/ninos/{nid}", json={}, headers=z).status_code == 422


def test_id_malformado(client, registrar):
    assert client.get("/ninos/no-es-uuid", headers=registrar()).status_code == 422


def test_borrado_definitivo_en_cascada(client, registrar, con_zona, db):
    z = con_zona(registrar())
    nid = _crear(client, z).json()["id"]
    db.execute(text("INSERT INTO sesiones (nino_id, ajustes) VALUES (CAST(:n AS uuid), '{}'::jsonb)"),
               {"n": nid})
    db.commit()

    assert client.delete(f"/ninos/{nid}", headers=z).status_code == 204
    assert client.get(f"/ninos/{nid}", headers=z).status_code == 404
    assert db.execute(text("SELECT count(*) FROM ninos")).scalar_one() == 0
    assert db.execute(text("SELECT count(*) FROM sesiones")).scalar_one() == 0


def test_especialista_no_accede_a_la_zona_de_ninos(client, registrar, db):
    h = registrar()
    db.execute(text("UPDATE usuarios SET rol = 'especialista'"))
    db.commit()
    assert client.get("/ninos", headers=h).status_code == 403