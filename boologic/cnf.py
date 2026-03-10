from .expressions import Biconditional, Expr, Implies, Var, Not, And, Or, Const


def to_cnf(expr: Expr) -> Expr:
    """Convert any Expr into conjunctive normal form (CNF)."""
    if isinstance(expr, Const):
        return expr
    expr = _eliminate_implications(expr)
    expr = _push_negations(expr)
    while True:
        new = _distribute(expr)
        if new == expr:
            break
        expr = new
    return _simplify_cnf(expr)


def _eliminate_implications(expr: Expr) -> Expr:
    """Replace implications and biconditionals with equivalent expressions."""
    if isinstance(expr, (Var, Const)):
        return expr
    if isinstance(expr, Not):
        return Not(_eliminate_implications(expr.operand))
    if isinstance(expr, And):
        return And(_eliminate_implications(expr.left),
                   _eliminate_implications(expr.right))
    if isinstance(expr, Or):
        return Or(_eliminate_implications(expr.left),
                  _eliminate_implications(expr.right))
    # Implies: A → B = ¬A ∨ B
    if isinstance(expr, Implies):
        return Or(Not(_eliminate_implications(expr.left)),
                  _eliminate_implications(expr.right))
    # Biconditional: A ↔ B = (A → B) ∧ (B → A)
    if isinstance(expr, Biconditional):
        A = _eliminate_implications(expr.left)
        B = _eliminate_implications(expr.right)
        return And(Or(Not(A), B), Or(Not(B), A))
    return expr


def _push_negations(expr: Expr) -> Expr:
    """Push negations inward using De Morgan’s laws."""
    if isinstance(expr, Var):
        return expr
    if isinstance(expr, Not):
        inner = expr.operand
        if isinstance(inner, Const):
            return Const(not inner.value)
        if isinstance(inner, Var):
            return expr
        if isinstance(inner, Not):
            return _push_negations(inner.operand)  # ¬¬A -> A
        if isinstance(inner, And):
            # ¬(A ∧ B) -> ¬A ∨ ¬B
            return Or(_push_negations(Not(inner.left)),
                      _push_negations(Not(inner.right)))
        if isinstance(inner, Or):
            # ¬(A ∨ B) -> ¬A ∧ ¬B
            return And(_push_negations(Not(inner.left)),
                       _push_negations(Not(inner.right)))
        # fallback
        return Not(_push_negations(inner))
    if isinstance(expr, And):
        return And(_push_negations(expr.left), _push_negations(expr.right))
    if isinstance(expr, Or):
        return Or(_push_negations(expr.left), _push_negations(expr.right))
    return expr


def _distribute(expr: Expr) -> Expr:
    if isinstance(expr, Or):
        left = _distribute(expr.left)
        right = _distribute(expr.right)

        # constant rules
        if isinstance(left, Const):
            return Const(True) if left.value else right
        if isinstance(right, Const):
            return Const(True) if right.value else left
        if isinstance(left, And):
            return And(_distribute(Or(left.left, right)),
                       _distribute(Or(left.right, right)))
        if isinstance(right, And):
            return And(_distribute(Or(left, right.left)),
                       _distribute(Or(left, right.right)))
        return Or(left, right)

    if isinstance(expr, And):
        left = _distribute(expr.left)
        right = _distribute(expr.right)
        # constant rules
        if isinstance(left, Const):
            return right if left.value else Const(False)
        if isinstance(right, Const):
            return left if right.value else Const(False)
        return And(left, right)
    return expr


def _flatten_or(expr: Expr) -> list[Expr]:
    if isinstance(expr, Or):
        return _flatten_or(expr.left) + _flatten_or(expr.right)
    return [expr]


def _flatten_and(expr: Expr) -> list[Expr]:
    if isinstance(expr, And):
        return _flatten_and(expr.left) + _flatten_and(expr.right)
    return [expr]


def _simplify_cnf(expr: Expr) -> Expr:
    def simplify_clause(e: Expr) -> Expr:
        literals = _flatten_or(e)

        seen: set[Expr] = set()
        negated_seen: set[Expr] = set()
        result: list[Expr] = []

        for lit in literals:
            if isinstance(lit, Const):
                if lit.value:
                    return Const(True)
                continue

            base = lit
            is_neg = False
            if isinstance(lit, Not) and isinstance(lit.operand, Var):
                base = lit.operand
                is_neg = True

            if is_neg:
                if base in seen:
                    return Const(True)
                if lit not in result:
                    result.append(lit)
                negated_seen.add(base)
            else:
                if base in negated_seen:
                    return Const(True)
                if lit not in result:
                    result.append(lit)
                seen.add(base)

        if not result:
            return Const(False)
        if len(result) == 1:
            return result[0]

        # Rebuild OR chain from list
        clause = result[0]
        for lit in result[1:]:
            clause = Or(clause, lit)
        return clause

    def simplify(node: Expr) -> Expr:
        if isinstance(node, And):
            parts = [simplify(p) for p in _flatten_and(node)]

            new_parts: list[Expr] = []
            for p in parts:
                if isinstance(p, Const):
                    if not p.value:
                        return Const(False)
                    continue
                if p not in new_parts:
                    new_parts.append(p)

            if not new_parts:
                return Const(True)
            if len(new_parts) == 1:
                return new_parts[0]

            conj = new_parts[0]
            for p in new_parts[1:]:
                conj = And(conj, p)
            return conj

        if isinstance(node, Or):
            return simplify_clause(node)

        return node

    simplified = simplify(expr)

    if isinstance(simplified, (Const, Var, Not)):
        return simplified

    def negate_lit(lit: Expr) -> Expr:
        if isinstance(lit, Not):
            return lit.operand
        return Not(lit)

    clauses: list[set[Expr]] = []
    for part in _flatten_and(simplified):
        if isinstance(part, Const):
            if not part.value:
                return Const(False)
            continue
        lits = set(_flatten_or(part))
        if not lits:
            return Const(False)
        drop_clause = False
        lit_set = set()
        for lit in lits:
            neg = negate_lit(lit)
            if neg in lits:
                drop_clause = True
                break
            lit_set.add(lit)
        if drop_clause:
            continue
        clauses.append(lit_set)

    if not clauses:
        return Const(True)

    while True:
        unit_lit: Expr | None = None
        for c in clauses:
            if len(c) == 1:
                (only,) = tuple(c)
                if isinstance(only, Const):
                    if only.value:
                        continue
                    return Const(False)
                unit_lit = only
                break

        if unit_lit is None:
            break

        new_clauses: list[set[Expr]] = []
        neg_unit = negate_lit(unit_lit)
        for c in clauses:
            if unit_lit in c:
                continue
            if neg_unit in c:
                new_c = {l for l in c if l != neg_unit}
                if not new_c:
                    return Const(False)
                new_clauses.append(new_c)
            else:
                new_clauses.append(c)
        clauses = new_clauses
        if not clauses:
            return Const(True)

    def clause_to_expr(clause: set[Expr]) -> Expr:
        lits = sorted(clause, key=str)
        e = lits[0]
        for lit in lits[1:]:
            e = Or(e, lit)
        return e

    # deterministically order the list of clauses as well
    ordered_clauses = sorted(
        clauses,
        key=lambda c: tuple(sorted((str(l) for l in c)))
    )

    if len(ordered_clauses) == 1:
        return clause_to_expr(ordered_clauses[0])

    conj: Expr = clause_to_expr(ordered_clauses[0])
    for clause in ordered_clauses[1:]:
        conj = And(conj, clause_to_expr(clause))
    return conj


def pretty_print_cnf(expr: Expr, indent: int = 0) -> str:
    """
    Nicely prints a CNF expression with line breaks and indentation.
    Each top-level AND gets its own line; ORs are grouped inside parentheses.
    """
    pad = "  " * indent

    if isinstance(expr, And):
        left = pretty_print_cnf(expr.left, indent)
        right = pretty_print_cnf(expr.right, indent)
        return f"{left}\n{pad}∧ {right}"

    if isinstance(expr, Or):
        terms = [str(e) for e in _flatten_or(expr)]
        return "(" + " ∨ ".join(terms) + ")"

    if isinstance(expr, Not):
        return f"¬{expr.operand}"

    if isinstance(expr, Var):
        return expr.name

    return str(expr)


def flatten_cnf(expr: Expr) -> str:
    """
    Convert a CNF Expr tree into a single-line string where
    clauses are joined by ∧ and OR clauses are flattened.
    """

    clauses = []

    def collect(e: Expr):
        if isinstance(e, And):
            collect(e.left)
            collect(e.right)
        else:
            expr_terms = _flatten_or(e)
            terms = [
                (str(True) if isinstance(t, Const) and t.value
                 else str(False) if isinstance(t, Const) and not t.value
                 else str(t))
                for t in expr_terms
            ]
            if len(terms) == 1:
                clauses.append(terms[0])
            else:
                clauses.append("(" + " ∨ ".join(terms) + ")")

    collect(expr)

    return " ∧ ".join(clauses)