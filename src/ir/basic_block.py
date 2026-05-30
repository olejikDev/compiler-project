# src/ir/basic_block.py
"""Basic block, Function IR, Program IR.
Sprint 4 requirements: IR-3, IR-4
"""

from typing import List, Optional, Set, Dict, TYPE_CHECKING
from .ir_instructions import Instruction, Label, Opcode, Temp, Var

if TYPE_CHECKING:
    pass


class BasicBlock:
    """Basic block — linear sequence of instructions.

    Properties:
        - Entry only at the beginning
        - Exit only at the end (terminator instruction)
        - No internal jumps
    """

    def __init__(self, label: Label, parent_function: Optional['FunctionIR'] = None):
        self.label = label
        self.instructions: List[Instruction] = []
        self.parent_function = parent_function

        # For CFG
        self.predecessors: Set['BasicBlock'] = set()
        self.successors: Set['BasicBlock'] = set()

    def add_instruction(self, inst: Instruction) -> None:
        """Add instruction to the end of the block."""
        if self.is_terminated():
            raise RuntimeError(
                f"Cannot add instruction to already terminated block {self.label}"
            )
        self.instructions.append(inst)

    def is_terminated(self) -> bool:
        """Check if block has a terminator instruction."""
        if not self.instructions:
            return False
        return self.instructions[-1].is_terminator()

    def get_terminator(self) -> Optional[Instruction]:
        """Return terminator instruction if exists."""
        if self.is_terminated():
            return self.instructions[-1]
        return None

    def get_target_labels(self) -> List[Label]:
        """Return labels that this block jumps to."""
        term = self.get_terminator()
        if term:
            return term.get_target_labels()
        return []

    def __repr__(self) -> str:
        lines = [f"{self.label}:"]
        for inst in self.instructions:
            lines.append(f"    {inst}")
        return "\n".join(lines)

    def __hash__(self):
        return hash(self.label.name)

    def __eq__(self, other):
        return isinstance(other, BasicBlock) and self.label == other.label


class FunctionIR:
    """IR representation of a function.

    Contains:
        - Function name and return type
        - Parameters
        - Basic blocks
        - Variable to temp mapping
    """

    def __init__(self, name: str, return_type: str = "void"):
        self.name = name
        self.return_type = return_type
        self.parameters: List[tuple[str, str]] = []  # (name, type)
        self.blocks: List[BasicBlock] = []
        self.entry_block: Optional[BasicBlock] = None

        # Variable -> Temp mapping
        self.var_mapping: Dict[str, Temp] = {}

        # Counters
        self._temp_counter = 0
        self._label_counter = 0

    def new_temp(self, hint: str = "t") -> Temp:
        """Create a new temporary variable."""
        self._temp_counter += 1
        return Temp(f"{hint}{self._temp_counter}")

    def new_label(self, hint: str = "L") -> Label:
        """Create a new label."""
        self._label_counter += 1
        return Label(f"{hint}_{self._label_counter}")

    def add_block(self, block: BasicBlock) -> None:
        """Add a block to the function."""
        block.parent_function = self
        self.blocks.append(block)
        if len(self.blocks) == 1:
            self.entry_block = block

    def get_block_by_label(self, label: Label) -> Optional[BasicBlock]:
        """Find block by label."""
        for block in self.blocks:
            if block.label == label:
                return block
        return None

    def __repr__(self) -> str:
        params_str = ", ".join(f"{t} {n}" for n, t in self.parameters)
        lines = [
            f"function {self.name}: {self.return_type} ({params_str})",
            "{"
        ]
        for block in self.blocks:
            lines.append(f"  {block}")
        lines.append("}")
        return "\n".join(lines)


class ProgramIR:
    """Complete IR program (collection of functions)."""

    def __init__(self):
        self.functions: List[FunctionIR] = []
        self.entry_function: str = "main"

    def add_function(self, function: FunctionIR) -> None:
        """Add a function to the program."""
        self.functions.append(function)

    def get_function(self, name: str) -> Optional[FunctionIR]:
        """Find function by name."""
        for func in self.functions:
            if func.name == name:
                return func
        return None

    def __repr__(self) -> str:
        lines = ["# IR Program"]
        for func in self.functions:
            lines.append(str(func))
        return "\n\n".join(lines)