from boologic.cnf import (
    reduce_cnf,
    to_cnf,
)
from boologic.expressions import And, Const, Not, Or


def test_implication_and_biconditional_rules(vars):
    A, B, C, *_ = vars

    expr1 = (A >> B) >> C
    assert to_cnf(expr1) == And(Or(A, C), Or(Not(B), C))
    assert reduce_cnf(to_cnf(expr1)) == And(Or(A, C), Or(Not(B), C))

    expr2 = A ^ B
    assert to_cnf(expr2) == And(Or(Not(A), B), Or(A, Not(B)))


def test_demorgan_laws(vars):
    A, B, *_ = vars

    assert to_cnf(~(A & B)) == Or(Not(A), Not(B))
    assert to_cnf(~(A | B)) == And(Not(A), Not(B))
    assert reduce_cnf(to_cnf(~(A | B))) == And(Not(A), Not(B))


def test_unit_propagation(vars):
    A, B, *_ = vars

    expr = A & (A >> B)
    cnf = to_cnf(expr)

    assert cnf == And(A, Or(Not(A), B))
    assert reduce_cnf(cnf) == And(A, B)


def test_constants_behaviour(vars):
    A, *_ = vars

    assert reduce_cnf(to_cnf(Const(True) & A)) == A
    assert reduce_cnf(to_cnf(Const(False) & A)) == Const(False)

    assert reduce_cnf(to_cnf((A | Const(True)) & A)) == A
    assert reduce_cnf(to_cnf((A | Const(False)) & A)) == A


def test_tautology_and_contradiction_rules(vars):
    A, B, *_ = vars

    assert reduce_cnf(to_cnf(A | ~A)) == Const(True)
    assert reduce_cnf(to_cnf(A & ~A)) == Const(False)

    assert reduce_cnf(to_cnf((A | ~A) & (B | ~B))) == Const(True)
    assert reduce_cnf(to_cnf((A & ~A) & (B | ~B))) == Const(False)


def test_complex_cnf_reduction(vars):
    A, B, C, D, *_ = vars

    expr = (A ^ (C >> ~D)) & B & (B >> A)

    reduced = reduce_cnf(to_cnf(expr))

    assert reduced == And(And(Or(Not(C), Not(D)), B), A)


def test_identity_cases(vars):
    A, *_ = vars

    assert to_cnf(Const(True)) == Const(True)
    assert reduce_cnf(to_cnf(Const(True))) == Const(True)

    assert to_cnf(Const(False)) == Const(False)
    assert reduce_cnf(to_cnf(Const(False))) == Const(False)

    assert to_cnf(A) == A
    assert reduce_cnf(to_cnf(A)) == A

    assert to_cnf(~A) == Not(A)
    assert reduce_cnf(to_cnf(~A)) == Not(A)


def test_or_and_edge_cases(vars):
    A, *_ = vars

    assert reduce_cnf(to_cnf(A | Const(True))) == Const(True)
    assert reduce_cnf(to_cnf(Const(True) | A)) == Const(True)

    assert reduce_cnf(to_cnf(A | Const(False))) == A
    assert reduce_cnf(to_cnf(Const(False) | A)) == A

    assert reduce_cnf(to_cnf(A & Const(True))) == A
    assert reduce_cnf(to_cnf(Const(True) & A)) == A

    assert reduce_cnf(to_cnf(A & Const(False))) == Const(False)


def test_nested_structural_cases(vars):
    A, B, *_ = vars

    assert reduce_cnf(to_cnf(A | (~A & B))) == Or(A, B)
