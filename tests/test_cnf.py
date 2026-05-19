from boologic.expressions import Var, Const, Not, And, Or
from boologic.cnf import to_cnf, reduce_cnf


def test_implication_chain(vars_):
    a, b, c, *_ = vars_
    expr = (a >> b) >> c
    cnf = to_cnf(expr)
    expected = And(Or(a, c), Or(Not(b), c))
    assert cnf == expected
    assert reduce_cnf(cnf) == expected


def test_biconditional(vars_):
    a, b, *_ = vars_
    expr = a ^ b
    cnf = to_cnf(expr)
    expected = And(Or(Not(a), b), Or(a, Not(b)))
    assert cnf == expected


def test_demorgan_and(vars_):
    a, b, *_ = vars_
    expr = ~(a & b)
    cnf = to_cnf(expr)
    expected = Or(Not(a), Not(b))
    assert cnf == expected


def test_demorgan_or(vars_):
    a, b, *_ = vars_
    expr = ~(a | b)
    cnf = to_cnf(expr)
    expected = And(Not(a), Not(b))
    assert cnf == expected
    assert reduce_cnf(cnf) == expected


def test_unit_propagation(vars_):
    a, b, *_ = vars_
    expr = a & (a >> b)
    cnf = to_cnf(expr)
    expected = And(a, Or(Not(a), b))
    assert cnf == expected
    reduced = reduce_cnf(cnf)
    assert reduced == And(a, b)


def test_constants_and(vars_, consts):
    a, *_ = vars_
    t, f = consts

    cnf_true_and_a = to_cnf(t & a)
    assert reduce_cnf(cnf_true_and_a) == a

    cnf_false_and_a = to_cnf(f & a)
    assert reduce_cnf(cnf_false_and_a) == Const(False)


def test_constants_in_clause(vars_, consts):
    a, *_ = vars_
    t, f = consts

    expr = (a | t) & a
    cnf = to_cnf(expr)
    assert reduce_cnf(cnf) == a

    expr2 = (a | f) & a
    cnf2 = to_cnf(expr2)
    assert reduce_cnf(cnf2) == a


def test_tautological_clause_removed(vars_):
    a, *_ = vars_
    b = Var("B")
    expr = (a | ~a) & b
    cnf = to_cnf(expr)
    assert reduce_cnf(cnf) == b


def test_contradiction_becomes_false(vars_):
    a, *_ = vars_
    expr = a & ~a
    cnf = to_cnf(expr)
    assert reduce_cnf(cnf) == Const(False)


def test_reduce_cnf_main_example(vars_):
    a, b, c, d, *_ = vars_
    expr = (a ^ (c >> ~d)) & b & (b >> a)
    cnf = to_cnf(expr)
    reduced = reduce_cnf(cnf)
    expected = And(And(Or(Not(c), Not(d)), b), a)
    assert reduced == expected


def test_trivial_true():
    expr = Const(True)
    cnf = to_cnf(expr)
    assert cnf == Const(True)
    assert reduce_cnf(cnf) == Const(True)


def test_trivial_false():
    expr = Const(False)
    cnf = to_cnf(expr)
    assert cnf == Const(False)
    assert reduce_cnf(cnf) == Const(False)


def test_single_literal(vars_):
    a, *_ = vars_
    expr = a
    cnf = to_cnf(expr)
    assert cnf == a
    assert reduce_cnf(cnf) == a

    expr_neg = ~a
    cnf_neg = to_cnf(expr_neg)
    assert cnf_neg == Not(a)
    assert reduce_cnf(cnf_neg) == Not(a)


def test_nested_contradiction(vars_):
    a, b, *_ = vars_
    expr = (a & ~a) & (b | ~b)
    cnf = to_cnf(expr)
    # The whole expression is unsatisfiable due to (a & ~a)
    assert reduce_cnf(cnf) == Const(False)


def test_nested_tautology(vars_):
    a, b, *_ = vars_
    expr = (a | ~a) & (b | ~b)
    cnf = to_cnf(expr)
    # Both ORs are tautologies, so the conjunction reduces to True
    assert reduce_cnf(cnf) == Const(True)


def test_or_with_true_and_false(vars_):
    a, *_ = vars_
    t = Const(True)
    f = Const(False)

    expr1 = a | t
    cnf1 = to_cnf(expr1)
    # OR with True is always True
    assert reduce_cnf(cnf1) == Const(True)

    expr2 = a | f
    cnf2 = to_cnf(expr2)
    # OR with False is just the variable itself
    assert reduce_cnf(cnf2) == a

    expr3 = a & t
    cnf3 = to_cnf(expr3)
    # AND with True is just the variable
    assert reduce_cnf(cnf3) == a

    expr4 = a & f
    cnf4 = to_cnf(expr4)
    # AND with False is always False
    assert reduce_cnf(cnf4) == Const(False)


def test_contradiction_inside_or(vars_):
    a, b, *_ = vars_
    expr = a | (~a & b)
    cnf = to_cnf(expr)
    # a ∨ (~a ∧ b) simplifies to a ∨ b
    assert reduce_cnf(cnf) == Or(a, b)