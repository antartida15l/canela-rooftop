import pytest

from app.modules.atencion.reglas import PARAMS, Monitor, reproducir


def L(t, atencion=0.8, emocion="neutral", rostro=True):
    if not rostro:
        return {"t": t, "rostro": False, "atencion": None, "emocion": None}
    return {"t": t, "rostro": True, "atencion": atencion, "emocion": emocion}


def serie(inicio, n, **kw):
    return [L(inicio + 3 * i, **kw) for i in range(n)]


CALIB = serie(0, 5)  # 5 lecturas buenas: t = 0..12


def resumen(res):
    return [(i["t"], i["tipo"], i["motivo"]) for i in res]


def test_parametros_acordados():
    assert PARAMS["intervalo_s"] == 3
    assert PARAMS["calibracion_lecturas"] == 5
    assert PARAMS["confirmaciones"] == 2
    assert PARAMS["min_entre_intervenciones_s"] == 60


def test_no_interviene_durante_la_calibracion():
    lecturas = serie(0, 5, emocion="enojo", atencion=0.1)
    assert reproducir(lecturas) == []


def test_atencion_baja_dispara_tras_dos_lecturas_seguidas_suavizadas():
    # EMA tras calibrar = 0.8; umbral = 0.48. Con 0.1: 0.52, 0.352, 0.2512
    res = reproducir(CALIB + serie(15, 4, atencion=0.1))
    assert resumen(res) == [(21, "aviso_suave", "atencion_baja")]


def test_una_lectura_aislada_no_dispara_nada():
    caida = CALIB + [L(15, atencion=0.1)] + serie(18, 10)
    assert reproducir(caida) == []
    una_emocion = CALIB + [L(15, emocion="enojo")] + serie(18, 10)
    assert reproducir(una_emocion) == []


def test_malestar_dispara_tras_dos_lecturas_seguidas():
    res = reproducir(CALIB + serie(15, 2, emocion="enojo"))
    assert resumen(res) == [(18, "aviso_suave", "malestar")]


def test_malestar_tiene_prioridad_sobre_atencion_baja():
    res = reproducir(CALIB + serie(15, 6, atencion=0.05, emocion="miedo"))
    assert res[0]["motivo"] == "malestar"


def test_escalado_aviso_luego_pausa_y_separacion_minima():
    res = reproducir(CALIB + serie(15, 36, emocion="enojo"))   # hasta t = 120
    assert resumen(res) == [(18, "aviso_suave", "malestar"), (78, "pausa", "malestar")]


def test_el_patron_se_repite_y_nunca_hay_menos_de_60_s_entre_intervenciones():
    res = reproducir(CALIB + serie(15, 200, emocion="enojo"))
    assert [i["tipo"] for i in res[:4]] == ["aviso_suave", "pausa", "aviso_suave", "pausa"]
    gaps = [b["t"] - a["t"] for a, b in zip(res, res[1:])]
    assert gaps and all(g >= 60 for g in gaps)


def test_si_pasa_mucho_tiempo_el_escalado_se_reinicia():
    lecturas = (CALIB + serie(15, 2, emocion="enojo")      # aviso en t = 18
                + serie(21, 93)                            # calma hasta t = 297
                + [L(300, emocion="enojo"), L(303, emocion="enojo")])
    res = reproducir(lecturas)
    assert resumen(res) == [(18, "aviso_suave", "malestar"), (303, "aviso_suave", "malestar")]


def test_ausencia_de_rostro_necesita_tres_lecturas_y_no_cuenta_como_desatencion():
    dos = CALIB + [L(15, rostro=False), L(18, rostro=False)] + serie(21, 5)
    assert reproducir(dos) == []
    tres = CALIB + [L(15, rostro=False), L(18, rostro=False), L(21, rostro=False)]
    assert resumen(reproducir(tres)) == [(21, "aviso_suave", "ausente")]


def test_parametros_configurables():
    lecturas = CALIB + serie(15, 2, emocion="enojo")
    assert reproducir(lecturas, {"confirmaciones": 3}) == []
    assert len(reproducir(CALIB + serie(15, 3, emocion="enojo"), {"confirmaciones": 3})) == 1


def test_el_umbral_se_adapta_a_la_atencion_base_del_nino():
    # Un niño con base baja (0.3) no debe disparar con 0.25: umbral = max(0.2, 0.18) = 0.2
    lecturas = serie(0, 5, atencion=0.3) + serie(15, 10, atencion=0.25)
    assert reproducir(lecturas) == []


def test_monitor_expone_el_estado_de_calibracion():
    m = Monitor()
    assert not m.calibrado
    for l in CALIB:
        m.procesar(l["t"], l["atencion"], l["emocion"])
    assert m.calibrado
    