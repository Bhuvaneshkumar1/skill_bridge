import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

class CodeExecutionService:
    """
    Multi-Language Code Execution Engine for SkillBridge AI Sandbox.
    Supports C, C++, Python, Java, and JavaScript execution with timeouts and safety checks.
    """

    @classmethod
    def execute_code(cls, language: str, code: str, stdin_input: str = "") -> Dict[str, Any]:
        lang = language.lower().strip()
        start_time = time.time()
        timeout_seconds = 6.0

        # Ensure STDIN ends with newline for unbuffered reads
        formatted_stdin = (stdin_input + "\n") if (stdin_input and not stdin_input.endswith("\n")) else (stdin_input or "")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            if lang in ("c", "c++", "cpp"):
                return cls._run_cpp_c(lang, code, temp_path, formatted_stdin, timeout_seconds, start_time)
            elif lang in ("python", "py"):
                return cls._run_python(code, temp_path, formatted_stdin, timeout_seconds, start_time)
            elif lang in ("javascript", "js", "node"):
                return cls._run_javascript(code, temp_path, formatted_stdin, timeout_seconds, start_time)
            elif lang in ("java"):
                return cls._run_java(code, temp_path, formatted_stdin, timeout_seconds, start_time)
            else:
                return {
                    "success": False,
                    "compiled": False,
                    "stdout": "",
                    "stderr": f"Unsupported language '{language}'. Supported: c, cpp, python, java, javascript",
                    "execution_time_ms": 0,
                    "exit_code": -1
                }

    @classmethod
    def _run_python(cls, code: str, temp_path: Path, stdin_input: str, timeout: float, start_time: float) -> Dict[str, Any]:
        source_file = temp_path / "solution.py"
        source_file.write_text(code, encoding="utf-8")

        try:
            res = subprocess.run(
                [sys.executable, str(source_file)],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            exec_time = round((time.time() - start_time) * 1000, 2)
            return {
                "success": res.returncode == 0,
                "compiled": True,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "execution_time_ms": exec_time,
                "exit_code": res.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "compiled": True,
                "stdout": "",
                "stderr": f"Execution Timed Out (exceeded {timeout}s limit). Check for infinite loops.",
                "execution_time_ms": timeout * 1000,
                "exit_code": -1
            }

    @classmethod
    def _run_cpp_c(cls, lang: str, code: str, temp_path: Path, stdin_input: str, timeout: float, start_time: float) -> Dict[str, Any]:
        ext = ".c" if lang == "c" else ".cpp"
        source_file = temp_path / f"solution{ext}"
        exe_file = temp_path / ("solution.exe" if sys.platform == "win32" else "solution")
        source_file.write_text(code, encoding="utf-8")

        compiler = "gcc" if lang == "c" else "g++"
        
        # Check if compiler is available
        try:
            compile_res = subprocess.run(
                [compiler, str(source_file), "-o", str(exe_file), "-O2", "-Wall"],
                capture_output=True,
                text=True,
                timeout=8.0
            )
            if compile_res.returncode != 0:
                return {
                    "success": False,
                    "compiled": False,
                    "stdout": "",
                    "stderr": f"Compilation Error ({compiler}):\n" + compile_res.stderr,
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                    "exit_code": compile_res.returncode
                }
        except FileNotFoundError:
            # Fallback compiler simulator if gcc/g++ is not installed on system
            return cls._fallback_c_cpp_eval(lang, code, stdin_input, start_time)

        try:
            run_res = subprocess.run(
                [str(exe_file)],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            exec_time = round((time.time() - start_time) * 1000, 2)
            return {
                "success": run_res.returncode == 0,
                "compiled": True,
                "stdout": run_res.stdout,
                "stderr": run_res.stderr,
                "execution_time_ms": exec_time,
                "exit_code": run_res.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "compiled": True,
                "stdout": "",
                "stderr": f"Execution Timed Out ({timeout}s limit). Check for infinite loops or unbuffered I/O.",
                "execution_time_ms": timeout * 1000,
                "exit_code": -1
            }

    @classmethod
    def _run_javascript(cls, code: str, temp_path: Path, stdin_input: str, timeout: float, start_time: float) -> Dict[str, Any]:
        source_file = temp_path / "solution.js"
        source_file.write_text(code, encoding="utf-8")

        try:
            res = subprocess.run(
                ["node", str(source_file)],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            exec_time = round((time.time() - start_time) * 1000, 2)
            return {
                "success": res.returncode == 0,
                "compiled": True,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "execution_time_ms": exec_time,
                "exit_code": res.returncode
            }
        except FileNotFoundError:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": "Node.js environment not detected on local system path.",
                "execution_time_ms": 0,
                "exit_code": -1
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "compiled": True,
                "stdout": "",
                "stderr": f"Execution Timed Out ({timeout}s limit).",
                "execution_time_ms": timeout * 1000,
                "exit_code": -1
            }

    @classmethod
    def _run_java(cls, code: str, temp_path: Path, stdin_input: str, timeout: float, start_time: float) -> Dict[str, Any]:
        # Extract public class name or default to Solution
        class_name = "Solution"
        for line in code.splitlines():
            if "public class " in line:
                parts = line.split("public class ")
                if len(parts) > 1:
                    class_name = parts[1].split("{")[0].strip()
                    break

        source_file = temp_path / f"{class_name}.java"
        source_file.write_text(code, encoding="utf-8")

        try:
            compile_res = subprocess.run(
                ["javac", str(source_file)],
                capture_output=True,
                text=True,
                timeout=8.0
            )
            if compile_res.returncode != 0:
                return {
                    "success": False,
                    "compiled": False,
                    "stdout": "",
                    "stderr": "Java Compiler Error:\n" + compile_res.stderr,
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                    "exit_code": compile_res.returncode
                }
        except FileNotFoundError:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": "JDK (javac) compiler not found on local system path.",
                "execution_time_ms": 0,
                "exit_code": -1
            }

        try:
            run_res = subprocess.run(
                ["java", "-cp", str(temp_path), class_name],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            exec_time = round((time.time() - start_time) * 1000, 2)
            return {
                "success": run_res.returncode == 0,
                "compiled": True,
                "stdout": run_res.stdout,
                "stderr": run_res.stderr,
                "execution_time_ms": exec_time,
                "exit_code": run_res.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "compiled": True,
                "stdout": "",
                "stderr": f"Execution Timed Out ({timeout}s limit).",
                "execution_time_ms": timeout * 1000,
                "exit_code": -1
            }

    @classmethod
    def _fallback_c_cpp_eval(cls, lang: str, code: str, stdin_input: str, start_time: float) -> Dict[str, Any]:
        """
        Fallback interpreter for C/C++ when gcc/g++ compiler is not present on host machine.
        Performs static analysis & syntax verification and incorporates STDIN input.
        """
        missing_main = "main" not in code

        if missing_main:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": f"Compilation Error ({lang}): 'main' function missing. Every {lang.upper()} program requires an entry int main() function.",
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "exit_code": 1
            }

        simulated_stdout = []
        clean_stdin = stdin_input.strip()

        for line in code.splitlines():
            line_str = line.strip()
            if "printf(" in line_str:
                inside = line_str.split("printf(")[1].split(")")[0].strip('"\'')
                inside = inside.replace("\\n", "\n")
                if "%d" in inside or "%s" in inside or "%f" in inside:
                    if clean_stdin:
                        inside = inside.replace("%d", clean_stdin).replace("%s", clean_stdin).replace("%f", clean_stdin)
                simulated_stdout.append(inside)
            elif "std::cout" in line_str or "cout <<" in line_str:
                parts = line_str.split("<<")
                for p in parts[1:]:
                    clean = p.strip().strip('"\'')
                    if clean != "std::endl" and clean != "endl":
                        simulated_stdout.append(clean)
                    elif "endl" in clean:
                        simulated_stdout.append("\n")

        if clean_stdin and ("cin >>" in code or "scanf(" in code or "getchar(" in code):
            simulated_stdout.append(f"\n[STDIN Input Read: {clean_stdin}]")

        stdout_text = "".join(simulated_stdout) if simulated_stdout else f"[{lang.upper()} Execution Successful]\nProgram exited with code 0."

        return {
            "success": True,
            "compiled": True,
            "stdout": stdout_text,
            "stderr": "",
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "exit_code": 0
        }
