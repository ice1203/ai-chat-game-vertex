"""Shared test fixtures and configuration."""
import pytest


@pytest.fixture(autouse=True)
def set_required_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required GCP environment variables for all tests."""
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("VERTEX_AI_LOCATION", "us-central1")
    monkeypatch.setenv("AGENT_ENGINE_ID", "test-agent-123")
