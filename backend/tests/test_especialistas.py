import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from test_reportes import insertar_sesion


@pytest.fixture
def escena(client, registrar, con_zona, nino_de, especialista_de):
    """Una familia con un niño, y un especialista aún sin acceso."""
    padre = registrar("padre@test.pe")
    zona = con_zona(padre)
    nino = nino_de(padre, condicion="tdah")
    esp = especialista_de("doc@test.pe")
    return {"padre": padre, "zona": zona, "nino": nino, "esp": esp}


def otorgar(client, e, alcance="completo", dias=30, email="doc@test.pe", zona=True):
    return client.post("/accesos", headers=e["zona"] if zona else e["padre"],
                       json={"nino_id": e["nino"], "email": email, "alcance": alcance, "dias": dias})


def accesos(client, e):
    return client.get(f"/accesos?nino_id={e['nino']}", headers=e["padre"]).json()


def auditoria(client, e):
    return client.get(f"/accesos/auditoria?nino_id={e['nino']}", headers=e["padre"]).json()


# ---------- Dar acceso ----------
def test_otorgar_acceso(client, escena):
    r = otorgar(client, escena, "resumen", 30)
    assert r.status_code == 201, r.text
    a = r.json()
    assert (a["especialista_email"], a["alcance"], a["estado"]) == ("doc@test.pe", "resumen", "vigente")
    assert a["revocado_en"] is None
    assert accesos(client, escena)[0]["id"] == a["id"]
    assert [x["accion"] for x in auditoria(client, escena)] == ["otorgado"]


def test_dar_acceso_exige_la_zona_de_padres(client, escena):
    r = otorgar(client, escena, zona=False)
    assert r.status_code == 403 and r.json()["detail"]["codigo"] == "zona_padres_requerida"
    assert accesos(client, escena) == []


@pytest.mark.parametrize("dias", [0, -1, 91, 365])
def test_el_acceso_dura_como_maximo_90_dias(client, escena, dias):
    assert otorgar(client, escena, dias=dias).status_code == 422


def test_noventa_dias_es_el_limite_permitido(client, escena):
    assert otorgar(client, escena, dias=90).status_code == 201


def test_la_base_tambien_impide_pasar_de_90_dias(client, escena, db):
    otorgar(client, escena, dias=90)
    with pytest.raises(IntegrityError):
        db.execute(text("UPDATE accesos_especialista SET expira_en = creado_en + INTERVAL '91 days'"))
        db.commit()
    db.rollback()


def test_solo_se_puede_dar_acceso_a_cuentas_de_especialista(client, escena, registrar):
    registrar("otro-padre@test.pe")
    assert otorgar(client, escena, email="otro-padre@test.pe").status_code == 404
    assert otorgar(client, escena, email="nadie@test.pe").status_code == 404
    assert otorgar(client, escena, email="DOC@test.pe").status_code == 201     # sin distinguir mayúsculas


def test_no_se_duplica_un_acceso_vigente_pero_se_puede_renovar_tras_revocar(client, escena):
    a = otorgar(client, escena).json()
    assert otorgar(client, escena, "resumen").status_code == 409
    assert client.delete(f"/accesos/{a['id']}", headers=escena["zona"]).status_code == 204
    assert otorgar(client, escena, "resumen").status_code == 201


def test_otra_familia_no_puede_dar_acceso_a_mi_hijo(client, escena, registrar, con_zona):
    otra = registrar("otra@test.pe")
    z = con_zona(otra)
    r = client.post("/accesos", headers=z, json={
        "nino_id": escena["nino"], "email": "doc@test.pe", "alcance": "completo", "dias": 30})
    assert r.status_code == 404
    assert accesos(client, escena) == []


# ---------- Qué ve el especialista ----------
def test_el_especialista_solo_ve_los_ninos_compartidos(client, escena, registrar, nino_de):
    otra = registrar("otra@test.pe")
    nino_de(otra, "Ajeno")
    assert client.get("/especialista/ninos", headers=escena["esp"]).json() == []

    otorgar(client, escena, "resumen", 10)
    lista = client.get("/especialista/ninos", headers=escena["esp"]).json()
    assert [(n["nombre"], n["edad"], n["alcance"]) for n in lista] == [("Luis", 8, "resumen")]


def test_alcance_resumen_vs_completo(client, escena, db):
    a = {"lecturas": 100, "atencion_media": 0.3, "pct_malestar": 0.4, "avisos": 1, "pausas_sugeridas": 0}
    for d in (4, 3, 2):
        insertar_sesion(db, escena["nino"], d, 12, atencion=a)
    url = f"/especialista/ninos/{escena['nino']}/reporte"

    acceso = otorgar(client, escena, "resumen").json()
    r = client.get(url, headers=escena["esp"]).json()
    assert r["alcance"] == "resumen" and r["resumen"]["sesiones"] == 3
    assert r["atencion"] is None and r["recomendaciones"] is None

    client.delete(f"/accesos/{acceso['id']}", headers=escena["zona"])
    otorgar(client, escena, "completo")
    r = client.get(url, headers=escena["esp"]).json()
    assert r["alcance"] == "completo" and r["atencion"]["sesiones_con_camara"] == 3
    assert r["recomendaciones"]


def test_el_especialista_nunca_ve_la_condicion_ni_el_detalle_crudo(client, escena, db):
    insertar_sesion(db, escena["nino"], 3, 12, marca="enojo")
    otorgar(client, escena, "completo")
    cuerpo = client.get(f"/especialista/ninos/{escena['nino']}/reporte", headers=escena["esp"]).text.lower()
    for prohibido in ("tdah", "perfil", "condicion", "detalle", "lecturas", "enojo"):
        assert prohibido not in cuerpo


def test_sin_acceso_no_se_ve_nada(client, escena):
    url = f"/especialista/ninos/{escena['nino']}/reporte"
    assert client.get(url, headers=escena["esp"]).status_code == 404
    assert client.get(url).status_code == 401


def test_un_acceso_no_da_permiso_sobre_otros_ninos(client, escena, registrar, nino_de):
    otro = nino_de(registrar("otra@test.pe"), "Ajeno")
    otorgar(client, escena)
    assert client.get(f"/especialista/ninos/{otro}/reporte", headers=escena["esp"]).status_code == 404


def test_otro_especialista_no_hereda_el_acceso(client, escena, especialista_de):
    otorgar(client, escena)
    otro = especialista_de("otro-doc@test.pe")
    assert client.get(f"/especialista/ninos/{escena['nino']}/reporte", headers=otro).status_code == 404
    assert client.get("/especialista/ninos", headers=otro).json() == []


# ---------- Revocar y caducar ----------
def test_revocar_corta_el_acceso_de_inmediato(client, escena):
    a = otorgar(client, escena).json()
    url = f"/especialista/ninos/{escena['nino']}/reporte"
    assert client.get(url, headers=escena["esp"]).status_code == 200

    assert client.delete(f"/accesos/{a['id']}", headers=escena["zona"]).status_code == 204
    assert client.get(url, headers=escena["esp"]).status_code == 404
    assert client.get("/especialista/ninos", headers=escena["esp"]).json() == []
    assert accesos(client, escena)[0]["estado"] == "revocado"
    assert "revocado" in [x["accion"] for x in auditoria(client, escena)]


def test_revocar_exige_zona_y_solo_el_dueno_puede(client, escena, registrar, con_zona):
    a = otorgar(client, escena).json()
    assert client.delete(f"/accesos/{a['id']}", headers=escena["padre"]).status_code == 403
    z_otra = con_zona(registrar("otra@test.pe"))
    assert client.delete(f"/accesos/{a['id']}", headers=z_otra).status_code == 404
    assert client.delete(f"/accesos/{a['id']}", headers=escena["zona"]).status_code == 204
    assert client.delete(f"/accesos/{a['id']}", headers=escena["zona"]).status_code == 404  # ya revocado


def test_el_acceso_caduca_solo(client, escena, db):
    otorgar(client, escena, dias=5)
    db.execute(text("UPDATE accesos_especialista SET expira_en = now() - INTERVAL '1 second'"))
    db.commit()
    assert client.get(f"/especialista/ninos/{escena['nino']}/reporte", headers=escena["esp"]).status_code == 404
    assert client.get("/especialista/ninos", headers=escena["esp"]).json() == []
    assert accesos(client, escena)[0]["estado"] == "expirado"
    assert otorgar(client, escena).status_code == 201          # y se puede volver a dar


# ---------- Auditoría ----------
def test_cada_consulta_queda_auditada_y_la_ve_el_padre(client, escena):
    otorgar(client, escena, "resumen")
    url = f"/especialista/ninos/{escena['nino']}/reporte"
    client.get(url, headers=escena["esp"])
    client.get(url + "?dias=90", headers=escena["esp"])

    eventos = auditoria(client, escena)
    assert [e["accion"] for e in eventos] == ["consultado", "consultado", "otorgado"]   # recientes primero
    assert all(e["especialista_email"] == "doc@test.pe" and e["alcance"] == "resumen" for e in eventos)
    assert all(e["fecha"] for e in eventos)


def test_las_consultas_rechazadas_no_se_registran_como_consulta(client, escena):
    client.get(f"/especialista/ninos/{escena['nino']}/reporte", headers=escena["esp"])   # sin acceso
    assert auditoria(client, escena) == []


def test_la_auditoria_es_privada_de_la_familia(client, escena, registrar):
    otorgar(client, escena)
    assert client.get(f"/accesos/auditoria?nino_id={escena['nino']}", headers=registrar("otra@test.pe")).json() == []
    assert client.get(f"/accesos?nino_id={escena['nino']}", headers=registrar("otra2@test.pe")).json() == []
    assert client.get(f"/accesos/auditoria?nino_id={escena['nino']}", headers=escena["esp"]).status_code == 403


# ---------- Roles y solo lectura ----------
def test_separacion_de_roles(client, escena, contenido_activo):
    otorgar(client, escena)
    esp, padre, admin = escena["esp"], escena["padre"], contenido_activo["admin"]
    assert client.get("/ninos", headers=esp).status_code == 403
    assert client.get(f"/reportes/{escena['nino']}", headers=esp).status_code == 403
    assert client.get(f"/accesos?nino_id={escena['nino']}", headers=esp).status_code == 403
    assert client.post("/sesiones", headers=esp, json={"nino_id": escena["nino"], "habilidad": "matematica_suma"}).status_code == 403
    assert client.get("/especialista/ninos", headers=padre).status_code == 403
    assert client.get("/especialista/ninos", headers=admin).status_code == 403


def test_el_especialista_no_puede_modificar_nada(client, escena):
    otorgar(client, escena, "completo")
    base = f"/especialista/ninos/{escena['nino']}/reporte"
    for metodo in ("post", "put", "patch", "delete"):
        r = getattr(client, metodo)(base, headers=escena["esp"])
        assert r.status_code == 405, (metodo, r.status_code)
    assert client.post("/especialista/ninos", headers=escena["esp"]).status_code == 405


# ---------- Borrado ----------
def test_borrar_al_nino_elimina_accesos_y_auditoria(client, escena, db):
    otorgar(client, escena)
    client.get(f"/especialista/ninos/{escena['nino']}/reporte", headers=escena["esp"])
    assert client.delete(f"/ninos/{escena['nino']}", headers=escena["zona"]).status_code == 204
    assert db.execute(text("SELECT count(*) FROM accesos_especialista")).scalar_one() == 0
    assert db.execute(text("SELECT count(*) FROM auditoria_accesos")).scalar_one() == 0


def test_si_se_borra_la_cuenta_del_especialista_la_auditoria_conserva_su_correo(client, escena, db):
    otorgar(client, escena)
    db.execute(text("DELETE FROM usuarios WHERE email = 'doc@test.pe'"))
    db.commit()
    eventos = auditoria(client, escena)
    assert eventos and eventos[0]["especialista_email"] == "doc@test.pe"
    assert accesos(client, escena) == []
