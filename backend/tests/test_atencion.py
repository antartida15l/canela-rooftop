import pytest
from sqlalchemy import text

SUMA = "matematica_suma"


def _lecturas(n=10, atencion=0.8, emocion="neutral"):
    return [{"t": 3 * i, "rostro": True, "atencion": atencion, "emocion": emocion}
            for i in range(n)]


def _perfectas(c):
    return [{"ejercicio_id": c["ids"]["suma-1"]["id"], "elecciones": [1], "ms": 2000},
            {"ejercicio_id": c["ids"]["suma-2"]["id"], "elecciones": [0], "ms": 2000},
            {"ejercicio_id": c["ids"]["suma-3"]["id"], "elecciones": [2], "ms": 2000}]


def _iniciar(client, h, nino):
    r = client.post("/sesiones", json={"nino_id": nino, "habilidad": SUMA}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def _cerrar(client, h, sesion, c, detalle):
    return client.post(f"/sesiones/{sesion['id']}/cerrar", headers=h,
                       json={"respuestas": _perfectas(c), "detalle": detalle})


def _detalle_guardado(db):
    return db.execute(text("SELECT detalle FROM sesiones")).scalar_one()


def test_los_parametros_de_atencion_se_congelan_en_la_sesion(
        client, registrar, nino_de, contenido_activo):
    h = registrar()
    s = _iniciar(client, h, nino_de(h))
    a = s["ajustes"]["atencion"]
    assert (a["intervalo_s"], a["calibracion_lecturas"], a["confirmaciones"],
            a["min_entre_intervenciones_s"]) == (3, 5, 2, 60)


def test_con_consentimiento_se_guardan_lecturas_y_resumen(
        client, registrar, nino_de, contenido_activo, db):
    h = registrar()
    nino = nino_de(h)
    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)
    s = _iniciar(client, h, nino)
    detalle = {"lecturas": _lecturas(10),
               "intervenciones": [{"t": 18, "tipo": "aviso_suave", "motivo": "malestar"}]}
    r = _cerrar(client, h, s, contenido_activo, detalle)
    assert r.status_code == 200, r.text

    res = r.json()["kpi"]["atencion"]
    assert (res["lecturas"], res["avisos"]) == (10, 1)
    assert len(_detalle_guardado(db)["lecturas"]) == 10

    obs = client.get(f"/sesiones/{s['id']}/observaciones", headers=h).json()
    assert obs and "no constituyen" in obs[-1]["texto"]


def test_sin_consentimiento_las_lecturas_se_descartan_pero_la_sesion_se_guarda(
        client, registrar, nino_de, contenido_activo, db):
    h = registrar()
    s = _iniciar(client, h, nino_de(h))
    assert s["ajustes"]["camara"] is False
    detalle = {"lecturas": _lecturas(10),
               "intervenciones": [{"t": 18, "tipo": "pausa", "motivo": "malestar"}],
               "pausas": [{"inicio_s": 60, "duracion_s": 30}]}
    r = _cerrar(client, h, s, contenido_activo, detalle)
    assert r.status_code == 200, r.text
    kpi = r.json()["kpi"]
    assert "atencion" not in kpi and kpi["lecturas_descartadas"] == 11
    guardado = _detalle_guardado(db)
    assert guardado["lecturas"] == [] and guardado["intervenciones"] == []
    assert len(guardado["pausas"]) == 1                       # las pausas no son datos de cámara
    assert r.json()["nota"] is not None
    assert client.get(f"/sesiones/{s['id']}/observaciones", headers=h).json() == []


def test_si_se_revoca_la_camara_durante_la_sesion_se_descartan_las_lecturas(
        client, registrar, nino_de, contenido_activo, db):
    h = registrar()
    nino = nino_de(h)
    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)
    s = _iniciar(client, h, nino)
    assert s["ajustes"]["camara"] is True

    client.put("/consentimientos/camara", json={"aceptado": False}, headers=h)
    r = _cerrar(client, h, s, contenido_activo, {"lecturas": _lecturas(5)})
    assert r.status_code == 200
    assert r.json()["kpi"]["lecturas_descartadas"] == 5
    assert _detalle_guardado(db)["lecturas"] == []


@pytest.mark.parametrize("detalle", [
    {"imagen": "data:image/png;base64,AAAA"},
    {"lecturas": [{"t": 0, "rostro": True, "atencion": 0.5, "frame": "xx"}]},
    {"lecturas": [{"t": 0, "rostro": True, "atencion": 1.5}]},
    {"lecturas": [{"t": 0, "rostro": True, "atencion": 0.5, "emocion": "aburrimiento"}]},
    {"lecturas": [{"t": 0, "rostro": False, "atencion": 0.5}]},
    {"lecturas": [{"t": 0, "rostro": True}]},
    {"lecturas": [{"t": 0, "rostro": True, "atencion": 0.5}] * 1501},
    {"intervenciones": [{"t": 0, "tipo": "castigo", "motivo": "malestar"}]},
])
def test_el_detalle_solo_acepta_etiquetas_y_numeros(
        client, registrar, nino_de, contenido_activo, detalle):
    h = registrar()
    client.put("/consentimientos/camara", json={"aceptado": True}, headers=h)
    s = _iniciar(client, h, nino_de(h))
    assert _cerrar(client, h, s, contenido_activo, detalle).status_code == 422


def test_observaciones_aisladas_entre_familias(client, registrar, nino_de, contenido_activo):
    ha = registrar("a@test.pe")
    client.put("/consentimientos/camara", json={"aceptado": True}, headers=ha)
    s = _iniciar(client, ha, nino_de(ha))
    _cerrar(client, ha, s, contenido_activo, {"lecturas": _lecturas(5)})

    hb = registrar("b@test.pe")
    assert client.get(f"/sesiones/{s['id']}/observaciones", headers=hb).status_code == 404
    assert client.get(f"/sesiones/{s['id']}/observaciones").status_code == 401
    assert client.get(f"/sesiones/{s['id']}/observaciones", headers=ha).status_code == 200