# src/main.py
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer


def main():
    parser = argparse.ArgumentParser(description='MiniCompiler - Educational Compiler')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Lex command
    lex_parser = subparsers.add_parser('lex', help='Run lexer only')
    lex_parser.add_argument('--input', '-i', required=True, help='Input source file')

    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Run parser only')
    parse_parser.add_argument('--input', '-i', required=True, help='Input source file')
    parse_parser.add_argument('--ast', action='store_true', help='Output AST')

    # Semantic analysis commands (Sprint 3)
    semantic_parser = subparsers.add_parser('semantic', help='Run semantic analysis')
    semantic_parser.add_argument('--input', '-i', required=True, help='Input source file')
    semantic_parser.add_argument('--dump-symbols', '-s', action='store_true', help='Dump symbol table')
    semantic_parser.add_argument('--dump-ast', '-a', action='store_true', help='Dump decorated AST')
    semantic_parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                                 help='Output format for symbol table')

    # Check command (full semantic check)
    check_parser = subparsers.add_parser('check', help='Run full semantic check')
    check_parser.add_argument('--input', '-i', required=True, help='Input source file')
    check_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    # Symbols command
    symbols_parser = subparsers.add_parser('symbols', help='Dump symbol table only')
    symbols_parser.add_argument('--input', '-i', required=True, help='Input source file')
    symbols_parser.add_argument('--format', '-f', choices=['text', 'json'], default='text', help='Output format')

    args = parser.parse_args()

    if args.command == 'lex':
        run_lexer(args.input)
    elif args.command == 'parse':
        run_parser(args.input, args.ast)
    elif args.command == 'semantic':
        run_semantic(args.input, args.dump_symbols, args.dump_ast, args.format)
    elif args.command == 'check':
        run_check(args.input, args.verbose)
    elif args.command == 'symbols':
        run_symbols(args.input, args.format)
    else:
        parser.print_help()


def run_lexer(input_file: str):
    """Run lexer on input file"""
    with open(input_file, 'r') as f:
        source = f.read()

    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    print("Tokens:")
    for token in tokens:
        print(f"  {token}")


def run_parser(input_file: str, show_ast: bool):
    """Run parser on input file"""
    with open(input_file, 'r') as f:
        source = f.read()

    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    parser = Parser(tokens)
    ast = parser.parse()

    print("Parsing completed successfully!")

    if show_ast:
        print("\nAST:")
        print(ast)


def run_semantic(input_file: str, dump_symbols: bool, dump_ast: bool, format: str):
    """Run semantic analysis on input file"""
    with open(input_file, 'r') as f:
        source = f.read()

    # Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    # Parsing
    parser = Parser(tokens)
    ast = parser.parse()

    # Semantic analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    # Output results
    if dump_symbols:
        print("=" * 50)
        print("SYMBOL TABLE")
        print("=" * 50)
        print(analyzer.dump_symbol_table(format))
        print()

    if dump_ast:
        print("=" * 50)
        print("DECORATED AST")
        print("=" * 50)
        print(analyzer.dump_decorated_ast())
        print()

    # Show errors
    if analyzer.has_errors():
        print("=" * 50)
        print("ERRORS")
        print("=" * 50)
        print(analyzer.dump_error_report())
        sys.exit(1)
    else:
        print("Semantic analysis completed successfully with no errors.")


def run_check(input_file: str, verbose: bool):
    """Run full semantic check"""
    with open(input_file, 'r') as f:
        source = f.read()

    print(f"Checking file: {input_file}")
    print()

    # Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    if verbose:
        print(f"Tokens: {len(tokens)}")
        for token in tokens:
            print(f"  {token}")
        print()

    # Parsing
    parser = Parser(tokens)
    ast = parser.parse()
    if verbose:
        print("AST generated successfully")
        print()

    # Semantic analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    # Output results
    print("=" * 50)
    print("SEMANTIC ANALYSIS RESULTS")
    print("=" * 50)

    if analyzer.has_errors():
        print(f"❌ FAILED: {len(analyzer.get_errors())} error(s) found")
        print()
        print(analyzer.dump_error_report())
        sys.exit(1)
    else:
        print("✅ PASSED: No semantic errors found")
        if verbose:
            print()
            print("Symbol Table:")
            print(analyzer.dump_symbol_table())
    print()


def run_symbols(input_file: str, format: str):
    """Dump symbol table only"""
    with open(input_file, 'r') as f:
        source = f.read()

    # Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    # Parsing
    parser = Parser(tokens)
    ast = parser.parse()

    # Semantic analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if analyzer.has_errors():
        print("Errors occurred during analysis:")
        print(analyzer.dump_error_report())
        sys.exit(1)

    # Output symbol table
    print(analyzer.dump_symbol_table(format))


if __name__ == '__main__':
    main()