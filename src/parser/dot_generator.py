# src/parser/dot_generator.py
from src.parser.ast import *


class DOTGenerator:
    def __init__(self):
        self.node_counter = 0
        self.nodes = []
        self.edges = []

    def generate(self, node: ASTNode, filename: str):
        self.node_counter = 0
        self.nodes = []
        self.edges = []

        self.visit(node)

        with open(filename, 'w') as f:
            f.write("digraph AST {\n")
            f.write('  node [shape=box, style=filled, fillcolor=lightyellow];\n')
            f.write('  edge [color=blue];\n')
            for node_line in self.nodes:
                f.write(f"  {node_line}\n")
            for edge in self.edges:
                f.write(f"  {edge}\n")
            f.write("}\n")

    def new_node(self, label: str, color: str = "lightblue") -> str:
        node_id = f"n{self.node_counter}"
        self.nodes.append(f'{node_id} [label="{label}", fillcolor={color}];')
        self.node_counter += 1
        return node_id

    def add_edge(self, parent: str, child: str):
        self.edges.append(f'{parent} -> {child};')

    def visit(self, node: ASTNode, parent_id: str = None) -> str:
        if isinstance(node, ProgramNode):
            node_id = self.new_node("Program", "lightgreen")
            for decl in node.declarations:
                child_id = self.visit(decl)
                self.add_edge(node_id, child_id)
            return node_id

        elif isinstance(node, FunctionDeclNode):
            label = f"Function\\n{node.name} -> {node.return_type}"
            node_id = self.new_node(label, "lightcoral")

            if node.parameters:
                params_id = self.new_node("Parameters", "lightgray")
                self.add_edge(node_id, params_id)
                for p in node.parameters:
                    p_id = self.new_node(f"{p.name}: {p.param_type}", "white")
                    self.add_edge(params_id, p_id)

            if node.body:
                body_id = self.visit(node.body)
                self.add_edge(node_id, body_id)

            return node_id

        elif isinstance(node, BlockStmtNode):
            node_id = self.new_node("Block", "lightyellow")
            for stmt in node.statements:
                child_id = self.visit(stmt)
                self.add_edge(node_id, child_id)
            return node_id

        elif isinstance(node, VarDeclStmtNode):
            label = f"VarDecl\\n{node.var_type} {node.name}"
            if node.initializer:
                label += f"\\n= {self.visit(node.initializer)}"
            node_id = self.new_node(label, "lightpink")
            if node.initializer:
                init_id = self.visit(node.initializer)
                self.add_edge(node_id, init_id)
            return node_id

        elif isinstance(node, IfStmtNode):
            node_id = self.new_node("If", "lightblue")
            cond_id = self.visit(node.condition)
            then_id = self.visit(node.then_branch)
            self.add_edge(node_id, cond_id)
            self.add_edge(node_id, then_id)
            if node.else_branch:
                else_id = self.visit(node.else_branch)
                self.add_edge(node_id, else_id)
            return node_id

        elif isinstance(node, WhileStmtNode):
            node_id = self.new_node("While", "lightblue")
            cond_id = self.visit(node.condition)
            body_id = self.visit(node.body)
            self.add_edge(node_id, cond_id)
            self.add_edge(node_id, body_id)
            return node_id

        elif isinstance(node, BinaryExprNode):
            node_id = self.new_node(node.operator, "lightpink")
            left_id = self.visit(node.left)
            right_id = self.visit(node.right)
            self.add_edge(node_id, left_id)
            self.add_edge(node_id, right_id)
            return node_id

        elif isinstance(node, LiteralExprNode):
            label = str(node.value)
            if node.literal_type == "string":
                label = f'"{label}"'
            return self.new_node(label, "white")

        elif isinstance(node, IdentifierExprNode):
            return self.new_node(node.name, "white")

        elif isinstance(node, ReturnStmtNode):
            node_id = self.new_node("Return", "lightgreen")
            if node.value:
                value_id = self.visit(node.value)
                self.add_edge(node_id, value_id)
            return node_id

        else:
            node_id = self.new_node(node.__class__.__name__, "lightblue")
            return node_id