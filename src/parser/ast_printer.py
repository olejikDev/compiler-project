# src/parser/ast_printer.py
from src.parser.ast import *


class ASTPrinter:
    def __init__(self):
        self.indent_level = 0

    def indent(self):
        self.indent_level += 1

    def dedent(self):
        self.indent_level -= 1

    def indent_str(self):
        return "  " * self.indent_level

    def print(self, node: ASTNode) -> str:
        return self.visit_node(node)

    def visit_node(self, node):
        method_name = f"visit_{node.__class__.__name__}"
        method = getattr(self, method_name, None)
        if method:
            return method(node)
        return f"Unknown({node.__class__.__name__})"

    def visit_ProgramNode(self, node: ProgramNode) -> str:
        result = f"Program [line {node.line}]:"
        if node.declarations:
            self.indent()
            for decl in node.declarations:
                result += f"\n{self.indent_str()}{self.visit_node(decl)}"
            self.dedent()
        return result

    def visit_FunctionDeclNode(self, node: FunctionDeclNode) -> str:
        params = ", ".join([self.visit_node(p) for p in node.parameters])
        result = f"FunctionDecl: {node.name}({params}) -> {node.return_type} [line {node.line}]"
        if node.body:
            self.indent()
            result += f"\n{self.indent_str()}Body:"
            self.indent()  # Дополнительный отступ для содержимого Body
            result += f"\n{self.indent_str()}{self.visit_node(node.body)}"
            self.dedent()
            self.dedent()
        return result

    def visit_StructDeclNode(self, node: StructDeclNode) -> str:
        result = f"StructDecl: {node.name} [line {node.line}]"
        if node.fields:
            self.indent()
            result += f"\n{self.indent_str()}Fields:"
            for field in node.fields:
                result += f"\n{self.indent_str()}{self.visit_node(field)}"
            self.dedent()
        return result

    def visit_VarDeclWrapper(self, node: VarDeclWrapper) -> str:
        return self.visit_node(node.var_decl)

    def visit_ParamNode(self, node: ParamNode) -> str:
        return f"{node.name}: {node.param_type}"

    def visit_BlockStmtNode(self, node: BlockStmtNode) -> str:
        result = f"Block [line {node.line}]:"
        if node.statements:
            self.indent()
            for stmt in node.statements:
                result += f"\n{self.indent_str()}{self.visit_node(stmt)}"
            self.dedent()
        return result

    def visit_VarDeclStmtNode(self, node: VarDeclStmtNode) -> str:
        init = f" = {self.visit_node(node.initializer)}" if node.initializer else ""
        return f"VarDecl: {node.var_type} {node.name}{init} [line {node.line}]"

    def visit_IfStmtNode(self, node: IfStmtNode) -> str:
        result = f"IfStmt [line {node.line}]:"
        self.indent()
        result += f"\n{self.indent_str()}Condition: {self.visit_node(node.condition)}"
        result += f"\n{self.indent_str()}Then: {self.visit_node(node.then_branch)}"
        if node.else_branch:
            result += f"\n{self.indent_str()}Else: {self.visit_node(node.else_branch)}"
        self.dedent()
        return result

    def visit_WhileStmtNode(self, node: WhileStmtNode) -> str:
        result = f"WhileStmt [line {node.line}]:"
        self.indent()
        result += f"\n{self.indent_str()}Condition: {self.visit_node(node.condition)}"
        result += f"\n{self.indent_str()}Body: {self.visit_node(node.body)}"
        self.dedent()
        return result

    def visit_ForStmtNode(self, node: ForStmtNode) -> str:
        result = f"ForStmt [line {node.line}]:"
        self.indent()
        if node.init:
            result += f"\n{self.indent_str()}Init: {self.visit_node(node.init)}"
        if node.condition:
            result += f"\n{self.indent_str()}Condition: {self.visit_node(node.condition)}"
        if node.update:
            result += f"\n{self.indent_str()}Update: {self.visit_node(node.update)}"
        result += f"\n{self.indent_str()}Body: {self.visit_node(node.body)}"
        self.dedent()
        return result

    def visit_ReturnStmtNode(self, node: ReturnStmtNode) -> str:
        value = self.visit_node(node.value) if node.value else "void"
        return f"Return: {value} [line {node.line}]"

    def visit_ExprStmtNode(self, node: ExprStmtNode) -> str:
        if node.expression is None:
            return f"; [line {node.line}]"
        return f"ExprStmt: {self.visit_node(node.expression)} [line {node.line}]"

    def visit_EmptyStmtNode(self, node: EmptyStmtNode) -> str:
        return f"; [line {node.line}]"

    def visit_BinaryExprNode(self, node: BinaryExprNode) -> str:
        if node.operator == '.':
            return f"{self.visit_node(node.left)}.{self.visit_node(node.right)}"
        return f"({self.visit_node(node.left)} {node.operator} {self.visit_node(node.right)})"

    def visit_UnaryExprNode(self, node: UnaryExprNode) -> str:
        if node.operator == '+':
            return self.visit_node(node.operand)
        return f"({node.operator}{self.visit_node(node.operand)})"

    def visit_LiteralExprNode(self, node: LiteralExprNode) -> str:
        if node.literal_type == "string":
            return f'"{node.value}"'
        return str(node.value)

    def visit_IdentifierExprNode(self, node: IdentifierExprNode) -> str:
        return node.name

    def visit_CallExprNode(self, node: CallExprNode) -> str:
        args = ", ".join([self.visit_node(arg) for arg in node.arguments])
        return f"{node.callee}({args})"

    def visit_AssignmentExprNode(self, node: AssignmentExprNode) -> str:
        return f"({self.visit_node(node.target)} {node.operator} {self.visit_node(node.value)})"