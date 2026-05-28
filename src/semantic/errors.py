# src/semantic/errors.py
from dataclasses import dataclass
from typing import Optional, List


class SemanticErrorCategory:
    UNDECLARED_IDENTIFIER = "undeclared_identifier"
    DUPLICATE_DECLARATION = "duplicate_declaration"
    TYPE_MISMATCH = "type_mismatch"
    ARGUMENT_COUNT_MISMATCH = "argument_count_mismatch"
    ARGUMENT_TYPE_MISMATCH = "argument_type_mismatch"
    INVALID_RETURN_TYPE = "invalid_return_type"
    INVALID_CONDITION_TYPE = "invalid_condition_type"
    USE_BEFORE_DECLARATION = "use_before_declaration"
    INVALID_ASSIGNMENT_TARGET = "invalid_assignment_target"
    INVALID_OPERAND_TYPE = "invalid_operand_type"
    FUNCTION_REDEFINITION = "function_redefinition"
    STRUCT_REDEFINITION = "struct_redefinition"
    FIELD_REDEFINITION = "field_redefinition"


@dataclass
class SemanticError:
    category: str
    message: str
    line: int
    column: int
    context: Optional[str] = None
    expected: Optional[str] = None
    found: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        lines = []
        lines.append(f"semantic error: {self.message}")
        lines.append(f"  --> line {self.line}, column {self.column}")

        if self.expected and self.found:
            lines.append(f"  = expected: {self.expected}")
            lines.append(f"  = found: {self.found}")

        if self.suggestion:
            lines.append(f"  = suggestion: {self.suggestion}")

        if self.context:
            lines.append(f"  = in {self.context}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "context": self.context,
            "expected": self.expected,
            "found": self.found,
            "suggestion": self.suggestion
        }