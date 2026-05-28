# tests/test_semantic.py
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.semantic.errors import SemanticErrorCategory


def analyze_code(code: str):
    """Helper to analyze code and return analyzer"""
    lexer = Lexer(code)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return analyzer


class TestSemanticAnalysis:

    # ============ VALID TESTS ============

    def test_valid_variable_declaration(self):
        code = """
        int x = 5;
        float y = 3.14;
        bool z = true;
        string s = "hello";
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_function_declaration(self):
        code = """
        fn add(int a, int b) -> int {
            return a + b;
        }
        fn main() -> int {
            return add(5, 10);
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_struct_declaration(self):
        code = """
        struct Point {
            int x;
            int y;
        }
        fn main() -> int {
            Point p;
            p.x = 5;
            p.y = 10;
            return p.x + p.y;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_expressions(self):
        code = """
        fn main() -> int {
            int a = 5 + 3 * 2;
            int b = 15 / 3 - 2;
            bool c = (a > b) && (a < 20);
            bool d = !c;
            return a;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_nested_scopes(self):
        code = """
        int x = 10;
        fn test() -> int {
            int x = 20;
            {
                int x = 30;
                return x;
            }
        }
        fn main() -> int {
            return test();
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_control_flow(self):
        code = """
        fn main() -> int {
            int x = 0;
            if (true) {
                x = 10;
            } else {
                x = 20;
            }
            while (x > 0) {
                x = x - 1;
            }
            return x;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_for_loop(self):
        code = """
        fn main() -> int {
            int sum = 0;
            for (int i = 0; i < 10; i = i + 1) {
                sum = sum + i;
            }
            return sum;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_type_conversion(self):
        code = """
        fn main() -> int {
            int a = 5;
            float b = a;
            float c = 3.14;
            float d = a + c;
            bool e = a < c;
            return a;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_nested_structs(self):
        code = """
        struct Point {
            int x;
            int y;
        }
        struct Rect {
            Point top_left;
            Point bottom_right;
        }
        fn main() -> int {
            Rect r;
            r.top_left.x = 0;
            r.top_left.y = 10;
            r.bottom_right.x = 5;
            r.bottom_right.y = 0;
            return r.bottom_right.x - r.top_left.x;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_recursive_function(self):
        code = """
        fn factorial(int n) -> int {
            if (n <= 1) {
                return 1;
            }
            return n * factorial(n - 1);
        }
        fn main() -> int {
            return factorial(5);
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_void_function(self):
        code = """
        fn print_msg() -> void {
            return;
        }
        fn main() -> int {
            print_msg();
            return 0;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_multiple_parameters(self):
        code = """
        fn process(int a, float b, bool c, string d, int e) -> int {
            if (c) {
                return a + e;
            }
            return a - e;
        }
        fn main() -> int {
            return process(10, 3.14, true, "hello", 5);
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_function_call_as_expression(self):
        code = """
        fn add(int a, int b) -> int {
            return a + b;
        }
        fn main() -> int {
            int x = add(5, add(3, 2));
            return x;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    def test_valid_shadowing(self):
        code = """
        int x = 10;
        fn test() -> int {
            int x = 20;
            return x;
        }
        fn main() -> int {
            int x = 30;
            return x;
        }
        """
        analyzer = analyze_code(code)
        assert not analyzer.has_errors()

    # ============ INVALID TESTS ============

    def test_duplicate_variable_declaration(self):
        code = """
        int x = 5;
        int x = 10;
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.DUPLICATE_DECLARATION for e in errors)

    def test_undeclared_variable(self):
        code = """
        int x = y;
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.UNDECLARED_IDENTIFIER for e in errors)

    def test_type_mismatch_assignment(self):
        code = """
        int x = 5;
        x = "hello";
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.TYPE_MISMATCH for e in errors)

    def test_function_return_type_mismatch(self):
        code = """
        fn add(int a, int b) -> int {
            return 3.14;
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.INVALID_RETURN_TYPE for e in errors)

    def test_function_missing_return(self):
        code = """
        fn add(int a, int b) -> int {
            int x = a + b;
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.INVALID_RETURN_TYPE for e in errors)

    def test_argument_count_mismatch(self):
        code = """
        fn add(int a, int b) -> int {
            return a + b;
        }
        fn main() {
            add(5);
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.ARGUMENT_COUNT_MISMATCH for e in errors)

    def test_if_condition_type(self):
        code = """
        fn test() {
            int x = 5;
            if (x) {
                x = 10;
            }
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.INVALID_CONDITION_TYPE for e in errors)

    def test_struct_field_access_invalid(self):
        code = """
        struct Point {
            int x;
            int y;
        }
        fn main() -> int {
            Point p;
            p.z = 5;
            return 0;
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.UNDECLARED_IDENTIFIER for e in errors)

    def test_uninitialized_variable(self):
        code = """
        fn test() -> int {
            int x;
            return x;
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.USE_BEFORE_DECLARATION for e in errors)

    def test_while_condition_type(self):
        code = """
        fn test() {
            int x = 5;
            while (x) {
                x = x - 1;
            }
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.INVALID_CONDITION_TYPE for e in errors)

    def test_for_condition_type(self):
        code = """
        fn test() {
            for (int i = 0; i; i = i + 1) {
                i = i + 1;
            }
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.INVALID_CONDITION_TYPE for e in errors)

    def test_argument_type_mismatch(self):
        code = """
        fn add(int a, int b) -> int {
            return a + b;
        }
        fn main() {
            add("hello", 5);
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.ARGUMENT_TYPE_MISMATCH for e in errors)

    def test_void_function_returning_value(self):
        code = """
        fn print_msg() -> void {
            return 5;
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.INVALID_RETURN_TYPE for e in errors)

    def test_return_outside_function(self):
        code = """
        return 5;
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.INVALID_RETURN_TYPE for e in errors)

    def test_duplicate_function_declaration(self):
        code = """
        fn add(int a, int b) -> int {
            return a + b;
        }
        fn add(int a, int b) -> int {
            return a * b;
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.FUNCTION_REDEFINITION for e in errors)

    def test_duplicate_struct_declaration(self):
        code = """
        struct Point {
            int x;
        }
        struct Point {
            int y;
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.STRUCT_REDEFINITION for e in errors)

    def test_duplicate_field_declaration(self):
        code = """
        struct Point {
            int x;
            int x;
        }
        """
        analyzer = analyze_code(code)
        assert analyzer.has_errors()
        errors = analyzer.get_errors()
        assert any(e.category == SemanticErrorCategory.FIELD_REDEFINITION for e in errors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])