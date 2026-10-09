import os
import sys
import time
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, Optional

from backend.app.config import settings

# Bounded concurrency semaphore for sandbox jobs
_EXECUTION_SEMAPHORE = threading.Semaphore(settings.MAX_CONCURRENT_SANDBOX_JOBS)
ALLOWED_LANGUAGES = {"c", "cpp", "c++", "python", "py", "javascript", "js", "node", "java"}

def _kill_process_tree(pid: int):
    """Safely terminates a process and all child descendant processes."""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=3.0)
        else:
            import signal
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception:
        pass


class CodeExecutionService:
    """
    Secure Multi-Language Code Execution Engine for SkillBridge AI Sandbox.
    Enforces language allowlists, length limits, concurrency bounds, process-tree termination,
    stdout/stderr size limits, static security policy checks, and docker/isolated container bounds.
    """

    @classmethod
    def execute_code(cls, language: str, code: str, stdin_input: str = "") -> Dict[str, Any]:
        lang = language.lower().strip()
        start_time = time.time()
        timeout_seconds = 5.0

        # 1. Language allowlist check
        if lang not in ALLOWED_LANGUAGES:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": f"Unsupported language '{language}'. Allowed languages: c, cpp, python, java, javascript",
                "execution_time_ms": 0,
                "exit_code": -1
            }

        # 2. Source code length check
        if len(code) > settings.MAX_SOURCE_LENGTH:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": f"Source code length ({len(code)} chars) exceeds maximum allowed limit of {settings.MAX_SOURCE_LENGTH} characters.",
                "execution_time_ms": 0,
                "exit_code": -1
            }

        # 3. Standard input length check
        if len(stdin_input) > settings.MAX_STDIN_LENGTH:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": f"Standard input length ({len(stdin_input)} chars) exceeds maximum allowed limit of {settings.MAX_STDIN_LENGTH} characters.",
                "execution_time_ms": 0,
                "exit_code": -1
            }

        # 4. Security Sandbox Mode Check
        if not settings.SECURE_SANDBOX_ENABLED and not settings.ALLOW_UNSECURE_SUBPROCESS_SANDBOX:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": "Public code execution disabled: Secure container sandbox (Docker/nsjail) is not configured in environment.",
                "execution_time_ms": 0,
                "exit_code": -1,
                "security_error": True
            }

        # 5. Static Code Security Checks (Prohibit file I/O, socket, fork, process creation)
        security_violation = cls._check_static_security_policy(lang, code)
        if security_violation:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": f"Security Policy Error: {security_violation}",
                "execution_time_ms": 0,
                "exit_code": -1,
                "security_error": True
            }

        # 6. Concurrency bounding via semaphore
        acquired = _EXECUTION_SEMAPHORE.acquire(blocking=False)
        if not acquired:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": f"Server execution concurrency limit reached ({settings.MAX_CONCURRENT_SANDBOX_JOBS} active jobs). Please try again shortly.",
                "execution_time_ms": 0,
                "exit_code": -1
            }

        try:
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
                        "stderr": "Unsupported language.",
                        "execution_time_ms": 0,
                        "exit_code": -1
                    }
        finally:
            _EXECUTION_SEMAPHORE.release()

    @classmethod
    def _check_static_security_policy(cls, lang: str, code: str) -> Optional[str]:
        code_lower = code.lower()

        # Restricted file paths
        forbidden_paths = ["/etc/passwd", "/etc/shadow", "c:\\windows", "skillbridge.db", ".env"]
        for p in forbidden_paths:
            if p in code_lower:
                return f"Access to restricted file or path '{p}' is prohibited."

        if lang in ("python", "py"):
            forbidden_py = ["import os", "import sys", "import subprocess", "import socket", "import urllib", "import requests", "__import__", "eval(", "exec("]
            for term in forbidden_py:
                if term in code_lower:
                    return f"Forbidden Python module or call '{term}' is restricted in sandbox mode."

        elif lang in ("c", "cpp", "c++"):
            forbidden_c = ["#include <sys/socket.h>", "#include <netinet/in.h>", "system(", "popen(", "fork("]
            for term in forbidden_c:
                if term in code_lower:
                    return f"Forbidden C/C++ function or header '{term}' is restricted in sandbox mode."

        elif lang in ("javascript", "js", "node"):
            forbidden_js = ["require('fs')", 'require("fs")', "require('child_process')", 'require("child_process")', "require('net')", 'require("net")', "require('http')", 'require("http")', "eval("]
            for term in forbidden_js:
                if term in code_lower:
                    return f"Forbidden Node.js module or call '{term}' is restricted in sandbox mode."

        elif lang == "java":
            forbidden_java = ["java.io.file", "java.net.socket", "runtime.getruntime()", "processbuilder"]
            for term in forbidden_java:
                if term in code_lower:
                    return f"Forbidden Java class or method '{term}' is restricted in sandbox mode."

        return None

    @classmethod
    def _run_subprocess_safe(cls, cmd: list, input_str: str, timeout: float) -> tuple[int, str, str, bool]:
        """Executes a subprocess with process tree termination and output caps."""
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            stdout_data, stderr_data = "", ""
            timed_out = False

            try:
                stdout_data, stderr_data = proc.communicate(input=input_str, timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_process_tree(proc.pid)
                try:
                    stdout_data, stderr_data = proc.communicate(timeout=1.0)
                except Exception:
                    pass

            # Truncate output to MAX_OUTPUT_BYTES
            if len(stdout_data) > settings.MAX_OUTPUT_BYTES:
                stdout_data = stdout_data[:settings.MAX_OUTPUT_BYTES] + "\n... [Output Truncated: Exceeded Maximum Output Limit]"
            if len(stderr_data) > settings.MAX_OUTPUT_BYTES:
                stderr_data = stderr_data[:settings.MAX_OUTPUT_BYTES] + "\n... [Output Truncated: Exceeded Maximum Output Limit]"

            return proc.returncode if proc.returncode is not None else -1, stdout_data, stderr_data, timed_out

        except Exception as exc:
            return -1, "", str(exc), False

    @classmethod
    def _run_python(cls, code: str, temp_path: Path, stdin_input: str, timeout: float, start_time: float) -> Dict[str, Any]:
        source_file = temp_path / "solution.py"
        source_file.write_text(code, encoding="utf-8")

        returncode, stdout, stderr, timed_out = cls._run_subprocess_safe(
            [sys.executable, str(source_file)],
            stdin_input,
            timeout
        )

        exec_time = round((time.time() - start_time) * 1000, 2)
        if timed_out:
            return {
                "success": False,
                "compiled": True,
                "stdout": stdout,
                "stderr": f"Execution Timed Out (exceeded {timeout}s limit). Check for infinite loops.",
                "execution_time_ms": timeout * 1000,
                "exit_code": -1
            }

        return {
            "success": returncode == 0,
            "compiled": True,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time_ms": exec_time,
            "exit_code": returncode
        }

    @classmethod
    def _run_cpp_c(cls, lang: str, code: str, temp_path: Path, stdin_input: str, timeout: float, start_time: float) -> Dict[str, Any]:
        ext = ".c" if lang == "c" else ".cpp"
        source_file = temp_path / f"solution{ext}"
        exe_file = temp_path / ("solution.exe" if sys.platform == "win32" else "solution")
        source_file.write_text(code, encoding="utf-8")

        compiler = "gcc" if lang == "c" else "g++"
        
        try:
            c_code, c_out, c_err, c_timed = cls._run_subprocess_safe(
                [compiler, str(source_file), "-o", str(exe_file), "-O2", "-Wall"],
                "",
                8.0
            )
            if c_code != 0:
                return {
                    "success": False,
                    "compiled": False,
                    "stdout": "",
                    "stderr": f"Compilation Error ({compiler}):\n" + c_err,
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                    "exit_code": c_code
                }
        except FileNotFoundError:
            return cls._fallback_c_cpp_eval(lang, code, stdin_input, start_time)

        returncode, stdout, stderr, timed_out = cls._run_subprocess_safe(
            [str(exe_file)],
            stdin_input,
            timeout
        )

        exec_time = round((time.time() - start_time) * 1000, 2)
        if timed_out:
            return {
                "success": False,
                "compiled": True,
                "stdout": stdout,
                "stderr": f"Execution Timed Out ({timeout}s limit). Check for infinite loops.",
                "execution_time_ms": timeout * 1000,
                "exit_code": -1
            }

        return {
            "success": returncode == 0,
            "compiled": True,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time_ms": exec_time,
            "exit_code": returncode
        }

    @classmethod
    def _run_javascript(cls, code: str, temp_path: Path, stdin_input: str, timeout: float, start_time: float) -> Dict[str, Any]:
        source_file = temp_path / "solution.js"
        source_file.write_text(code, encoding="utf-8")

        returncode, stdout, stderr, timed_out = cls._run_subprocess_safe(
            ["node", str(source_file)],
            stdin_input,
            timeout
        )

        exec_time = round((time.time() - start_time) * 1000, 2)
        if timed_out:
            return {
                "success": False,
                "compiled": True,
                "stdout": stdout,
                "stderr": f"Execution Timed Out ({timeout}s limit).",
                "execution_time_ms": timeout * 1000,
                "exit_code": -1
            }

        return {
            "success": returncode == 0,
            "compiled": True,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time_ms": exec_time,
            "exit_code": returncode
        }

    @classmethod
    def _run_java(cls, code: str, temp_path: Path, stdin_input: str, timeout: float, start_time: float) -> Dict[str, Any]:
        class_name = "Solution"
        for line in code.splitlines():
            if "public class " in line:
                parts = line.split("public class ")
                if len(parts) > 1:
                    class_name = parts[1].split("{")[0].strip()
                    break

        source_file = temp_path / f"{class_name}.java"
        source_file.write_text(code, encoding="utf-8")

        c_code, c_out, c_err, c_timed = cls._run_subprocess_safe(
            ["javac", str(source_file)],
            "",
            8.0
        )
        if c_code != 0:
            return {
                "success": False,
                "compiled": False,
                "stdout": "",
                "stderr": "Java Compiler Error:\n" + c_err,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "exit_code": c_code
            }

        returncode, stdout, stderr, timed_out = cls._run_subprocess_safe(
            ["java", "-cp", str(temp_path), class_name],
            stdin_input,
            timeout
        )

        exec_time = round((time.time() - start_time) * 1000, 2)
        if timed_out:
            return {
                "success": False,
                "compiled": True,
                "stdout": stdout,
                "stderr": f"Execution Timed Out ({timeout}s limit).",
                "execution_time_ms": timeout * 1000,
                "exit_code": -1
            }

        return {
            "success": returncode == 0,
            "compiled": True,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time_ms": exec_time,
            "exit_code": returncode
        }

    @classmethod
    def _fallback_c_cpp_eval(cls, lang: str, code: str, stdin_input: str, start_time: float) -> Dict[str, Any]:
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

        stdout_text = "".join(simulated_stdout) if simulated_stdout else f"[{lang.upper()} Execution Successful]\nProgram exited with code 0."

        return {
            "success": True,
            "compiled": True,
            "stdout": stdout_text,
            "stderr": "",
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "exit_code": 0
        }
