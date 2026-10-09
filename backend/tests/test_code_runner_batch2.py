import pytest
from backend.app.services.code_runner import CodeExecutionService
from backend.app.config import settings

def test_valid_python_program():
    res = CodeExecutionService.execute_code("python", "print('Hello SkillBridge Sandbox')")
    assert res["success"] is True
    assert "Hello SkillBridge Sandbox" in res["stdout"]
    assert res["exit_code"] == 0

def test_invalid_language_rejected():
    res = CodeExecutionService.execute_code("brainfuck", "+++++.")
    assert res["success"] is False
    assert "Unsupported language" in res["stderr"]

def test_oversized_source_rejected(monkeypatch):
    monkeypatch.setattr(settings, "MAX_SOURCE_LENGTH", 20)
    res = CodeExecutionService.execute_code("python", "print('This code is way longer than twenty chars')")
    assert res["success"] is False
    assert "exceeds maximum allowed limit" in res["stderr"]

def test_oversized_stdin_rejected(monkeypatch):
    monkeypatch.setattr(settings, "MAX_STDIN_LENGTH", 10)
    res = CodeExecutionService.execute_code("python", "import sys\nprint('ok')", stdin_input="123456789012345")
    assert res["success"] is False
    assert "Standard input length" in res["stderr"]

def test_attempted_file_read_blocked():
    res = CodeExecutionService.execute_code("python", "f = open('/etc/passwd', 'r')")
    assert res["success"] is False
    assert res.get("security_error") is True
    assert "Security Policy Error" in res["stderr"]

def test_attempted_network_access_blocked():
    res = CodeExecutionService.execute_code("python", "import socket\ns = socket.socket()")
    assert res["success"] is False
    assert res.get("security_error") is True
    assert "Forbidden Python module" in res["stderr"]

def test_attempted_child_process_blocked():
    res = CodeExecutionService.execute_code("python", "import subprocess\nsubprocess.run(['ls'])")
    assert res["success"] is False
    assert res.get("security_error") is True

def test_infinite_loop_timeout():
    res = CodeExecutionService.execute_code("python", "while True: pass")
    assert res["success"] is False
    assert "Execution Timed Out" in res["stderr"]

def test_excessive_output_truncation(monkeypatch):
    monkeypatch.setattr(settings, "MAX_OUTPUT_BYTES", 50)
    res = CodeExecutionService.execute_code("python", "for i in range(100): print('Long output line number', i)")
    assert res["success"] is True
    assert "[Output Truncated:" in res["stdout"]

def test_disabled_public_execution_when_unisolated(monkeypatch):
    monkeypatch.setattr(settings, "SECURE_SANDBOX_ENABLED", False)
    monkeypatch.setattr(settings, "ALLOW_UNSECURE_SUBPROCESS_SANDBOX", False)
    res = CodeExecutionService.execute_code("python", "print('hello')")
    assert res["success"] is False
    assert res.get("security_error") is True
    assert "Public code execution disabled" in res["stderr"]
