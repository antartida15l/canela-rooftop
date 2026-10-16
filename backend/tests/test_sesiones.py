import json
from uuid import uuid4

import pytest
from sqlalchemy import text

SUMA = "matematica_suma"


def _iniciar(client, h, nino, habilidad=SUMA):
    return client.post("/sesiones", json={"nino_id": nino, "habilidad": habilidad}, headers=h)


def _resp(c, codigo, elecciones, ms=3000):
    return {"ejercicio_id": c["ids"][codigo]["id"], "elecciones": elecciones, "ms": ms}


def _perfectas(c):
    return [_resp(c, "suma-1", [1]), _resp(c, "suma-2", [0]), _resp(c, "suma-3", [2])]


def _escenario(client, registrar, nino_de, email="padre@test.pe"):
    h = registrar(email)
    return h, nino_de(h)


def test_iniciar_congela_ajustes_y_no_revela_el_perfil(
        client, registrar, nino_de, contenido_activo):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    assert s["fin"] is None and s["nota"] is None and s["kpi"] == {}
    assert s["ajustes"]["habilidad"] == SUMA
    assert "perfil" not in s["ajustes"] and "condicion" not in s["ajustes"]
    assert s["ajustes"]["ejercicios_objetivo"] == 10


def test_cambiar_el_perfil_despues_no_altera_la_sesion_en_curso(
        client, registrar, nino_de, contenido_activo, db):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    original = s["ajustes"]["sesion_min"]

    db.execute(text("UPDATE perfiles_apoyo SET ajustes = ajustes || "
                    "jsonb_build_object('sesion_min', 99) WHERE codigo = 'general'"))
    db.commit()
    try:
        leida = client.get(f"/sesiones/{s['id']}", headers=h).json()
        assert leida["ajustes"]["sesion_min"] == original
        nueva = _iniciar(client, h, nino).json()
        assert nueva["ajustes"]["sesion_min"] == 99
    finally:
        db.execute(text("UPDATE perfiles_apoyo SET ajustes = ajustes || "
                        "jsonb_build_object('sesion_min', CAST(:v AS int)) "
                        "WHERE codigo = 'general'"), {"v": original})
        db.commit()


def test_camara_segun_consentimiento_vigente(client, registrar, nino_de, contenido_activo):
    h, nino = _escenario(client, registrar, nino_de)
    sin = _iniciar(client, h, nino).json()
    assert sin["ajustes"]["camara"] is False

    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)
    con = _iniciar(client, h, nino).json()
    assert con["ajustes"]["camara"] is True
    assert client.get(f"/sesiones/{sin['id']}", headers=h).json()["ajustes"]["camara"] is False


def test_iniciar_sin_ejercicios_activos(client, registrar, nino_de, contenido_activo):
    h, nino = _escenario(client, registrar, nino_de)
    assert _iniciar(client, h, nino, "matematica_resta").status_code == 409


def test_ejercicios_no_incluyen_la_respuesta_correcta(
        client, registrar, nino_de, contenido_activo):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    r = client.get(f"/sesiones/{s['id']}/ejercicios?cantidad=5", headers=h)
    assert r.status_code == 200
    assert "correcta" not in json.dumps(r.json())
    esperados = {contenido_activo["ids"][c]["id"] for c in ("suma-1", "suma-2", "suma-3")}
    assert {e["id"] for e in r.json()} == esperados  # solo la habilidad de la sesión


def test_cierre_en_lote_perfecto(client, registrar, nino_de, contenido_activo, objetivo_3, db):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    r = client.post(f"/sesiones/{s['id']}/cerrar", headers=h, json={
        "respuestas": _perfectas(contenido_activo),
        "detalle": {"pausas": [{"inicio_s": 120, "duracion_s": 30}]}})
    assert r.status_code == 200, r.text
    assert r.json()["nota"] == 20.0
    assert r.json()["kpi"]["correctas"] == 3

    cerrada = client.get(f"/sesiones/{s['id']}", headers=h).json()
    assert cerrada["fin"] and cerrada["nota"] == 20.0
    assert db.execute(text("SELECT count(*) FROM respuestas")).scalar_one() == 3
    assert "detalle" not in cerrada


def test_la_correccion_la_hace_el_servidor(
        client, registrar, nino_de, contenido_activo, objetivo_3, db):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    c = contenido_activo
    r = client.post(f"/sesiones/{s['id']}/cerrar", headers=h, json={"respuestas": [
        _resp(c, "suma-1", [0, 1]),       # acierta al 2.º intento
        _resp(c, "suma-2", [2, 2, 2]),    # nunca acierta
        _resp(c, "suma-3", [2]),          # acierta al 1.º
    ]})
    assert r.json()["nota"] == pytest.approx(12.63, abs=0.01)

    filas = {f.e: (f.correcta, f.intentos) for f in db.execute(text(
        "SELECT ejercicio_id::text AS e, correcta, intentos FROM respuestas"))}
    assert filas[c["ids"]["suma-1"]["id"]] == (True, 2)
    assert filas[c["ids"]["suma-2"]["id"]] == (False, 3)
    assert filas[c["ids"]["suma-3"]["id"]] == (True, 1)


def test_la_atencion_no_cambia_la_nota(
        client, registrar, nino_de, contenido_activo, objetivo_3):
    h, nino = _escenario(client, registrar, nino_de)
    notas = []
    for atencion in (0.05, 0.95):
        s = _iniciar(client, h, nino).json()
        r = client.post(f"/sesiones/{s['id']}/cerrar", headers=h, json={
            "respuestas": _perfectas(contenido_activo),
            "detalle": {"atencion": {"promedio": atencion},
                        "emociones": [{"t": 3, "etiqueta": "frustracion"}]}})
        notas.append(r.json()["nota"])
    assert notas[0] == notas[1] == 20.0


def test_cerrar_dos_veces(client, registrar, nino_de, contenido_activo):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    assert client.post(f"/sesiones/{s['id']}/cerrar", headers=h,
                       json={"respuestas": []}).status_code == 200
    assert client.post(f"/sesiones/{s['id']}/cerrar", headers=h,
                       json={"respuestas": []}).status_code == 409
    assert client.get(f"/sesiones/{s['id']}/ejercicios", headers=h).status_code == 409


def test_cierre_sin_respuestas_no_penaliza(client, registrar, nino_de, contenido_activo):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    r = client.post(f"/sesiones/{s['id']}/cerrar", headers=h, json={"respuestas": []})
    assert r.json()["nota"] is None and r.json()["kpi"]["respondidas"] == 0


def test_lote_invalido_no_deja_la_sesion_a_medias(
        client, registrar, nino_de, contenido_activo, db):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    c = contenido_activo
    url = f"/sesiones/{s['id']}/cerrar"

    inexistente = {"ejercicio_id": str(uuid4()), "elecciones": [0], "ms": 1000}
    otra_habilidad = _resp(c, "lectura-1", [1])
    duplicado = [_resp(c, "suma-1", [1]), _resp(c, "suma-1", [1])]
    fuera_de_rango = {**_resp(c, "suma-1", [5])}  # suma-1 tiene 3 opciones

    for lote in ([inexistente], [otra_habilidad], duplicado, [fuera_de_rango]):
        assert client.post(url, headers=h, json={"respuestas": lote}).status_code == 422

    assert db.execute(text("SELECT count(*) FROM respuestas")).scalar_one() == 0
    assert client.get(f"/sesiones/{s['id']}", headers=h).json()["fin"] is None
    assert client.post(url, headers=h, json={"respuestas": _perfectas(c)}).status_code == 200


@pytest.mark.parametrize("respuesta", [
    {"elecciones": [], "ms": 1000},
    {"elecciones": [0, 0, 0, 0], "ms": 1000},
    {"elecciones": [-1], "ms": 1000},
    {"elecciones": [0], "ms": -5},
])
def test_formato_de_respuesta_invalido(client, registrar, nino_de, contenido_activo, respuesta):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    cuerpo = {"respuestas": [{"ejercicio_id": contenido_activo["ids"]["suma-1"]["id"],
                              **respuesta}]}
    assert client.post(f"/sesiones/{s['id']}/cerrar", headers=h, json=cuerpo).status_code == 422


def test_detalle_demasiado_grande(client, registrar, nino_de, contenido_activo):
    h, nino = _escenario(client, registrar, nino_de)
    s = _iniciar(client, h, nino).json()
    r = client.post(f"/sesiones/{s['id']}/cerrar", headers=h,
                    json={"respuestas": [], "detalle": {"x": "a" * 250_000}})
    assert r.status_code == 422


def test_historial_del_nino(client, registrar, nino_de, contenido_activo):
    h, nino = _escenario(client, registrar, nino_de)
    primera = _iniciar(client, h, nino).json()
    segunda = _iniciar(client, h, nino).json()
    lista = client.get(f"/sesiones?nino_id={nino}", headers=h).json()
    assert [s["id"] for s in lista] == [segunda["id"], primera["id"]]  # más reciente primero
    assert all("detalle" not in s for s in lista)


def test_aislamiento_de_sesiones_entre_familias(
        client, registrar, nino_de, contenido_activo):
    ha, nino_a = _escenario(client, registrar, nino_de, "a@test.pe")
    hb = registrar("b@test.pe")
    s = _iniciar(client, ha, nino_a).json()
    sid = s["id"]

    assert _iniciar(client, hb, nino_a).status_code == 404            # iniciar con niño ajeno
    assert client.get(f"/sesiones/{sid}", headers=hb).status_code == 404
    assert client.get(f"/sesiones/{sid}/ejercicios", headers=hb).status_code == 404
    assert client.post(f"/sesiones/{sid}/cerrar", headers=hb,
                       json={"respuestas": _perfectas(contenido_activo)}).status_code == 404
    assert client.get(f"/sesiones?nino_id={nino_a}", headers=hb).json() == []

    # La sesión de A sigue abierta e intacta
    assert client.get(f"/sesiones/{sid}", headers=ha).json()["fin"] is None
    assert client.post(f"/sesiones/{sid}/cerrar", headers=ha,
                       json={"respuestas": _perfectas(contenido_activo)}).status_code == 200


def test_requiere_sesion_iniciada(client):
    assert client.post("/sesiones", json={"nino_id": str(uuid4()), "habilidad": SUMA}
                       ).status_code == 401