import json

import pytest
from sqlalchemy import text


def insertar_sesion(db, nino_id, dias_atras, nota, habilidad="matematica_suma", respondidas=10,
                    correctas=8, duracion_s=600, atencion=None, cerrada=True, marca=None):
    kpi = {"respondidas": respondidas, "correctas": correctas, "duracion_s": duracion_s}
    if atencion:
        kpi["atencion"] = atencion
    detalle = {"lecturas": [{"t": 0, "rostro": True, "atencion": 0.5, "emocion": marca}]} if marca else {}
    db.execute(text("""
        INSERT INTO sesiones (nino_id, inicio, fin, ajustes, kpi, detalle, nota)
        VALUES (CAST(:n AS uuid), now() - (:d * INTERVAL '1 day'),
                CASE WHEN :c THEN now() - (:d * INTERVAL '1 day') + INTERVAL '10 minutes' END,
                CAST(:aj AS jsonb), CAST(:k AS jsonb), CAST(:de AS jsonb), :nota)"""),
        {"n": nino_id, "d": dias_atras, "c": cerrada, "aj": json.dumps({"habilidad": habilidad}),
         "k": json.dumps(kpi if cerrada else {}), "de": json.dumps(detalle),
         "nota": nota if cerrada else None})
    db.commit()


@pytest.fixture
def familia(client, registrar, nino_de):
    h = registrar("padre@test.pe")
    return h, nino_de(h, condicion="tdah")


def test_reporte_del_padre(client, familia, db):
    h, nino = familia
    for dias, nota in [(20, 10), (15, 11), (6, 15), (2, 16)]:
        insertar_sesion(db, nino, dias, nota)
    r = client.get(f"/reportes/{nino}?dias=30", headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["alcance"] == "completo" and j["periodo_dias"] == 30
    assert j["nino"] == {"nombre": "Luis", "edad": 8}
    assert j["resumen"]["sesiones"] == 4 and j["resumen"]["nota_media"] == 13.0
    assert j["resumen"]["tendencia"] == "mejora"
    assert j["resumen"]["minutos"] == 40
    assert [s["nota"] for s in j["sesiones"]] == [16.0, 15.0, 11.0, 10.0]  # recientes primero
    assert j["recomendaciones"][-1]["texto"].startswith("Este reporte es orientativo")


def test_el_periodo_filtra_y_las_sesiones_sin_cerrar_se_ignoran(client, familia, db):
    h, nino = familia
    insertar_sesion(db, nino, 5, 14)
    insertar_sesion(db, nino, 60, 20)                       # fuera de 30 días
    insertar_sesion(db, nino, 1, None, cerrada=False)       # abandonada
    assert client.get(f"/reportes/{nino}?dias=30", headers=h).json()["resumen"]["sesiones"] == 1
    assert client.get(f"/reportes/{nino}?dias=90", headers=h).json()["resumen"]["sesiones"] == 2


@pytest.mark.parametrize("dias", [0, 6, 366])
def test_periodo_invalido(client, familia, dias):
    h, nino = familia
    assert client.get(f"/reportes/{nino}?dias={dias}", headers=h).status_code == 422


def test_sin_sesiones_el_reporte_sirve_igual(client, familia):
    h, nino = familia
    j = client.get(f"/reportes/{nino}", headers=h).json()
    assert j["resumen"]["sesiones"] == 0 and "Aún no hay sesiones" in j["recomendaciones"][0]["texto"]


def test_el_reporte_no_filtra_la_condicion_ni_el_detalle_crudo(client, familia, db):
    h, nino = familia                                       # condición declarada: TDAH
    insertar_sesion(db, nino, 3, 12, marca="enojo")
    cuerpo = client.get(f"/reportes/{nino}", headers=h).text.lower()
    for prohibido in ("tdah", "perfil", "condicion", "detalle", "lecturas", "enojo"):
        assert prohibido not in cuerpo


def test_el_reporte_resume_la_camara(client, familia, db):
    h, nino = familia
    a = {"lecturas": 100, "atencion_media": 0.3, "pct_malestar": 0.4, "avisos": 2, "pausas_sugeridas": 1}
    for d in (3, 2, 1):
        insertar_sesion(db, nino, d, 12, atencion=a)
    j = client.get(f"/reportes/{nino}", headers=h).json()
    assert j["atencion"]["sesiones_con_camara"] == 3 and j["atencion"]["avisos"] == 6
    assert any("malestar" in r["texto"] for r in j["recomendaciones"])


def test_aislamiento_y_roles(client, familia, registrar, especialista_de, db):
    h, nino = familia
    assert client.get(f"/reportes/{nino}", headers=registrar("otra@test.pe")).status_code == 404
    assert client.get(f"/reportes/{nino}").status_code == 401
    assert client.get(f"/reportes/{nino}", headers=especialista_de()).status_code == 403
    assert client.get("/reportes/no-es-uuid", headers=h).status_code == 422
