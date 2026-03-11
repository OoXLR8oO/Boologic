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
    return expr


def reduce_cnf(expr: Expr) -> Expr:
    """
    Reduce a CNF expression by simplifying clauses, applying unit propagation,
    and removing subsumed clauses.

    This assumes the input is already in CNF; for arbitrary expressions do:
    `reduce_cnf(to_cnf(expr))`.
    """
    return _reduce_cnf(expr)


def _reduce_cnf(expr: Expr) -> Expr:
    simplified = _simplify_cnf(expr)

    if isinstance(simplified, (Const, Var, Not)):
        return simplified

    def negate_lit(lit: Expr) -> Expr:
        if isinstance(lit, Not):
            return lit.operand
        return Not(lit)

    def clause_to_expr(clause: frozenset[Expr]) -> Expr:
        lits = sorted(
            clause,
            key=lambda l: (lit_pos.get(l, 10**9), str(l))
        )
        out: Expr = lits[0]
        for lit in lits[1:]:
            out = Or(out, lit)
        return out

    lit_pos: dict[Expr, int] = {}
    clause_pos: dict[frozenset[Expr], int] = {}
    _pos = 0

    def note_lit(l: Expr) -> None:
        nonlocal _pos
        if l not in lit_pos:
            lit_pos[l] = _pos
            _pos += 1

    def note_clause(c: frozenset[Expr], first_pos: int) -> None:
        if c not in clause_pos:
            clause_pos[c] = first_pos

    def clause_key(clause: frozenset[Expr]) -> tuple[int, tuple[int, ...], tuple[str, ...]]:
        cpos = clause_pos.get(clause, 10**9)
        lpos = tuple(sorted(lit_pos.get(l, 10**9) for l in clause))
        s = tuple(str(l) for l in clause)
        return (cpos, lpos, s)

    clauses: set[frozenset[Expr]] = set()
    for part in _flatten_and(simplified):
        if isinstance(part, Const):
            if not part.value:
                return Const(False)
            continue

        if isinstance(part, Or):
            part = _simplify_cnf(part)

        if isinstance(part, Const):
            if part.value:
                continue
            return Const(False)

        lits_in_order = _flatten_or(part)
        litset = frozenset(lits_in_order)
        if not litset:
            return Const(False)

        if any(negate_lit(l) in litset for l in litset):
            continue

        first_clause_pos = 10**9
        for l in lits_in_order:
            note_lit(l)
            first_clause_pos = min(first_clause_pos, lit_pos[l])
        note_clause(litset, first_clause_pos)
        clauses.add(litset)

    if not clauses:
        return Const(True)

    clauses_list = sorted(clauses, key=clause_key)
    units: set[Expr] = set()
    while True:
        unit: Expr | None = None
        for c in clauses_list:
            if len(c) == 1:
                (only,) = tuple(c)
                if isinstance(only, Const):
                    if only.value:
                        continue
                    return Const(False)
                unit = only
                break

        if unit is None:
            break

        if unit in units:
            clauses_list = [c for c in clauses_list if not (len(c) == 1 and unit in c)]
            continue

        if negate_lit(unit) in units:
            return Const(False)

        units.add(unit)
        neg_unit = negate_lit(unit)

        new_clauses: set[frozenset[Expr]] = set()
        for c in clauses_list:
            if unit in c:
                continue
            if neg_unit in c:
                reduced = frozenset(l for l in c if l != neg_unit)
                if not reduced:
                    return Const(False)
                # new clause order: as early as any of its literals
                if reduced not in clause_pos:
                    clause_pos[reduced] = min(lit_pos.get(l, 10**9) for l in reduced)
                new_clauses.add(reduced)
            else:
                new_clauses.add(c)

        clauses_list = sorted(new_clauses, key=clause_key)

    for u in units:
        note_lit(u)
        uc = frozenset({u})
        note_clause(uc, lit_pos.get(u, 10**9))
        clauses_list.append(uc)
    clauses_list = sorted(set(clauses_list), key=clause_key)

    kept: list[frozenset[Expr]] = []
    for c in clauses_list:
        if any(k.issubset(c) for k in kept):
            continue
        kept = [k for k in kept if not c.issubset(k)]
        kept.append(c)
    kept = sorted(kept, key=clause_key)

    if not kept:
        return Const(True)
    if len(kept) == 1:
        return clause_to_expr(kept[0])

    conj: Expr = clause_to_expr(kept[0])
    for c in kept[1:]:
        conj = And(conj, clause_to_expr(c))
    return conj


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
    # Biconditional: A ↔ B = (¬A ∨ B) ∧ (A ∨ ¬B)
    if isinstance(expr, Biconditional):
        A = _eliminate_implications(expr.left)
        B = _eliminate_implications(expr.right)
        return And(Or(Not(A), B), Or(A, Not(B)))
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
            pos_vars: set[Var] = set()
            neg_vars: set[Var] = set()

            for p in parts:
                if isinstance(p, Const):
                    if not p.value:
                        return Const(False)
                    continue

                if isinstance(p, Var):
                    if p in neg_vars:
                        return Const(False)
                    pos_vars.add(p)
                elif isinstance(p, Not) and isinstance(p.operand, Var):
                    v = p.operand
                    if v in pos_vars:
                        return Const(False)
                    neg_vars.add(v)

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

    return simplify(expr)


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