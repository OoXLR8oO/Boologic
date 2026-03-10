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
            return expr
        expr = new


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
        if isinstance(e, Const):
            return [str(True) if e.value else str(False)]
        return [str(e)]

    clauses = []

    def collect(e: Expr):
        if isinstance(e, And):
            collect(e.left)
            collect(e.right)
        else:
            terms = flatten_or(e)
            if len(terms) == 1:
                clauses.append(terms[0])
            else:
                clauses.append("(" + " ∨ ".join(terms) + ")")

    collect(expr)

    return " ∧ ".join(clauses)