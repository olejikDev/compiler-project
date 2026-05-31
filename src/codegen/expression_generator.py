# src/codegen/expression_generator.py
"""Expression code generation with short-circuit evaluation.
Sprint 6 requirements: LOGIC-1, LOGIC-2, LOGIC-3, LOGIC-4, EXPR-1, EXPR-2
"""

from typing import List, Tuple, Optional
from .label_manager import LabelManager


class ExpressionGenerator:
    """Generates x86-64 assembly for expressions with short-circuit."""

    def __init__(self, label_manager: LabelManager = None):
        self.label_manager = label_manager or LabelManager()
        self.assembly: List[str] = []

    def generate_logical_and(self, left_gen: callable, right_gen: callable) -> Tuple[List[str], str]:
        """Generate short-circuit AND (&&)."""
        result = []
        false_label = self.label_manager.new_label("and_false")
        end_label = self.label_manager.new_label("and_end")

        # Generate left operand
        left_asm, left_reg = left_gen()
        result.extend(left_asm)

        # Test left operand
        result.append(f"    cmp {left_reg}, 0")
        result.append(f"    je {false_label}")

        # Generate right operand (only if left is true)
        right_asm, right_reg = right_gen()
        result.extend(right_asm)

        # Store result
        result_reg = self.label_manager.new_label("result")
        result.append(f"    mov eax, {right_reg}")
        result.append(f"    jmp {end_label}")

        # False path
        result.append(f"{false_label}:")
        result.append("    mov eax, 0")

        # End
        result.append(f"{end_label}:")

        return result, "eax"

    def generate_logical_or(self, left_gen: callable, right_gen: callable) -> Tuple[List[str], str]:
        """Generate short-circuit OR (||)."""
        result = []
        true_label = self.label_manager.new_label("or_true")
        end_label = self.label_manager.new_label("or_end")

        # Generate left operand
        left_asm, left_reg = left_gen()
        result.extend(left_asm)

        # Test left operand
        result.append(f"    cmp {left_reg}, 0")
        result.append(f"    jne {true_label}")

        # Generate right operand (only if left is false)
        right_asm, right_reg = right_gen()
        result.extend(right_asm)

        # Store result
        result.append(f"    mov eax, {right_reg}")
        result.append(f"    jmp {end_label}")

        # True path
        result.append(f"{true_label}:")
        result.append("    mov eax, 1")

        # End
        result.append(f"{end_label}:")

        return result, "eax"

    def generate_logical_not(self, operand_gen: callable) -> Tuple[List[str], str]:
        """Generate logical NOT (!)."""
        result = []

        # Generate operand
        op_asm, op_reg = operand_gen()
        result.extend(op_asm)

        # XOR with 1 to flip boolean
        result.append(f"    xor {op_reg}, 1")

        return result, op_reg

    def generate_comparison(self, op: str, left_gen: callable, right_gen: callable) -> Tuple[List[str], str]:
        """Generate comparison (==, !=, <, <=, >, >=)."""
        result = []

        # Generate operands
        left_asm, left_reg = left_gen()
        right_asm, right_reg = right_gen()
        result.extend(left_asm)
        result.extend(right_asm)

        # Compare
        result.append(f"    cmp {left_reg}, {right_reg}")

        # Set based on comparison
        cmp_map = {
            '==': 'sete',
            '!=': 'setne',
            '<': 'setl',
            '<=': 'setle',
            '>': 'setg',
            '>=': 'setge',
        }

        set_inst = cmp_map.get(op, 'sete')
        result.append(f"    {set_inst} al")
        result.append("    movzx eax, al")

        return result, "eax"

    def generate_arithmetic(self, op: str, left_gen: callable, right_gen: callable) -> Tuple[List[str], str]:
        """Generate arithmetic operation (+, -, *, /, %)."""
        result = []

        # Generate operands
        left_asm, left_reg = left_gen()
        right_asm, right_reg = right_gen()
        result.extend(left_asm)
        result.extend(right_asm)

        # Perform operation
        if op == '+':
            result.append(f"    add {left_reg}, {right_reg}")
        elif op == '-':
            result.append(f"    sub {left_reg}, {right_reg}")
        elif op == '*':
            result.append(f"    imul {left_reg}, {right_reg}")
        elif op == '/':
            result.append(f"    mov eax, {left_reg}")
            result.append("    cdq")
            result.append(f"    idiv {right_reg}")
            result.append(f"    mov {left_reg}, eax")
        elif op == '%':
            result.append(f"    mov eax, {left_reg}")
            result.append("    cdq")
            result.append(f"    idiv {right_reg}")
            result.append(f"    mov {left_reg}, edx")

        return result, left_reg