# src/main.py
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir import IRGenerator, ControlFlowGraph


def main():
    parser = argparse.ArgumentParser(description='MiniCompiler - Educational Compiler')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Lex command (Sprint 1)
    lex_parser = subparsers.add_parser('lex', help='Run lexer only')
    lex_parser.add_argument('--input', '-i', required=True, help='Input source file')

    # Parse command (Sprint 2)
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

    # IR command (Sprint 4)
    ir_parser = subparsers.add_parser('ir', help='Generate Intermediate Representation (IR)')
    ir_parser.add_argument('--input', '-i', required=True, help='Input source file')
    ir_parser.add_argument('--output', '-o', help='Output file (optional, prints to stdout if not specified)')
    ir_parser.add_argument('--format', '-f', choices=['text', 'dot', 'cfg'], default='text',
                           help='Output format: text (IR code), dot (Graphviz CFG), cfg (text CFG)')
    ir_parser.add_argument('--stats', action='store_true', help='Show IR statistics')
    ir_parser.add_argument('--function', help='Generate IR only for specific function (default: all)')

    # Compile command (Sprint 5)
    compile_parser = subparsers.add_parser('compile', help='Compile to x86-64 assembly')
    compile_parser.add_argument('--input', '-i', required=True, help='Input source file')
    compile_parser.add_argument('--output', '-o', help='Output assembly file (default: input.asm)')
    compile_parser.add_argument('--target', choices=['x86_64', 'x86'], default='x86_64', help='Target architecture')

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
    elif args.command == 'ir':
        run_ir(args.input, args.output, args.format, args.stats, args.function)
    elif args.command == 'compile':
        run_compile(args.input, args.output, args.target)
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
        print(f"[FAIL] {len(analyzer.get_errors())} error(s) found")
        print()
        print(analyzer.dump_error_report())
        sys.exit(1)
    else:
        print("[PASS] No semantic errors found")
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


def run_ir(input_file: str, output_file: str, format: str, show_stats: bool, function_name: str = None):
    """Generate IR from source file (Sprint 4)"""
    with open(input_file, 'r') as f:
        source = f.read()

    print(f"Generating IR from: {input_file}")
    print()

    # Sprint 1: Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    # Sprint 2: Parsing
    parser = Parser(tokens)
    ast = parser.parse()

    # Sprint 3: Semantic analysis (required for decorated AST with type info)
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if analyzer.has_errors():
        print("[ERROR] Semantic errors found, cannot generate IR:")
        print(analyzer.dump_error_report())
        sys.exit(1)

    # Sprint 4: IR generation
    ir_gen = IRGenerator()
    program_ir = ir_gen.generate(ast)

    # Filter by function name if specified
    if function_name:
        func = program_ir.get_function(function_name)
        if not func:
            print(f"[ERROR] Function '{function_name}' not found in program")
            sys.exit(1)
        # Create a new program with just this function
        filtered_program = type(program_ir)()
        filtered_program.add_function(func)
        filtered_program.entry_function = function_name
        program_ir = filtered_program

    # Prepare output based on format
    output = ""

    if format == 'text':
        output = str(program_ir)

    elif format == 'dot':
        if not program_ir.functions:
            output = "No functions found in program"
        else:
            outputs = []
            for func in program_ir.functions:
                cfg = ControlFlowGraph(func)
                outputs.append(f"// CFG for {func.name}\n{cfg.to_dot()}")
            output = "\n\n".join(outputs)

    elif format == 'cfg':
        if not program_ir.functions:
            output = "No functions found in program"
        else:
            outputs = []
            for func in program_ir.functions:
                cfg = ControlFlowGraph(func)
                outputs.append(f"CFG for {func.name}:")
                outputs.append("=" * 40)
                for block in func.blocks:
                    succ_names = [str(s.label) for s in block.successors]
                    pred_names = [str(p.label) for p in block.predecessors]
                    outputs.append(f"  {block.label}:")
                    outputs.append(f"    preds: {', '.join(pred_names) if pred_names else 'none'}")
                    outputs.append(f"    succs: {', '.join(succ_names) if succ_names else 'none'}")
                    outputs.append(f"    instructions: {len(block.instructions)}")
                outputs.append("")
            output = "\n".join(outputs)

    # Add statistics if requested
    if show_stats and program_ir.functions:
        output += "\n\n"
        output += "=" * 50 + "\n"
        output += "IR STATISTICS\n"
        output += "=" * 50 + "\n"

        total_blocks = 0
        total_instructions = 0
        total_temps = 0
        total_edges = 0
        total_functions = len(program_ir.functions)

        for func in program_ir.functions:
            cfg = ControlFlowGraph(func)
            stats = cfg.get_statistics()
            total_blocks += stats['num_blocks']
            total_edges += stats['num_edges']
            total_temps += len(func.var_mapping)

            for block in func.blocks:
                total_instructions += len(block.instructions)

            output += f"\nFunction '{func.name}':\n"
            output += f"  Basic blocks: {stats['num_blocks']}\n"
            output += f"  Edges: {stats['num_edges']}\n"
            output += f"  Instructions: {len([inst for block in func.blocks for inst in block.instructions])}\n"
            output += f"  Temporaries: {len(func.var_mapping)}\n"
            output += f"  Has cycles: {stats['has_cycles']}\n"

        output += "\n" + "-" * 40 + "\n"
        output += "TOTAL:\n"
        output += f"  Functions: {total_functions}\n"
        output += f"  Basic blocks: {total_blocks}\n"
        output += f"  Edges: {total_edges}\n"
        output += f"  Instructions: {total_instructions}\n"
        output += f"  Temporaries: {total_temps}\n"

    # Write output
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"[OK] IR written to {output_file}")
    else:
        print(output)


def run_compile(input_file: str, output_file: str = None, target: str = "x86_64"):
    """Compile source to x86-64 assembly (Sprint 5)"""
    from src.codegen import X86Generator

    with open(input_file, 'r') as f:
        source = f.read()

    print(f"Compiling: {input_file}")
    print()

    # Sprint 1: Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    # Sprint 2: Parsing
    parser = Parser(tokens)
    ast = parser.parse()

    # Sprint 3: Semantic analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if analyzer.has_errors():
        print("[ERROR] Semantic errors found, cannot generate assembly:")
        print(analyzer.dump_error_report())
        sys.exit(1)

    # Sprint 4: IR generation
    ir_gen = IRGenerator()
    program_ir = ir_gen.generate(ast)

    # Sprint 5: x86-64 code generation
    asm_gen = X86Generator(use_nasm=True)
    assembly = asm_gen.generate(program_ir)

    # Determine output filename
    if not output_file:
        output_file = input_file.replace('.src', '.asm')
        if output_file == input_file:
            output_file = 'output.asm'

    # Write assembly file
    with open(output_file, 'w') as f:
        f.write(assembly)

    print(f"[OK] Assembly written to {output_file}")
    print()
    print("To assemble and run:")
    print(f"  nasm -f elf64 {output_file} -o {output_file.replace('.asm', '.o')}")
    print(f"  nasm -f elf64 src/runtime/runtime.asm -o runtime.o")
    print(f"  gcc -m64 -nostdlib -o program {output_file.replace('.asm', '.o')} runtime.o -Wl,-e,main")
    print(f"  ./program")
    print()
    print("Or with GCC (if libc is used):")
    print(f"  gcc -no-pie -o program {output_file} src/runtime/runtime.asm")


if __name__ == '__main__':
    main()