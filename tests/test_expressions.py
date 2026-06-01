from boologic.expressions import (
    And,
    Biconditional,
    Const,
    Implies,
    Not,
    Or,
    Var,
)


def test_variable_evaluation():
    var = Var("A")

    assert var.evaluate({"A": True}) is True
    assert var.evaluate({"A": False}) is False


def test_operator_syntax_construction(vars):
    A, B, C, D, *_ = vars

    assert ~A == Not(A)
    assert A & B == And(A, B)
    assert A | B == Or(A, B)
    assert A >> B == Implies(A, B)
    assert A ^ B == Biconditional(A, B)

    assert (A & B) >> C == Implies(And(A, B), C)
    assert (A & B) ^ (C | D) == Biconditional(And(A, B), Or(C, D))


def test_string_representation_of_compound_expressions(vars):
    A, B, C, D, *_ = vars

    assert str(Implies(And(A, B), Or(C, D))) == "A ∧ B → C ∨ D"
    assert str(Biconditional(And(A, B), Or(C, D))) == "A ∧ B ↔ C ∨ D"
    assert str(Not(A)) == "¬A"


def test_boolean_constants_evaluation():
    assert Const(True).evaluate({}) is True
    assert Const(False).evaluate({}) is False


def test_constant_variable_set():
    assert Const(True).variables() == set()


def test_constant_string_representation():
    assert str(Const(True)) == "True"
    assert str(Const(False)) == "False"


def test_constant_behavior_inside_binary_expressions(vars):
    A, B, *_ = vars

    assert (A & Const(True)).evaluate({"A": True}) is True
    assert (A & Const(False)).evaluate({"A": True}) is False

    assert (A | Const(True)).evaluate({"A": False}) is True
    assert (A | Const(False)).evaluate({"A": False}) is False


def test_negation_of_constants():
    assert Not(Const(True)).evaluate({}) is False
    assert Not(Const(False)).evaluate({}) is True


def test_implication_with_constants(vars):
    A, *_ = vars

    assert (A >> Const(True)).evaluate({"A": True}) is True
    assert (A >> Const(False)).evaluate({"A": True}) is False
    assert (Const(True) >> A).evaluate({"A": True}) is True
    assert (Const(False) >> A).evaluate({"A": False}) is True


def test_biconditional_with_constant_true(vars):
    A, *_ = vars

    assert (A ^ Const(True)).evaluate({"A": True}) is True
    assert (A ^ Const(True)).evaluate({"A": False}) is False


def test_constant_folding_in_simplification(vars):
    A, *_ = vars

    assert Not(Const(True)).simplify() == Const(False)
    assert Not(Const(False)).simplify() == Const(True)

    assert And(Const(True), Const(True)).simplify() == Const(True)
    assert And(Const(True), Const(False)).simplify() == Const(False)

    assert Or(Const(True), A).simplify() == Const(True)
    assert Or(Const(False), A).simplify() == A


def test_idempotent_binary_simplification(vars):
    A, *_ = vars

    assert And(A, A).simplify() == A
    assert Or(A, A).simplify() == A


def test_double_negation_simplification(vars):
    A, *_ = vars

    assert Not(Not(A)).simplify() == A


def test_string_formatting_with_operator_precedence(vars):
    A, B, *_ = vars

    assert "¬" in str(Not(And(A, B)))
    assert "¬" in str(And(Not(A), B))


def test_or_simplification_with_constants_all_cases(vars):
    A, *_ = vars

    assert Or(Const(True), A).simplify() == Const(True)
    assert Or(Const(False), A).simplify() == A
    assert Or(A, Const(True)).simplify() == Const(True)
    assert Or(A, Const(False)).simplify() == A
