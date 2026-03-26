from boologic.expressions import And, Expr, Not
from boologic.cnf import to_cnf, reduce_cnf, expr_to_clauses
from . import (
    literal_var, 
    literal_value, 
    find_unit_clause, 
    simplify_clauses, 
    find_pure_literal, 
    choose_variable
    )


def dpll(clauses: list[list[Expr]], assignment: dict[str, bool], all_vars: set[str] | None = None) -> dict[str, bool] | bool:
    """
    DPLL SAT solver.

    clauses: CNF clause list
    assignment: partial variable assignment
    all_vars: full set of variables in the problem
    """
    if all_vars is None:
        all_vars = {literal_var(lit).name for clause in clauses for lit in clause}

    # Success: all clauses satisfied
    if not clauses:
        return assignment | {v: True for v in all_vars if v not in assignment}

    # Failure: empty clause
    if [] in clauses:
        return False

    # Helper to extend assignment
    def assign(var: str, value: bool):
        new_assignment = assignment.copy()
        new_assignment[var] = value
        return new_assignment

    # Unit propagation
    unit = find_unit_clause(clauses)
    if unit:
        var, value = literal_var(unit).name, literal_value(unit)
        return dpll(
            simplify_clauses(clauses, var, value),
            assign(var, value),
            all_vars
        )

    # Pure literal elimination
    pure = find_pure_literal(clauses)
    if pure:
        var, value = pure
        return dpll(
            simplify_clauses(clauses, var, value),
            assign(var, value),
            all_vars
        )

    # Branching
    var = choose_variable(clauses)
    for value in (True, False):
        result = dpll(
            simplify_clauses(clauses, var, value),
            assign(var, value),
            all_vars
        )
        if result:
            return result
    return False


def solve(expr: Expr) -> dict[str, bool] | bool:
    cnf = to_cnf(expr)
    clauses = expr_to_clauses(reduce_cnf(cnf))
    all_vars = {literal_var(lit).name for clause in clauses for lit in clause}
    return dpll(clauses, {}, all_vars)


def model(expr: Expr) -> dict[str, bool] | None:
    """Return a model if satisfiable, None otherwise."""
    result = solve(expr)
    return result if result else None


def is_satisfiable(expr: Expr) -> bool:
    return solve(expr) is not False


def is_tautology(expr: Expr) -> bool:
    return solve(Not(expr)) is False


def is_contradiction(expr: Expr) -> bool:
    return solve(expr) is False


def entails(kb: Expr, query: Expr) -> bool:
    return solve(And(kb, Not(query))) is False