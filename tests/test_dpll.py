from boologic.expressions import Not, And, Or
from boologic.solvers.dpll import (
    solve,
    is_satisfiable,
    is_contradiction,
    is_tautology,
    model,
    entails,
)


def test_single_variable_sat(four_vars):
    A, *_ = four_vars

    assert solve(A) == {"A": True}
    assert is_satisfiable(A)


def test_direct_contradiction(four_vars):
    A, *_ = four_vars
    expr = And(A, Not(A))

    assert solve(expr) is False
    assert is_contradiction(expr)


def test_tautology_clause(four_vars):
    A, *_ = four_vars
    expr = Or(A, Not(A))

    assert is_tautology(expr)
    assert is_satisfiable(expr)


def test_simple_disjunction(four_vars):
    A, B, *_ = four_vars

    m = model(Or(A, B))
    assert m is not None
    assert m["A"] or m["B"]


def test_unit_propagation(four_vars):
    A, B, *_ = four_vars

    expr = And(A, Or(Not(A), B))  # A → B
    assert model(expr) == {"A": True, "B": True}


def test_xor_constraint(four_vars):
    A, B, *_ = four_vars

    expr = And(Or(A, B), Or(Not(A), Not(B)))
    m = model(expr)

    assert m is not None
    assert m["A"] != m["B"]


def test_implication_chain(four_vars):
    A, B, C, *_ = four_vars

    expr = And(
        A,
        And(
            Or(Not(A), B),
            Or(Not(B), C),
        ),
    )

    m = model(expr)

    assert m["A"]
    assert m["B"]
    assert m["C"]


def test_pure_literal_elimination(four_vars):
    A, B, C, *_ = four_vars

    expr = And(
        Or(A, B),
        Or(A, C),
    )

    m = model(expr)
    assert m["A"] is True


def test_complex_satisfiable(vars_):
    a, b, c, d, *_ = vars_

    expr = And(
        Or(a, Or(b, c)),
        And(
            Or(Not(a), b),
            And(
                Or(Not(b), c),
                Or(Not(c), d),
            ),
        ),
    )

    m = model(expr)
    assert m is not None


def test_complex_unsatisfiable(vars_):
    a, b, c, d, *_ = vars_

    expr = And(
        Or(a, b),
        And(
            Or(Not(a), c),
            And(
                Or(Not(b), c),
                Not(c),
            ),
        ),
    )

    assert solve(expr) is False
    assert not is_satisfiable(expr)
    assert is_contradiction(expr)


def test_3sat_unsat(four_vars):
    A, B, *_ = four_vars

    expr = And(
        Or(A, B),
        And(
            Or(Not(A), B),
            And(
                Or(A, Not(B)),
                Or(Not(A), Not(B)),
            ),
        ),
    )

    assert solve(expr) is False


def test_entailment(four_vars):
    A, B, *_ = four_vars

    kb = And(A, Or(A, B))
    assert not entails(kb, B)

    kb2 = And(A, Or(Not(A), B))
    assert entails(kb2, B)