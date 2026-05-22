from boologic.cnf import expr_to_clauses, reduce_cnf, to_cnf
from boologic.expressions import And, Expr, Not

from . import (
    choose_variable,
    find_pure_literal,
    find_unit_clause,
    literal_value,
    literal_var,
    simplify_clauses,
)


def dpll(
    clauses: list[list[Expr]],
    assignment: dict[str, bool],
    all_vars: set[str] | None = None,
) -> dict[str, bool] | None:
    if all_vars is None:
        all_vars = {
            literal_var(lit).name for clause in clauses for lit in clause
        }

    if not clauses:
        return {
            **assignment,
            **{v: True for v in all_vars if v not in assignment},
        }

    if [] in clauses:
        return None

    def assign(var: str, value: bool) -> dict[str, bool]:
        return assignment | {var: value}

    # Unit propagation
    unit = find_unit_clause(clauses)
    if unit is not None:
        lit = literal_var(unit)
        var = lit.name
        value = literal_value(unit)

        return dpll(
            simplify_clauses(clauses, var, value),
            assign(var, value),
            all_vars,
        )

    # Pure literal elimination
    pure = find_pure_literal(clauses)
    if pure is not None:
        var, value = pure
        return dpll(
            simplify_clauses(clauses, var, value),
            assign(var, value),
            all_vars,
        )

    # Branching
    var_opt = choose_variable(clauses)
    if var_opt is None:
        return None

    chosen_var = var_opt

    for value in (True, False):
        result = dpll(
            simplify_clauses(clauses, chosen_var, value),
            assign(chosen_var, value),
            all_vars,
        )
        if result is not None:
            return result

    return None


def solve(expr: Expr) -> dict[str, bool] | None:
    cnf = to_cnf(expr)
    clauses = expr_to_clauses(reduce_cnf(cnf))

    all_vars = {literal_var(lit).name for clause in clauses for lit in clause}

    return dpll(clauses, {}, all_vars)


def model(expr: Expr) -> dict[str, bool] | None:
    return solve(expr)


def is_satisfiable(expr: Expr) -> bool:
    return solve(expr) is not None


def is_tautology(expr: Expr) -> bool:
    return solve(Not(expr)) is None


def is_contradiction(expr: Expr) -> bool:
    return solve(expr) is None


def entails(kb: Expr, query: Expr) -> bool:
    return solve(And(kb, Not(query))) is None
