"""Tests for configuration management (TDD RED phase - written before implementation)."""
import pytest


def test_settings_loads_required_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should load GCP_PROJECT_ID, VERTEX_AI_LOCATION, AGENT_ENGINE_ID from env."""
    monkeypatch.setenv("GCP_PROJECT_ID", "my-project")
    monkeypatch.setenv("VERTEX_AI_LOCATION", "us-central1")
    monkeypatch.setenv("AGENT_ENGINE_ID", "9999888777")

    from app.core.config import Settings
    settings = Settings()

    assert settings.gcp_project_id == "my-project"
    assert settings.vertex_ai_location == "us-central1"
    assert settings.agent_engine_id == "9999888777"


def test_settings_has_default_values() -> None:
    """Settings should provide sensible defaults for optional fields."""
    from app.core.config import Settings
    settings = Settings()

    assert settings.app_name == "ai-chat-game-vertex"
    assert settings.user_id == "demo_user_001"
    assert settings.backend_port == 8000
    assert settings.frontend_port == 3000
    assert settings.backend_host == "localhost"


def test_settings_missing_required_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should raise an error when required fields are missing and no .env file."""
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("VERTEX_AI_LOCATION", raising=False)
    monkeypatch.delenv("AGENT_ENGINE_ID", raising=False)

    from pydantic import ValidationError
    from app.core.config import Settings

    # Pass _env_file=None to bypass .env file reading
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
