import argparse
import sys
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.parser.ast_printer import ASTPrinter
from src.parser.dot_generator import DOTGenerator


def main():
    parser = argparse.ArgumentParser(description='MiniCompiler')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Lexer command
    lex_parser = subparsers.add_parser('lex', help='Run lexer')
    lex_parser.add_argument('--input', required=True, help='Input source file')
    lex_parser.add_argument('--output', help='Output file (default: stdout)')

    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Run parser')
    parse_parser.add_argument('--input', required=True, help='Input source file')
    parse_parser.add_argument('--output', help='Output file (default: stdout)')
    parse_parser.add_argument('--format', choices=['text', 'dot'],
                              default='text', help='Output format')
    parse_parser.add_argument('--verbose', action='store_true',
                              help='Show additional parsing information')

    args = parser.parse_args()

    if args.command == 'lex':
        run_lexer(args)
    elif args.command == 'parse':
        run_parser(args)
    else:
        parser.print_help()


def run_lexer(args):
    with open(args.input, 'r', encoding='utf-8') as f:
        source = f.read()

    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    output = "\n".join(str(t) for t in tokens)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
    else:
        print(output)


def run_parser(args):
    with open(args.input, 'r', encoding='utf-8') as f:
        source = f.read()

    # Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    if args.verbose:
        print(f"Tokens: {len(tokens)}", file=sys.stderr)

    # Syntax analysis
    parser = Parser(tokens)
    ast = parser.parse()

    if parser.errors:
        print(f"Parsing completed with {len(parser.errors)} error(s):", file=sys.stderr)
        for error in parser.errors:
            print(f"  {error}", file=sys.stderr)
        if args.format == 'text':
            sys.exit(1)

    # Output AST
    if args.format == 'text':
        printer = ASTPrinter()
        output = printer.print(ast)
    elif args.format == 'dot':
        dot_gen = DOTGenerator()
        output_file = args.output if args.output else "ast.dot"
        dot_gen.generate(ast, output_file)
        output = f"AST saved to {output_file}"

    if args.output and args.format != 'dot':
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
    elif args.format != 'dot':
        print(output)


if __name__ == "__main__":
    main()