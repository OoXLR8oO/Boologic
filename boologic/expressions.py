from __future__ import annotations  # safe in py3.14, helps mypy a lot

from abc import ABC, abstractmethod
from collections.abc import Mapping

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from .enums import Precedence


class Expr(ABC):
    @abstractmethod
    def evaluate(self, assignment: Mapping[str, bool]) -> bool: ...

    @abstractmethod
    def variables(self) -> set[str]: ...

    @property
    @abstractmethod
    def precedence(self) -> Precedence: ...

    def simplify(self) -> Expr:
        return self

    def format(self, child: Expr) -> str:
        if child.precedence < self.precedence:
            return f"({child})"
        return str(child)

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
class UnaryExpr(Expr, ABC):
    operand: Expr


@dataclass(frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class BinaryExpr(Expr, ABC):
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Var(Expr):
    name: str

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return assignment[self.name]

    def variables(self) -> set[str]:
        return {self.name}

    @property
    def precedence(self) -> Precedence:
        return Precedence.VAR

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Const(Expr):
    value: bool

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.value

    def variables(self) -> set[str]:
        return set()

    @property
    def precedence(self) -> Precedence:
        return Precedence.CONST

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Not(UnaryExpr):
    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return not self.operand.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.operand.variables()

    def simplify(self) -> Expr:
        inner = self.operand.simplify()

        if isinstance(inner, Not):
            return inner.operand

        if isinstance(inner, Const):
            return Const(not inner.value)

        return Not(inner)

    @property
    def precedence(self) -> Precedence:
        return Precedence.NOT

    def __str__(self) -> str:
        return f"¬{self.format(self.operand)}"


@dataclass(frozen=True)
class And(BinaryExpr):
    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) and self.right.evaluate(
            assignment
        )

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        left = self.left.simplify()
        right = self.right.simplify()

        if isinstance(left, Const) and isinstance(right, Const):
            return Const(left.value and right.value)

        if isinstance(left, Const):
            if left.value is True:
                return right
            return Const(False)

        if isinstance(right, Const):
            if right.value is True:
                return left
            return Const(False)

        if left == right:
            return left

        return And(left, right)

    @property
    def precedence(self) -> Precedence:
        return Precedence.AND

    def __str__(self) -> str:
        return f"{self.format(self.left)} ∧ {self.format(self.right)}"


@dataclass(frozen=True)
class Or(BinaryExpr):
    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) or self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        left = self.left.simplify()
        right = self.right.simplify()

        if isinstance(left, Const):
            if left.value is True:
                return Const(True)
            return right

        if isinstance(right, Const):
            if right.value is True:
                return Const(True)
            return left

        if left == right:
            return left

        return Or(left, right)

    @property
    def precedence(self) -> Precedence:
        return Precedence.OR

    def __str__(self) -> str:
        return f"{self.format(self.left)} ∨ {self.format(self.right)}"


@dataclass(frozen=True)
class Implies(BinaryExpr):
    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return (not self.left.evaluate(assignment)) or self.right.evaluate(
            assignment
        )

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        return Or(Not(self.left), self.right).simplify()

    @property
    def precedence(self) -> Precedence:
        return Precedence.IMPLIES

    def __str__(self) -> str:
        return f"{self.format(self.left)} → {self.format(self.right)}"


@dataclass(frozen=True)
class Biconditional(BinaryExpr):
    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) == self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        return And(
            Implies(self.left, self.right),
            Implies(self.right, self.left),
        ).simplify()

    @property
    def precedence(self) -> Precedence:
        return Precedence.BICONDITIONAL

    def __str__(self) -> str:
        return f"{self.format(self.left)} ↔ {self.format(self.right)}"
