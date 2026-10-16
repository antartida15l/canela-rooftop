import json

from sqlalchemy import text

SUMA = "matematica_suma"
# (código, opción correcta, opción incorrecta) de los ejercicios del fixture
CASOS = [("suma-1", 1, 0), ("suma-2", 0, 1), ("suma-3", 2, 0)]


def _sesion(client, h, nino):
    r = client.post("/sesiones", json={"nino_id": nino, "habilidad": SUMA}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def _cerrar(client, h, sesion, contenido, aciertos):
    respuestas = [
        {"ejercicio_id": contenido["ids"][cod]["id"],
         "elecciones": [ok] if acierto else [mal] * 3, "ms": 2000}
        for (cod, ok, mal), acierto in zip(CASOS, aciertos)
    ]
    r = client.post(f"/sesiones/{sesion['id']}/cerrar", json={"respuestas": respuestas},
                    headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def _dominio(client, h, nino):
    r = client.get(f"/dominio/{nino}", headers=h)
    assert r.status_code == 200, r.text
    return r.json()["habilidades"]


def _fijar_dominio(db, nino, estado):
    db.execute(text("UPDATE ninos SET dominio = CAST(:d AS jsonb) WHERE id = CAST(:n AS uuid)"),
               {"d": json.dumps({SUMA: estado}), "n": nino})
    db.commit()


def test_sin_sesiones_el_dominio_esta_vacio(client, registrar, nino_de):
    h = registrar()
    assert _dominio(client, h, nino_de(h)) == {}


def test_sube_de_nivel_tras_dos_sesiones_correctas(client, registrar, nino_de, contenido_activo):
    h = registrar()
    nino = nino_de(h)

    _cerrar(client, h, _sesion(client, h, nino), contenido_activo, [True] * 3)
    est = _dominio(client, h, nino)[SUMA]
    assert (est["nivel"], est["muestras"], est["racha"]) == (1, 3, 3)

    cierre = _cerrar(client, h, _sesion(client, h, nino), contenido_activo, [True] * 3)
    resumen = cierre["kpi"]["dominio"]
    assert (resumen["nivel_antes"], resumen["nivel_despues"]) == (1, 2)
    assert len(resumen["cambios"]) == 1

    est = _dominio(client, h, nino)[SUMA]
    assert (est["nivel"], est["muestras"], est["racha"]) == (2, 0, 0)


def test_sin_ejercicios_del_nivel_se_sirve_uno_inferior_y_no_cuenta(
        client, registrar, nino_de, contenido_activo, db):
    h = registrar()
    nino = nino_de(h)
    _fijar_dominio(db, nino, {"nivel": 2, "dominio": 0.0, "racha": 0, "ventana": []})

    s = _sesion(client, h, nino)
    lote = client.get(f"/sesiones/{s['id']}/ejercicios?cantidad=5", headers=h).json()
    assert len(lote) == 3 and all(e["nivel"] == 1 for e in lote)  # no hay nivel 2: baja a 1

    _cerrar(client, h, s, contenido_activo, [False] * 3)
    est = _dominio(client, h, nino)[SUMA]
    assert (est["nivel"], est["racha"], est["muestras"]) == (2, 0, 0)  # no penaliza


def test_nivel_alto_sirve_ejercicios_mas_dificiles_y_baja_con_dos_fallos(
        client, registrar, nino_de, contenido_activo, db):
    admin = contenido_activo["admin"]
    for codigo in ("suma-n2-a", "suma-n2-b"):
        r = client.post("/contenido/ejercicios", headers=admin, json={
            "codigo": codigo, "habilidad": SUMA, "nivel": 2,
            "contenido": {"tipo": "opcion_multiple", "enunciado": "14 + 9 = ?",
                          "opciones": ["a", "b"], "correcta": 1}})
        client.post(f"/contenido/ejercicios/{r.json()['id']}/activar", headers=admin)

    h = registrar()
    nino = nino_de(h)
    _fijar_dominio(db, nino, {"nivel": 2, "dominio": 0.0, "racha": 0, "ventana": []})

    s = _sesion(client, h, nino)
    lote = client.get(f"/sesiones/{s['id']}/ejercicios?cantidad=5", headers=h).json()
    assert len(lote) == 2 and all(e["nivel"] == 2 for e in lote)

    respuestas = [{"ejercicio_id": e["id"], "elecciones": [0, 0, 0], "ms": 1500} for e in lote]
    r = client.post(f"/sesiones/{s['id']}/cerrar", json={"respuestas": respuestas}, headers=h)
    assert r.status_code == 200
    assert r.json()["kpi"]["dominio"]["cambios"][0]["motivo"] == "bajada"
    assert _dominio(client, h, nino)[SUMA]["nivel"] == 1


def test_un_lote_invalido_no_cambia_el_dominio(client, registrar, nino_de, contenido_activo):
    h = registrar()
    nino = nino_de(h)
    s = _sesion(client, h, nino)
    malo = [{"ejercicio_id": "00000000-0000-0000-0000-000000000000",
             "elecciones": [0], "ms": 1000}]
    assert client.post(f"/sesiones/{s['id']}/cerrar", json={"respuestas": malo},
                       headers=h).status_code == 422
    assert _dominio(client, h, nino) == {}


def test_aislamiento_del_dominio_entre_familias(client, registrar, nino_de, contenido_activo):
    ha = registrar("a@test.pe")
    nino_a = nino_de(ha)
    _cerrar(client, ha, _sesion(client, ha, nino_a), contenido_activo, [True] * 3)

    hb = registrar("b@test.pe")
    assert client.get(f"/dominio/{nino_a}", headers=hb).status_code == 404
    assert client.get(f"/dominio/{nino_a}").status_code == 401
    assert _dominio(client, ha, nino_a)[SUMA]["muestras"] == 3


def test_la_ventana_no_se_expone_al_padre(client, registrar, nino_de, contenido_activo):
    h = registrar()
    nino = nino_de(h)
    _cerrar(client, h, _sesion(client, h, nino), contenido_activo, [True, False, True])
    assert "ventana" not in json.dumps(_dominio(client, h, nino))