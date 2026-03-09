from enum import IntEnum

class Precedence(IntEnum):
    BICONDITIONAL = 1
    IMPLIES = 2
    OR = 3
    AND = 4
    NOT = 5
    VAR = 6