import os
from pathlib import Path
from backend.app.config import Settings
from backend.app.services.nvidia_model_router import NVIDIAModelRouter

def test_config_defaults_and_database_path(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings()
    assert settings.PROJECT_NAME == "SkillBridge AI"
    assert settings.HOST == "127.0.0.1"
    assert settings.PORT == 8000
    assert isinstance(settings.DATABASE_URL, str)
    assert "skillbridge.db" in settings.DATABASE_URL

def test_missing_api_key_router_fallback(monkeypatch):
    # Reset router client and API key
    NVIDIAModelRouter._client = None
    monkeypatch.setattr("backend.app.config.settings.NVIDIA_API_KEY", "")
    monkeypatch.setenv("NVIDIA_API_KEY", "")

    client = NVIDIAModelRouter.get_client()
    # Should return None instead of using any hardcoded fallback string
    assert client is None

    result = NVIDIAModelRouter.chat_completion_with_fallback(
        task_type="orchestration",
        messages=[{"role": "user", "content": "Hello"}]
    )
    assert result["success"] is False
    assert "No NVIDIA_API_KEY configured" in result["error"]

def test_demo_mode_setting():
    settings = Settings()
    assert isinstance(settings.DEMO_MODE, bool)
