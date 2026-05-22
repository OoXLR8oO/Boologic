from boologic.expressions import Expr, Not, Var

Literal = Var | Not


def literal_var(lit: Expr) -> Var:
    if isinstance(lit, Not):
        operand = lit.operand
        assert isinstance(operand, Var)
        return operand
    assert isinstance(lit, Var)
    return lit


def literal_value(lit: Expr) -> bool:
    return not isinstance(lit, Not)


def simplify_clauses(
    clauses: list[list[Expr]], var_name: str, value: bool
) -> list[list[Expr]]:
    new_clauses: list[list[Expr]] = []

    for clause in clauses:
        if any(
            literal_var(lit).name == var_name and literal_value(lit) == value
            for lit in clause
        ):
            continue

        new_clause = [
            lit
            for lit in clause
            if not (
                literal_var(lit).name == var_name
                and literal_value(lit) != value
            )
        ]

        if not new_clause:
            return [[]]

        new_clauses.append(new_clause)

    return new_clauses


def find_unit_clause(clauses: list[list[Expr]]) -> Expr | None:
    return next((c[0] for c in clauses if len(c) == 1), None)


def find_pure_literal(clauses: list[list[Expr]]) -> tuple[str, bool] | None:
    polarity: dict[str, set[bool]] = {}

    for clause in clauses:
        for lit in clause:
            v = literal_var(lit)
            polarity.setdefault(v.name, set()).add(literal_value(lit))

    for var_name, signs in polarity.items():
        if len(signs) == 1:
            return var_name, next(iter(signs))

    return None


def choose_variable(clauses: list[list[Expr]]) -> str | None:
    for clause in clauses:
        for lit in clause:
            return literal_var(lit).name
    return None
