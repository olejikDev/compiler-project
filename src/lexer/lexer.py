# src/lexer/lexer.py
from .token import Token, TokenType
from src.utils.error import LexerError


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.token_index = 0

    def next_token(self):
        if self.token_index >= len(self.tokens):
            if self.is_at_end():
                if not self.tokens or self.tokens[-1].type != TokenType.END_OF_FILE:
                    self.add_eof_token()
            else:
                self.start = self.current
                self.start_line = self.line
                self.start_col = self.column
                self.scan_token()

        if self.token_index < len(self.tokens):
            token = self.tokens[self.token_index]
            self.token_index += 1
            return token
        return Token(TokenType.END_OF_FILE, "", self.line, self.column)

    def peek_token(self):
        if self.token_index >= len(self.tokens):
            if self.is_at_end():
                if not self.tokens or self.tokens[-1].type != TokenType.END_OF_FILE:
                    self.add_eof_token()
            else:
                saved_start = self.start
                saved_current = self.current
                saved_line = self.line
                saved_column = self.column

                self.start = self.current
                self.start_line = self.line
                self.start_col = self.column
                self.scan_token()

                self.start = saved_start
                self.current = saved_current
                self.line = saved_line
                self.column = saved_column

        return self.tokens[self.token_index] if self.token_index < len(self.tokens) else None

    def get_line(self):
        return self.line

    def get_column(self):
        return self.column

    def scan_tokens(self):
        self.token_index = 0
        self.tokens = []

        while not self.is_at_end():
            self.start = self.current
            self.start_line = self.line
            self.start_col = self.column
            self.scan_token()

        self.add_eof_token()
        return self.tokens

    def add_eof_token(self):
        if not self.tokens or self.tokens[-1].type != TokenType.END_OF_FILE:
            if self.tokens:
                last_token = self.tokens[-1]
                if last_token.type == TokenType.END_OF_FILE:
                    pass
                else:
                    self.line = last_token.line
                    self.column = last_token.column + len(last_token.lexeme)
            else:
                self.line = 1
                self.column = 1

            self.tokens.append(Token(TokenType.END_OF_FILE, "", self.line, self.column))

    def is_at_end(self):
        return self.current >= len(self.source)

    def scan_token(self):
        char = self.advance()

        try:
            match char:
                case ' ' | '\t' | '\r':
                    pass
                case '\n':
                    self.line += 1
                    self.column = 1
                case '/':
                    if self.match('='):
                        self.add_token(TokenType.SLASH_EQUALS)
                    else:
                        self.add_token(TokenType.SLASH)
                case '"':
                    self.string()
                case _ if char.isdigit():
                    self.number()
                case _ if char.isalpha() or char == '_':
                    self.identifier()
                case _:
                    self.operator_or_delimiter(char)
        except LexerError as e:
            print(e)

    def advance(self):
        if self.is_at_end():
            return '\0'
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def peek(self):
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def match(self, expected):
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def handle_slash(self):
        if self.match('/'):
            # Однострочный комментарий - пропускаем до конца строки
            while self.peek() != '\n' and not self.is_at_end():
                self.advance()
            # Не добавляем токен!
        elif self.match('*'):
            # Многострочный комментарий
            while not (self.peek() == '*' and self.peek_next() == '/') and not self.is_at_end():
                if self.peek() == '\n':
                    self.line += 1
                    self.column = 1
                self.advance()
            if self.is_at_end():
                raise LexerError("Unterminated multi-line comment", self.start_line, self.start_col)
            self.advance()
            self.advance()
            # Не добавляем токен!
        else:
            self.add_token(TokenType.SLASH)

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            self.advance()
        if self.is_at_end():
            raise LexerError("Unterminated string literal", self.start_line, self.start_col)
        self.advance()
        value = self.source[self.start + 1: self.current - 1]
        self.add_token(TokenType.STRING_LITERAL, value)

    def number(self):
        while self.peek().isdigit():
            self.advance()
        if self.peek() == '.' and self.peek_next().isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
            text = self.source[self.start:self.current]
            self.add_token(TokenType.FLOAT_LITERAL, float(text))
        else:
            text = self.source[self.start:self.current]
            self.add_token(TokenType.INT_LITERAL, int(text))

    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        text = self.source[self.start:self.current]
        if len(text) > 255:
            raise LexerError("Identifier exceeds maximum length of 255 characters", self.start_line, self.start_col)
        keywords = {
            'if': TokenType.KW_IF, 'else': TokenType.KW_ELSE,
            'while': TokenType.KW_WHILE, 'for': TokenType.KW_FOR,
            'int': TokenType.KW_INT, 'float': TokenType.KW_FLOAT,
            'bool': TokenType.KW_BOOL, 'return': TokenType.KW_RETURN,
            'true': TokenType.KW_TRUE, 'false': TokenType.KW_FALSE,
            'void': TokenType.KW_VOID, 'struct': TokenType.KW_STRUCT,
            'fn': TokenType.KW_FN
        }
        token_type = keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(token_type)

    def operator_or_delimiter(self, char):
        match char:
            case '+':
                if self.match('='):
                    self.add_token(TokenType.PLUS_EQUALS)
                else:
                    self.add_token(TokenType.PLUS)
            case '-':
                if self.match('='):
                    self.add_token(TokenType.MINUS_EQUALS)
                elif self.match('>'):
                    self.add_token(TokenType.ARROW)
                else:
                    self.add_token(TokenType.MINUS)
            case '*':
                if self.match('='):
                    self.add_token(TokenType.STAR_EQUALS)
                else:
                    self.add_token(TokenType.STAR)
            case '%':
                self.add_token(TokenType.PERCENT)
            case '!':
                if self.match('='):
                    self.add_token(TokenType.BANG_EQ)
                else:
                    self.add_token(TokenType.BANG)
            case '=':
                if self.match('='):
                    self.add_token(TokenType.EQ_EQ)
                else:
                    self.add_token(TokenType.ASSIGN)
            case '<':
                if self.match('='):
                    self.add_token(TokenType.LESS_EQ)
                else:
                    self.add_token(TokenType.LESS)
            case '>':
                if self.match('='):
                    self.add_token(TokenType.GREATER_EQ)
                else:
                    self.add_token(TokenType.GREATER)
            case '&':
                if self.match('&'):
                    self.add_token(TokenType.AND)
                else:
                    raise LexerError("Unexpected character '&', expected '&&'", self.line, self.column - 1)
            case '|':
                if self.match('|'):
                    self.add_token(TokenType.OR)
                else:
                    raise LexerError("Unexpected character '|', expected '||'", self.line, self.column - 1)
            case '(':
                self.add_token(TokenType.LPAREN)
            case ')':
                self.add_token(TokenType.RPAREN)
            case '{':
                self.add_token(TokenType.LBRACE)
            case '}':
                self.add_token(TokenType.RBRACE)
            case '[':
                self.add_token(TokenType.LBRACKET)
            case ']':
                self.add_token(TokenType.RBRACKET)
            case ';':
                self.add_token(TokenType.SEMICOLON)
            case ',':
                self.add_token(TokenType.COMMA)
            case '.':
                self.add_token(TokenType.DOT)
            case _:
                raise LexerError(f"Unexpected character: '{char}'", self.line, self.column - 1)

    def add_token(self, token_type, literal=None):
        lexeme = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, lexeme, self.start_line, self.start_col, literal))