from app.modules.dominio.estimador import actualizar, estado_inicial


def _n(estado, *aciertos, nivel=1):
    return actualizar(estado, [(nivel, a) for a in aciertos])


def test_estado_inicial():
    e = estado_inicial()
    assert (e["nivel"], e["racha"], e["ventana"], e["dominio"]) == (1, 0, [], 0.0)


def test_la_racha_cuenta_y_cambia_de_signo():
    e, _ = _n(estado_inicial(), True, True, True)
    assert e["racha"] == 3
    e, _ = _n(e, False)
    assert e["racha"] == -1
    e, _ = _n(e, True)
    assert e["racha"] == 1


def test_sube_con_racha_dominio_y_minimo_de_muestras():
    e, c = _n(estado_inicial(), True, True, True, True)
    assert e["nivel"] == 1 and c == []  # solo 4 muestras
    e, c = _n(e, True)
    assert e["nivel"] == 2
    assert (c[0]["de"], c[0]["a"], c[0]["motivo"]) == (1, 2, "subida")
    assert e["ventana"] == [] and e["racha"] == 0 and e["dominio"] == 0.0


def test_no_sube_si_el_dominio_no_supera_65():
    e, _ = _n(estado_inicial(), *[False] * 4, *[True] * 6)
    assert e["nivel"] == 1 and e["dominio"] == 0.6   # racha 6, pero 6/10 no supera 0.65
    e, _ = _n(e, True)                                # la ventana pasa a 7/10
    assert e["nivel"] == 2


def test_no_sube_con_racha_menor_a_2_aunque_el_dominio_sea_alto():
    e, _ = _n(estado_inicial(), True, True, True, True, False, True)
    assert e["nivel"] == 1 and e["racha"] == 1
    e, _ = _n(e, True)
    assert e["nivel"] == 2


def test_baja_con_racha_de_menos_2():
    base = {"nivel": 2, "dominio": 0.0, "racha": 0, "ventana": []}
    e, c = _n(base, False, nivel=2)
    assert e["nivel"] == 2 and c == []
    e, c = _n(e, False, nivel=2)
    assert e["nivel"] == 1 and c[0]["motivo"] == "bajada"


def test_limites_de_nivel():
    e, c = _n(estado_inicial(), *[False] * 5)
    assert e["nivel"] == 1 and c == []
    alto = {"nivel": 3, "dominio": 0.0, "racha": 0, "ventana": []}
    e, c = _n(alto, *[True] * 8, nivel=3)
    assert e["nivel"] == 3 and c == []


def test_ignora_respuestas_de_otro_nivel():
    e, c = actualizar(estado_inicial(), [(2, True), (3, False)])
    assert e == estado_inicial() and c == []


def test_ventana_maxima_de_10():
    e, _ = _n(estado_inicial(), *([True, False] * 8))
    assert len(e["ventana"]) == 10


def test_alternar_aciertos_y_fallos_no_cambia_el_nivel():
    e, c = _n(estado_inicial(), *([True, False] * 10))
    assert e["nivel"] == 1 and c == []


def test_no_modifica_el_estado_recibido():
    original = estado_inicial()
    actualizar(original, [(1, True)] * 5)
    assert original == estado_inicial()