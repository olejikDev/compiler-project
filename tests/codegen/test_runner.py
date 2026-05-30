# tests/codegen/test_runner.py
"""Test runner for x86-64 code generation (Sprint 5)."""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class CodeGenTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

        # Настройка PATH для NASM и GCC
        nasm_path = "C:\\Users\\ogubi\\AppData\\Local\\bin\\NASM"
        mingw_path = "C:\\mingw64\\mingw64\\bin"

        os.environ["PATH"] = os.environ["PATH"] + ";" + nasm_path + ";" + mingw_path

        self.nasm_available = shutil.which("nasm") is not None
        self.gcc_available = shutil.which("gcc") is not None

        print(f"NASM available: {self.nasm_available}")
        print(f"GCC available: {self.gcc_available}")
        print(f"NASM path: {shutil.which('nasm')}")
        print(f"GCC path: {shutil.which('gcc')}")

    def compile_and_run(self, source_code: str) -> tuple:
        if not self.nasm_available or not self.gcc_available:
            return -1, "NASM or GCC not available"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Пишем исходник
            src_file = tmp_path / "test.src"
            with open(src_file, 'w') as f:
                f.write(source_code)

            print(f"  [DEBUG] Source written to {src_file}")

            # Компилируем через наш компилятор
            result = subprocess.run(
                [sys.executable, "-m", "src.main", "compile", "--input", str(src_file), "--output",
                 str(tmp_path / "test.asm")],
                capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent
            )
            if result.returncode != 0:
                print(f"  [DEBUG] Compilation failed: {result.stderr}")
                return -1, f"Compilation error: {result.stderr}"

            print(f"  [DEBUG] Assembly generated")

            # Собираем ассемблер
            result = subprocess.run(
                ["nasm", "-f", "elf64", str(tmp_path / "test.asm"), "-o", str(tmp_path / "test.o")],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  [DEBUG] NASM failed: {result.stderr}")
                return -1, f"NASM error: {result.stderr}"

            print(f"  [DEBUG] Object file generated")

            # Собираем runtime
            runtime_asm = Path(__file__).parent.parent.parent / "src" / "runtime" / "runtime.asm"
            result = subprocess.run(
                ["nasm", "-f", "elf64", str(runtime_asm), "-o", str(tmp_path / "runtime.o")],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  [DEBUG] Runtime NASM failed: {result.stderr}")
                return -1, f"Runtime NASM error: {result.stderr}"

            print(f"  [DEBUG] Runtime object generated")

            # Линкуем
            result = subprocess.run(
                ["gcc", "-m64", "-nostdlib", "-o", str(tmp_path / "program"),
                 str(tmp_path / "test.o"), str(tmp_path / "runtime.o"), "-Wl,-e,main"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  [DEBUG] Linking failed: {result.stderr}")
                return -1, f"Linking error: {result.stderr}"

            print(f"  [DEBUG] Program linked")

            # Запускаем
            result = subprocess.run([str(tmp_path / "program")], capture_output=True, text=True)
            print(f"  [DEBUG] Program ran, exit code: {result.returncode}")
            return result.returncode, result.stdout

    def run_test(self, test_name: str, source_code: str, expected_exit_code: int):
        print(f"\n{'=' * 60}")
        print(f"Test: {test_name}")
        print(f"{'=' * 60}")

        try:
            exit_code, output = self.compile_and_run(source_code)
            print(f"  Exit code: {exit_code} (expected: {expected_exit_code})")
            if output:
                print(f"  Output: {output}")

            if exit_code == expected_exit_code:
                print(f"\n   TEST PASSED")
                self.passed += 1
                return True
            else:
                print(f"\n   TEST FAILED")
                self.failed += 1
                self.errors.append((test_name, "Exit code mismatch", f"Expected {expected_exit_code}, got {exit_code}"))
                return False
        except Exception as e:
            print(f"\n   TEST FAILED - Exception: {e}")
            self.failed += 1
            self.errors.append((test_name, "Exception", str(e)))
            return False

    def test_add(self):
        source = """
        fn main() -> int {
            int a = 5;
            int b = 3;
            int c = a + b;
            return c;
        }
        """
        self.run_test("Addition (5+3=8)", source, 8)

    def test_sub(self):
        source = """
        fn main() -> int {
            int a = 10;
            int b = 4;
            int c = a - b;
            return c;
        }
        """
        self.run_test("Subtraction (10-4=6)", source, 6)

    def test_mul(self):
        source = """
        fn main() -> int {
            int a = 6;
            int b = 7;
            int c = a * b;
            return c;
        }
        """
        self.run_test("Multiplication (6*7=42)", source, 42)

    def run_all_tests(self):
        print("\n" + "=" * 60)
        print("CODE GENERATION TESTS - SPRINT 5")
        print("=" * 60)

        if not self.nasm_available:
            print("\n NASM not found!")
            return
        if not self.gcc_available:
            print("\n GCC not found!")
            return

        self.test_add()
        self.test_sub()
        self.test_mul()
        self.print_summary()

    def print_summary(self):
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
                print(f"   {msg[:200]}")

        print("\n" + "=" * 60)
        if self.failed == 0:
            print(" ALL TESTS PASSED!")
        else:
            print(f" {self.failed} test(s) failed")
        print("=" * 60)


def main():
    runner = CodeGenTestRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()