from boologic.expressions import Var, And, Not, Or, Implies, Biconditional, Const


def test_var_evaluate():
    A = Var("A")
    assert A.evaluate({"A": True}) is True
    assert A.evaluate({"A": False}) is False


def test_ascii_to_code(four_vars):
    A, B, C, D = four_vars
    assert ~A == Not(A)
    assert A & B == And(A, B)
    assert A | B == Or(A, B)
    assert A >> B == Implies(A, B)
    assert A ^ B == Biconditional(A, B)
    assert (A & B) >> C == Implies(And(A, B), C)
    assert (A & B) ^ (C | D) == Biconditional(And(A, B), Or(C, D))


def test_code_to_unicode(four_vars):
    A, B, C, D = four_vars
    assert Implies(And(A, B), Or(C, D)).__str__() == "A ∧ B → C ∨ D"
    assert Biconditional(And(A, B), Or(C, D)).__str__() == "A ∧ B ↔ C ∨ D"
    assert Not(A).__str__() == "¬A"


def test_const_evaluate():
    assert Const(True).evaluate({}) is True
    assert Const(False).evaluate({}) is False


def test_const_variables():
    assert Const(True).variables() == set()


def test_const_string():
    assert str(Const(True)) == "True"
    assert str(Const(False)) == "False"


def test_const_in_expressions(four_vars):
    A, B, _, _ = four_vars
    assert (A & Const(True)).evaluate({"A": True}) is True
    assert (A & Const(False)).evaluate({"A": True}) is False
    assert (A | Const(True)).evaluate({"A": False}) is True
    assert (A | Const(False)).evaluate({"A": False}) is False


def test_not_const():
    assert Not(Const(True)).evaluate({}) is False
    assert Not(Const(False)).evaluate({}) is True


def test_const_implication(four_vars):
    A, _, _, _ = four_vars
    assert (A >> Const(True)).evaluate({"A": True}) is True
    assert (A >> Const(False)).evaluate({"A": True}) is False
    assert (Const(True) >> A).evaluate({"A": True}) is True
    assert (Const(False) >> A).evaluate({"A": False}) is True


def test_const_biconditional(four_vars):
    A, _, _, _ = four_vars
    assert (A ^ Const(True)).evaluate({"A": True}) is True
    assert (A ^ Const(True)).evaluate({"A": False}) is False