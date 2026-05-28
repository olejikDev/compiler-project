# src/semantic/analyzer.py
from typing import List, Optional, Any, Dict
from src.parser.ast import (
    ProgramNode, FunctionDeclNode, StructDeclNode, VarDeclWrapper,
    VarDeclStmtNode, BlockStmtNode, ExprStmtNode, IfStmtNode,
    WhileStmtNode, ForStmtNode, ReturnStmtNode, EmptyStmtNode,
    ExpressionNode, LiteralExprNode, IdentifierExprNode, BinaryExprNode,
    UnaryExprNode, CallExprNode, AssignmentExprNode, StatementNode,
    StmtWrapper
)
from src.semantic.symbol_table import SymbolTable, Symbol, SymbolKind, Scope
from src.semantic.types import *
from src.semantic.errors import SemanticError, SemanticErrorCategory


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticError] = []
        self.current_function: Optional[Symbol] = None
        self.in_loop: bool = False
        self.struct_types: Dict[str, Type] = {}
        self.ast = None

    def analyze(self, ast: ProgramNode) -> None:
        """Perform semantic analysis on the AST"""
        self.ast = ast

        # First pass: collect all declarations
        for decl in ast.declarations:
            if isinstance(decl, FunctionDeclNode):
                self._declare_function(decl)
            elif isinstance(decl, StructDeclNode):
                self._declare_struct(decl)
            # StmtWrapper не содержит объявлений, пропускаем

        # Second pass: analyze bodies
        for decl in ast.declarations:
            if isinstance(decl, FunctionDeclNode):
                self.visit_function_decl(decl)
            elif isinstance(decl, StructDeclNode):
                self.visit_struct_decl(decl)
            elif isinstance(decl, VarDeclWrapper):
                self.visit_var_decl_wrapper(decl)
            elif isinstance(decl, StmtWrapper):
                self.visit_statement(decl.statement)

    def get_errors(self) -> List[SemanticError]:
        return self.errors

    def get_symbol_table(self) -> SymbolTable:
        return self.symbol_table

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def add_error(self, category: str, message: str, line: int, column: int,
                  context: Optional[str] = None, expected: Optional[str] = None,
                  found: Optional[str] = None, suggestion: Optional[str] = None):
        error = SemanticError(
            category=category,
            message=message,
            line=line,
            column=column,
            context=context,
            expected=expected,
            found=found,
            suggestion=suggestion
        )
        self.errors.append(error)

    # ============ Output Methods ============

    def dump_symbol_table(self, format: str = "text") -> str:
        """Dump symbol table in text or JSON format"""
        if format == "json":
            import json
            return json.dumps(self.symbol_table.to_dict(), indent=2)
        else:
            return str(self.symbol_table)

    def dump_decorated_ast(self) -> str:
        """Print AST with type annotations"""
        if not self.ast:
            return "No AST to dump"
        return self._ast_to_string(self.ast)

    def dump_error_report(self) -> str:
        """Dump error report summary"""
        if not self.errors:
            return "No errors found."

        lines = [f"Semantic Analysis Report: {len(self.errors)} error(s) found", "=" * 50]
        for i, error in enumerate(self.errors, 1):
            lines.append(f"{i}. {error}")
            lines.append("-" * 40)
        return "\n".join(lines)

    def _ast_to_string(self, node, indent: int = 0) -> str:
        """Convert decorated AST to readable string with types"""
        if node is None:
            return ""

        prefix = "  " * indent

        if isinstance(node, ProgramNode):
            result = ["Program [decorated]:"]
            for decl in node.declarations:
                result.append(self._ast_to_string(decl, indent + 1))
            return "\n".join(result)

        elif isinstance(node, FunctionDeclNode):
            type_str = f" -> {node.type_annotation}" if hasattr(node,
                                                                'type_annotation') and node.type_annotation else ""
            result = [f"{prefix}Function: {node.name}{type_str} (line {node.line})"]
            if node.parameters:
                result.append(f"{prefix}  Parameters:")
                for param in node.parameters:
                    param_type = param.type_annotation if hasattr(param, 'type_annotation') else param.param_type
                    result.append(f"{prefix}    - {param.name}: {param_type}")
            if node.body:
                result.append(self._ast_to_string(node.body, indent + 1))
            return "\n".join(result)

        elif isinstance(node, StructDeclNode):
            result = [f"{prefix}Struct: {node.name} (line {node.line})"]
            if node.fields:
                result.append(f"{prefix}  Fields:")
                for field in node.fields:
                    result.append(f"{prefix}    - {field.name}: {field.var_type}")
            return "\n".join(result)

        elif isinstance(node, BlockStmtNode):
            result = [f"{prefix}Block:"]
            for stmt in node.statements:
                result.append(self._ast_to_string(stmt, indent + 1))
            return "\n".join(result)

        elif isinstance(node, VarDeclStmtNode):
            type_str = f" [{node.type_annotation}]" if hasattr(node, 'type_annotation') and node.type_annotation else ""
            init = f" = {self._ast_to_string(node.initializer, 0)}" if node.initializer else ""
            return f"{prefix}VarDecl: {node.name}{type_str}{init}"

        elif isinstance(node, ReturnStmtNode):
            type_str = f" [{node.type_annotation}]" if hasattr(node, 'type_annotation') and node.type_annotation else ""
            value = self._ast_to_string(node.value, 0) if node.value else ""
            return f"{prefix}Return{type_str}: {value}"

        elif isinstance(node, IfStmtNode):
            cond = self._ast_to_string(node.condition, 0)
            cond_type = f" [{node.condition.type_annotation}]" if hasattr(node.condition, 'type_annotation') else ""
            result = [f"{prefix}If{cond_type}: {cond}"]
            result.append(f"{prefix}  Then:")
            result.append(self._ast_to_string(node.then_branch, indent + 2))
            if node.else_branch:
                result.append(f"{prefix}  Else:")
                result.append(self._ast_to_string(node.else_branch, indent + 2))
            return "\n".join(result)

        elif isinstance(node, WhileStmtNode):
            cond = self._ast_to_string(node.condition, 0)
            cond_type = f" [{node.condition.type_annotation}]" if hasattr(node.condition, 'type_annotation') else ""
            result = [f"{prefix}While{cond_type}: {cond}"]
            result.append(self._ast_to_string(node.body, indent + 1))
            return "\n".join(result)

        elif isinstance(node, ForStmtNode):
            result = [f"{prefix}For:"]
            if node.init:
                result.append(f"{prefix}  Init: {self._ast_to_string(node.init, 0)}")
            if node.condition:
                cond_type = f" [{node.condition.type_annotation}]" if hasattr(node.condition, 'type_annotation') else ""
                result.append(f"{prefix}  Condition: {self._ast_to_string(node.condition, 0)}{cond_type}")
            if node.update:
                result.append(f"{prefix}  Update: {self._ast_to_string(node.update, 0)}")
            result.append(self._ast_to_string(node.body, indent + 1))
            return "\n".join(result)

        elif isinstance(node, ExprStmtNode):
            return f"{prefix}{self._ast_to_string(node.expression, 0)}"

        elif isinstance(node, BinaryExprNode):
            left = self._ast_to_string(node.left, 0)
            right = self._ast_to_string(node.right, 0)
            type_str = f" [{node.type_annotation}]" if hasattr(node, 'type_annotation') else ""
            return f"({left} {node.operator} {right}){type_str}"

        elif isinstance(node, UnaryExprNode):
            operand = self._ast_to_string(node.operand, 0)
            type_str = f" [{node.type_annotation}]" if hasattr(node, 'type_annotation') else ""
            return f"({node.operator}{operand}){type_str}"

        elif isinstance(node, LiteralExprNode):
            type_str = f":{node.type_annotation}" if hasattr(node, 'type_annotation') else ""
            return f"{node.value}{type_str}"

        elif isinstance(node, IdentifierExprNode):
            type_str = f":{node.type_annotation}" if hasattr(node, 'type_annotation') else ""
            init_mark = "*" if (
                        hasattr(node, 'symbol_ref') and node.symbol_ref and not node.symbol_ref.is_initialized) else ""
            return f"{node.name}{init_mark}{type_str}"

        elif isinstance(node, CallExprNode):
            type_str = f" -> {node.type_annotation}" if hasattr(node, 'type_annotation') else ""
            args = ", ".join([self._ast_to_string(arg, 0) for arg in node.arguments])
            return f"{node.callee}({args}){type_str}"

        elif isinstance(node, AssignmentExprNode):
            target = self._ast_to_string(node.target, 0)
            value = self._ast_to_string(node.value, 0)
            type_str = f" [{node.type_annotation}]" if hasattr(node, 'type_annotation') else ""
            return f"({target} = {value}){type_str}"

        elif isinstance(node, VarDeclWrapper):
            return self._ast_to_string(node.var_decl, indent)

        else:
            return f"{prefix}{str(node)}"

    # ============ Declaration Methods ============

    def _declare_function(self, node: FunctionDeclNode):
        """Declare function in symbol table (first pass)"""
        existing = self.symbol_table.lookup_global(node.name)
        if existing and existing.kind == SymbolKind.FUNCTION:
            self.add_error(
                SemanticErrorCategory.FUNCTION_REDEFINITION,
                f"Function '{node.name}' already defined",
                node.line, node.column,
                suggestion=f"Rename the function or remove previous definition at line {existing.line}"
            )
            return

        param_symbols = []
        for param in node.parameters:
            param_type = self._type_from_string(param.param_type)
            param_symbol = Symbol(
                name=param.name,
                kind=SymbolKind.PARAMETER,
                type=param_type,
                line=param.line,
                column=param.column,
                is_initialized=True
            )
            param_symbols.append(param_symbol)

        return_type = self._type_from_string(node.return_type)
        func_symbol = Symbol(
            name=node.name,
            kind=SymbolKind.FUNCTION,
            type=return_type,
            line=node.line,
            column=node.column,
            parameters=param_symbols
        )

        self.symbol_table.insert(node.name, func_symbol)

    def _declare_struct(self, node: StructDeclNode):
        """Declare struct in symbol table (first pass)"""
        existing = self.symbol_table.lookup_global(node.name)
        if existing and existing.kind == SymbolKind.STRUCT:
            self.add_error(
                SemanticErrorCategory.STRUCT_REDEFINITION,
                f"Struct '{node.name}' already defined",
                node.line, node.column,
                suggestion=f"Rename the struct or remove previous definition"
            )
            return

        struct_type = create_struct_type(node.name)
        self.struct_types[node.name] = struct_type

        fields = {}
        field_set = set()

        for field in node.fields:
            if field.name in field_set:
                self.add_error(
                    SemanticErrorCategory.FIELD_REDEFINITION,
                    f"Field '{field.name}' already defined in struct '{node.name}'",
                    field.line, field.column
                )
                continue

            field_type = self._type_from_string(field.var_type)
            field_symbol = Symbol(
                name=field.name,
                kind=SymbolKind.FIELD,
                type=field_type,
                line=field.line,
                column=field.column,
                is_initialized=True
            )
            fields[field.name] = field_symbol
            field_set.add(field.name)

        struct_symbol = Symbol(
            name=node.name,
            kind=SymbolKind.STRUCT,
            type=struct_type,
            line=node.line,
            column=node.column,
            fields=fields
        )

        self.symbol_table.insert(node.name, struct_symbol)

    # ============ Visitor Methods ============

    def visit_function_decl(self, node: FunctionDeclNode):
        """Analyze function body"""
        func_symbol = self.symbol_table.lookup(node.name)
        if not func_symbol:
            return

        self.current_function = func_symbol
        self.symbol_table.enter_scope(f"function {node.name}")

        for param in node.parameters:
            param_type = self._type_from_string(param.param_type)
            param_symbol = Symbol(
                name=param.name,
                kind=SymbolKind.PARAMETER,
                type=param_type,
                line=param.line,
                column=param.column,
                is_initialized=True
            )
            self.symbol_table.insert(param.name, param_symbol)

        if node.body:
            self.visit_block(node.body)

        return_type = func_symbol.type
        if return_type != VOID_TYPE:
            has_return = self._check_has_return(node.body)
            if not has_return:
                self.add_error(
                    SemanticErrorCategory.INVALID_RETURN_TYPE,
                    f"Function '{node.name}' must return a value of type {return_type}",
                    node.line, node.column,
                    expected=str(return_type),
                    suggestion="Add a return statement"
                )

        self.symbol_table.exit_scope()
        self.current_function = None

    def _check_has_return(self, node: StatementNode) -> bool:
        """Check if a statement or block contains a return statement"""
        if isinstance(node, ReturnStmtNode):
            return True
        elif isinstance(node, BlockStmtNode):
            for stmt in node.statements:
                if self._check_has_return(stmt):
                    return True
        elif isinstance(node, IfStmtNode):
            then_return = self._check_has_return(node.then_branch)
            else_return = self._check_has_return(node.else_branch) if node.else_branch else False
            return then_return and else_return
        return False

    def visit_struct_decl(self, node: StructDeclNode):
        """Analyze struct declaration"""
        pass

    def visit_var_decl_wrapper(self, node: VarDeclWrapper):
        """Analyze variable declaration at global scope"""
        self.visit_var_decl_stmt(node.var_decl)

    def visit_var_decl_stmt(self, node: VarDeclStmtNode, in_function: bool = False):
        """Analyze variable declaration statement"""
        existing = self.symbol_table.get_current_scope().lookup_local(node.name)
        if existing:
            self.add_error(
                SemanticErrorCategory.DUPLICATE_DECLARATION,
                f"Variable '{node.name}' already declared in this scope",
                node.line, node.column,
                suggestion=f"Variable already defined at line {existing.line}"
            )
            return

        var_type = self._type_from_string(node.var_type)

        # Handle struct types - если тип не найден, проверяем не структура ли это
        if var_type == UNKNOWN_TYPE or (hasattr(var_type, 'kind') and var_type.kind == TypeKind.UNKNOWN):
            struct_symbol = self.symbol_table.lookup_global(node.var_type)
            if struct_symbol and struct_symbol.kind == SymbolKind.STRUCT:
                var_type = struct_symbol.type

        is_initialized = False
        if node.initializer:
            initializer_type = self.visit_expression(node.initializer)
            is_initialized = True

            if initializer_type and not initializer_type.is_compatible_with(var_type):
                self.add_error(
                    SemanticErrorCategory.TYPE_MISMATCH,
                    f"Type mismatch in variable initialization",
                    node.line, node.column,
                    expected=str(var_type),
                    found=str(initializer_type)
                )

        var_symbol = Symbol(
            name=node.name,
            kind=SymbolKind.VARIABLE,
            type=var_type,
            line=node.line,
            column=node.column,
            initializer=node.initializer,
            is_initialized=is_initialized
        )

        self.symbol_table.insert(node.name, var_symbol)
        node.type_annotation = var_type

        return var_type

    def visit_block(self, node: BlockStmtNode):
        """Analyze block statement"""
        self.symbol_table.enter_scope("block")

        for stmt in node.statements:
            self.visit_statement(stmt)

        self.symbol_table.exit_scope()

    def visit_statement(self, node: StatementNode):
        """Dispatch to appropriate statement visitor"""
        if isinstance(node, BlockStmtNode):
            self.visit_block(node)
        elif isinstance(node, VarDeclStmtNode):
            self.visit_var_decl_stmt(node, in_function=True)
        elif isinstance(node, ExprStmtNode):
            self.visit_expr_stmt(node)
        elif isinstance(node, IfStmtNode):
            self.visit_if_stmt(node)
        elif isinstance(node, WhileStmtNode):
            self.visit_while_stmt(node)
        elif isinstance(node, ForStmtNode):
            self.visit_for_stmt(node)
        elif isinstance(node, ReturnStmtNode):
            self.visit_return_stmt(node)
        elif isinstance(node, EmptyStmtNode):
            pass

    def visit_expr_stmt(self, node: ExprStmtNode):
        """Analyze expression statement"""
        if node.expression:
            self.visit_expression(node.expression)

    def visit_if_stmt(self, node: IfStmtNode):
        """Analyze if statement"""
        cond_type = self.visit_expression(node.condition)
        if cond_type != BOOL_TYPE and cond_type != UNKNOWN_TYPE:
            self.add_error(
                SemanticErrorCategory.INVALID_CONDITION_TYPE,
                "If condition must be boolean",
                node.condition.line, node.condition.column,
                expected="bool",
                found=str(cond_type)
            )

        self.visit_statement(node.then_branch)
        if node.else_branch:
            self.visit_statement(node.else_branch)

    def visit_while_stmt(self, node: WhileStmtNode):
        """Analyze while statement"""
        cond_type = self.visit_expression(node.condition)
        if cond_type != BOOL_TYPE and cond_type != UNKNOWN_TYPE:
            self.add_error(
                SemanticErrorCategory.INVALID_CONDITION_TYPE,
                "While condition must be boolean",
                node.condition.line, node.condition.column,
                expected="bool",
                found=str(cond_type)
            )

        old_in_loop = self.in_loop
        self.in_loop = True
        self.visit_statement(node.body)
        self.in_loop = old_in_loop

    def visit_for_stmt(self, node: ForStmtNode):
        """Analyze for statement"""
        self.symbol_table.enter_scope("for loop")

        if node.init:
            if isinstance(node.init, VarDeclStmtNode):
                self.visit_var_decl_stmt(node.init, in_function=True)
            elif isinstance(node.init, ExprStmtNode):
                self.visit_expr_stmt(node.init)

        if node.condition:
            cond_type = self.visit_expression(node.condition)
            if cond_type != BOOL_TYPE and cond_type != UNKNOWN_TYPE:
                self.add_error(
                    SemanticErrorCategory.INVALID_CONDITION_TYPE,
                    "For condition must be boolean",
                    node.condition.line, node.condition.column,
                    expected="bool",
                    found=str(cond_type)
                )

        if node.update:
            self.visit_expression(node.update)

        old_in_loop = self.in_loop
        self.in_loop = True
        self.visit_statement(node.body)
        self.in_loop = old_in_loop

        self.symbol_table.exit_scope()

    def visit_return_stmt(self, node: ReturnStmtNode):
        """Analyze return statement"""
        if not self.current_function:
            self.add_error(
                SemanticErrorCategory.INVALID_RETURN_TYPE,
                "Return statement outside of function",
                node.line, node.column
            )
            return

        expected_type = self.current_function.type

        if node.value:
            actual_type = self.visit_expression(node.value)

            if expected_type == VOID_TYPE:
                self.add_error(
                    SemanticErrorCategory.INVALID_RETURN_TYPE,
                    "Void function cannot return a value",
                    node.line, node.column,
                    expected="void",
                    found=str(actual_type)
                )
            elif not actual_type.is_compatible_with(expected_type):
                self.add_error(
                    SemanticErrorCategory.INVALID_RETURN_TYPE,
                    f"Return type mismatch: expected {expected_type}, got {actual_type}",
                    node.line, node.column,
                    expected=str(expected_type),
                    found=str(actual_type)
                )
        else:
            if expected_type != VOID_TYPE:
                self.add_error(
                    SemanticErrorCategory.INVALID_RETURN_TYPE,
                    f"Function must return a value of type {expected_type}",
                    node.line, node.column,
                    expected=str(expected_type),
                    found="void",
                    suggestion="Add a return value"
                )

    def visit_expression(self, node: ExpressionNode) -> Type:
        """Dispatch to appropriate expression visitor and return type"""
        if isinstance(node, LiteralExprNode):
            return self.visit_literal(node)
        elif isinstance(node, IdentifierExprNode):
            return self.visit_identifier(node)
        elif isinstance(node, BinaryExprNode):
            return self.visit_binary(node)
        elif isinstance(node, UnaryExprNode):
            return self.visit_unary(node)
        elif isinstance(node, CallExprNode):
            return self.visit_call(node)
        elif isinstance(node, AssignmentExprNode):
            return self.visit_assignment(node)

        return UNKNOWN_TYPE

    def visit_literal(self, node: LiteralExprNode) -> Type:
        """Analyze literal expression"""
        type_map = {
            "int": INT_TYPE,
            "float": FLOAT_TYPE,
            "bool": BOOL_TYPE,
            "string": STRING_TYPE
        }
        result_type = type_map.get(node.literal_type, UNKNOWN_TYPE)
        node.type_annotation = result_type
        return result_type

    def _check_initialization(self, var_name: str, node: IdentifierExprNode):
        """Check if variable is initialized before use"""
        symbol = self.symbol_table.lookup(var_name)

        if symbol and symbol.kind in [SymbolKind.VARIABLE, SymbolKind.PARAMETER]:
            # Skip initialization check for struct types
            if symbol.type and symbol.type.kind == TypeKind.STRUCT:
                return
            if not symbol.is_initialized:
                self.add_error(
                    SemanticErrorCategory.USE_BEFORE_DECLARATION,
                    f"Variable '{var_name}' may be uninitialized",
                    node.line, node.column,
                    suggestion=f"Initialize '{var_name}' before using it"
                )

    def _mark_initialized(self, var_name: str):
        """Mark a variable as initialized in current scope"""
        symbol = self.symbol_table.lookup(var_name)
        if symbol:
            symbol.is_initialized = True

    def visit_identifier(self, node: IdentifierExprNode) -> Type:
        """Analyze identifier expression"""
        symbol = self.symbol_table.lookup(node.name)

        if not symbol:
            self.add_error(
                SemanticErrorCategory.UNDECLARED_IDENTIFIER,
                f"Undeclared variable '{node.name}'",
                node.line, node.column,
                suggestion="Declare the variable before using it"
            )
            node.type_annotation = UNKNOWN_TYPE
            return UNKNOWN_TYPE

        if symbol.kind in [SymbolKind.VARIABLE, SymbolKind.PARAMETER]:
            self._check_initialization(node.name, node)

        node.symbol_ref = symbol
        node.type_annotation = symbol.type
        return symbol.type

    def visit_binary(self, node: BinaryExprNode) -> Type:
        """Analyze binary expression"""
        if node.operator == '.':
            # Field access
            left_type = self.visit_expression(node.left)

            if left_type.kind != TypeKind.STRUCT:
                self.add_error(
                    SemanticErrorCategory.TYPE_MISMATCH,
                    f"Cannot access field on non-struct type",
                    node.line, node.column,
                    expected="struct",
                    found=str(left_type)
                )
                node.type_annotation = UNKNOWN_TYPE
                return UNKNOWN_TYPE

            if not isinstance(node.right, IdentifierExprNode):
                self.add_error(
                    SemanticErrorCategory.INVALID_ASSIGNMENT_TARGET,
                    "Invalid field access",
                    node.line, node.column
                )
                node.type_annotation = UNKNOWN_TYPE
                return UNKNOWN_TYPE

            field_name = node.right.name
            struct_symbol = self.symbol_table.lookup(left_type.name)

            if not struct_symbol or not struct_symbol.fields:
                self.add_error(
                    SemanticErrorCategory.UNDECLARED_IDENTIFIER,
                    f"Struct '{left_type.name}' has no fields",
                    node.line, node.column
                )
                node.type_annotation = UNKNOWN_TYPE
                return UNKNOWN_TYPE

            field_symbol = struct_symbol.fields.get(field_name)
            if not field_symbol:
                available = ', '.join(struct_symbol.fields.keys())
                self.add_error(
                    SemanticErrorCategory.UNDECLARED_IDENTIFIER,
                    f"Struct '{left_type.name}' has no field '{field_name}'",
                    node.line, node.column,
                    suggestion=f"Available fields: {available}"
                )
                node.type_annotation = UNKNOWN_TYPE
                return UNKNOWN_TYPE

            node.type_annotation = field_symbol.type
            return field_symbol.type

        # Regular binary operations
        left_type = self.visit_expression(node.left)
        right_type = self.visit_expression(node.right)

        result_type = self._get_binary_result_type(node.operator, left_type, right_type)

        if result_type == UNKNOWN_TYPE:
            self.add_error(
                SemanticErrorCategory.TYPE_MISMATCH,
                f"Invalid operands for operator '{node.operator}'",
                node.line, node.column,
                expected="compatible types",
                found=f"{left_type} {node.operator} {right_type}"
            )

        node.type_annotation = result_type
        return result_type

    def _check_field_access(self, node: BinaryExprNode, left_type: Type) -> Type:
        """Check field access (struct.field)"""
        if left_type.kind != TypeKind.STRUCT:
            self.add_error(
                SemanticErrorCategory.TYPE_MISMATCH,
                "Cannot access field on non-struct type",
                node.line, node.column,
                expected="struct type",
                found=str(left_type)
            )
            return UNKNOWN_TYPE

        struct_symbol = self.symbol_table.lookup(left_type.name)
        if not struct_symbol or not struct_symbol.fields:
            self.add_error(
                SemanticErrorCategory.UNDECLARED_IDENTIFIER,
                f"Struct '{left_type.name}' has no fields",
                node.line, node.column
            )
            return UNKNOWN_TYPE

        if not isinstance(node.right, IdentifierExprNode):
            self.add_error(
                SemanticErrorCategory.INVALID_ASSIGNMENT_TARGET,
                "Invalid field access",
                node.line, node.column
            )
            return UNKNOWN_TYPE

        field_name = node.right.name
        field_symbol = struct_symbol.fields.get(field_name)

        if not field_symbol:
            available = ', '.join(struct_symbol.fields.keys())
            self.add_error(
                SemanticErrorCategory.UNDECLARED_IDENTIFIER,
                f"Struct '{left_type.name}' has no field '{field_name}'",
                node.line, node.column,
                suggestion=f"Available fields: {available}"
            )
            return UNKNOWN_TYPE

        return field_symbol.type

    def _get_binary_result_type(self, operator: str, left: Type, right: Type) -> Type:
        """Determine result type of binary operation"""
        if operator in ['+', '-', '*', '/', '%']:
            if left == INT_TYPE and right == INT_TYPE:
                return INT_TYPE
            elif left == FLOAT_TYPE or right == FLOAT_TYPE:
                return FLOAT_TYPE
            return UNKNOWN_TYPE
        elif operator in ['==', '!=', '<', '<=', '>', '>=']:
            if left.is_compatible_with(right) or right.is_compatible_with(left):
                return BOOL_TYPE
            return UNKNOWN_TYPE
        elif operator in ['&&', '||', 'and', 'or']:
            if left == BOOL_TYPE and right == BOOL_TYPE:
                return BOOL_TYPE
            return UNKNOWN_TYPE
        return UNKNOWN_TYPE

    def visit_unary(self, node: UnaryExprNode) -> Type:
        """Analyze unary expression"""
        operand_type = self.visit_expression(node.operand)

        if node.operator == '-':
            if operand_type in [INT_TYPE, FLOAT_TYPE]:
                node.type_annotation = operand_type
                return operand_type
            self.add_error(
                SemanticErrorCategory.INVALID_OPERAND_TYPE,
                f"Cannot apply unary minus to type {operand_type}",
                node.line, node.column,
                expected="numeric type",
                found=str(operand_type)
            )
        elif node.operator == '!':
            if operand_type == BOOL_TYPE:
                node.type_annotation = BOOL_TYPE
                return BOOL_TYPE
            self.add_error(
                SemanticErrorCategory.INVALID_OPERAND_TYPE,
                f"Cannot apply logical NOT to type {operand_type}",
                node.line, node.column,
                expected="bool",
                found=str(operand_type)
            )

        node.type_annotation = UNKNOWN_TYPE
        return UNKNOWN_TYPE

    def visit_call(self, node: CallExprNode) -> Type:
        """Analyze function call expression"""
        func_symbol = self.symbol_table.lookup(node.callee)

        if not func_symbol or func_symbol.kind != SymbolKind.FUNCTION:
            self.add_error(
                SemanticErrorCategory.UNDECLARED_IDENTIFIER,
                f"Undeclared function '{node.callee}'",
                node.line, node.column,
                suggestion="Declare the function before calling it"
            )
            node.type_annotation = UNKNOWN_TYPE
            return UNKNOWN_TYPE

        expected_count = len(func_symbol.parameters) if func_symbol.parameters else 0
        actual_count = len(node.arguments)

        if expected_count != actual_count:
            self.add_error(
                SemanticErrorCategory.ARGUMENT_COUNT_MISMATCH,
                f"Function '{node.callee}' expects {expected_count} arguments, got {actual_count}",
                node.line, node.column,
                expected=str(expected_count),
                found=str(actual_count)
            )
            node.type_annotation = UNKNOWN_TYPE
            return UNKNOWN_TYPE

        for i, (arg, param) in enumerate(zip(node.arguments, func_symbol.parameters)):
            arg_type = self.visit_expression(arg)
            param_type = param.type

            if not arg_type.is_compatible_with(param_type):
                self.add_error(
                    SemanticErrorCategory.ARGUMENT_TYPE_MISMATCH,
                    f"Argument {i + 1} type mismatch in call to '{node.callee}'",
                    arg.line, arg.column,
                    expected=str(param_type),
                    found=str(arg_type)
                )

        node.type_annotation = func_symbol.type
        return func_symbol.type

    def visit_assignment(self, node: AssignmentExprNode) -> Type:
        """Analyze assignment expression"""
        # Проверка: присваивание строки числу
        if isinstance(node.value, LiteralExprNode) and node.value.literal_type == 'string':
            if isinstance(node.target, IdentifierExprNode):
                target_symbol = self.symbol_table.lookup(node.target.name)
                if target_symbol and target_symbol.type == INT_TYPE:
                    self.add_error(
                        SemanticErrorCategory.TYPE_MISMATCH,
                        "Type mismatch in assignment: cannot assign string to int",
                        node.line, node.column,
                        expected="int",
                        found="string"
                    )
                    node.type_annotation = UNKNOWN_TYPE
                    return UNKNOWN_TYPE
                elif target_symbol and target_symbol.type == FLOAT_TYPE:
                    self.add_error(
                        SemanticErrorCategory.TYPE_MISMATCH,
                        "Type mismatch in assignment: cannot assign string to float",
                        node.line, node.column,
                        expected="float",
                        found="string"
                    )
                    node.type_annotation = UNKNOWN_TYPE
                    return UNKNOWN_TYPE

        # Handle field access: p.x = 5
        if isinstance(node.target, BinaryExprNode) and node.target.operator == '.':
            struct_expr = node.target.left
            field_name = node.target.right.name if isinstance(node.target.right, IdentifierExprNode) else None

            if not field_name:
                self.add_error(
                    SemanticErrorCategory.INVALID_ASSIGNMENT_TARGET,
                    "Invalid field access",
                    node.line, node.column
                )
                return UNKNOWN_TYPE

            struct_type = self.visit_expression(struct_expr)
            value_type = self.visit_expression(node.value)

            if struct_type.kind != TypeKind.STRUCT:
                self.add_error(
                    SemanticErrorCategory.TYPE_MISMATCH,
                    f"Cannot access field on non-struct type",
                    node.line, node.column,
                    expected="struct",
                    found=str(struct_type)
                )
                return UNKNOWN_TYPE

            struct_symbol = self.symbol_table.lookup(struct_type.name)
            if not struct_symbol or not struct_symbol.fields:
                self.add_error(
                    SemanticErrorCategory.UNDECLARED_IDENTIFIER,
                    f"Struct '{struct_type.name}' has no fields",
                    node.line, node.column
                )
                return UNKNOWN_TYPE

            field_symbol = struct_symbol.fields.get(field_name)
            if not field_symbol:
                available = ', '.join(struct_symbol.fields.keys())
                self.add_error(
                    SemanticErrorCategory.UNDECLARED_IDENTIFIER,
                    f"Struct '{struct_type.name}' has no field '{field_name}'",
                    node.line, node.column,
                    suggestion=f"Available fields: {available}"
                )
                return UNKNOWN_TYPE

            if not value_type.is_compatible_with(field_symbol.type):
                self.add_error(
                    SemanticErrorCategory.TYPE_MISMATCH,
                    f"Type mismatch in field assignment: cannot assign {value_type} to field '{field_name}' of type {field_symbol.type}",
                    node.line, node.column,
                    expected=str(field_symbol.type),
                    found=str(value_type)
                )

            node.type_annotation = field_symbol.type
            return field_symbol.type

        # Regular variable assignment
        if not isinstance(node.target, IdentifierExprNode):
            self.add_error(
                SemanticErrorCategory.INVALID_ASSIGNMENT_TARGET,
                "Invalid assignment target",
                node.line, node.column
            )
            return UNKNOWN_TYPE

        target_type = self.visit_identifier(node.target)
        value_type = self.visit_expression(node.value)

        if isinstance(node.target, IdentifierExprNode):
            self._mark_initialized(node.target.name)

        if not value_type.is_compatible_with(target_type):
            self.add_error(
                SemanticErrorCategory.TYPE_MISMATCH,
                f"Type mismatch in assignment: cannot assign {value_type} to {target_type}",
                node.line, node.column,
                expected=str(target_type),
                found=str(value_type)
            )

        node.type_annotation = target_type
        return target_type

    def _type_from_string(self, type_str: str) -> Type:
        """Convert string type to Type object"""
        type_map = {
            'int': INT_TYPE,
            'float': FLOAT_TYPE,
            'bool': BOOL_TYPE,
            'string': STRING_TYPE,
            'void': VOID_TYPE
        }

        if type_str in type_map:
            return type_map[type_str]

        if type_str in self.struct_types:
            return self.struct_types[type_str]

        symbol = self.symbol_table.lookup_global(type_str)
        if symbol and symbol.kind == SymbolKind.STRUCT:
            return symbol.type

        return UNKNOWN_TYPE