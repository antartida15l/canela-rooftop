import pytest
from fastapi import HTTPException

from app.modules.consentimientos import service
from app.modules.consentimientos.deps import requiere_consentimiento


def _estado(client, h):
    r = client.get("/consentimientos", headers=h)
    assert r.status_code == 200, r.text
    return {c["tipo"]: c for c in r.json()}


def test_requiere_token(client):
    assert client.get("/consentimientos").status_code == 401


def test_tras_registro_solo_terminos_aceptados(client, registrar):
    est = _estado(client, registrar())
    assert est["terminos"]["aceptado"] is True
    assert est["camara"]["aceptado"] is False
    assert est["investigacion"]["aceptado"] is False
    assert not any(c["requiere_reaceptacion"] for c in est.values())


def test_aceptar_y_revocar_camara_con_historial(client, registrar):
    h = registrar()
    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)
    assert _estado(client, h)["camara"]["aceptado"] is True

    client.put("/consentimientos/camara", json={"aceptado": False}, headers=h)
    assert _estado(client, h)["camara"]["aceptado"] is False

    hist = client.get("/consentimientos/camara/historial", headers=h).json()
    assert [x["aceptado"] for x in hist] == [False, True]  # más reciente primero


def test_terminos_no_se_pueden_retirar(client, registrar):
    h = registrar()
    r = client.put("/consentimientos/terminos", json={"aceptado": False}, headers=h)
    assert r.status_code == 409
    assert _estado(client, h)["terminos"]["aceptado"] is True


def test_tipo_invalido(client, registrar):
    h = registrar()
    assert client.put("/consentimientos/hackeo", json={"aceptado": True}, headers=h).status_code == 422
    assert client.get("/consentimientos/hackeo/historial", headers=h).status_code == 422


def test_nueva_version_exige_reaceptar(client, registrar, monkeypatch):
    h = registrar()
    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)

    monkeypatch.setitem(service.VERSIONES, "camara", "2026-02")  # se publica texto nuevo
    c = _estado(client, h)["camara"]
    assert c["aceptado"] is False
    assert c["requiere_reaceptacion"] is True
    assert c["version_aceptada"] == "2026-01"

    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)
    c = _estado(client, h)["camara"]
    assert c["aceptado"] is True and c["requiere_reaceptacion"] is False


def test_consentimientos_aislados_entre_familias(client, registrar):
    a = registrar("a@test.pe")
    b = registrar("b@test.pe")
    client.put("/consentimientos/camara", json={"aceptado": True}, headers=a)

    assert _estado(client, a)["camara"]["aceptado"] is True
    assert _estado(client, b)["camara"]["aceptado"] is False
    assert client.get("/consentimientos/camara/historial", headers=b).json() == []


def test_dependencia_requiere_consentimiento(client, registrar, db):
    h = registrar()
    uid = client.get("/auth/yo", headers=h).json()["id"]
    usuario = {"id": uid}
    check = requiere_consentimiento("camara")

    with pytest.raises(HTTPException) as e:
        check(u=usuario, db=db)
    assert e.value.status_code == 403
    assert e.value.detail["codigo"] == "consentimiento_requerido"

    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)
    assert check(u=usuario, db=db) is usuario


def test_consentimiento_vigente_bool(client, registrar, db):
    h = registrar()
    uid = client.get("/auth/yo", headers=h).json()["id"]
    assert service.consentimiento_vigente(db, uid, "camara") is False
    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)
    assert service.consentimiento_vigente(db, uid, "camara") is True