ORIGEN = "http://localhost:5173"


def test_el_preflight_del_frontend_esta_permitido(client):
    r = client.options("/auth/login", headers={
        "Origin": ORIGEN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization,x-zona-padres",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ORIGEN
    assert r.headers["access-control-allow-credentials"] == "true"


def test_una_respuesta_normal_lleva_la_cabecera_cors(client):
    r = client.get("/salud", headers={"Origin": ORIGEN})
    assert r.headers["access-control-allow-origin"] == ORIGEN
    assert r.headers["access-control-allow-credentials"] == "true"


def test_los_errores_tambien_llevan_la_cabecera_cors(client):
    r = client.get("/auth/yo", headers={"Origin": ORIGEN})   # 401 sin token
    assert r.status_code == 401
    assert r.headers["access-control-allow-origin"] == ORIGEN


def test_otros_origenes_no_estan_permitidos(client):
    r = client.options("/auth/login", headers={
        "Origin": "https://sitio-malicioso.example",
        "Access-Control-Request-Method": "POST",
    })
    assert "access-control-allow-origin" not in r.headers
    r = client.get("/salud", headers={"Origin": "https://sitio-malicioso.example"})
    assert "access-control-allow-origin" not in r.headers
