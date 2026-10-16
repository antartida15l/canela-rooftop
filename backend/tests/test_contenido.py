from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

CONTENIDO = {"tipo": "opcion_multiple", "enunciado": "2 + 2 = ?",
             "opciones": ["3", "4"], "correcta": 1}


def _nuevo(client, h, codigo="sumas-x", **kw):
    cuerpo = {"codigo": codigo, "habilidad": "matematica_suma", "nivel": 1,
              "contenido": CONTENIDO, **kw}
    return client.post("/contenido/ejercicios", json=cuerpo, headers=h)


def test_solo_admin_gestiona_contenido(client, registrar, contenido_activo):
    padre = registrar("padre@test.pe")
    assert _nuevo(client, padre).status_code == 403
    assert client.get("/contenido/ejercicios", headers=padre).status_code == 403
    eid = contenido_activo["ids"]["suma-1"]["id"]
    assert client.post(f"/contenido/ejercicios/{eid}/desactivar", headers=padre).status_code == 403
    assert client.get("/contenido/ejercicios").status_code == 401


def test_borrador_nace_inactivo_y_versiona(client, registrar, db):
    h = registrar("admin@test.pe")
    db.execute(text("UPDATE usuarios SET rol = 'admin'"))
    db.commit()
    v1 = _nuevo(client, h).json()
    v2 = _nuevo(client, h).json()
    assert (v1["version"], v1["activo"]) == (1, False)
    assert (v2["version"], v2["activo"]) == (2, False)
    assert v1["revisado_por"] is None


@pytest.mark.parametrize("contenido", [
    {**CONTENIDO, "correcta": 2},                 # fuera de rango
    {**CONTENIDO, "opciones": ["solo una"], "correcta": 0},
    {**CONTENIDO, "tipo": "arrastrar"},
    {**CONTENIDO, "enunciado": ""},
])
def test_contenido_invalido(client, registrar, db, contenido):
    h = registrar("admin@test.pe")
    db.execute(text("UPDATE usuarios SET rol = 'admin'"))
    db.commit()
    assert _nuevo(client, h, contenido=contenido).status_code == 422


def test_nivel_y_codigo_invalidos(client, registrar, db):
    h = registrar("admin@test.pe")
    db.execute(text("UPDATE usuarios SET rol = 'admin'"))
    db.commit()
    assert _nuevo(client, h, nivel=4).status_code == 422
    assert _nuevo(client, h, codigo="MAL CODIGO").status_code == 422


def test_activar_registra_revisor_y_desactiva_version_anterior(client, registrar, db):
    h = registrar("admin@test.pe")
    db.execute(text("UPDATE usuarios SET rol = 'admin'"))
    db.commit()
    v1 = _nuevo(client, h).json()
    v2 = _nuevo(client, h).json()

    a1 = client.post(f"/contenido/ejercicios/{v1['id']}/activar", headers=h).json()
    assert a1["activo"] and a1["revisado_por"] == "admin@test.pe" and a1["revisado_en"]

    client.post(f"/contenido/ejercicios/{v2['id']}/activar", headers=h)
    estado = {e["version"]: e["activo"]
              for e in client.get("/contenido/ejercicios", headers=h).json()}
    assert estado == {1: False, 2: True}


def test_la_base_impide_activar_sin_revision(client, registrar, db):
    h = registrar("admin@test.pe")
    db.execute(text("UPDATE usuarios SET rol = 'admin'"))
    db.commit()
    eid = _nuevo(client, h).json()["id"]
    with pytest.raises(IntegrityError):
        db.execute(text("UPDATE ejercicios SET activo = true WHERE id = CAST(:i AS uuid)"),
                   {"i": eid})
        db.commit()
    db.rollback()


def test_activar_inexistente(client, registrar, db):
    h = registrar("admin@test.pe")
    db.execute(text("UPDATE usuarios SET rol = 'admin'"))
    db.commit()
    assert client.post(f"/contenido/ejercicios/{uuid4()}/activar", headers=h).status_code == 404