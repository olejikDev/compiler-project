# src/ir/control_flow.py
"""Control Flow Graph (CFG) construction and analysis.
Sprint 4 requirements: OUT-2, OUT-4
"""

from typing import List, Set, Dict, Optional
from .ir_instructions import Label
from .basic_block import BasicBlock, FunctionIR, ProgramIR


class ControlFlowGraph:
    """Control Flow Graph for a function.

    Nodes = Basic blocks
    Edges = Jumps between blocks
    """

    def __init__(self, function: FunctionIR):
        self.function = function
        self._build()

    def _build(self) -> None:
        """Build CFG from function's instructions."""
        # Build block map
        block_map: Dict[Label, BasicBlock] = {}
        for block in self.function.blocks:
            block_map[block.label] = block
            block.predecessors.clear()
            block.successors.clear()

        # Build edges
        for block in self.function.blocks:
            target_labels = block.get_target_labels()

            for target_label in target_labels:
                target_block = block_map.get(target_label)
                if target_block:
                    block.successors.add(target_block)
                    target_block.predecessors.add(block)

            # Fallthrough to next block if not terminated
            if not block.is_terminated():
                idx = self.function.blocks.index(block)
                if idx + 1 < len(self.function.blocks):
                    next_block = self.function.blocks[idx + 1]
                    block.successors.add(next_block)
                    next_block.predecessors.add(block)

    def get_blocks_in_order(self) -> List[BasicBlock]:
        """Return blocks in reverse post-order."""
        visited = set()
        order = []

        def dfs(block: BasicBlock):
            if block in visited:
                return
            visited.add(block)
            for succ in block.successors:
                dfs(succ)
            order.append(block)

        if self.function.entry_block:
            dfs(self.function.entry_block)

        return list(reversed(order))

    def has_cycles(self) -> bool:
        """Check if CFG has cycles."""
        visited = set()
        rec_stack = set()

        def has_cycle(block: BasicBlock) -> bool:
            if block in rec_stack:
                return True
            if block in visited:
                return False

            visited.add(block)
            rec_stack.add(block)

            for succ in block.successors:
                if has_cycle(succ):
                    return True

            rec_stack.remove(block)
            return False

        if self.function.entry_block:
            return has_cycle(self.function.entry_block)
        return False

    def to_dot(self) -> str:
        """Export CFG to Graphviz DOT format."""
        lines = ["digraph CFG {"]
        lines.append('    rankdir="TD";')
        lines.append('    node [shape=box, style="rounded"];')

        # Nodes
        for block in self.function.blocks:
            label_lines = [str(block.label)]
            for i, inst in enumerate(block.instructions[:4]):
                label_lines.append(f"  {inst}")
            if len(block.instructions) > 4:
                label_lines.append(f"  ... ({len(block.instructions)} total)")

            label_text = "\\n".join(label_lines)
            lines.append(f'    "{block.label}" [label="{label_text}"];')

        # Edges
        for block in self.function.blocks:
            for succ in block.successors:
                lines.append(f'    "{block.label}" -> "{succ.label}";')

        lines.append("}")
        return "\n".join(lines)

    def get_statistics(self) -> dict:
        """Collect CFG statistics (OUT-4)."""
        stats = {
            "num_blocks": len(self.function.blocks),
            "num_edges": sum(len(b.successors) for b in self.function.blocks),
            "has_cycles": self.has_cycles(),
            "blocks_without_predecessors": 0,
            "blocks_without_successors": 0,
        }

        for block in self.function.blocks:
            if len(block.predecessors) == 0 and block != self.function.entry_block:
                stats["blocks_without_predecessors"] += 1
            if len(block.successors) == 0:
                stats["blocks_without_successors"] += 1

        return stats


def build_cfg_for_program(program: ProgramIR) -> Dict[str, ControlFlowGraph]:
    """Build CFG for all functions in program."""
    cfgs = {}
    for func in program.functions:
        cfgs[func.name] = ControlFlowGraph(func)
    return cfgs