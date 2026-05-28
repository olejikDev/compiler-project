# src/semantic/types.py
from enum import Enum
from typing import Dict, List, Optional, Any


class TypeKind(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    VOID = "void"
    STRUCT = "struct"
    FUNCTION = "function"
    UNKNOWN = "unknown"


class Type:
    def __init__(self, kind: TypeKind, name: Optional[str] = None):
        self.kind = kind
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        if self.kind != other.kind:
            return False
        if self.kind == TypeKind.STRUCT:
            return self.name == other.name
        return True

    def __str__(self):
        if self.kind == TypeKind.STRUCT:
            return f"struct {self.name}"
        return self.kind.value

    def is_compatible_with(self, other: 'Type') -> bool:
        """Check if THIS type can be assigned to OTHER type"""
        # Same type
        if self == other:
            return True

        # Unknown type is compatible with anything (for error recovery)
        if self.kind == TypeKind.UNKNOWN or other.kind == TypeKind.UNKNOWN:
            return True

        # int can be assigned to float (widening)
        if self.kind == TypeKind.INT and other.kind == TypeKind.FLOAT:
            return True

        # Same type families
        if self.kind == TypeKind.INT and other.kind == TypeKind.INT:
            return True
        if self.kind == TypeKind.FLOAT and other.kind == TypeKind.FLOAT:
            return True
        if self.kind == TypeKind.BOOL and other.kind == TypeKind.BOOL:
            return True
        if self.kind == TypeKind.STRING and other.kind == TypeKind.STRING:
            return True

        return False

    def get_size(self) -> int:
        """Get size in bytes (for future code generation)"""
        sizes = {
            TypeKind.INT: 4,
            TypeKind.FLOAT: 4,
            TypeKind.BOOL: 1,
            TypeKind.STRING: 8,
            TypeKind.VOID: 0,
            TypeKind.UNKNOWN: 0
        }
        if self.kind == TypeKind.STRUCT:
            return 0
        return sizes.get(self.kind, 0)


INT_TYPE = Type(TypeKind.INT)
FLOAT_TYPE = Type(TypeKind.FLOAT)
BOOL_TYPE = Type(TypeKind.BOOL)
STRING_TYPE = Type(TypeKind.STRING)
VOID_TYPE = Type(TypeKind.VOID)
UNKNOWN_TYPE = Type(TypeKind.UNKNOWN)


def create_struct_type(name: str) -> Type:
    return Type(TypeKind.STRUCT, name)


def create_function_type(param_types: List[Type], return_type: Type) -> Dict:
    return {
        "kind": TypeKind.FUNCTION,
        "params": param_types,
        "return": return_type
    }