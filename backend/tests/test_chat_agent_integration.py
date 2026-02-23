"""Integration tests for ChatAgent against the deployed Vertex AI Agent Engine.

These tests call the real Agent Engine and require:
- Valid GCP credentials (ADC: `gcloud auth application-default login`)
- GCP_PROJECT_ID, VERTEX_AI_LOCATION, AGENT_ENGINE_ID set in .env
- Network access to GCP

Run with:
    uv run pytest -m integration -v

Default test runs skip these (addopts = "-m not integration" in pyproject.toml).
"""
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------


def _load_real_env() -> dict[str, str]:
    """Load key-value pairs from the project root .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    env: dict[str, str] = {}
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


@pytest.fixture(autouse=True)
def real_gcp_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Override test env vars with real GCP values from .env.

    The global conftest sets fake values (test-project, test-agent-123) which
    must be replaced with real values for integration tests to reach actual GCP.
    """
    from app.core.config import get_settings

    real_env = _load_real_env()
    for key, value in real_env.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def character_config():
    """Load character config from data/characters/character.json."""
    from app.models.image import CharacterConfig

    json_path = (
        Path(__file__).parent.parent.parent / "data" / "characters" / "character.json"
    )
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return CharacterConfig(**data)


@pytest.fixture
def chat_agent(character_config):
    """Return an initialized ChatAgent connected to the deployed Agent Engine."""
    from app.core.config import get_settings
    from app.services.agent import ChatAgent

    settings = get_settings()
    agent = ChatAgent(
        project_id=settings.gcp_project_id,
        location=settings.vertex_ai_location,
        agent_engine_id=settings.agent_engine_id,
        character_config=character_config,
    )
    agent.initialize()
    return agent


TEST_USER_ID = "integration_test_user"


# ---------------------------------------------------------------------------
# 構造化レスポンス確認 (Task 3.4)
# ---------------------------------------------------------------------------


@pytest.mark.timeout(120)
async def test_run_returns_structured_response(chat_agent) -> None:
    """ChatAgent.run() should return a valid StructuredResponse from the deployed agent."""
    from app.models.conversation import StructuredResponse

    response, session_id = await chat_agent.run(
        user_id=TEST_USER_ID,
        session_id=None,
        message="こんにちは！",
        scene="indoor",
        emotion="neutral",
    )

    assert isinstance(response, StructuredResponse)
    assert isinstance(session_id, str)
    assert len(session_id) > 0


@pytest.mark.timeout(120)
async def test_all_response_fields_have_correct_types(chat_agent) -> None:
    """All StructuredResponse fields should have the expected types and constraints."""
    from app.models.conversation import Emotion, Scene

    response, _ = await chat_agent.run(
        user_id=TEST_USER_ID,
        session_id=None,
        message="今日はどんな気分ですか？",
        scene="cafe",
        emotion="happy",
    )

    assert isinstance(response.dialogue, str)
    assert len(response.dialogue) > 0
    assert isinstance(response.narration, str)
    assert isinstance(response.emotion, Emotion)
    assert isinstance(response.scene, Scene)
    assert isinstance(response.affinity_level, int)
    assert 0 <= response.affinity_level <= 100


# ---------------------------------------------------------------------------
# セッション継続性確認 (Task 3.4)
# ---------------------------------------------------------------------------


@pytest.mark.timeout(240)
async def test_session_id_maintained_across_turns(chat_agent) -> None:
    """Session ID returned by run() should stay the same across multiple turns."""
    # Turn 1: session_id=None → new session created
    _, session_id_1 = await chat_agent.run(
        user_id=TEST_USER_ID,
        session_id=None,
        message="こんにちは",
        scene="indoor",
        emotion="neutral",
    )

    # Turn 2: reuse session_id from turn 1
    _, session_id_2 = await chat_agent.run(
        user_id=TEST_USER_ID,
        session_id=session_id_1,
        message="今日はいい天気ですね",
        scene="indoor",
        emotion="happy",
    )

    assert session_id_2 == session_id_1


@pytest.mark.timeout(240)
async def test_multi_turn_conversation_returns_responses(chat_agent) -> None:
    """Multiple turns in the same session should each return a valid response."""
    from app.models.conversation import StructuredResponse

    messages = [
        "こんにちは！初めまして。",
        "好きな食べ物は何ですか？",
        "それは美味しそうですね！",
    ]

    session_id = None
    for msg in messages:
        response, session_id = await chat_agent.run(
            user_id=TEST_USER_ID,
            session_id=session_id,
            message=msg,
            scene="cafe",
            emotion="happy",
        )
        assert isinstance(response, StructuredResponse)
        assert len(response.dialogue) > 0


# ---------------------------------------------------------------------------
# フォールバック確認 (Task 3.4)
# ---------------------------------------------------------------------------


async def test_parse_failure_falls_back_to_defaults(chat_agent) -> None:
    """Invalid JSON from the stream should produce a fallback StructuredResponse."""
    from app.models.conversation import Emotion, Scene

    # Inject a mock stream that returns invalid JSON (simulates malformed response)
    async def broken_stream(**kwargs):  # type: ignore[return]
        yield {"content": {"role": "model", "parts": [{"text": "this is not json"}]}}

    original = chat_agent._adk_app.async_stream_query
    chat_agent._adk_app.async_stream_query = broken_stream

    try:
        response, _ = await chat_agent.run(
            user_id=TEST_USER_ID,
            session_id="dummy-session-fallback-test",
            message="テスト",
            scene="indoor",
            emotion="neutral",
        )
    finally:
        chat_agent._adk_app.async_stream_query = original

    assert response.emotion == Emotion.neutral
    assert response.scene == Scene.indoor
    assert response.affinity_level == 0
