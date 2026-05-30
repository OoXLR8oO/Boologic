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


def test_operator_syntax_construction(four_vars):
    A, B, C, D = four_vars

    assert ~A == Not(A)
    assert A & B == And(A, B)
    assert A | B == Or(A, B)
    assert A >> B == Implies(A, B)
    assert A ^ B == Biconditional(A, B)

    assert (A & B) >> C == Implies(And(A, B), C)
    assert (A & B) ^ (C | D) == Biconditional(And(A, B), Or(C, D))


def test_string_representation_of_compound_expressions(four_vars):
    A, B, C, D = four_vars

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


def test_constant_behavior_inside_binary_expressions(four_vars):
    A, B, _, _ = four_vars

    assert (A & Const(True)).evaluate({"A": True}) is True
    assert (A & Const(False)).evaluate({"A": True}) is False

    assert (A | Const(True)).evaluate({"A": False}) is True
    assert (A | Const(False)).evaluate({"A": False}) is False


def test_negation_of_constants():
    assert Not(Const(True)).evaluate({}) is False
    assert Not(Const(False)).evaluate({}) is True


def test_implication_with_constants(four_vars):
    A, _, _, _ = four_vars

    assert (A >> Const(True)).evaluate({"A": True}) is True
    assert (A >> Const(False)).evaluate({"A": True}) is False
    assert (Const(True) >> A).evaluate({"A": True}) is True
    assert (Const(False) >> A).evaluate({"A": False}) is True


def test_biconditional_with_constant_true(four_vars):
    A, _, _, _ = four_vars

    assert (A ^ Const(True)).evaluate({"A": True}) is True
    assert (A ^ Const(True)).evaluate({"A": False}) is False


def test_constant_folding_in_simplification():
    assert Not(Const(True)).simplify() == Const(False)
    assert Not(Const(False)).simplify() == Const(True)

    assert And(Const(True), Const(True)).simplify() == Const(True)
    assert And(Const(True), Const(False)).simplify() == Const(False)

    assert Or(Const(True), Var("A")).simplify() == Const(True)
    assert Or(Const(False), Var("A")).simplify() == Var("A")


def test_idempotent_binary_simplification():
    a = Var("A")

    assert And(a, a).simplify() == a
    assert Or(a, a).simplify() == a


def test_double_negation_simplification():
    a = Var("A")
    assert Not(Not(a)).simplify() == a


def test_string_formatting_with_operator_precedence():
    a = Var("A")
    b = Var("B")

    assert "¬" in str(Not(And(a, b)))
    assert "¬" in str(And(Not(a), b))


def test_or_simplification_with_constants_all_cases():
    a = Var("A")

    assert Or(Const(True), a).simplify() == Const(True)
    assert Or(Const(False), a).simplify() == a
    assert Or(a, Const(True)).simplify() == Const(True)
    assert Or(a, Const(False)).simplify() == a
