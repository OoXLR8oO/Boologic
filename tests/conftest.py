import pytest

from boologic.expressions import Const, Var


@pytest.fixture
def four_vars():
    A, B, C, D = Var("A"), Var("B"), Var("C"), Var("D")
    return A, B, C, D


@pytest.fixture
def vars_():
    a = Var("A")
    b = Var("B")
    c = Var("C")
    d = Var("D")
    e = Var("E")
    f = Var("F")
    return a, b, c, d, e, f


@pytest.fixture
def consts():
    return Const(True), Const(False)
