from enum import Enum
from dataclasses import dataclass

class TokenType(Enum):
    # Keywords
    KW_IF = 'KW_IF'
    KW_ELSE = 'KW_ELSE'
    KW_WHILE = 'KW_WHILE'
    KW_FOR = 'KW_FOR'
    KW_INT = 'KW_INT'
    KW_FLOAT = 'KW_FLOAT'
    KW_BOOL = 'KW_BOOL'
    KW_RETURN = 'KW_RETURN'
    KW_TRUE = 'KW_TRUE'
    KW_FALSE = 'KW_FALSE'
    KW_VOID = 'KW_VOID'
    KW_STRUCT = 'KW_STRUCT'
    KW_FN = 'KW_FN'

    # Literals
    INT_LITERAL = 'INT_LITERAL'
    FLOAT_LITERAL = 'FLOAT_LITERAL'
    STRING_LITERAL = 'STRING_LITERAL'

    # Operators
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    STAR = 'STAR'
    SLASH = 'SLASH'
    PERCENT = 'PERCENT'
    EQ_EQ = 'EQ_EQ'
    BANG_EQ = 'BANG_EQ'
    LESS = 'LESS'
    LESS_EQ = 'LESS_EQ'
    GREATER = 'GREATER'
    GREATER_EQ = 'GREATER_EQ'
    AND = 'AND'
    OR = 'OR'
    BANG = 'BANG'
    ASSIGN = 'ASSIGN'

    # Delimiters
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    LBRACE = 'LBRACE'
    RBRACE = 'RBRACE'
    LBRACKET = 'LBRACKET'
    RBRACKET = 'RBRACKET'
    SEMICOLON = 'SEMICOLON'
    COMMA = 'COMMA'
    DOT = 'DOT'

    # Special
    IDENTIFIER = 'IDENTIFIER'
    END_OF_FILE = 'END_OF_FILE'


@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    literal: object = None

    def __str__(self):
        if self.literal is not None:
            return f"{self.line}:{self.column} {self.type.value} \"{self.lexeme}\" {self.literal}"
        return f"{self.line}:{self.column} {self.type.value} \"{self.lexeme}\""