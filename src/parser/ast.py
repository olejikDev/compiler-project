# src/parser/ast.py
from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class ASTNode:
    line: int
    column: int


@dataclass
class ExpressionNode(ASTNode):
    pass


@dataclass
class StatementNode(ASTNode):
    pass


@dataclass
class DeclarationNode(ASTNode):
    pass


# ============ Expressions ============

@dataclass
class LiteralExprNode(ExpressionNode):
    value: Union[int, float, str, bool]
    literal_type: str  # "int", "float", "string", "bool"
    line: int
    column: int


@dataclass
class IdentifierExprNode(ExpressionNode):
    name: str
    line: int
    column: int


@dataclass
class BinaryExprNode(ExpressionNode):
    left: ExpressionNode
    operator: str
    right: ExpressionNode
    line: int
    column: int


@dataclass
class UnaryExprNode(ExpressionNode):
    operator: str
    operand: ExpressionNode
    line: int
    column: int


@dataclass
class CallExprNode(ExpressionNode):
    callee: str
    arguments: List[ExpressionNode]
    line: int
    column: int


@dataclass
class AssignmentExprNode(ExpressionNode):
    target: IdentifierExprNode
    operator: str  # "=", "+=", "-=", "*=", "/="
    value: ExpressionNode
    line: int
    column: int


# ============ Statements ============

@dataclass
class BlockStmtNode(StatementNode):
    statements: List[StatementNode]
    line: int
    column: int


@dataclass
class ExprStmtNode(StatementNode):
    expression: Optional[ExpressionNode]
    line: int
    column: int


@dataclass
class EmptyStmtNode(StatementNode):
    line: int
    column: int


@dataclass
class IfStmtNode(StatementNode):
    condition: ExpressionNode
    then_branch: StatementNode
    else_branch: Optional[StatementNode]
    line: int
    column: int


@dataclass
class WhileStmtNode(StatementNode):
    condition: ExpressionNode
    body: StatementNode
    line: int
    column: int


@dataclass
class ForStmtNode(StatementNode):
    init: Optional[StatementNode]  # VarDeclStmtNode или ExprStmtNode
    condition: Optional[ExpressionNode]
    update: Optional[ExpressionNode]
    body: StatementNode
    line: int
    column: int


@dataclass
class ReturnStmtNode(StatementNode):
    value: Optional[ExpressionNode]
    line: int
    column: int


@dataclass
class VarDeclStmtNode(StatementNode):
    var_type: str
    name: str
    initializer: Optional[ExpressionNode]
    line: int
    column: int


# ============ Declarations ============

@dataclass
class ParamNode(ASTNode):
    param_type: str
    name: str
    line: int
    column: int


@dataclass
class FunctionDeclNode(DeclarationNode):
    return_type: str
    name: str
    parameters: List[ParamNode]
    body: Optional[BlockStmtNode]
    line: int
    column: int


@dataclass
class StructDeclNode(DeclarationNode):
    name: str
    fields: List[VarDeclStmtNode]
    line: int
    column: int


@dataclass
class ProgramNode(DeclarationNode):
    declarations: List[DeclarationNode]
    line: int
    column: int


@dataclass
class VarDeclWrapper(DeclarationNode):
    var_decl: VarDeclStmtNode
    line: int
    column: int