# Boologic

A lightweight Python library for working with **boolean propositional logic** expressions.

Boologic allows you to construct logical expressions either:

- explicitly with classes
- implicitly using Python operators

Expressions are rendered using proper logical symbols:

```text
¬  ∧  ∨  →  ↔
```

---

## Features

- Clean symbolic boolean logic expressions
- Python operator overloading
- Explicit class-based API
- Unicode pretty-printing
- Mix-and-match syntax support
- Built-in logical constants

---

## Installation

```bash
pip install boologic
```

---

## Quick Start

### Create Variables

Use the `Var` class to create propositional variables:

```python
from boologic import Var

A = Var("A")
B = Var("B")
```

---

## Building Expressions

### Operator Syntax (Recommended)

```python
expr = (A & B) >> ~A
print(expr)
```

Output:

```text
(A ∧ B) → ¬A
```

### Explicit Class Syntax

```python
from boologic import And, Implies, Not

expr = Implies(And(A, B), Not(A))
print(expr)
```

Output:

```text
(A ∧ B) → ¬A
```

### Mixed Syntax

Both styles can be combined safely:

```python
from boologic import Implies

expr = Implies(A & B, ~A)
```

---

## Supported Operators

| Logic | Python Operator | Symbol |
| --- | --- | --- |
| NOT | `~A` | `¬A` |
| AND | `A & B` | `A ∧ B` |
| OR | `A \| B` | `A ∨ B` |
| IMPLIES | `A >> B` | `A → B` |
| BICONDITIONAL | `A ^ B` | `A ↔ B` |

---

## Constants

Boologic uses its own `Const` class instead of Python's built-in
`True` and `False`.

### Example

```python
from boologic import Const

expr = Const(True) | A
```

This is interpreted internally as:

```python
Or(Const(True), A)
```

---

## Important: Operator Precedence

Python's operator precedence rules **do not match standard logical precedence**.

Always use parentheses `()` to ensure expressions are evaluated correctly.

### Recommended

```python
expr = (A & B) >> C
```

### Avoid

```python
expr = A & B >> C
```

The second example may not behave as expected.

---

## Binary Operator Design

All binary operators are primarily designed around handling **two operands at a time**.

For clarity and correctness, always prefer explicit grouping:

```python
(A & B) & C
```

instead of:

```python
A & B & C
```

---

## Example Expressions

### Negation

```python
~A
```

Output:

```text
¬A
```

### Conjunction

```python
A & B
```

Output:

```text
A ∧ B
```

### Disjunction

```python
A | B
```

Output:

```text
A ∨ B
```

### Implication

```python
A >> B
```

Output:

```text
A → B
```

### Biconditional

```python
A ^ B
```

Output:

```text
A ↔ B
```

---

## Recommended Style

For best readability:

- use parentheses generously
- prefer operator syntax for concise expressions
- use explicit classes for complex/generated expressions

---

## Full Example

```python
from boologic import Const, Var

A = Var("A")
B = Var("B")
C = Var("C")

expr = ((A & B) >> C) | ~Const(False)

print(expr)
```

Output:

```text
((A ∧ B) → C) ∨ ¬False
```

---

## License

MIT License
