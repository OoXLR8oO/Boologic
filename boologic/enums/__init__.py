from enum import IntEnum

class Precedence(IntEnum):
    VAR = 6
    NOT = 5
    AND = 4
    OR = 3
    IMPLIES = 2
    BICONDITIONAL = 1