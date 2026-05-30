# src/ir/ir_instructions.py
"""IR instruction set and operand types.
Sprint 4 requirements: IR-1, IR-2
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union


# ============================================================
# 1. Операнды (IR-2)
# ============================================================

class Operand:
    """Base class for all operands."""
    pass


@dataclass
class Temp(Operand):
    """Temporary variable (virtual register): t1, t2, t3..."""
    name: str

    def __repr__(self) -> str:
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Temp) and self.name == other.name


@dataclass
class Var(Operand):
    """Source variable name (before lowering to memory/temp)."""
    name: str

    def __repr__(self) -> str:
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name


@dataclass
class Const(Operand):
    """Constant value: integer, float, bool, string."""
    value: Union[int, float, bool, str]

    def __repr__(self) -> str:
        if isinstance(self.value, bool):
            return "true" if self.value else "false"
        elif isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return isinstance(other, Const) and self.value == other.value


@dataclass
class Label(Operand):
    """Label for basic block: L1, entry, then_1, else_1, end_1..."""
    name: str

    def __repr__(self) -> str:
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Label) and self.name == other.name


# ============================================================
# 2. Opcodes (IR-1)
# ============================================================

class Opcode(Enum):
    """IR instruction set (three-address code)."""

    # Arithmetic
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    NEG = "neg"

    # Logical
    AND = "and"
    OR = "or"
    NOT = "not"

    # Comparisons (result: 0 or 1)
    CMP_EQ = "cmp_eq"
    CMP_NE = "cmp_ne"
    CMP_LT = "cmp_lt"
    CMP_LE = "cmp_le"
    CMP_GT = "cmp_gt"
    CMP_GE = "cmp_ge"

    # Memory
    LOAD = "load"
    STORE = "store"
    ALLOCA = "alloca"

    # Control flow
    JUMP = "jump"
    JUMP_IF = "jump_if"
    JUMP_IF_NOT = "jump_if_not"
    LABEL = "label"

    # Functions
    CALL = "call"
    RETURN = "return"
    PARAM = "param"

    # Data movement
    MOVE = "move"
    PHI = "phi"

    # Pseudo (for debugging)
    COMMENT = "comment"

    def __repr__(self) -> str:
        return self.value


# ============================================================
# 3. Instruction
# ============================================================

@dataclass
class Instruction:
    """Single IR instruction."""
    opcode: Opcode
    dest: Optional[Temp] = None
    args: List[Operand] = field(default_factory=list)
    label: Optional[Label] = None
    comment: str = ""

    def __post_init__(self):
        if self.args is None:
            self.args = []

    def is_terminator(self) -> bool:
        """Check if this instruction terminates a basic block."""
        return self.opcode in {
            Opcode.JUMP,
            Opcode.JUMP_IF,
            Opcode.JUMP_IF_NOT,
            Opcode.RETURN,
        }

    def get_target_labels(self) -> List[Label]:
        """Return labels that this instruction jumps to."""
        if self.opcode == Opcode.JUMP and len(self.args) > 0:
            if isinstance(self.args[0], Label):
                return [self.args[0]]
        elif self.opcode in (Opcode.JUMP_IF, Opcode.JUMP_IF_NOT) and len(self.args) >= 2:
            if isinstance(self.args[1], Label):
                return [self.args[1]]
        return []

    def __repr__(self) -> str:
        if self.opcode == Opcode.LABEL and self.label:
            return f"{self.label}:"

        parts = [self.opcode.value]
        if self.dest:
            parts.append(str(self.dest))
            if self.args:
                parts.append("=")

        if self.args:
            parts.append(", ".join(str(arg) for arg in self.args))

        result = " ".join(parts)
        if self.comment:
            result += f"  # {self.comment}"
        return result