# Boologic

This is a basic library for implementing boolean propositional logic.

There are two main ways to use this library:

Explicitly via classes (e.g. Implies(A, B))
Implicitly via operators (e.g. A >> B)

Both approaches will represent expressions with proper symbols (¬, ∧, ∨, →, ↔)
when printed. It is possible to use a mix of both approaches without the
code breaking (e.g. Implies(A & B)).

These are the operators used:
NOT (~)
AND (&)
OR (|)
IMPLIES (>>)
BICONDITIONAL (^)

Initialise literals (variables) using the Var class. This library works primarily 
with the built-in Const(bool) class rather than standard True/False.

E.g. (Const(True) | A) is recognised as Or(Const(True), A) in syntax.

**NOTE: 
When using the above operators, Python's operator precedence does 
not match correct precedence of operators. Use brackets () to ensure
desired order of operations.

All binary operators are designed with binary handling (only 2 variables)
in mind. Brackets () are recommended to avoid unintended behaviour.**