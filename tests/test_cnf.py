from boologic.cnf import (
    reduce_cnf,
    to_cnf,
)
from boologic.expressions import And, Const, Not, Or, Var


def test_implication_and_biconditional_rules(vars_):
    a, b, c, *_ = vars_

    expr1 = (a >> b) >> c
    assert to_cnf(expr1) == And(Or(a, c), Or(Not(b), c))
    assert reduce_cnf(to_cnf(expr1)) == And(Or(a, c), Or(Not(b), c))

    expr2 = a ^ b
    assert to_cnf(expr2) == And(Or(Not(a), b), Or(a, Not(b)))


def test_demorgan_laws(vars_):
    a, b, *_ = vars_

    assert to_cnf(~(a & b)) == Or(Not(a), Not(b))
    assert to_cnf(~(a | b)) == And(Not(a), Not(b))
    assert reduce_cnf(to_cnf(~(a | b))) == And(Not(a), Not(b))


def test_unit_propagation(vars_):
    a, b, *_ = vars_

    expr = a & (a >> b)
    cnf = to_cnf(expr)

    assert cnf == And(a, Or(Not(a), b))
    assert reduce_cnf(cnf) == And(a, b)


def test_constants_behaviour(vars_):
    a, *_ = vars_
    t, f = Const(True), Const(False)

    assert reduce_cnf(to_cnf(t & a)) == a
    assert reduce_cnf(to_cnf(f & a)) == Const(False)

    assert reduce_cnf(to_cnf((a | t) & a)) == a
    assert reduce_cnf(to_cnf((a | f) & a)) == a


def test_tautology_and_contradiction_rules(vars_):
    a, b, *_ = vars_

    assert reduce_cnf(to_cnf(a | ~a)) == Const(True)
    assert reduce_cnf(to_cnf(a & ~a)) == Const(False)

    assert reduce_cnf(to_cnf((a | ~a) & (b | ~b))) == Const(True)
    assert reduce_cnf(to_cnf((a & ~a) & (b | ~b))) == Const(False)


def test_complex_cnf_reduction(vars_):
    a, b, c, d, *_ = vars_

    expr = (a ^ (c >> ~d)) & b & (b >> a)

    reduced = reduce_cnf(to_cnf(expr))

    assert reduced == And(And(Or(Not(c), Not(d)), b), a)


def test_identity_cases():
    a = Var("A")

    assert to_cnf(Const(True)) == Const(True)
    assert reduce_cnf(to_cnf(Const(True))) == Const(True)

    assert to_cnf(Const(False)) == Const(False)
    assert reduce_cnf(to_cnf(Const(False))) == Const(False)

    assert to_cnf(a) == a
    assert reduce_cnf(to_cnf(a)) == a

    assert to_cnf(~a) == Not(a)
    assert reduce_cnf(to_cnf(~a)) == Not(a)


def test_or_and_edge_cases():
    a = Var("A")

    assert reduce_cnf(to_cnf(a | Const(True))) == Const(True)
    assert reduce_cnf(to_cnf(Const(True) | a)) == Const(True)

    assert reduce_cnf(to_cnf(a | Const(False))) == a
    assert reduce_cnf(to_cnf(Const(False) | a)) == a

    assert reduce_cnf(to_cnf(a & Const(True))) == a
    assert reduce_cnf(to_cnf(Const(True) & a)) == a

    assert reduce_cnf(to_cnf(a & Const(False))) == Const(False)


def test_nested_structural_cases():
    a = Var("A")
    b = Var("B")

    assert reduce_cnf(to_cnf(a | (~a & b))) == Or(a, b)
