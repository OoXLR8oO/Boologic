from boologic.expressions import And, Not, Or
from boologic.solvers.dpll import (
    entails,
    is_contradiction,
    is_satisfiable,
    is_tautology,
    model,
    solve,
)


def test_single_variable_sat(vars):
    A, *_ = vars

    assert solve(A) == {"A": True}
    assert is_satisfiable(A)


def test_direct_contradiction(vars):
    A, *_ = vars
    expr = And(A, Not(A))

    assert solve(expr) is None
    assert is_contradiction(expr)


def test_tautology_clause(vars):
    A, *_ = vars
    expr = Or(A, Not(A))

    assert is_tautology(expr)
    assert is_satisfiable(expr)


def test_simple_disjunction(vars):
    A, B, *_ = vars

    m = model(Or(A, B))
    assert m is not None
    assert m["A"] or m["B"]


def test_unit_propagation(vars):
    A, B, *_ = vars

    expr = And(A, Or(Not(A), B))
    assert model(expr) == {"A": True, "B": True}


def test_xor_constraint(vars):
    A, B, *_ = vars

    expr = And(Or(A, B), Or(Not(A), Not(B)))
    m = model(expr)

    assert m is not None
    assert m["A"] != m["B"]


def test_implication_chain(vars):
    A, B, C, *_ = vars

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


def test_pure_literal_elimination(vars):
    A, B, C, *_ = vars

    expr = And(
        Or(A, B),
        Or(A, C),
    )

    m = model(expr)
    assert m["A"] is True


def test_complex_satisfiable(vars):
    A, B, C, D, *_ = vars

    expr = And(
        Or(A, Or(B, C)),
        And(
            Or(Not(A), B),
            And(
                Or(Not(B), C),
                Or(Not(C), D),
            ),
        ),
    )

    assert model(expr) is not None


def test_complex_unsatisfiable(vars):
    A, B, C, D, *_ = vars

    expr = And(
        Or(A, B),
        And(
            Or(Not(A), C),
            And(
                Or(Not(B), C),
                Not(C),
            ),
        ),
    )

    assert solve(expr) is None
    assert not is_satisfiable(expr)
    assert is_contradiction(expr)


def test_3sat_unsat(vars):
    A, B, *_ = vars

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

    assert solve(expr) is None
    assert is_contradiction(expr)


def test_entailment(vars):
    A, B, *_ = vars

    kb = And(A, Or(A, B))
    assert not entails(kb, B)

    kb2 = And(A, Or(Not(A), B))
    assert entails(kb2, B)
