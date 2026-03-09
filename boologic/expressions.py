from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections.abc import Mapping
from .enums import Precedence


class Expr(ABC):
    @abstractmethod
    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        ...

    @abstractmethod
    def variables(self) -> set[str]:
        ...

    @property
    @abstractmethod
    def precedence(self) -> Precedence:
        ...

    def simplify(self) -> Expr:
        return self

    def fully_simplify(self) -> Expr:
        expr: Expr = self
        while True:
            new = expr.simplify()
            if new == expr:
                return expr
            expr = new

    def __invert__(self) -> Expr:
        return Not(self)

    def __and__(self, other: Expr) -> Expr:
        return And(self, other)

    def __or__(self, other: Expr) -> Expr:
        return Or(self, other)

    def __rshift__(self, other: Expr) -> Expr:
        return Implies(self, other)

    def __xor__(self, other: Expr) -> Expr:
        return Biconditional(self, other)


@dataclass(frozen=True)
class Var(Expr):
    name: str

    def __str__(self) -> str:
        return self.name

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        if self.name not in assignment:
            raise ValueError(f"Variable {self.name} not in assignment")
        return assignment[self.name]

    def variables(self) -> set[str]:
        return {self.name}

    def simplify(self) -> Expr:
        return self

    @property
    def precedence(self):
        return Precedence.VAR
    

@dataclass(frozen=True)
class Not(Expr):
    operand: Expr

    def __str__(self) -> str:
        return f"¬{self.operand}"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return not self.operand.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.operand.variables()

    def simplify(self) -> Expr:
        inner = self.operand.simplify()
        if isinstance(inner, Not):
            return inner.operand
        return Not(inner)

    @property
    def precedence(self):
        return Precedence.NOT


@dataclass(frozen=True)
class And(Expr):
    left: Expr
    right: Expr

    def __str__(self) -> str:
        return f"({self.left} ∧ {self.right})"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) and self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        l = self.left.simplify()
        r = self.right.simplify()
        return l if l == r else And(l, r)

    @property
    def precedence(self):
        return Precedence.AND


@dataclass(frozen=True)
class Or(Expr):
    left: Expr
    right: Expr

    def __str__(self) -> str:
        return f"({self.left} ∨ {self.right})"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) or self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        l = self.left.simplify()
        r = self.right.simplify()
        return l if l == r else Or(l, r)

    @property
    def precedence(self):
        return Precedence.OR


@dataclass(frozen=True)
class Implies(Expr):
    left: Expr
    right: Expr

    def __str__(self) -> str:
        return f"({self.left} → {self.right})"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return (not self.left.evaluate(assignment)) or self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        return Or(Not(self.left), self.right).simplify()

    @property
    def precedence(self):
        return Precedence.IMPLIES


@dataclass(frozen=True)
class Biconditional(Expr):
    left: Expr
    right: Expr

    def __str__(self) -> str:
        return f"({self.left} ↔ {self.right})"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) == self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        return And(Implies(self.left, self.right), Implies(self.right, self.left)).simplify()

    @property
    def precedence(self):
        return Precedence.BICONDITIONAL