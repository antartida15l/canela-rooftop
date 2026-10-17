import re
from datetime import datetime, timezone

import pytest

from app.modules.reportes.calculo import AVISO_REPORTE, construir, tendencia

DIAGNOSTICOS = re.compile(
    r"\b(tdah|tea|autismo|autista|dislexia|discalculia|trastorno|d[eé]ficit|padece|sufre)\b", re.I)
AHORA = datetime(2026, 3, 1, tzinfo=timezone.utc)


def sesion(i, nota, habilidad="matematica_suma", respondidas=10, correctas=8, duracion_s=600,
           atencion=None):
    kpi = {"respondidas": respondidas, "correctas": correctas, "duracion_s": duracion_s}
    if atencion:
        kpi["atencion"] = atencion
    return {"id": f"s{i}", "inicio": AHORA, "habilidad": habilidad, "nota": nota, "kpi": kpi}


NINO = {"nombre": "Luis", "edad": 8, "dominio": {}}


def textos(reporte):
    return [r["texto"] for r in reporte["recomendaciones"]]


@pytest.mark.parametrize("notas,esperado", [
    ([10, 12, 14], "insuficiente"),
    ([10, 10, 14, 14], "mejora"),
    ([14, 14, 10, 10], "baja"),
    ([12, 12.5, 12, 12.4], "estable"),
])
def test_tendencia(notas, esperado):
    assert tendencia(notas) == esperado


def test_sin_sesiones():
    r = construir(NINO, [], 30, "completo")
    assert r["resumen"]["sesiones"] == 0 and r["resumen"]["nota_media"] is None
    assert r["sesiones"] == [] and r["atencion"] is None
    assert "Aún no hay sesiones" in textos(r)[0]
    assert textos(r)[-1] == AVISO_REPORTE


def test_resumen_numerico():
    ss = [sesion(1, 12, correctas=6, duracion_s=300), sesion(2, 16, correctas=10, duracion_s=900)]
    r = construir(NINO, ss, 30, "completo")["resumen"]
    assert r["sesiones"] == 2 and r["minutos"] == 20
    assert r["nota_media"] == 14.0
    assert r["aciertos_pct"] == 0.8          # 16 de 20


def test_habilidades_combina_sesiones_y_dominio():
    nino = {**NINO, "dominio": {"matematica_suma": {"nivel": 2, "dominio": 0.7},
                                "lectura_comprension": {"nivel": 1, "dominio": 0.2}}}
    r = construir(nino, [sesion(1, 14), sesion(2, 18)], 30, "completo")
    por = {h["habilidad"]: h for h in r["habilidades"]}
    assert por["matematica_suma"]["sesiones"] == 2 and por["matematica_suma"]["nota_media"] == 16.0
    assert por["matematica_suma"]["nivel"] == 2
    assert por["lectura_comprension"]["sesiones"] == 0 and por["lectura_comprension"]["nota_media"] is None


def test_sesiones_van_de_la_mas_reciente_a_la_mas_antigua():
    ids = [s["id"] for s in construir(NINO, [sesion(1, 10), sesion(2, 12), sesion(3, 14)], 30, "resumen")["sesiones"]]
    assert ids == ["s3", "s2", "s1"]


def test_atencion_se_pondera_por_lecturas():
    a1 = {"lecturas": 100, "atencion_media": 0.8, "pct_malestar": 0.0, "avisos": 1, "pausas_sugeridas": 0}
    a2 = {"lecturas": 300, "atencion_media": 0.4, "pct_malestar": 0.4, "avisos": 2, "pausas_sugeridas": 1}
    r = construir(NINO, [sesion(1, 12, atencion=a1), sesion(2, 12, atencion=a2)], 30, "completo")
    at = r["atencion"]
    assert at["sesiones_con_camara"] == 2
    assert at["atencion_media"] == pytest.approx(0.5, abs=0.001)    # (80 + 120) / 400
    assert at["pct_malestar"] == pytest.approx(0.3, abs=0.001)
    assert (at["avisos"], at["pausas_sugeridas"]) == (3, 1)


def test_el_alcance_resumen_no_incluye_atencion_ni_recomendaciones():
    a = {"lecturas": 100, "atencion_media": 0.8, "pct_malestar": 0.0, "avisos": 0, "pausas_sugeridas": 0}
    r = construir(NINO, [sesion(1, 12, atencion=a)], 30, "resumen")
    assert r["atencion"] is None and r["recomendaciones"] is None
    assert r["resumen"]["sesiones"] == 1 and r["habilidades"]


def test_recomendacion_por_pocas_sesiones():
    assert any("pocas" in t or "regularidad" in t for t in textos(construir(NINO, [sesion(1, 14)], 30, "completo")))
    muchas = [sesion(i, 14) for i in range(10)]
    assert not any("regularidad" in t for t in textos(construir(NINO, muchas, 30, "completo")))


def test_recomendacion_por_notas_bajas_y_mejora():
    bajas = [sesion(i, 6) for i in range(10)]
    assert any("bajo" in t for t in textos(construir(NINO, bajas, 30, "completo")))
    mejora = [sesion(i, n) for i, n in enumerate([8, 8, 14, 14, 14, 14, 14, 14])]
    assert any("mejora" in t for t in textos(construir(NINO, mejora, 30, "completo")))
    empeora = [sesion(i, n) for i, n in enumerate([16, 16, 16, 16, 10, 10, 10, 10])]
    assert any("bajaron" in t for t in textos(construir(NINO, empeora, 30, "completo")))


def test_recomendacion_por_dominio_alto_en_el_nivel_maximo():
    nino = {**NINO, "dominio": {"matematica_suma": {"nivel": 3, "dominio": 0.9}}}
    assert any("explorar otra habilidad" in t for t in textos(construir(nino, [sesion(1, 18)], 30, "completo")))


def test_recomendacion_por_atencion_baja_y_malestar():
    a = {"lecturas": 100, "atencion_media": 0.2, "pct_malestar": 0.5, "avisos": 1, "pausas_sugeridas": 0}
    t = " ".join(textos(construir(NINO, [sesion(i, 12, atencion=a) for i in range(5)], 30, "completo")))
    assert "atención baja" in t and "malestar" in t


@pytest.mark.parametrize("alcance", ["resumen", "completo"])
def test_el_reporte_nunca_diagnostica_ni_revela_la_condicion(alcance):
    a = {"lecturas": 100, "atencion_media": 0.1, "pct_malestar": 0.9, "avisos": 9, "pausas_sugeridas": 9}
    nino = {"nombre": "Luis", "edad": 8,
            "dominio": {"matematica_suma": {"nivel": 3, "dominio": 0.95}}}
    r = construir(nino, [sesion(i, n, atencion=a) for i, n in enumerate([4, 5, 6, 7, 5, 4, 3, 2])], 30, alcance)
    plano = repr(r)
    assert not DIAGNOSTICOS.search(plano)
    assert "perfil" not in plano and "condicion" not in plano
    if alcance == "completo":
        assert textos(r)[-1] == AVISO_REPORTE
