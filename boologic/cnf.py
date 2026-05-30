from __future__ import annotations

from boologic.expressions import (
    And,
    Biconditional,
    Const,
    Expr,
    Implies,
    Not,
    Or,
    Var,
)


def to_cnf(expr: Expr) -> Expr:
    """Convert expression to CNF."""
    return simplify(distribute_or(push_negations(eliminate_implications(expr))))


def flatten(expr: Expr, node_type: type[Expr]) -> list[Expr]:
    """Flatten nested AND/OR expressions."""
    if isinstance(expr, node_type):
        left = getattr(expr, "left", None)
        right = getattr(expr, "right", None)
        if left is not None and right is not None:
            return flatten(left, node_type) + flatten(right, node_type)
    return [expr]


def eliminate_implications(expr: Expr) -> Expr:
    match expr:
        case Var() | Const():
            return expr

        case Not(op):
            return Not(eliminate_implications(op))

        case And(l, r):
            return And(eliminate_implications(l), eliminate_implications(r))

        case Or(l, r):
            return Or(eliminate_implications(l), eliminate_implications(r))

        case Implies(l, r):
            return Or(
                Not(eliminate_implications(l)),
                eliminate_implications(r),
            )

        case Biconditional(l, r):
            A = eliminate_implications(l)
            B = eliminate_implications(r)
            return And(Or(Not(A), B), Or(A, Not(B)))

        case _:
            return expr


def push_negations(expr: Expr) -> Expr:
    match expr:
        case Not(Const(v)):
            return Const(not v)

        case Not(Not(inner)):
            return push_negations(inner)

        case Not(And(l, r)):
            return Or(push_negations(Not(l)), push_negations(Not(r)))

        case Not(Or(l, r)):
            return And(push_negations(Not(l)), push_negations(Not(r)))

        case Not(op):
            return Not(push_negations(op))

        case And(l, r):
            return And(push_negations(l), push_negations(r))

        case Or(l, r):
            return Or(push_negations(l), push_negations(r))

        case Var() | Const():
            return expr

        case _:
            return expr


def distribute_or(expr: Expr) -> Expr:
    if isinstance(expr, And):
        return And(distribute_or(expr.left), distribute_or(expr.right))

    if isinstance(expr, Or):
        left = distribute_or(expr.left)
        right = distribute_or(expr.right)

        if isinstance(left, And):
            return And(
                distribute_or(Or(left.left, right)),
                distribute_or(Or(left.right, right)),
            )

        if isinstance(right, And):
            return And(
                distribute_or(Or(left, right.left)),
                distribute_or(Or(left, right.right)),
            )
        return Or(left, right)

    return expr


def simplify(expr: Expr) -> Expr:
    if isinstance(expr, And):
        parts = [simplify(p) for p in flatten(expr, And)]
        seen, neg = set(), set()
        cleaned = []

        for p in parts:
            if isinstance(p, Const):
                if not p.value:
                    return Const(False)
                continue

            if isinstance(p, Not):
                if p.operand in seen:
                    return Const(False)
                neg.add(p.operand)
            else:
                if p in neg:
                    return Const(False)
                seen.add(p)

            if p not in cleaned:
                cleaned.append(p)

        if not cleaned:
            return Const(True)

        result = cleaned[0]
        for p in cleaned[1:]:
            result = And(result, p)
        return result

    if isinstance(expr, Or):
        parts = [simplify(p) for p in flatten(expr, Or)]
        seen, neg = set(), set()
        cleaned = []

        for p in parts:
            if isinstance(p, Const):
                if p.value:
                    return Const(True)
                continue

            if isinstance(p, Not):
                if p.operand in seen:
                    return Const(True)
                neg.add(p.operand)
            else:
                if p in neg:
                    return Const(True)
                seen.add(p)

            if p not in cleaned:
                cleaned.append(p)

        if not cleaned:
            return Const(False)

        result = cleaned[0]
        for p in cleaned[1:]:
            result = Or(result, p)
        return result

    if isinstance(expr, Not):
        inner = simplify(expr.operand)
        if isinstance(inner, Const):
            return Const(not inner.value)
        if isinstance(inner, Not):
            return simplify(inner.operand)
        return Not(inner)

    return expr


def reduce_cnf(expr: Expr) -> Expr:
    clauses = [list(c) for c in expr_to_clauses(expr)]
    units: set[Expr] = set()

    while True:
        new_units = set()
        for clause in clauses:
            if len(clause) == 1:
                new_units.add(clause[0])

        if new_units.issubset(units):
            break

        for lit in new_units:
            neg = lit.operand if isinstance(lit, Not) else Not(lit)
            if neg in units:
                return Const(False)
            units.add(lit)

        new_clauses = []
        for clause in clauses:
            if any(lit in units for lit in clause):
                if len(clause) == 1:
                    new_clauses.append(clause)
                continue

            reduced = []
            for lit in clause:
                neg = lit.operand if isinstance(lit, Not) else Not(lit)
                if neg in units:
                    continue
                reduced.append(lit)

            if not reduced:
                return Const(False)

            new_clauses.append(reduced)

        clauses = new_clauses

    return clauses_to_expr(clauses)


def expr_to_clauses(expr: Expr) -> list[list[Expr]]:
    if isinstance(expr, Const):
        if expr.value:
            return []
        return [[]]

    clauses: list[list[Expr]] = []
    for part in flatten(expr, And):
        clauses.append(flatten(part, Or))
    return clauses


def clauses_to_expr(clauses: list[list[Expr]]) -> Expr:
    if not clauses:
        return Const(True)

    if any(len(clause) == 0 for clause in clauses):
        return Const(False)

    def build_clause(clause: list[Expr]) -> Expr:
        result = clause[0]
        for lit in clause[1:]:
            result = Or(result, lit)
        return result

    result = build_clause(clauses[0])
    for clause in clauses[1:]:
        result = And(result, build_clause(clause))
    return result
