# src/codegen/control_flow_generator.py
"""Control flow generation for x86-64.
Sprint 6 requirements: COND-1, COND-2, COND-3, LOOP-1, LOOP-2
"""

from typing import List, Optional
from .label_manager import LabelManager


class ControlFlowGenerator:
    """Generates x86-64 assembly for control flow structures."""

    def __init__(self, label_manager: LabelManager = None):
        self.label_manager = label_manager or LabelManager()
        self.assembly: List[str] = []

    def generate_if(self, condition_asm: List[str], then_asm: List[str],
                    else_asm: Optional[List[str]] = None) -> List[str]:
        """Generate if/if-else statement assembly."""
        result = []
        else_label = self.label_manager.new_label("else")
        end_label = self.label_manager.new_label("endif")

        # Condition code (should end with conditional jump)
        result.extend(condition_asm)

        # Jump to else if condition false
        result.append(f"    je {else_label}")

        # Then block
        result.extend(then_asm)
        result.append(f"    jmp {end_label}")

        # Else block (if exists)
        result.append(f"{else_label}:")
        if else_asm:
            result.extend(else_asm)

        # End label
        result.append(f"{end_label}:")

        return result

    def generate_while(self, condition_asm: List[str], body_asm: List[str]) -> List[str]:
        """Generate while loop assembly."""
        result = []
        cond_label = self.label_manager.new_label("while_cond")
        end_label = self.label_manager.new_label("while_end")

        # Push loop labels for break/continue
        self.label_manager.push_loop(cond_label, end_label)

        # Jump to condition
        result.append(f"    jmp {cond_label}")

        # Condition block
        result.append(f"{cond_label}:")
        result.extend(condition_asm)
        result.append(f"    je {end_label}")

        # Body block
        result.extend(body_asm)
        result.append(f"    jmp {cond_label}")

        # End label
        result.append(f"{end_label}:")

        # Pop loop labels
        self.label_manager.pop_loop()

        return result

    def generate_for(self, init_asm: List[str], condition_asm: List[str],
                     update_asm: List[str], body_asm: List[str]) -> List[str]:
        """Generate for loop assembly."""
        result = []
        cond_label = self.label_manager.new_label("for_cond")
        body_label = self.label_manager.new_label("for_body")
        step_label = self.label_manager.new_label("for_step")
        end_label = self.label_manager.new_label("for_end")

        # Push loop labels
        self.label_manager.push_loop(cond_label, end_label)
        self.label_manager.label_stack[-1]['continue'] = step_label

        # Initialization
        result.extend(init_asm)

        # Jump to condition
        result.append(f"    jmp {cond_label}")

        # Condition block
        result.append(f"{cond_label}:")
        result.extend(condition_asm)
        result.append(f"    je {end_label}")
        result.append(f"    jmp {body_label}")

        # Body block
        result.append(f"{body_label}:")
        result.extend(body_asm)

        # Step block
        result.append(f"{step_label}:")
        result.extend(update_asm)
        result.append(f"    jmp {cond_label}")

        # End label
        result.append(f"{end_label}:")

        # Pop loop labels
        self.label_manager.pop_loop()

        return result

    def generate_break(self) -> List[str]:
        """Generate break statement assembly."""
        break_label = self.label_manager.get_break_label()
        if break_label:
            return [f"    jmp {break_label}"]
        return ["    ; BREAK outside loop - error"]

    def generate_continue(self) -> List[str]:
        """Generate continue statement assembly."""
        continue_label = self.label_manager.get_continue_label()
        if continue_label:
            return [f"    jmp {continue_label}"]
        return ["    ; CONTINUE outside loop - error"]