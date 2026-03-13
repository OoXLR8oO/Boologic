from boologic.expressions import Not, Expr


def literal_var(lit) -> Expr:
    return lit.operand if isinstance(lit, Not) else lit


def literal_value(lit) -> bool:
    return False if isinstance(lit, Not) else True


def simplify_clauses(clauses, var_name, value) -> list[list[Expr]]:
    new_clauses = []

    for clause in clauses:
        new_clause = [
            lit for lit in clause
            if literal_var(lit).name != var_name or literal_value(lit) == value
        ]
        # Clause satisfied
        if any(literal_var(lit).name == var_name and literal_value(lit) == value for lit in clause):
            continue
        # Empty clause → conflict
        if not new_clause:
            return [[]]
        new_clauses.append(new_clause)

    return new_clauses


def find_unit_clause(clauses) -> Expr:
    return next((c[0] for c in clauses if len(c) == 1), None)


def find_pure_literal(clauses) -> Expr | None:
    polarity = {}
    for clause in clauses:
        for lit in clause:
            v = literal_var(lit)
            polarity.setdefault(v.name, set()).add(literal_value(lit))

    for var_name, signs in polarity.items():
        if len(signs) == 1:
            return var_name, next(iter(signs))
    return None


def choose_variable(clauses) -> Expr | None:
    for clause in clauses:
        for lit in clause:
            return literal_var(lit).name
    return None