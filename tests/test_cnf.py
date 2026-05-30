from boologic.cnf import (
    clauses_to_expr,
    flatten,
    pretty_print_cnf,
    reduce_cnf,
    to_cnf,
)
from boologic.expressions import And, Const, Not, Or, Var

# ----------------------------
# helpers
# ----------------------------


def CNF(expr):
    return to_cnf(expr)


def RED(expr):
    return reduce_cnf(expr)


# ----------------------------
# implication / structural CNF rules
# ----------------------------


def test_implication_and_biconditional_rules(vars_):
    a, b, c, *_ = vars_

    expr1 = (a >> b) >> c
    assert CNF(expr1) == And(Or(a, c), Or(Not(b), c))
    assert RED(CNF(expr1)) == And(Or(a, c), Or(Not(b), c))

    expr2 = a ^ b
    assert CNF(expr2) == And(Or(Not(a), b), Or(a, Not(b)))


# ----------------------------
# De Morgan laws
# ----------------------------


def test_demorgan_laws(vars_):
    a, b, *_ = vars_

    assert CNF(~(a & b)) == Or(Not(a), Not(b))
    assert CNF(~(a | b)) == And(Not(a), Not(b))
    assert RED(CNF(~(a | b))) == And(Not(a), Not(b))


# ----------------------------
# unit propagation behaviour
# ----------------------------


def test_unit_propagation(vars_):
    a, b, *_ = vars_

    expr = a & (a >> b)
    cnf = CNF(expr)

    assert cnf == And(a, Or(Not(a), b))
    assert RED(cnf) == And(a, b)


# ----------------------------
# constants in CNF contexts
# ----------------------------


def test_constants_behaviour(vars_):
    a, *_ = vars_
    t, f = Const(True), Const(False)

    assert RED(CNF(t & a)) == a
    assert RED(CNF(f & a)) == Const(False)

    assert RED(CNF((a | t) & a)) == a
    assert RED(CNF((a | f) & a)) == a


# ----------------------------
# tautology + contradiction elimination
# ----------------------------


def test_tautology_and_contradiction_rules(vars_):
    a, b, *_ = vars_

    assert RED(CNF(a | ~a)) == Const(True)
    assert RED(CNF(a & ~a)) == Const(False)

    assert RED(CNF((a | ~a) & (b | ~b))) == Const(True)
    assert RED(CNF((a & ~a) & (b | ~b))) == Const(False)


# ----------------------------
# mixed CNF simplification scenario
# ----------------------------


def test_complex_cnf_reduction(vars_):
    a, b, c, d, *_ = vars_

    expr = (a ^ (c >> ~d)) & b & (b >> a)

    reduced = RED(CNF(expr))

    assert reduced == And(And(Or(Not(c), Not(d)), b), a)


# ----------------------------
# identity elements (single pass)
# ----------------------------


def test_identity_cases():
    a = Var("A")

    assert CNF(Const(True)) == Const(True)
    assert RED(CNF(Const(True))) == Const(True)

    assert CNF(Const(False)) == Const(False)
    assert RED(CNF(Const(False))) == Const(False)

    assert CNF(a) == a
    assert RED(CNF(a)) == a

    assert CNF(~a) == Not(a)
    assert RED(CNF(~a)) == Not(a)


# ----------------------------
# OR/AND algebra edge cases
# ----------------------------


def test_or_and_edge_cases():
    a = Var("A")

    assert RED(CNF(a | Const(True))) == Const(True)
    assert RED(CNF(Const(True) | a)) == Const(True)

    assert RED(CNF(a | Const(False))) == a
    assert RED(CNF(Const(False) | a)) == a

    assert RED(CNF(a & Const(True))) == a
    assert RED(CNF(Const(True) & a)) == a

    assert RED(CNF(a & Const(False))) == Const(False)


# ----------------------------
# nested structural cases
# ----------------------------


def test_nested_structural_cases():
    a = Var("A")
    b = Var("B")

    assert RED(CNF(a | (~a & b))) == Or(a, b)


# ----------------------------
# low-level function coverage
# ----------------------------


def test_low_level_helpers():
    class Dummy:
        pass

    dummy = Dummy()
    assert to_cnf(dummy) is dummy

    a = Var("A")
    assert flatten(a, And) == [a]
    assert flatten(a, Or) == [a]

    assert isinstance(clauses_to_expr([[]]), Const)


# ----------------------------
# pretty printing
# ----------------------------


def test_pretty_printing():
    a, b, c = Var("A"), Var("B"), Var("C")

    expr = And(And(a, b), c)
    out = pretty_print_cnf(expr, indent=2)

    assert "∧" in out
