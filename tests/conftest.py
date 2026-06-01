import pytest

from boologic.expressions import Var


@pytest.fixture
def vars():
    a = Var("A")
    b = Var("B")
    c = Var("C")
    d = Var("D")
    e = Var("E")
    f = Var("F")
    return a, b, c, d, e, f
