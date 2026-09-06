import pytest
from core.numlib import INF, NEG_INF, str_to_num, is_infinity


def test_inf_comparisons():
    assert INF > 99999999
    assert NEG_INF < -99999999
    assert INF >= INF
    assert INF == INF
    assert NEG_INF == NEG_INF
    assert INF > NEG_INF
    assert is_infinity(INF)
    assert not is_infinity(99)


def test_inf_arithmetic():
    assert INF + 1 == INF
    assert INF * 2 == INF
    assert INF * -1 == NEG_INF
    assert NEG_INF * -1 == INF

    assert 10 / INF == 0.0
    assert 10 / NEG_INF == 0.0


def test_inf_exceptions():
    with pytest.raises(ValueError):
        _ = INF - INF
    with pytest.raises(ValueError):
        _ = NEG_INF - NEG_INF
    with pytest.raises(ZeroDivisionError):
        _ = INF / INF


def test_str_to_num():
    assert str_to_num("42") == 42
    assert str_to_num("3.14") == 3.14
    assert str_to_num("inf") is INF
    assert str_to_num("-inf") is NEG_INF
