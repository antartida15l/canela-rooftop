import inspect

import pytest

from app.modules.sesiones.calificacion import calcular_nota, corregir, credito


def test_corregir_cuenta_hasta_el_primer_acierto():
    c = {"correcta": 1}
    assert corregir(c, [1]) == (True, 1)
    assert corregir(c, [0, 1]) == (True, 2)
    assert corregir(c, [0, 0, 1]) == (True, 3)
    assert corregir(c, [0, 2, 2]) == (False, 3)
    assert corregir(c, [0, 0, 0, 1]) == (False, 3)  # el 4.º intento no cuenta


def test_credito_baja_con_los_intentos():
    assert credito(True, 1) == 1.0
    assert credito(True, 2) == pytest.approx(0.7)
    assert credito(True, 3) == pytest.approx(0.4)
    assert credito(False, 1) == 0.0


def test_todo_correcto_al_primer_intento_es_20():
    assert calcular_nota([(1, True, 1)] * 10, objetivo=10)[0] == 20.0


def test_todo_incorrecto_solo_conserva_el_peso_del_progreso():
    assert calcular_nota([(1, False, 3)] * 10, objetivo=10)[0] == 3.0


def test_fallar_un_ejercicio_dificil_pesa_mas_que_uno_facil():
    falla_dificil = calcular_nota([(3, False, 3), (1, True, 1)], objetivo=2)[0]
    falla_facil = calcular_nota([(3, True, 1), (1, False, 3)], objetivo=2)[0]
    assert falla_facil > falla_dificil


def test_menos_ejercicios_que_el_objetivo_baja_poco():
    assert calcular_nota([(1, True, 1)] * 5, objetivo=10)[0] == 18.5


def test_sin_respuestas_no_hay_nota():
    assert calcular_nota([], objetivo=10)[0] is None


def test_la_nota_no_recibe_atencion():
    """El cálculo solo admite aciertos y progreso, nunca atención o emociones."""
    assert list(inspect.signature(calcular_nota).parameters) == ["items", "objetivo"]