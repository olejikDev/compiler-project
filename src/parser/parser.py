# src/parser/parser.py
from typing import List, Optional
from src.lexer.token import Token, TokenType
from src.parser.ast import *
from src.utils.error import ParserError


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.errors: List[ParserError] = []

    def parse(self) -> ProgramNode:
        """Program ::= { Declaration }"""
        declarations = []
        while not self.is_at_end():
            if self.peek() and self.peek().type == TokenType.END_OF_FILE:
                break

            try:
                decl = self.parse_declaration()
                declarations.append(decl)
            except ParserError as e:
                self.errors.append(e)
                self.synchronize()

        return ProgramNode(
            declarations=declarations,
            line=1,
            column=1
        )

    # ============ Declarations ============

    def parse_declaration(self) -> DeclarationNode:
        """Declaration ::= FunctionDecl | StructDecl | VarDecl | Statement"""
        if self.check(TokenType.KW_FN):
            return self.parse_function_decl()
        elif self.check(TokenType.KW_STRUCT):
            return self.parse_struct_decl()
        elif self.check_type_keyword():
            stmt = self.parse_var_decl()
            return VarDeclWrapper(
                var_decl=stmt,
                line=stmt.line,
                column=stmt.column
            )
        else:
            # Parse as statement and wrap it
            stmt = self.parse_statement()
            from src.parser.ast import StmtWrapper
            return StmtWrapper(
                statement=stmt,
                line=stmt.line,
                column=stmt.column
            )
    def parse_function_decl(self) -> FunctionDeclNode:
        """FunctionDecl ::= 'fn' Identifier '(' [ Parameters ] ')' ['->' Type] Block"""
        fn_token = self.consume(TokenType.KW_FN, "Expected 'fn'")
        fn_line, fn_col = fn_token.line, fn_token.column

        name_token = self.consume(TokenType.IDENTIFIER, "Expected function name")
        name = name_token.lexeme

        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        parameters = self.parse_parameters()
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")

        return_type = "void"
        if self.check(TokenType.ARROW):
            self.advance()
            return_type = self.parse_type()

        body = self.parse_block()

        return FunctionDeclNode(
            return_type=return_type,
            name=name,
            parameters=parameters,
            body=body,
            line=fn_line,
            column=fn_col
        )

    def parse_struct_decl(self) -> StructDeclNode:
        """StructDecl ::= 'struct' Identifier '{' { FieldDecl } '}'"""
        struct_token = self.consume(TokenType.KW_STRUCT, "Expected 'struct'")
        struct_line, struct_col = struct_token.line, struct_token.column

        name_token = self.consume(TokenType.IDENTIFIER, "Expected struct name")
        name = name_token.lexeme

        self.consume(TokenType.LBRACE, "Expected '{' after struct name")

        fields = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            field_line, field_col = self.peek().line, self.peek().column
            field_type = self.parse_type()
            field_name_token = self.consume(TokenType.IDENTIFIER, "Expected field name")
            self.consume(TokenType.SEMICOLON, "Expected ';' after field name")

            field = VarDeclStmtNode(
                var_type=field_type,
                name=field_name_token.lexeme,
                initializer=None,
                line=field_line,
                column=field_col
            )
            fields.append(field)

        self.consume(TokenType.RBRACE, "Expected '}' after struct fields")

        return StructDeclNode(
            name=name,
            fields=fields,
            line=struct_line,
            column=struct_col
        )

    # ============ Statements ============

    def parse_statement(self) -> StatementNode:
        # Пустой оператор
        if self.check(TokenType.SEMICOLON):
            self.advance()
            return EmptyStmtNode(line=self.previous().line, column=self.previous().column)
        # Блок
        elif self.check(TokenType.LBRACE):
            return self.parse_block()
        # If-else
        elif self.check(TokenType.KW_IF):
            return self.parse_if_statement()
        # While
        elif self.check(TokenType.KW_WHILE):
            return self.parse_while_statement()
        # For
        elif self.check(TokenType.KW_FOR):
            return self.parse_for_statement()
        # Return
        elif self.check(TokenType.KW_RETURN):
            return self.parse_return_statement()
        # Объявление переменной (ключевые типы или идентификатор как тип)
        elif self.check_type_keyword() or (self.check(
                TokenType.IDENTIFIER) and self.peek_next() and self.peek_next().type == TokenType.IDENTIFIER):
            return self.parse_var_decl()
        # ВСЕ ОСТАЛЬНОЕ - выражение
        else:
            return self.parse_expression_statement()

    def parse_block(self) -> BlockStmtNode:
        """Block ::= '{' { Statement } '}'"""
        brace_token = self.consume(TokenType.LBRACE, "Expected '{'")
        block_line, block_col = brace_token.line, brace_token.column

        statements = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            statements.append(self.parse_statement())

        self.consume(TokenType.RBRACE, "Expected '}' after block")

        return BlockStmtNode(
            statements=statements,
            line=block_line,
            column=block_col
        )

    def parse_if_statement(self) -> IfStmtNode:
        """IfStmt ::= 'if' '(' Expression ')' Statement ['else' Statement]"""
        if_token = self.consume(TokenType.KW_IF, "Expected 'if'")
        if_line, if_col = if_token.line, if_token.column

        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")

        then_branch = self.parse_statement()

        else_branch = None
        if self.check(TokenType.KW_ELSE):
            self.advance()
            else_branch = self.parse_statement()

        return IfStmtNode(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
            line=if_line,
            column=if_col
        )

    def parse_while_statement(self) -> WhileStmtNode:
        """WhileStmt ::= 'while' '(' Expression ')' Statement"""
        while_token = self.consume(TokenType.KW_WHILE, "Expected 'while'")
        while_line, while_col = while_token.line, while_token.column

        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")

        body = self.parse_statement()

        return WhileStmtNode(
            condition=condition,
            body=body,
            line=while_line,
            column=while_col
        )

    def parse_for_statement(self) -> ForStmtNode:
        """ForStmt ::= 'for' '(' [ExprStmt] ';' [Expression] ';' [Expression] ')' Statement"""
        for_token = self.consume(TokenType.KW_FOR, "Expected 'for'")
        for_line, for_col = for_token.line, for_token.column

        self.consume(TokenType.LPAREN, "Expected '(' after 'for'")

        init = None
        if not self.check(TokenType.SEMICOLON):
            if self.check_type_keyword():
                init = self.parse_var_decl()
            else:
                init = self.parse_expression_statement()
        else:
            self.consume(TokenType.SEMICOLON, "Expected ';' after for initialization")

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after for condition")

        update = None
        if not self.check(TokenType.RPAREN):
            update = self.parse_expression()

        self.consume(TokenType.RPAREN, "Expected ')' after for clauses")

        body = self.parse_statement()

        return ForStmtNode(
            init=init,
            condition=condition,
            update=update,
            body=body,
            line=for_line,
            column=for_col
        )

    def parse_return_statement(self) -> ReturnStmtNode:
        """ReturnStmt ::= 'return' [Expression] ';'"""
        return_token = self.consume(TokenType.KW_RETURN, "Expected 'return'")
        return_line, return_col = return_token.line, return_token.column

        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.parse_expression()

        self.consume(TokenType.SEMICOLON, "Expected ';' after return statement")

        return ReturnStmtNode(
            value=value,
            line=return_line,
            column=return_col
        )

    def parse_expression_statement(self) -> ExprStmtNode:
        """ExprStmt ::= Expression ';'"""
        expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExprStmtNode(
            expression=expr,
            line=expr.line,
            column=expr.column
        )

    def parse_var_decl(self) -> VarDeclStmtNode:
        """VarDecl ::= Type Identifier ['=' Expression] ';'"""
        decl_line, decl_col = self.peek().line, self.peek().column

        var_type = self.parse_type()
        name_token = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        name = name_token.lexeme

        initializer = None
        if self.check(TokenType.ASSIGN):
            self.advance()
            initializer = self.parse_expression()

        self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")

        return VarDeclStmtNode(
            var_type=var_type,
            name=name,
            initializer=initializer,
            line=decl_line,
            column=decl_col
        )

    # ============ Expressions ============

    def parse_expression(self) -> ExpressionNode:
        """Parse an expression (starting with assignment)"""
        return self.parse_assignment()

    def parse_assignment(self) -> ExpressionNode:
        """Parse assignment: =, +=, -=, *=, /="""
        expr = self.parse_logical_or()

        # Regular assignment
        if self.check(TokenType.ASSIGN):
            operator = self.advance().lexeme
            value = self.parse_assignment()

            if not isinstance(expr, (IdentifierExprNode, BinaryExprNode)):
                raise ParserError(f"Invalid assignment target: {expr.__class__.__name__}",
                                  expr.line, expr.column)

            expr = AssignmentExprNode(
                target=expr,
                operator=operator,
                value=value,
                line=expr.line,
                column=expr.column
            )
        # Compound assignment: +=
        elif self.check(TokenType.PLUS_EQUALS):
            self.advance()  # consume '+='
            value = self.parse_assignment()

            if not isinstance(expr, (IdentifierExprNode, BinaryExprNode)):
                raise ParserError(f"Invalid assignment target: {expr.__class__.__name__}",
                                  expr.line, expr.column)

            # Transform x += y into x = x + y
            binary_op = BinaryExprNode(
                left=expr,
                operator='+',
                right=value,
                line=expr.line,
                column=expr.column
            )
            expr = AssignmentExprNode(
                target=expr,
                operator='=',
                value=binary_op,
                line=expr.line,
                column=expr.column
            )
        # Compound assignment: -=
        elif self.check(TokenType.MINUS_EQUALS):
            self.advance()  # consume '-='
            value = self.parse_assignment()

            if not isinstance(expr, (IdentifierExprNode, BinaryExprNode)):
                raise ParserError(f"Invalid assignment target: {expr.__class__.__name__}",
                                  expr.line, expr.column)

            # Transform x -= y into x = x - y
            binary_op = BinaryExprNode(
                left=expr,
                operator='-',
                right=value,
                line=expr.line,
                column=expr.column
            )
            expr = AssignmentExprNode(
                target=expr,
                operator='=',
                value=binary_op,
                line=expr.line,
                column=expr.column
            )
        # Compound assignment: *=
        elif self.check(TokenType.STAR_EQUALS):
            self.advance()  # consume '*='
            value = self.parse_assignment()

            if not isinstance(expr, (IdentifierExprNode, BinaryExprNode)):
                raise ParserError(f"Invalid assignment target: {expr.__class__.__name__}",
                                  expr.line, expr.column)

            # Transform x *= y into x = x * y
            binary_op = BinaryExprNode(
                left=expr,
                operator='*',
                right=value,
                line=expr.line,
                column=expr.column
            )
            expr = AssignmentExprNode(
                target=expr,
                operator='=',
                value=binary_op,
                line=expr.line,
                column=expr.column
            )
        # Compound assignment: /=
        elif self.check(TokenType.SLASH_EQUALS):
            self.advance()  # consume '/='
            value = self.parse_assignment()

            if not isinstance(expr, (IdentifierExprNode, BinaryExprNode)):
                raise ParserError(f"Invalid assignment target: {expr.__class__.__name__}",
                                  expr.line, expr.column)

            # Transform x /= y into x = x / y
            binary_op = BinaryExprNode(
                left=expr,
                operator='/',
                right=value,
                line=expr.line,
                column=expr.column
            )
            expr = AssignmentExprNode(
                target=expr,
                operator='=',
                value=binary_op,
                line=expr.line,
                column=expr.column
            )

        return expr
    def parse_logical_or(self) -> ExpressionNode:
        """Parse logical OR (|| or 'or')"""
        expr = self.parse_logical_and()

        while self.check(TokenType.OR):
            operator = self.advance().lexeme
            right = self.parse_logical_and()
            expr = BinaryExprNode(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column
            )

        return expr

    def parse_logical_and(self) -> ExpressionNode:
        """Parse logical AND (&& or 'and')"""
        expr = self.parse_equality()

        while self.check(TokenType.AND):
            operator = self.advance().lexeme
            right = self.parse_equality()
            expr = BinaryExprNode(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column
            )

        return expr

    def parse_equality(self) -> ExpressionNode:
        """Parse equality (==, !=)"""
        expr = self.parse_relational()

        while self.check(TokenType.EQ_EQ, TokenType.BANG_EQ):
            operator = self.advance().lexeme
            right = self.parse_relational()
            expr = BinaryExprNode(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column
            )

        return expr

    def parse_relational(self) -> ExpressionNode:
        """Parse relational (<, <=, >, >=)"""
        expr = self.parse_additive()

        while self.check(TokenType.LESS, TokenType.LESS_EQ,
                         TokenType.GREATER, TokenType.GREATER_EQ):
            operator = self.advance().lexeme
            right = self.parse_additive()
            expr = BinaryExprNode(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column
            )

        return expr

    def parse_additive(self) -> ExpressionNode:
        """Parse additive (+, -)"""
        expr = self.parse_multiplicative()

        while self.check(TokenType.PLUS, TokenType.MINUS):
            operator = self.advance().lexeme
            right = self.parse_multiplicative()
            expr = BinaryExprNode(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column
            )

        return expr

    def parse_multiplicative(self) -> ExpressionNode:
        """Parse multiplicative (*, /, %)"""
        expr = self.parse_unary()

        while self.check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self.advance().lexeme
            right = self.parse_unary()
            expr = BinaryExprNode(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column
            )

        return expr

    def parse_unary(self) -> ExpressionNode:
        """Parse unary (-, !, +)"""
        if self.check(TokenType.MINUS, TokenType.BANG, TokenType.PLUS):
            operator = self.advance().lexeme
            operand = self.parse_unary()
            # Unary plus is a no-op
            if operator == '+':
                return operand
            return UnaryExprNode(
                operator=operator,
                operand=operand,
                line=self.previous().line,
                column=self.previous().column
            )

        return self.parse_primary()

    def parse_primary(self) -> ExpressionNode:
        if self.check(TokenType.INT_LITERAL):
            token = self.advance()
            return LiteralExprNode(
                value=token.literal,
                literal_type="int",
                line=token.line,
                column=token.column
            )

        elif self.check(TokenType.FLOAT_LITERAL):
            token = self.advance()
            return LiteralExprNode(
                value=token.literal,
                literal_type="float",
                line=token.line,
                column=token.column
            )

        elif self.check(TokenType.STRING_LITERAL):
            token = self.advance()
            return LiteralExprNode(
                value=token.literal,
                literal_type="string",
                line=token.line,
                column=token.column
            )

        elif self.check(TokenType.KW_TRUE, TokenType.KW_FALSE):
            token = self.advance()
            value = token.type == TokenType.KW_TRUE
            return LiteralExprNode(
                value=value,
                literal_type="bool",
                line=token.line,
                column=token.column
            )

        elif self.check(TokenType.IDENTIFIER):
            token = self.advance()
            name = token.lexeme

            # Проверяем, является ли это вызовом функции
            if self.check(TokenType.LPAREN):
                self.advance()
                arguments = self.parse_arguments()
                self.consume(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallExprNode(
                    callee=name,
                    arguments=arguments,
                    line=token.line,
                    column=token.column
                )
            else:
                expr = IdentifierExprNode(
                    name=name,
                    line=token.line,
                    column=token.column
                )

            # Обработка доступа к полям (точка)
            while self.check(TokenType.DOT):
                self.advance()
                field_token = self.consume(TokenType.IDENTIFIER, "Expected field name after '.'")
                expr = BinaryExprNode(
                    left=expr,
                    operator=".",
                    right=IdentifierExprNode(
                        name=field_token.lexeme,
                        line=field_token.line,
                        column=field_token.column
                    ),
                    line=token.line,
                    column=token.column
                )

            return expr

        elif self.check(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        token = self.peek()
        raise ParserError(f"Unexpected token {token.type.value}", token.line, token.column)
    # ============ Helpers ============

    def parse_parameters(self) -> List[ParamNode]:
        """Parse function parameters"""
        params = []

        if not self.check(TokenType.RPAREN):
            params.append(self.parse_parameter())
            while self.check(TokenType.COMMA):
                self.advance()
                if self.check(TokenType.RPAREN):
                    raise ParserError("Expected parameter name. Got RPAREN",
                                      self.previous().line, self.previous().column + 1)
                params.append(self.parse_parameter())

        return params

    def parse_parameter(self) -> ParamNode:
        """Parse a single parameter"""
        param_line, param_col = self.peek().line, self.peek().column
        param_type = self.parse_type()
        name_token = self.consume(TokenType.IDENTIFIER, "Expected parameter name")

        return ParamNode(
            param_type=param_type,
            name=name_token.lexeme,
            line=param_line,
            column=param_col
        )

    def parse_arguments(self) -> List[ExpressionNode]:
        """Parse function call arguments"""
        args = []

        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.check(TokenType.COMMA):
                self.advance()
                args.append(self.parse_expression())

        return args

    def parse_type(self) -> str:
        """Parse a type annotation"""
        if self.check(TokenType.KW_INT, TokenType.KW_FLOAT,
                      TokenType.KW_BOOL, TokenType.KW_VOID,
                      TokenType.IDENTIFIER):
            return self.advance().lexeme

        token = self.peek()
        raise ParserError(f"Expected type, got {token.type.value}", token.line, token.column)

    def check_type_keyword(self) -> bool:
        """Check if current token is a type keyword"""
        return self.check(TokenType.KW_INT, TokenType.KW_FLOAT,
                          TokenType.KW_BOOL, TokenType.KW_VOID)

    def peek_next(self) -> Optional[Token]:
        """Look at the next token without consuming it"""
        if self.current + 1 >= len(self.tokens):
            return None
        return self.tokens[self.current + 1]

    # ============ Core token methods ============

    def match(self, *types) -> bool:
        """Check if current token matches any of the given types and consume it if so"""
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def check(self, *types) -> bool:
        """Check if current token matches any of the given types without consuming"""
        if self.is_at_end():
            return False
        token = self.peek()
        if token is None:
            return False
        return token.type in types

    def advance(self) -> Token:
        """Move to next token and return the previous one"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def peek(self) -> Token:
        """Return current token without consuming"""
        if self.current >= len(self.tokens):
            return None
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Return the previously consumed token"""
        if self.current - 1 < 0:
            return None
        return self.tokens[self.current - 1]

    def consume(self, token_type: TokenType, message: str = "") -> Token:
        """Consume a token of the expected type or raise an error"""
        if self.check(token_type):
            return self.advance()

        token = self.peek()
        if token:
            error_msg = f"{message or f'Expected {token_type.value}'}. Got {token.type.value}"
            raise ParserError(error_msg, token.line, token.column)
        else:
            raise ParserError(f"{message or f'Expected {token_type.value}'}. Got EOF", 1, 1)

    def is_at_end(self) -> bool:
        """Check if we've reached the end of the token stream"""
        if self.current >= len(self.tokens):
            return True
        token = self.tokens[self.current]
        if token is None:
            return True
        return token.type == TokenType.END_OF_FILE

    def synchronize(self):
        """Synchronize after an error by skipping to the next statement boundary"""
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            token = self.peek()
            if token and token.type in [TokenType.KW_FN, TokenType.KW_STRUCT,
                                        TokenType.KW_IF, TokenType.KW_WHILE,
                                        TokenType.KW_FOR, TokenType.KW_RETURN,
                                        TokenType.LBRACE]:
                return

            self.advance()