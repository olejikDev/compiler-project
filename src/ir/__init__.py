# src/ir/__init__.py
"""IR (Intermediate Representation) module for Sprint 4."""

from .ir_instructions import (
    Operand, Temp, Var, Const, Label,
    Opcode, Instruction
)
from .basic_block import BasicBlock, FunctionIR, ProgramIR
from .control_flow import ControlFlowGraph
from .ir_generator import IRGenerator

__all__ = [
    'Operand', 'Temp', 'Var', 'Const', 'Label',
    'Opcode', 'Instruction',
    'BasicBlock', 'FunctionIR', 'ProgramIR',
    'ControlFlowGraph',
    'IRGenerator',
]