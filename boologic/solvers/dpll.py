from boologic.expressions import And
from boologic.cnf import to_cnf, reduce_cnf, expr_to_clauses
from . import *


def dpll(clauses, assignment, all_vars=None):
    """
    DPLL algorithm with complete variable assignment.
    all_vars: optional set of all variable names to assign defaults for free vars
    """
    if all_vars is None:
        # Collect all variables from clauses
        all_vars = {literal_var(lit).name for clause in clauses for lit in clause}

    if not clauses:
        # All clauses satisfied, fill in free variables with True
        full_assignment = assignment.copy()
        for var in all_vars:
            if var not in full_assignment:
                full_assignment[var] = True
        return full_assignment

    if [] in clauses:
        return False

    # Unit propagation
    unit = find_unit_clause(clauses)
    if unit:
        var, value = literal_var(unit).name, literal_value(unit)
        new_assignment = assignment.copy()
        new_assignment[var] = value
        return dpll(simplify_clauses(clauses, var, value), new_assignment, all_vars)

    # Pure literal elimination
    pure = find_pure_literal(clauses)
    if pure:
        var, value = pure
        new_assignment = assignment.copy()
        new_assignment[var] = value
        return dpll(simplify_clauses(clauses, var, value), new_assignment, all_vars)

    # Branching
    var = choose_variable(clauses)
    for value in (True, False):
        new_assignment = assignment.copy()
        new_assignment[var] = value
        result = dpll(simplify_clauses(clauses, var, value), new_assignment, all_vars)
        if result:
            return result

    return False


def solve(expr):
    """Full SAT pipeline: CNF conversion, reduction, and DPLL."""
    cnf = to_cnf(expr)
    reduced = reduce_cnf(cnf)
    clauses = expr_to_clauses(reduced)
    return dpll(clauses, {}, {literal_var(lit).name for clause in clauses for lit in clause})


def model(expr):
    """Return a model if satisfiable, None otherwise."""
    result = solve(expr)
    return result if result else None


def is_satisfiable(expr):
    return solve(expr) is not False


def is_tautology(expr):
    return solve(Not(expr)) is False


def is_contradiction(expr):
    return solve(expr) is False


def entails(kb, query):
    return solve(And(kb, Not(query))) is False