# src/ir/ir_generator.py
"""IR Generator — traverses decorated AST and produces IR.
Sprint 4 requirements: GEN-1, GEN-2, GEN-3, GEN-4, GEN-5
Sprint 6 requirements: LOOP-2 (for loop)
"""

from typing import Optional, List
from .ir_instructions import (
    Instruction, Opcode, Temp, Var, Const, Label, Operand
)
from .basic_block import BasicBlock, FunctionIR, ProgramIR


class IRGenerator:
    """Generate IR from decorated AST (after semantic analysis)."""

    def __init__(self):
        self.program = ProgramIR()
        self.current_function: Optional[FunctionIR] = None
        self.current_block: Optional[BasicBlock] = None

        # For break/continue support
        self.loop_break_targets: List[Label] = []
        self.loop_continue_targets: List[Label] = []

    def generate(self, ast) -> ProgramIR:
        """Main entry point: generate IR from AST."""
        self._visit(ast)
        return self.program

    # ============================================================
    # Helpers
    # ============================================================

    def _new_temp(self, hint: str = "t") -> Temp:
        if not self.current_function:
            raise RuntimeError("No current function")
        return self.current_function.new_temp(hint)

    def _new_label(self, hint: str = "L") -> Label:
        if not self.current_function:
            raise RuntimeError("No current function")
        return self.current_function.new_label(hint)

    def _emit(self, opcode: Opcode, dest: Optional[Temp] = None,
              args: List[Operand] = None, comment: str = "") -> Optional[Temp]:
        if not self.current_block:
            raise RuntimeError("No current block")
        inst = Instruction(opcode, dest, args or [], comment=comment)
        self.current_block.add_instruction(inst)
        return dest

    def _visit(self, node) -> Optional[Operand]:
        if node is None:
            return None

        class_name = node.__class__.__name__
        method_name = f"_visit_{class_name}"

        if hasattr(self, method_name):
            return getattr(self, method_name)(node)
        else:
            return None

    # ============================================================
    # Program and Declarations
    # ============================================================

    def _visit_ProgramNode(self, node) -> None:
        for decl in node.declarations:
            self._visit(decl)

    def _visit_FunctionDeclNode(self, node) -> None:
        # Create function
        self.current_function = FunctionIR(node.name, node.return_type)

        # Add parameters
        for param in node.parameters:
            self.current_function.parameters.append((param.name, param.param_type))

        # Create entry block
        entry_label = self._new_label("entry")
        entry_block = BasicBlock(entry_label, self.current_function)
        self.current_function.add_block(entry_block)
        self.current_block = entry_block

        # Map parameters to temporaries
        for param in node.parameters:
            temp = self._new_temp(param.name)
            self.current_function.var_mapping[param.name] = temp
            self._emit(Opcode.MOVE, temp, [Var(param.name)], comment=f"param {param.name}")

        # Generate body
        if node.body:
            self._visit(node.body)

        # Implicit return for void functions
        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.RETURN, comment="implicit return")

        # Add to program
        self.program.add_function(self.current_function)
        self.current_function = None
        self.current_block = None

    def _visit_StructDeclNode(self, node) -> None:
        pass

    def _visit_VarDeclWrapper(self, node) -> None:
        self._visit(node.var_decl)

    def _visit_StmtWrapper(self, node) -> None:
        self._visit(node.statement)

    # ============================================================
    # Statements
    # ============================================================

    def _visit_BlockStmtNode(self, node) -> None:
        for stmt in node.statements:
            self._visit(stmt)

    def _visit_VarDeclStmtNode(self, node) -> None:
        temp = self._new_temp(node.name)
        self.current_function.var_mapping[node.name] = temp

        if node.initializer:
            init_val = self._visit(node.initializer)
            if init_val:
                self._emit(Opcode.MOVE, temp, [init_val], comment=f"init {node.name}")

    def _visit_IfStmtNode(self, node) -> None:
        """IfStmtNode — if-else statement."""
        cond = self._visit(node.condition)
        if cond is None:
            return

        then_label = self._new_label("then")
        else_label = self._new_label("else")
        end_label = self._new_label("endif")

        # Emit conditional jump - this is the last instruction in current block
        self._emit(Opcode.JUMP_IF, args=[cond, then_label], comment="if condition true")
        # Fall-through goes to else block - no explicit JUMP needed

        # Current block ends here (JUMP_IF is terminator)
        # Create ELSE block as fall-through from JUMP_IF
        else_block = BasicBlock(else_label, self.current_function)
        self.current_function.add_block(else_block)
        self.current_block = else_block

        if node.else_branch:
            self._visit(node.else_branch)
        if not self.current_block.is_terminated():
            self._emit(Opcode.JUMP, args=[end_label], comment="jump to end")

        # Create THEN block
        then_block = BasicBlock(then_label, self.current_function)
        self.current_function.add_block(then_block)
        self.current_block = then_block

        self._visit(node.then_branch)
        if not self.current_block.is_terminated():
            self._emit(Opcode.JUMP, args=[end_label], comment="jump to end")

        # Create END block
        end_block = BasicBlock(end_label, self.current_function)
        self.current_function.add_block(end_block)
        self.current_block = end_block

    def _visit_WhileStmtNode(self, node) -> None:
        """WhileStmtNode — while loop."""
        # Save old targets
        old_break = self.loop_break_targets
        old_continue = self.loop_continue_targets

        cond_label = self._new_label("while_cond")
        body_label = self._new_label("while_body")
        end_label = self._new_label("while_end")

        self.loop_break_targets = [end_label] + old_break
        self.loop_continue_targets = [cond_label] + old_continue

        # Jump to condition block
        self._emit(Opcode.JUMP, args=[cond_label], comment="jump to condition")

        # Create condition block
        cond_block = BasicBlock(cond_label, self.current_function)
        self.current_function.add_block(cond_block)
        self.current_block = cond_block

        cond = self._visit(node.condition)
        # JUMP_IF is the terminator - on true go to body, on false fall through to end
        self._emit(Opcode.JUMP_IF, args=[cond, body_label], comment="condition true")
        # No explicit JUMP to end needed - fall through goes to end block

        # Create end block (fall through from condition)
        end_block = BasicBlock(end_label, self.current_function)
        self.current_function.add_block(end_block)
        # Don't switch to end block yet - we need to create body block first

        # Create body block (target of JUMP_IF)
        body_block = BasicBlock(body_label, self.current_function)
        self.current_function.add_block(body_block)
        self.current_block = body_block

        self._visit(node.body)
        if not self.current_block.is_terminated():
            self._emit(Opcode.JUMP, args=[cond_label], comment="loop back")

        # Now switch to end block
        self.current_block = end_block

        # Restore targets
        self.loop_break_targets = old_break
        self.loop_continue_targets = old_continue

    def _visit_ForStmtNode(self, node) -> None:
        """ForStmtNode — for loop (FIXED)."""
        # Save old targets
        old_break = self.loop_break_targets
        old_continue = self.loop_continue_targets

        cond_label = self._new_label("for_cond")
        body_label = self._new_label("for_body")
        step_label = self._new_label("for_step")
        end_label = self._new_label("for_end")

        self.loop_break_targets = [end_label] + old_break
        self.loop_continue_targets = [step_label] + old_continue

        # Initialization
        if node.init:
            self._visit(node.init)

        # Jump to condition
        self._emit(Opcode.JUMP, args=[cond_label], comment="jump to condition")

        # Create condition block
        cond_block = BasicBlock(cond_label, self.current_function)
        self.current_function.add_block(cond_block)
        self.current_block = cond_block

        # Evaluate condition
        if node.condition:
            cond = self._visit(node.condition)
            self._emit(Opcode.JUMP_IF, args=[cond, body_label], comment="condition true")
            # Fall through to end if condition false - no extra JUMP needed
        else:
            # No condition -> always true
            self._emit(Opcode.JUMP, args=[body_label], comment="no condition")

        # Create end block (fall through from condition)
        end_block = BasicBlock(end_label, self.current_function)
        self.current_function.add_block(end_block)

        # Create body block
        body_block = BasicBlock(body_label, self.current_function)
        self.current_function.add_block(body_block)
        self.current_block = body_block

        self._visit(node.body)
        if not self.current_block.is_terminated():
            self._emit(Opcode.JUMP, args=[step_label], comment="jump to step")

        # Create step block
        step_block = BasicBlock(step_label, self.current_function)
        self.current_function.add_block(step_block)
        self.current_block = step_block

        if node.update:
            self._visit(node.update)
        self._emit(Opcode.JUMP, args=[cond_label], comment="loop back")

        # Switch to end block
        self.current_block = end_block

        # Restore targets
        self.loop_break_targets = old_break
        self.loop_continue_targets = old_continue

    def _visit_ReturnStmtNode(self, node) -> None:
        if node.value:
            val = self._visit(node.value)
            if val:
                self._emit(Opcode.RETURN, args=[val], comment="return value")
        else:
            self._emit(Opcode.RETURN, comment="return void")

    def _visit_ExprStmtNode(self, node) -> None:
        if node.expression:
            self._visit(node.expression)

    def _visit_EmptyStmtNode(self, node) -> None:
        pass

    # ============================================================
    # Expressions
    # ============================================================

    def _visit_BinaryExprNode(self, node) -> Optional[Temp]:
        if node.operator == '.':
            return None

        left = self._visit(node.left)
        right = self._visit(node.right)

        if left is None or right is None:
            return None

        dest = self._new_temp()

        arith_map = {'+': Opcode.ADD, '-': Opcode.SUB, '*': Opcode.MUL,
                     '/': Opcode.DIV, '%': Opcode.MOD}
        cmp_map = {'==': Opcode.CMP_EQ, '!=': Opcode.CMP_NE,
                   '<': Opcode.CMP_LT, '<=': Opcode.CMP_LE,
                   '>': Opcode.CMP_GT, '>=': Opcode.CMP_GE}
        logic_map = {'&&': Opcode.AND, '||': Opcode.OR}

        if node.operator in arith_map:
            self._emit(arith_map[node.operator], dest, [left, right])
        elif node.operator in cmp_map:
            self._emit(cmp_map[node.operator], dest, [left, right])
        elif node.operator in logic_map:
            self._emit(logic_map[node.operator], dest, [left, right])
        else:
            return None

        return dest

    def _visit_UnaryExprNode(self, node) -> Optional[Temp]:
        operand = self._visit(node.operand)
        if operand is None:
            return None

        if node.operator == '-':
            dest = self._new_temp()
            self._emit(Opcode.NEG, dest, [operand])
            return dest
        elif node.operator == '!':
            dest = self._new_temp()
            self._emit(Opcode.NOT, dest, [operand])
            return dest
        elif node.operator == '+':
            return operand

        return None

    def _visit_LiteralExprNode(self, node) -> Const:
        return Const(node.value)

    def _visit_IdentifierExprNode(self, node) -> Optional[Temp]:
        if self.current_function and node.name in self.current_function.var_mapping:
            return self.current_function.var_mapping[node.name]

        temp = self._new_temp(node.name)
        if self.current_function:
            self.current_function.var_mapping[node.name] = temp
        return temp

    def _visit_CallExprNode(self, node) -> Optional[Temp]:
        dest = None
        if hasattr(node, 'type_annotation'):
            type_str = str(node.type_annotation)
            if type_str not in ('void', 'unknown'):
                dest = self._new_temp()

        self._emit(Opcode.CALL, dest, [Const(node.callee)], comment=f"call {node.callee}")
        return dest

    def _visit_AssignmentExprNode(self, node) -> Optional[Temp]:
        """AssignmentExprNode — assignment: x = expr."""
        # Get target temp
        target_temp = None

        # Check the type of target
        if hasattr(node.target, 'name'):
            # IdentifierExprNode or similar
            if self.current_function and node.target.name in self.current_function.var_mapping:
                target_temp = self.current_function.var_mapping[node.target.name]

        # Compute value
        value_temp = self._visit(node.value)

        if target_temp and value_temp:
            self._emit(Opcode.MOVE, target_temp, [value_temp], comment="assignment")
            return target_temp

        return None