from abc import ABC, abstractmethod
from collections.abc import Mapping

from pydantic.dataclasses import dataclass
from pydantic import ConfigDict

from .enums import Precedence


class Expr(ABC):
    @abstractmethod
    def evaluate(self, assignment: Mapping[str, bool]) -> bool: ...

    @abstractmethod
    def variables(self) -> set[str]: 
        ...

    @property
    @abstractmethod
    def precedence(self) -> Precedence: 
        ...

    def simplify(self) -> Expr:
        return self

    def format(self, child: Expr) -> str:
        return f"({child})" if child.precedence < self.precedence else str(child)

    # operators
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


@dataclass(frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class UnaryExpr(Expr):
    operand: Expr


@dataclass(frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class BinaryExpr(Expr):
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Var(Expr):
    name: str

    def evaluate(self, assignment):
        return assignment[self.name]

    def variables(self):
        return {self.name}

    @property
    def precedence(self):
        return Precedence.VAR

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class Const(Expr):
    value: bool

    def evaluate(self, assignment):
        return self.value

    def variables(self):
        return set()

    @property
    def precedence(self):
        return Precedence.VAR

    def __str__(self):
        return str(self.value)


@dataclass(frozen=True)
class Not(UnaryExpr):

    def evaluate(self, assignment):
        return not self.operand.evaluate(assignment)

    def variables(self):
        return self.operand.variables()

    def simplify(self):
        inner = self.operand.simplify()
        return inner.operand if isinstance(inner, Not) else Not(inner)

    @property
    def precedence(self):
        return Precedence.NOT

    def __str__(self):
        return f"¬{self.format(self.operand)}"


@dataclass(frozen=True)
class And(BinaryExpr):

    def evaluate(self, assignment):
        return self.left.evaluate(assignment) and self.right.evaluate(assignment)

    def variables(self):
        return self.left.variables() | self.right.variables()

    def simplify(self):
        left, right = self.left.simplify(), self.right.simplify()
        return left if left == right else And(left, right)

    @property
    def precedence(self):
        return Precedence.AND

    def __str__(self):
        return f"{self.format(self.left)} ∧ {self.format(self.right)}"


@dataclass(frozen=True)
class Or(BinaryExpr):

    def evaluate(self, assignment):
        return self.left.evaluate(assignment) and self.right.evaluate(assignment)

    def variables(self):
        return self.left.variables() | self.right.variables()

    def simplify(self):
        left, right = self.left.simplify(), self.right.simplify()
        return left if left == right else Or(left, right)

    @property
    def precedence(self):
        return Precedence.AND

    def __str__(self):
        return f"{self.format(self.left)} ∨ {self.format(self.right)}"


@dataclass(frozen=True)
class Implies(BinaryExpr):

    def evaluate(self, assignment):
        return (not self.left.evaluate(assignment)) or self.right.evaluate(assignment)

    def variables(self):
        return self.left.variables() | self.right.variables()

    def simplify(self):
        return Or(Not(self.left), self.right).simplify()

    @property
    def precedence(self):
        return Precedence.IMPLIES

    def __str__(self):
        return f"{self.format(self.left)} → {self.format(self.right)}"


@dataclass(frozen=True)
class Biconditional(BinaryExpr):

    def evaluate(self, assignment):
        return self.left.evaluate(assignment) == self.right.evaluate(assignment)

    def variables(self):
        return self.left.variables() | self.right.variables()

    def simplify(self):
        return And(
            Implies(self.left, self.right),
            Implies(self.right, self.left),
        ).simplify()

    @property
    def precedence(self):
        return Precedence.BICONDITIONAL

    def __str__(self):
        return f"{self.format(self.left)} ↔ {self.format(self.right)}"

    def __repr__(self):
        return f"Biconditional({self.left!r}, {self.right!r})"