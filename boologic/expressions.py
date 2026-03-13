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

    def format(self, child: Expr) -> str:
        if child.precedence < self.precedence:
            return f"({child})"
        return str(child)

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

    def __repr__(self) -> str:
        return self.name

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
    def precedence(self) -> Precedence:
        return Precedence.VAR


@dataclass(frozen=True)
class Const(Expr):
    value: bool

    def __repr__(self) -> str:
        return f"Const({self.value})"

    def __str__(self) -> str:
        return str(self.value)

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.value

    def variables(self) -> set[str]:
        return set()

    @property
    def precedence(self) -> Precedence:
        return Precedence.VAR
    

@dataclass(frozen=True)
class Not(Expr):
    operand: Expr

    def __repr__(self) -> str:
        return f"Not({self.operand!r})"

    def __str__(self) -> str:
        return f"¬{self.format(self.operand)}"

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
    def precedence(self) -> Precedence:
        return Precedence.NOT


@dataclass(frozen=True)
class And(Expr):
    left: Expr
    right: Expr

    def __repr__(self) -> str:
        return f"And({self.left}, {self.right})"

    def __str__(self) -> str:
        return f"{self.format(self.left)} ∧ {self.format(self.right)}"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) and self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        left = self.left.simplify()
        right = self.right.simplify()
        return left if left == right else And(left, right)

    @property
    def precedence(self) -> Precedence:
        return Precedence.AND


@dataclass(frozen=True)
class Or(Expr):
    left: Expr
    right: Expr

    def __repr__(self) -> str:
        return f"Or({self.left}, {self.right})"

    def __str__(self) -> str:
        return f"{self.format(self.left)} ∨ {self.format(self.right)}"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) or self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        left = self.left.simplify()
        right = self.right.simplify()
        return left if left == right else Or(left, right)

    @property
    def precedence(self) -> Precedence:
        return Precedence.OR


@dataclass(frozen=True)
class Implies(Expr):
    left: Expr
    right: Expr

    def __repr__(self) -> str:
        return f"Implies({self.left}, {self.right})"

    def __str__(self) -> str:
        return f"{self.format(self.left)} → {self.format(self.right)}"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return (not self.left.evaluate(assignment)) or self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        return Or(Not(self.left), self.right).simplify()

    @property
    def precedence(self) -> Precedence:
        return Precedence.IMPLIES


@dataclass(frozen=True)
class Biconditional(Expr):
    left: Expr
    right: Expr

    def __repr__(self) -> str:
        return f"Biconditional({self.left}, {self.right})"

    def __str__(self) -> str:
        return f"{self.format(self.left)} ↔ {self.format(self.right)}"

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return self.left.evaluate(assignment) == self.right.evaluate(assignment)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def simplify(self) -> Expr:
        return And(Implies(self.left, self.right), Implies(self.right, self.left)).simplify()

    @property
    def precedence(self) -> Precedence:
        return Precedence.BICONDITIONAL