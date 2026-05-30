from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class StackSlot:
    """Represents a slot on the stack."""
    name: str
    offset: int
    size: int
    alignment: int = 8


class StackFrame:
    """Manages stack frame layout for a function."""

    def __init__(self, name: str):
        self.name = name
        self.slots: Dict[str, StackSlot] = {}
        self.current_offset = -8
        self.param_offsets: Dict[int, int] = {}
        self.total_size = 0
        self.is_leaf = True

    def allocate_local(self, name: str, size: int = 8, alignment: int = 8) -> int:
        """Allocate a local variable on the stack."""
        self.current_offset -= size
        self.current_offset -= (self.current_offset % alignment)

        slot = StackSlot(name=name, offset=self.current_offset, size=size, alignment=alignment)
        self.slots[name] = slot
        return slot.offset

    def get_local_offset(self, name: str) -> Optional[int]:
        """Get offset of a local variable."""
        if name in self.slots:
            return self.slots[name].offset
        return None

    def calculate_frame_size(self) -> int:
        """Calculate total frame size (aligned to 16 bytes)."""
        if not self.slots:
            return 0

        min_offset = min(slot.offset for slot in self.slots.values())
        self.total_size = -min_offset
        self.total_size = (self.total_size + 15) & ~15
        return self.total_size

    def generate_prologue(self) -> List[str]:
        """Generate assembly for function prologue."""
        asm = []
        asm.append("    push rbp")
        asm.append("    mov rbp, rsp")

        frame_size = self.calculate_frame_size()
        if frame_size > 0:
            asm.append(f"    sub rsp, {frame_size}")

        return asm

    def generate_epilogue(self) -> List[str]:
        """Generate assembly for function epilogue."""
        asm = []
        frame_size = self.calculate_frame_size()
        if frame_size > 0:
            asm.append("    mov rsp, rbp")
        asm.append("    pop rbp")
        asm.append("    ret")
        return asm


class ABIConstants:
    """System V AMD64 ABI constants."""

    INT_ARG_REGS = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
    FP_ARG_REGS = ['xmm0', 'xmm1', 'xmm2', 'xmm3', 'xmm4', 'xmm5', 'xmm6', 'xmm7']
    CALLER_SAVED = ['rax', 'rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11']
    CALLEE_SAVED = ['rbx', 'rbp', 'rsp', 'r12', 'r13', 'r14', 'r15']
    RETURN_REG = 'rax'
    RETURN_REG_FP = 'xmm0'

    SYS_READ = 0
    SYS_WRITE = 1
    SYS_EXIT = 60
    STACK_ALIGNMENT = 16
    RED_ZONE_SIZE = 128


