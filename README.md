This is a basic library for implementing boolean propositional logic.

There are two main ways to use this library:

Explicitly via classes (e.g. Implies(A, B))
Implicitly via operators (e.g. A >> B)

Both approaches represent expressions with proper symbols (¬, ∧, ∨, →, ↔)
when printed.

These are the operators used:
NOT (~)
AND (&)
OR (|)
IMPLIES (>>)
BICONDITIONAL (^)

NOTE: 
When using the above operators, Python's operator precedence does 
not match correct precedence of operators. Use brackets () to ensure
desired order of operations.

All binary operators are designed with binary handling (only 2 variables)
in mind. Brackets () are recommended to avoid unintended behaviour.