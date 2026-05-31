# tests/control_flow/test_runner.py
"""Test runner for control flow features (Sprint 6)."""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ControlFlowTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

        # Setup PATH
        nasm_path = "C:\\Users\\ogubi\\AppData\\Local\\bin\\NASM"
        mingw_path = "C:\\mingw64\\mingw64\\bin"
        os.environ["PATH"] = os.environ["PATH"] + ";" + nasm_path + ";" + mingw_path

    def compile_and_run(self, source_code: str) -> tuple:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            src_file = tmp_path / "test.src"
            with open(src_file, 'w') as f:
                f.write(source_code)

            # Compile
            result = subprocess.run(
                [sys.executable, "-m", "src.main", "compile", "--input", str(src_file), "--output",
                 str(tmp_path / "test.asm")],
                capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent
            )
            if result.returncode != 0:
                return -1, f"Compilation error: {result.stderr}"

            # Assemble
            result = subprocess.run(
                ["nasm", "-f", "elf64", str(tmp_path / "test.asm"), "-o", str(tmp_path / "test.o")],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                return -1, f"NASM error: {result.stderr}"

            # Assemble runtime
            runtime_asm = Path(__file__).parent.parent.parent / "src" / "runtime" / "runtime.asm"
            result = subprocess.run(
                ["nasm", "-f", "elf64", str(runtime_asm), "-o", str(tmp_path / "runtime.o")],
                capture_output=True, text=True
            )

            # Link
            result = subprocess.run(
                ["gcc", "-m64", "-nostdlib", "-o", str(tmp_path / "program"),
                 str(tmp_path / "test.o"), str(tmp_path / "runtime.o"), "-Wl,-e,main"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                return -1, f"Linking error: {result.stderr}"

            # Run
            result = subprocess.run([str(tmp_path / "program")], capture_output=True, text=True)
            return result.returncode, result.stdout

    def test_if_statement(self):
        source = """
        fn main() -> int {
            int x = 10;
            int y = 0;
            if (x > 5) {
                y = 100;
            } else {
                y = 200;
            }
            return y;
        }
        """
        exit_code, _ = self.compile_and_run(source)
        self.run_test("If statement (x>5 => 100)", exit_code, 100)

    def test_if_else_statement(self):
        source = """
        fn main() -> int {
            int x = 3;
            int y = 0;
            if (x > 5) {
                y = 100;
            } else {
                y = 200;
            }
            return y;
        }
        """
        exit_code, _ = self.compile_and_run(source)
        self.run_test("If-else statement (x<=5 => 200)", exit_code, 200)

    def test_while_loop(self):
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
        exit_code, _ = self.compile_and_run(source)
        self.run_test("While loop (sum 0..9 = 45)", exit_code, 45)

    def test_for_loop(self):
        source = """
        fn main() -> int {
            int sum = 0;
            for (int i = 0; i < 10; i = i + 1) {
                sum = sum + i;
            }
            return sum;
        }
        """
        exit_code, _ = self.compile_and_run(source)
        self.run_test("For loop (sum 0..9 = 45)", exit_code, 45)

    def test_logical_and(self):
        source = """
        fn main() -> int {
            int a = 5;
            int b = 10;
            int result = 0;
            if (a > 0 && b > 5) {
                result = 100;
            }
            return result;
        }
        """
        exit_code, _ = self.compile_and_run(source)
        self.run_test("Logical AND (true && true => 100)", exit_code, 100)

    def test_logical_or(self):
        source = """
        fn main() -> int {
            int a = 0;
            int b = 10;
            int result = 0;
            if (a > 0 || b > 5) {
                result = 100;
            }
            return result;
        }
        """
        exit_code, _ = self.compile_and_run(source)
        self.run_test("Logical OR (false || true => 100)", exit_code, 100)

    def run_test(self, test_name: str, actual: int, expected: int):
        print(f"  {test_name}: got {actual}, expected {expected}")
        if actual == expected:
            print(f"    [PASS]")
            self.passed += 1
        else:
            print(f"    [FAIL]")
            self.failed += 1
            self.errors.append((test_name, actual, expected))

    def run_all_tests(self):
        print("\n" + "=" * 60)
        print("CONTROL FLOW TESTS - SPRINT 6")
        print("=" * 60)

        self.test_if_statement()
        self.test_if_else_statement()
        self.test_while_loop()
        self.test_for_loop()
        self.test_logical_and()
        self.test_logical_or()

        print("\n" + "=" * 60)
        print(f"Passed: {self.passed}, Failed: {self.failed}")
        print("=" * 60)


def main():
    runner = ControlFlowTestRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()