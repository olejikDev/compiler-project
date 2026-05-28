# src/semantic/symbol_table.py
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from .types import Type, INT_TYPE, UNKNOWN_TYPE


class SymbolKind(Enum):
    VARIABLE = "variable"
    FUNCTION = "function"
    PARAMETER = "parameter"
    STRUCT = "struct"
    FIELD = "field"


@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    type: Type
    line: int
    column: int
    # Additional info
    initializer: Optional[Any] = None
    parameters: Optional[List['Symbol']] = None  # For functions
    fields: Optional[Dict[str, 'Symbol']] = None  # For structs
    stack_offset: Optional[int] = None
    is_initialized: bool = False


class Scope:
    def __init__(self, name: str = "global", parent: Optional['Scope'] = None):
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.children: List[Scope] = []
        self.depth = parent.depth + 1 if parent else 0

    def insert(self, name: str, symbol: Symbol) -> bool:
        """Insert symbol into current scope, return False if duplicate"""
        if name in self.symbols:
            return False
        self.symbols[name] = symbol
        return True

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Lookup symbol only in current scope"""
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Lookup symbol in current and parent scopes"""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def __str__(self) -> str:
        return self._format_scope()

    def _format_scope(self, indent: int = 0) -> str:
        lines = []
        prefix = "  " * indent
        lines.append(f"{prefix}Scope: {self.name} (depth={self.depth})")

        if self.symbols:
            lines.append(f"{prefix}  Symbols:")
            for name, symbol in self.symbols.items():
                init_status = "[init]" if symbol.is_initialized else "[uninit]"
                type_str = str(symbol.type)
                lines.append(f"{prefix}    {name}: {symbol.kind.value} -> {type_str} {init_status} (line {symbol.line})")

        for child in self.children:
            lines.append(child._format_scope(indent + 1))

        return "\n".join(lines)


class SymbolTable:
    def __init__(self):
        """Constructor creating global scope"""
        self.global_scope = Scope("global")
        self.current_scope = self.global_scope
        self.all_symbols: Dict[str, Symbol] = {}

    def enter_scope(self, name: str = "block") -> Scope:
        """Push new nested scope"""
        new_scope = Scope(name, self.current_scope)
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope
        return new_scope

    def exit_scope(self) -> Optional[Scope]:
        """Pop current scope"""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
            return self.current_scope
        return None

    def insert(self, name: str, symbol_info: Symbol) -> bool:
        """Add symbol to current scope"""
        if self.current_scope.insert(name, symbol_info):
            self.all_symbols[name] = symbol_info
            return True
        return False

    def lookup(self, name: str) -> Optional[Symbol]:
        """Search from current to outer scopes"""
        return self.current_scope.lookup(name)

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Search only current scope"""
        return self.current_scope.lookup_local(name)

    def lookup_global(self, name: str) -> Optional[Symbol]:
        """Search only global scope"""
        return self.global_scope.lookup_local(name)

    def get_current_scope(self) -> Scope:
        return self.current_scope

    def __str__(self) -> str:
        return str(self.global_scope)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output"""
        def scope_to_dict(scope: Scope) -> dict:
            return {
                "name": scope.name,
                "depth": scope.depth,
                "symbols": {
                    name: {
                        "name": sym.name,
                        "kind": sym.kind.value,
                        "type": str(sym.type),
                        "line": sym.line,
                        "column": sym.column,
                        "initialized": sym.is_initialized
                    }
                    for name, sym in scope.symbols.items()
                },
                "children": [scope_to_dict(child) for child in scope.children]
            }
        return scope_to_dict(self.global_scope)