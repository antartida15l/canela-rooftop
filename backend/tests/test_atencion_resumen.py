import re

import pytest

from app.modules.atencion.observaciones import AVISO_LEGAL, generar
from app.modules.atencion.resumen import resumir


def _l(t, atencion, emocion, rostro=True):
    return {"t": t, "rostro": rostro, "atencion": atencion, "emocion": emocion}


def test_resumir_sin_lecturas():
    assert resumir([], [], []) is None


def test_resumir_agregados():
    lecturas = [_l(0, 0.8, "neutral"), _l(3, 0.6, "feliz"),
                _l(6, None, None, rostro=False), _l(9, 0.2, "enojo")]
    r = resumir(lecturas, [{"t": 9, "tipo": "aviso_suave", "motivo": "malestar"}],
                [{"inicio_s": 5, "duracion_s": 30}])
    assert r["lecturas"] == 4
    assert r["atencion_media"] == pytest.approx(0.533, abs=0.001)
    assert r["pct_atencion_alta"] == pytest.approx(0.667, abs=0.001)
    assert r["pct_sin_rostro"] == 0.25
    assert r["pct_malestar"] == pytest.approx(0.333, abs=0.001)
    assert r["emociones"]["enojo"] == pytest.approx(0.333, abs=0.001)
    assert (r["avisos"], r["pausas_sugeridas"], r["pausas_realizadas"]) == (1, 0, 1)


RESUMENES = [
    {"lecturas": 100, "atencion_media": 0.2, "pct_atencion_alta": 0.1, "pct_sin_rostro": 0.5,
     "emociones": {"enojo": 0.6}, "pct_malestar": 0.6, "avisos": 4, "pausas_sugeridas": 3,
     "pausas_realizadas": 2},
    {"lecturas": 100, "atencion_media": 0.9, "pct_atencion_alta": 1.0, "pct_sin_rostro": 0.0,
     "emociones": {"feliz": 1.0}, "pct_malestar": 0.0, "avisos": 0, "pausas_sugeridas": 0,
     "pausas_realizadas": 0},
    {"lecturas": 10, "atencion_media": None, "pct_atencion_alta": None, "pct_sin_rostro": 1.0,
     "emociones": {}, "pct_malestar": 0.0, "avisos": 0, "pausas_sugeridas": 0,
     "pausas_realizadas": 0},
]
ETIQUETAS_DIAGNOSTICAS = re.compile(
    r"\b(tdah|tea|autismo|autista|dislexia|discalculia|trastorno|d[eé]ficit|padece|sufre)\b", re.I)


def test_sin_resumen_no_hay_observaciones():
    assert generar("Luis", None) == []


@pytest.mark.parametrize("resumen", RESUMENES)
def test_las_observaciones_nunca_diagnostican(resumen):
    textos = [o["texto"] for o in generar("Luis", resumen)]
    assert textos[-1] == AVISO_LEGAL
    assert not any(ETIQUETAS_DIAGNOSTICAS.search(t) for t in textos)


def test_sesion_dificil_genera_observaciones_con_matices():
    textos = " ".join(o["texto"] for o in generar("Luis", RESUMENES[0]))
    assert "Luis" in textos and "puede" in textos.lower()
    assert "malestar" in textos and "avisos o pausas" in textos


def test_sesion_buena_genera_mensaje_positivo():
    obs = generar("Luis", RESUMENES[1])
    assert any("buena orientación" in o["texto"] for o in obs)
    assert not any(o["nivel"] == "atencion" for o in obs)