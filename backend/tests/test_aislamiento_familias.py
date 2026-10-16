def _crear_nino(client, zona, nombre="Luis", edad=8, condicion="tdah"):
    r = client.post("/ninos", json={"nombre": nombre, "edad": edad, "condicion": condicion},
                    headers=zona)
    assert r.status_code == 201, r.text
    return r.json()


def test_familia_b_no_ve_ni_toca_ninos_de_familia_a(client, registrar, con_zona):
    ha = registrar("a@test.pe")
    za = con_zona(ha)
    nino = _crear_nino(client, za)
    nid = nino["id"]

    hb = registrar("b@test.pe")
    zb = con_zona(hb)

    # Listado: B no ve nada
    assert client.get("/ninos", headers=hb).json() == []
    # Lectura, edición, condición y borrado: 404 aunque B tenga zona de padres propia
    assert client.get(f"/ninos/{nid}", headers=hb).status_code == 404
    assert client.patch(f"/ninos/{nid}", json={"nombre": "Hack"}, headers=zb).status_code == 404
    assert client.get(f"/ninos/{nid}/condicion", headers=zb).status_code == 404
    assert client.delete(f"/ninos/{nid}", headers=zb).status_code == 404

    # El niño de A sigue intacto
    intacto = client.get(f"/ninos/{nid}", headers=ha).json()
    assert intacto["nombre"] == "Luis"
    assert client.get(f"/ninos/{nid}/condicion", headers=za).json() == {"condicion": "tdah"}


def test_token_de_zona_de_otra_familia_no_sirve(client, registrar, con_zona):
    za = con_zona(registrar("a@test.pe"))
    hb = registrar("b@test.pe")
    con_zona(hb)  # B define su PIN
    mezclado = {**hb, "X-Zona-Padres": za["X-Zona-Padres"]}  # access de B + zona de A
    r = client.post("/ninos", json={"nombre": "X", "edad": 8}, headers=mezclado)
    assert r.status_code == 403


def test_cada_familia_lista_solo_los_suyos(client, registrar, con_zona):
    ha, hb = registrar("a@test.pe"), registrar("b@test.pe")
    za, zb = con_zona(ha), con_zona(hb)
    _crear_nino(client, za, "Ana")
    _crear_nino(client, za, "Beto")
    _crear_nino(client, zb, "Carla")
    assert sorted(n["nombre"] for n in client.get("/ninos", headers=ha).json()) == ["Ana", "Beto"]
    assert [n["nombre"] for n in client.get("/ninos", headers=hb).json()] == ["Carla"]