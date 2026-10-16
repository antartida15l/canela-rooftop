from uuid import uuid4

import pytest
from sqlalchemy import text

SUMA = "matematica_suma"


def _preparar(client, registrar, nino_de, email="padre@test.pe"):
    h = registrar(email)
    nino = nino_de(h)
    s = client.post("/sesiones", json={"nino_id": nino, "habilidad": SUMA}, headers=h).json()
    return h, s


def _verificar(client, h, sesion, ejercicio_id, eleccion):
    return client.post(f"/sesiones/{sesion['id']}/ejercicios/{ejercicio_id}/verificar",
                       json={"eleccion": eleccion}, headers=h)


def test_indica_si_la_opcion_es_correcta_sin_revelar_nada_mas(
        client, registrar, nino_de, contenido_activo):
    h, s = _preparar(client, registrar, nino_de)
    ej = contenido_activo["ids"]["suma-1"]           # la correcta es la opción 1
    bien = _verificar(client, h, s, ej["id"], 1)
    mal = _verificar(client, h, s, ej["id"], 0)
    assert bien.status_code == mal.status_code == 200
    assert bien.json() == {"correcta": True}
    assert mal.json() == {"correcta": False}         # solo un booleano: no dice cuál era la correcta


def test_verificar_no_guarda_nada(client, registrar, nino_de, contenido_activo, db):
    h, s = _preparar(client, registrar, nino_de)
    _verificar(client, h, s, contenido_activo["ids"]["suma-1"]["id"], 1)
    assert db.execute(text("SELECT count(*) FROM respuestas")).scalar_one() == 0
    assert client.get(f"/sesiones/{s['id']}", headers=h).json()["fin"] is None


def test_en_una_sesion_cerrada_no_se_puede_verificar(client, registrar, nino_de, contenido_activo):
    h, s = _preparar(client, registrar, nino_de)
    client.post(f"/sesiones/{s['id']}/cerrar", headers=h, json={"respuestas": []})
    assert _verificar(client, h, s, contenido_activo["ids"]["suma-1"]["id"], 1).status_code == 409


@pytest.mark.parametrize("eleccion,estado", [(3, 422), (5, 422), (6, 422), (-1, 422)])
def test_opcion_fuera_de_rango(client, registrar, nino_de, contenido_activo, eleccion, estado):
    h, s = _preparar(client, registrar, nino_de)           # suma-1 tiene 3 opciones (0, 1, 2)
    assert _verificar(client, h, s, contenido_activo["ids"]["suma-1"]["id"], eleccion).status_code == estado


def test_ejercicio_inexistente_o_de_otra_habilidad(client, registrar, nino_de, contenido_activo):
    h, s = _preparar(client, registrar, nino_de)
    assert _verificar(client, h, s, str(uuid4()), 0).status_code == 422
    assert _verificar(client, h, s, contenido_activo["ids"]["lectura-1"]["id"], 1).status_code == 422


def test_un_ejercicio_desactivado_no_se_puede_probar(client, registrar, nino_de, contenido_activo):
    h, s = _preparar(client, registrar, nino_de)
    eid = contenido_activo["ids"]["suma-1"]["id"]
    client.post(f"/contenido/ejercicios/{eid}/desactivar", headers=contenido_activo["admin"])
    assert _verificar(client, h, s, eid, 1).status_code == 422   # evita tantear borradores


def test_aislamiento_entre_familias(client, registrar, nino_de, contenido_activo):
    ha, s = _preparar(client, registrar, nino_de, "a@test.pe")
    hb = registrar("b@test.pe")
    eid = contenido_activo["ids"]["suma-1"]["id"]
    assert _verificar(client, hb, s, eid, 1).status_code == 404
    assert client.post(f"/sesiones/{s['id']}/ejercicios/{eid}/verificar", json={"eleccion": 1}
                       ).status_code == 401
    assert _verificar(client, ha, s, eid, 1).status_code == 200
