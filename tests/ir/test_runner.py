# tests/ir/test_runner.py
"""Test runner for IR generation tests (Sprint 4)."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir import IRGenerator, ControlFlowGraph


class IRTestRunner:
    """Run IR generation tests and compare with expected output."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_test(self, test_name: str, source_code: str, expected_output: str = None):
        """Run a single test."""
        print(f"\n{'=' * 60}")
        print(f"Test: {test_name}")
        print(f"{'=' * 60}")

        try:
            # Step 1: Lexical analysis
            print("  [1/4] Lexical analysis...")
            lexer = Lexer(source_code)
            tokens = lexer.scan_tokens()
            print(f"        ✅ {len(tokens)} tokens generated")

            # Step 2: Parsing
            print("  [2/4] Parsing...")
            parser = Parser(tokens)
            ast = parser.parse()
            print(f"        ✅ AST generated")

            # Step 3: Semantic analysis
            print("  [3/4] Semantic analysis...")
            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)

            if analyzer.has_errors():
                print(f"        ❌ Semantic errors found:")
                for err in analyzer.get_errors():
                    print(f"           - {err}")
                self.failed += 1
                self.errors.append((test_name, "Semantic error", str(analyzer.get_errors())))
                return False

            print(f"        ✅ No semantic errors")

            # Step 4: IR generation
            print("  [4/4] IR generation...")
            ir_gen = IRGenerator()
            program_ir = ir_gen.generate(ast)
            generated_output = str(program_ir)
            print(f"        ✅ IR generated ({len(program_ir.functions)} functions)")

            # Compare with expected if provided
            if expected_output:
                if self._compare_output(generated_output, expected_output):
                    print(f"\n  ✅ TEST PASSED")
                    self.passed += 1
                    return True
                else:
                    print(f"\n  ❌ TEST FAILED - Output mismatch")
                    self.failed += 1
                    self.errors.append((test_name, "Output mismatch",
                                        f"Expected:\n{expected_output}\n\nGot:\n{generated_output}"))
                    return False
            else:
                # Print generated output for manual inspection
                print(f"\n  📄 Generated IR:")
                print("-" * 40)
                print(generated_output)
                print("-" * 40)
                print(f"\n  ✅ TEST PASSED (manual verification required)")
                self.passed += 1
                return True

        except Exception as e:
            print(f"\n  ❌ TEST FAILED - Exception: {e}")
            self.failed += 1
            self.errors.append((test_name, "Exception", str(e)))
            return False

    def _compare_output(self, generated: str, expected: str) -> bool:
        """Compare generated IR with expected output (ignoring whitespace differences)."""
        # Normalize both strings
        gen_lines = [line.strip() for line in generated.split('\n') if line.strip()]
        exp_lines = [line.strip() for line in expected.split('\n') if line.strip()]

        return gen_lines == exp_lines

    def run_all_tests(self):
        """Run all predefined tests."""
        print("\n" + "=" * 60)
        print("IR GENERATION TESTS - SPRINT 4")
        print("=" * 60)

        # Test 1: Arithmetic operations
        self.test_arithmetic()

        # Test 2: If-else statement
        self.test_if_else()

        # Test 3: While loop
        self.test_while_loop()

        # Test 4: Function call
        self.test_function_call()

        # Test 5: Return statement
        self.test_return()

        # Print summary
        self.print_summary()

    def test_arithmetic(self):
        """Test IR generation for arithmetic operations."""
        source = """
        fn main() -> int {
            int x = 10;
            int y = 20;
            int z = x + y * 2;
            return z;
        }
        """

        self.run_test("Arithmetic operations", source)

    def test_if_else(self):
        """Test IR generation for if-else statement."""
        source = """
        fn main() -> int {
            int x = 5;
            int y = 0;

            if (x > 0) {
                y = 10;
            } else {
                y = 20;
            }

            return y;
        }
        """

        self.run_test("If-Else statement", source)

    def test_while_loop(self):
        """Test IR generation for while loop."""
        source = """
        fn main() -> int {
            int i = 0;
            int sum = 0;

            while (i < 10) {
                sum = sum + i;
                i = i + 1;
            }

            return sum;
        }
        """

        self.run_test("While loop", source)

    def test_function_call(self):
        """Test IR generation for function calls."""
        source = """
        fn add(int a, int b) -> int {
            return a + b;
        }

        fn main() -> int {
            int result = add(5, 3);
            return result;
        }
        """

        self.run_test("Function call", source)

    def test_return(self):
        """Test IR generation for return statement."""
        source = """
        fn main() -> int {
            return 42;
        }
        """

        self.run_test("Return statement", source)

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f" Passed: {self.passed}")
        print(f" Failed: {self.failed}")

        if self.errors:
            print("\n" + "=" * 60)
            print("ERROR DETAILS")
            print("=" * 60)
            for i, (test, err_type, msg) in enumerate(self.errors, 1):
                print(f"\n{i}. {test} - {err_type}:")
                print(f"   {msg[:200]}..." if len(msg) > 200 else f"   {msg}")

        print("\n" + "=" * 60)
        if self.failed == 0:
            print(" ALL TESTS PASSED!")
        else:
            print(f"  {self.failed} test(s) failed")
        print("=" * 60)


def main():
    """Main entry point."""
    runner = IRTestRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()