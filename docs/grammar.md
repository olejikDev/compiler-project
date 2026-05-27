# docs/grammar.md

# MiniCompiler Formal Grammar Specification

## Lexical Tokens

Terminal symbols correspond to token types from Sprint 1:

- **Keywords**: `fn`, `if`, `else`, `while`, `for`, `return`, `int`, `float`, `bool`, `void`, `struct`, `true`, `false`
- **Operators**: `+`, `-`, `*`, `/`, `%`, `=`, `+=`, `-=`, `*=`, `/=`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `&&`, `||`, `!`
- **Delimiters**: `(`, `)`, `{`, `}`, `;`, `,`, `:`, `->`
- **Literals**: Integer, Float, String, Boolean
- **Identifiers**: Letter (a-z, A-Z) followed by letters, digits, or underscores

## Grammar Rules (EBNF)

```ebnf
Program        ::= { Declaration }
Declaration    ::= FunctionDecl | StructDecl | VarDecl
FunctionDecl   ::= "fn" Identifier "(" [ Parameters ] ")" [ "->" Type ] Block
StructDecl     ::= "struct" Identifier "{" { VarDecl } "}"
VarDecl        ::= Type Identifier [ "=" Expression ] ";"

Statement      ::= Block | IfStmt | WhileStmt | ForStmt | ReturnStmt
                | ExprStmt | VarDecl
Block          ::= "{" { Statement } "}"
IfStmt         ::= "if" "(" Expression ")" Statement [ "else" Statement ]
WhileStmt      ::= "while" "(" Expression ")" Statement
ForStmt        ::= "for" "(" [ ExprStmt ] ";" [ Expression ] ";" [ Expression ] ")" Statement
ReturnStmt     ::= "return" [ Expression ] ";"
ExprStmt       ::= Expression ";"

Expression     ::= Assignment
Assignment     ::= LogicalOr { ("=" | "+=" | "-=" | "*=" | "/=") Assignment }
LogicalOr      ::= LogicalAnd { "||" LogicalAnd }
LogicalAnd     ::= Equality { "&&" Equality }
Equality       ::= Relational { ("==" | "!=") Relational }
Relational     ::= Additive { ("<" | "<=" | ">" | ">=") Additive }
Additive       ::= Multiplicative { ("+" | "-") Multiplicative }
Multiplicative ::= Unary { ("*" | "/" | "%") Unary }
Unary          ::= [ "-" | "!" ] Primary
Primary        ::= Literal | Identifier | "(" Expression ")" | Call
Call           ::= Identifier "(" [ Arguments ] ")"
Arguments      ::= Expression { "," Expression }

Type           ::= "int" | "float" | "bool" | "void" | Identifier
Parameters     ::= Parameter { "," Parameter }
Parameter      ::= Type Identifier
Literal        ::= Integer | Float | String | Boolean