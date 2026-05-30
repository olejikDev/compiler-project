from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class LiveRange:
    """Live range of a temporary variable."""
    temp: str
    start: int
    end: int
    register: Optional[str] = None
    spilled: bool = False


class RegisterAllocator:
    """Simple linear scan register allocator."""

    def __init__(self):
        self.available_regs = ['rax', 'rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11']
        self.registers: Dict[str, str] = {}  # temp -> register
        self.spill_slots: Dict[str, int] = {}  # temp -> stack offset
        self.next_spill_offset = -8

    def allocate(self, live_ranges: List[LiveRange]) -> Dict[str, str]:
        """Allocate registers for temporaries."""
        # Sort by start time
        sorted_ranges = sorted(live_ranges, key=lambda x: x.start)

        active: List[LiveRange] = []

        for r in sorted_ranges:
            # Expire old ranges
            self._expire_old_ranges(active, r.start)

            if len(active) >= len(self.available_regs):
                # Spill
                self._spill(active, r)
            else:
                # Allocate register
                reg = self._get_free_register(active)
                if reg:
                    r.register = reg
                    self.registers[r.temp] = reg
                    active.append(r)

        return self.registers

    def _expire_old_ranges(self, active: List[LiveRange], current_pos: int):
        """Remove expired ranges from active list."""
        active[:] = [r for r in active if r.end > current_pos]

    def _get_free_register(self, active: List[LiveRange]) -> Optional[str]:
        """Get a free register."""
        used_regs = {r.register for r in active if r.register}
        for reg in self.available_regs:
            if reg not in used_regs:
                return reg
        return None

    def _spill(self, active: List[LiveRange], new_range: LiveRange):
        """Spill a register to stack."""
        # Spill the one with furthest end
        to_spill = max(active, key=lambda x: x.end)
        to_spill.spilled = True

        # Allocate spill slot
        if to_spill.temp not in self.spill_slots:
            self.spill_slots[to_spill.temp] = self.next_spill_offset
            self.next_spill_offset -= 8

        # Remove from active
        active.remove(to_spill)

        # Allocate register for new range
        reg = to_spill.register
        new_range.register = reg
        self.registers[new_range.temp] = reg
        active.append(new_range)

    def get_register(self, temp: str) -> Optional[str]:
        """Get register for a temporary."""
        return self.registers.get(temp)

    def get_spill_slot(self, temp: str) -> Optional[int]:
        """Get stack offset for a spilled temporary."""
        return self.spill_slots.get(temp)


