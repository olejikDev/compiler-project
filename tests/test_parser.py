#!/usr/bin/env python3
import sys
import os
import glob

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.parser.ast_printer import ASTPrinter


def get_parser_output(source_code: str) -> tuple[str, list]:
    """Запускает парсер и возвращает (AST, список ошибок)"""
    lexer = Lexer(source_code)
    tokens = lexer.scan_tokens()

    parser = Parser(tokens)
    ast = parser.parse()

    printer = ASTPrinter()
    ast_output = printer.print(ast)

    errors = [str(e) for e in parser.errors]

    return ast_output, errors


def run_tests():
    base_path = os.path.dirname(__file__)

    # Собираем все валидные тесты
    valid_files = []
    for subdir in ['expressions', 'statements', 'declarations', 'full_programs']:
        pattern = os.path.join(base_path, 'parser', 'valid', subdir, '*.src')
        valid_files.extend(glob.glob(pattern))

    # Собираем невалидные тесты
    invalid_files = glob.glob(os.path.join(base_path, 'parser', 'invalid', 'syntax_errors', '*.src'))

    valid_files = sorted(valid_files)
    invalid_files = sorted(invalid_files)

    print("=" * 70)
    print("Parser Tests (Sprint 2)")
    print("=" * 70)

    passed = 0
    failed = 0

    # Валидные тесты
    print("\n--- VALID TESTS ---")
    for filepath in valid_files:
        # Ожидаемый файл: тот же путь, но с .expected вместо .src
        expected_filepath = filepath.replace('.src', '.expected')

        if not os.path.exists(expected_filepath):
            print(f"  [SKIP] {os.path.basename(filepath)} (missing {os.path.basename(expected_filepath)})")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        with open(expected_filepath, 'r', encoding='utf-8') as f:
            expected = f.read().strip()

        actual_output, errors = get_parser_output(source)
        actual_output = actual_output.strip()

        if errors:
            print(f"  [FAIL] {os.path.basename(filepath)} - Parser errors: {errors[0][:80]}")
            failed += 1
        elif actual_output == expected:
            print(f"  [PASS] {os.path.basename(filepath)}")
            passed += 1
        else:
            print(f"  [FAIL] {os.path.basename(filepath)}")
            # Показываем diff для первых строк
            expected_lines = expected.split('\n')
            actual_lines = actual_output.split('\n')
            print(f"    Expected first line: {expected_lines[0] if expected_lines else ''}")
            print(f"    Actual first line:   {actual_lines[0] if actual_lines else ''}")
            if len(expected_lines) > 1 and len(actual_lines) > 1:
                print(f"    Expected second line: {expected_lines[1] if len(expected_lines) > 1 else ''}")
                print(f"    Actual second line:   {actual_lines[1] if len(actual_lines) > 1 else ''}")
            failed += 1

    # Невалидные тесты
    print("\n--- INVALID TESTS (Syntax Errors) ---")
    for filepath in invalid_files:
        expected_filepath = filepath.replace('.src', '.expected')

        if not os.path.exists(expected_filepath):
            print(f"  [SKIP] {os.path.basename(filepath)} (missing {os.path.basename(expected_filepath)})")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        with open(expected_filepath, 'r', encoding='utf-8') as f:
            expected_error = f.read().strip()

        _, errors = get_parser_output(source)

        if errors:
            actual_error = errors[0]
            if expected_error in actual_error:
                print(f"  [PASS] {os.path.basename(filepath)}")
                passed += 1
            else:
                print(f"  [FAIL] {os.path.basename(filepath)}")
                print(f"    Expected error: {expected_error}")
                print(f"    Actual error:   {actual_error[:80]}")
                failed += 1
        else:
            print(f"  [FAIL] {os.path.basename(filepath)} - Expected error but got none")
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)