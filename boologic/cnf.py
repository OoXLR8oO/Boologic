from boologic.expressions import Expr, Implies, Not, And, Or, Biconditional, Var, Const


def to_cnf(expr: Expr) -> Expr:
    """Convert expression to CNF."""
    expr = eliminate_implications(expr)
    expr = push_negations(expr)
    expr = distribute_or(expr)
    return simplify(expr)


def flatten(expr: Expr, node_type) -> list[Expr]:
    """Flatten nested AND/OR expressions."""
    if isinstance(expr, node_type):
        return flatten(expr.left, node_type) + flatten(expr.right, node_type)
    return [expr]


def eliminate_implications(expr: Expr) -> Expr:
    match expr:
        case Var() | Const():
            return expr

        case Not(op):
            return Not(eliminate_implications(op))

        case And(l, r):
            return And(
                eliminate_implications(l),
                eliminate_implications(r)
            )

        case Or(l, r):
            return Or(
                eliminate_implications(l),
                eliminate_implications(r)
            )

        case Implies(l, r):
            # A → B  ==  ¬A ∨ B
            return Or(
                Not(eliminate_implications(l)),
                eliminate_implications(r)
            )

        case Biconditional(l, r):
            # A ↔ B
            A = eliminate_implications(l)
            B = eliminate_implications(r)
            return And(
                Or(Not(A), B),
                Or(A, Not(B))
            )
    return expr


def push_negations(expr: Expr) -> Expr:
    match expr:
        case Not(Const(v)):
            return Const(not v)

        case Not(Not(inner)):
            return push_negations(inner)

        case Not(And(l, r)):
            return Or(
                push_negations(Not(l)),
                push_negations(Not(r))
            )

        case Not(Or(l, r)):
            return And(
                push_negations(Not(l)),
                push_negations(Not(r))
            )

        case Not(op):
            return Not(push_negations(op))

        case And(l, r):
            return And(
                push_negations(l),
                push_negations(r)
            )

        case Or(l, r):
            return Or(
                push_negations(l),
                push_negations(r)
            )
    return expr


def distribute_or(expr: Expr) -> Expr:
    if isinstance(expr, And):
        return And(
            distribute_or(expr.left),
            distribute_or(expr.right)
        )

    if isinstance(expr, Or):
        left = distribute_or(expr.left)
        right = distribute_or(expr.right)

        if isinstance(left, And):
            return And(
                distribute_or(Or(left.left, right)),
                distribute_or(Or(left.right, right))
            )

        if isinstance(right, And):
            return And(
                distribute_or(Or(left, right.left)),
                distribute_or(Or(left, right.right))
            )
        return Or(left, right)
    return expr


def simplify(expr: Expr) -> Expr:
    if isinstance(expr, And):
        parts = [simplify(p) for p in flatten(expr, And)]
        if any(p == Const(False) for p in parts):
            return Const(False)
        parts = [p for p in parts if p != Const(True)]
        if not parts:
            return Const(True)
        result = parts[0]
        for p in parts[1:]:
            result = And(result, p)
        return result

    if isinstance(expr, Or):
        parts = flatten(expr, Or)
        seen = set()
        neg = set()
        cleaned = []
        for p in parts:
            if isinstance(p, Not) and p.operand in seen:
                return Const(True)
            if p in neg:
                return Const(True)
            if isinstance(p, Not):
                neg.add(p.operand)
            else:
                seen.add(p)
            if p not in cleaned:
                cleaned.append(p)
        if not cleaned:
            return Const(False)
        result = cleaned[0]
        for p in cleaned[1:]:
            result = Or(result, p)
        return result
    return expr


def reduce_cnf(expr: Expr) -> Expr:
    """Reduce a CNF expression using unit propagation and subsumption."""
    clauses = expr_to_clauses(expr)
    units: set[Expr] = set()
    changed = True
    while changed:
        changed = False
        # discover unit clauses
        for clause in clauses:
            if len(clause) == 1:
                lit = clause[0]
                neg = lit.operand if isinstance(lit, Not) else Not(lit)
                if neg in units:
                    return Const(False)
                if lit not in units:
                    units.add(lit)
                    changed = True
        new_clauses = []

        for clause in clauses:
            # clause satisfied by a unit literal
            if any(lit in units for lit in clause):
                if len(clause) == 1:
                    new_clauses.append(clause)
                continue
            reduced = []

            for lit in clause:
                # compute negation of literal
                neg = lit.operand if isinstance(lit, Not) else Not(lit)
                if neg in units:
                    continue
                reduced.append(lit)
            if not reduced:
                return Const(False)
            new_clauses.append(reduced)
        clauses = new_clauses

    # subsumption
    result: list[list[Expr]] = []
    for clause in clauses:
        sc = set[Expr](clause)
        if any(set[Expr](c).issubset(sc) for c in result):
            continue
        result = [
            c for c in result
            if not sc.issubset(set(c))
        ]
        result.append(clause)
    return clauses_to_expr(result)


def expr_to_clauses(expr: Expr) -> list[list[Expr]]:
    """Convert CNF expression tree to clause list."""
    clauses = []
    for part in flatten(expr, And):
        clauses.append(flatten(part, Or))
    return clauses


def clauses_to_expr(clauses: list[list[Expr]]) -> Expr:
    """Convert clause list back to Expr tree."""
    if not clauses:
        return Const(True)

    def build_clause(clause):
        result = clause[0]
        for lit in clause[1:]:
            result = Or(result, lit)
        return result

    result = build_clause(clauses[0])
    for clause in clauses[1:]:
        result = And(result, build_clause(clause))
    return result


def pretty_print_cnf(expr: Expr, indent: int = 0) -> str:
    """Print CNF with each clause on a new line."""
    pad = "  " * indent
    if isinstance(expr, And):
        left = pretty_print_cnf(expr.left, indent)
        right = pretty_print_cnf(expr.right, indent)
        return f"{left}\n{pad}∧ {right}"

    if isinstance(expr, Or):
        terms = [str(e) for e in flatten(expr, Or)]
        return "(" + " ∨ ".join(terms) + ")"

    if isinstance(expr, Not):
        return f"¬{expr.operand}"

    if isinstance(expr, Var):
        return expr.name
    return str(expr)


def flatten_cnf(expr: Expr) -> str:
    """Return CNF as a single-line string."""
    clauses = []
    for clause in flatten(expr, And):
        terms = flatten(clause, Or)
        if len(terms) == 1:
            clauses.append(str(terms[0]))
        else:
            clauses.append("(" + " ∨ ".join(str(t) for t in terms) + ")")
    return " ∧ ".join(clauses)