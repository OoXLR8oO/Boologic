from .expressions import Biconditional, Expr, Implies, Var, Not, And, Or


def to_cnf(expr: Expr) -> Expr:
    """Convert any Expr into conjunctive normal form (CNF)."""
    expr = _eliminate_implications(expr)
    expr = _push_negations(expr)
    while True:
        new = _distribute(expr)
        if new == expr:
            return flatten_cnf(expr)
        expr = new


def _eliminate_implications(expr: Expr) -> Expr:
    """Replace implications and biconditionals with equivalent expressions."""
    if isinstance(expr, Var):
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
    """Distribute OR over AND to get CNF."""
    if isinstance(expr, Or):
        if isinstance(expr.left, And):
            return And(_distribute(Or(expr.left.left, expr.right)),
                       _distribute(Or(expr.left.right, expr.right)))
        if isinstance(expr.right, And):
            return And(_distribute(Or(expr.left, expr.right.left)),
                       _distribute(Or(expr.left, expr.right.right)))
        return Or(_distribute(expr.left), _distribute(expr.right))
    if isinstance(expr, And):
        return And(_distribute(expr.left), _distribute(expr.right))
    return expr  # Var or Not


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
        def flatten_or(e: Expr):
            if isinstance(e, Or):
                return flatten_or(e.left) + flatten_or(e.right)
            return [str(e)]
        terms = flatten_or(expr)
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

    def flatten_or(e: Expr):
        if isinstance(e, Or):
            return flatten_or(e.left) + flatten_or(e.right)
        return [str(e)]

    clauses = []

    def collect(e: Expr):
        if isinstance(e, And):
            collect(e.left)
            collect(e.right)
        else:
            terms = flatten_or(e)
            clauses.append("(" + " ∨ ".join(terms) + ")")

    collect(expr)

    return " ∧ ".join(clauses)