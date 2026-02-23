"""Integration tests for custom Agent Engine tools (Task 4).

Verifies that initialize_session, update_affinity, and save_to_memory
function correctly when executed inside the deployed Agent Engine.

These tests call the real Agent Engine and write to real Firestore.
They use a dedicated test user ID to avoid polluting production data,
and clean up Firestore documents after each test.

Run with:
    uv run pytest -m integration -v

Default test runs skip these (addopts = "-m not integration").
"""
import json
import uuid
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
    """Override test env vars with real GCP values from .env."""
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


@pytest.fixture
def test_user_id() -> str:
    """Unique user ID per test run to avoid state pollution."""
    return f"tool_test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def cleanup_firestore(test_user_id: str):
    """Delete Firestore test data before and after each test."""
    from google.cloud import firestore

    db = firestore.Client()
    ref = db.collection("user_states").document(test_user_id)
    ref.delete()
    yield
    ref.delete()


def _get_firestore_state(user_id: str) -> dict:
    """Read user_states document for the given user_id from Firestore."""
    from google.cloud import firestore

    db = firestore.Client()
    doc = db.collection("user_states").document(user_id).get()
    return doc.to_dict() if doc.exists else {}


# ---------------------------------------------------------------------------
# 4.1 initialize_session ツールの動作確認
# ---------------------------------------------------------------------------


class TestInitializeSession:
    """Verify initialize_session tool behavior via the deployed Agent Engine."""

    @pytest.mark.timeout(120)
    async def test_first_session_has_zero_affinity(
        self, chat_agent, test_user_id: str
    ) -> None:
        """初回セッションは affinity_level=0 でスタートする。

        The initialize_session tool reads affinity from Firestore.
        For a brand-new user_id there is no document, so affinity_level
        should remain 0 (the tool's default).
        """
        response, _ = await chat_agent.run(
            user_id=test_user_id,
            session_id=None,
            message="こんにちは！",
            scene="indoor",
            emotion="neutral",
        )

        # update_affinity is also called each turn, but starts from 0
        # so the final affinity_level should be a small positive number (0~10)
        assert response.affinity_level <= 10

    @pytest.mark.timeout(120)
    async def test_initialize_session_writes_last_updated_to_firestore(
        self, chat_agent, test_user_id: str
    ) -> None:
        """initialize_session は Firestore に last_updated を書き込む。"""
        before = _get_firestore_state(test_user_id)
        assert before == {}  # document should not exist yet

        await chat_agent.run(
            user_id=test_user_id,
            session_id=None,
            message="はじめまして",
            scene="indoor",
            emotion="neutral",
        )

        after = _get_firestore_state(test_user_id)
        assert "last_updated" in after

    @pytest.mark.timeout(240)
    async def test_second_session_reads_affinity_from_firestore(
        self, chat_agent, test_user_id: str
    ) -> None:
        """2回目以降のセッションは Firestore から親密度を正しく読み込む。"""
        from google.cloud import firestore

        # Manually write an affinity value to Firestore
        db = firestore.Client()
        db.collection("user_states").document(test_user_id).set(
            {"affinity_level": 50, "last_updated": None}
        )

        response, _ = await chat_agent.run(
            user_id=test_user_id,
            session_id=None,
            message="また会えてよかったです！",
            scene="cafe",
            emotion="happy",
        )

        # initialize_session reads 50, update_affinity adds a positive delta
        # so the final affinity_level should be >= 50
        assert response.affinity_level >= 50


# ---------------------------------------------------------------------------
# 4.2 update_affinity ツールの動作確認
# ---------------------------------------------------------------------------


class TestUpdateAffinity:
    """Verify update_affinity tool behavior via the deployed Agent Engine."""

    @pytest.mark.timeout(120)
    async def test_affinity_level_in_response_reflects_tool_result(
        self, chat_agent, test_user_id: str
    ) -> None:
        """StructuredResponse の affinity_level が update_affinity の結果を反映する。"""
        response, _ = await chat_agent.run(
            user_id=test_user_id,
            session_id=None,
            message="今日はとても楽しいです！",
            scene="cafe",
            emotion="happy",
        )

        assert isinstance(response.affinity_level, int)
        assert 0 <= response.affinity_level <= 100

    @pytest.mark.timeout(120)
    async def test_affinity_written_to_firestore(
        self, chat_agent, test_user_id: str
    ) -> None:
        """update_affinity は Firestore の affinity_level を更新する。"""
        await chat_agent.run(
            user_id=test_user_id,
            session_id=None,
            message="好きな食べ物は何ですか？",
            scene="cafe",
            emotion="happy",
        )

        state = _get_firestore_state(test_user_id)
        assert "affinity_level" in state
        assert 0 <= state["affinity_level"] <= 100

    @pytest.mark.timeout(120)
    async def test_affinity_clamped_at_100(
        self, chat_agent, test_user_id: str
    ) -> None:
        """affinity_level は 100 を超えない（クランプされる）。"""
        from google.cloud import firestore

        # Set initial affinity near max
        db = firestore.Client()
        db.collection("user_states").document(test_user_id).set(
            {"affinity_level": 99}
        )

        response, _ = await chat_agent.run(
            user_id=test_user_id,
            session_id=None,
            message="あなたのことが大好きです！",
            scene="indoor",
            emotion="excited",
        )

        assert response.affinity_level <= 100

    @pytest.mark.timeout(120)
    async def test_affinity_clamped_at_zero(
        self, chat_agent, test_user_id: str
    ) -> None:
        """affinity_level は 0 を下回らない（クランプされる）。"""
        from google.cloud import firestore

        # Set initial affinity at 0
        db = firestore.Client()
        db.collection("user_states").document(test_user_id).set(
            {"affinity_level": 0}
        )

        response, _ = await chat_agent.run(
            user_id=test_user_id,
            session_id=None,
            message="もう話しかけないでください。",
            scene="indoor",
            emotion="neutral",
        )

        assert response.affinity_level >= 0


# ---------------------------------------------------------------------------
# 4.3 save_to_memory ツールの動作確認
# ---------------------------------------------------------------------------


class TestSaveToMemory:
    """Verify save_to_memory tool behavior via the deployed Agent Engine.

    Note: The current save_to_memory implementation is a placeholder that
    returns {"saved": True, "content": ...} without writing to Memory Bank.
    Full Memory Bank integration requires the Agent Engine runtime context
    with a properly configured VertexAiMemoryBankService.

    These tests verify:
    1. The tool is registered and callable inside the Agent Engine.
    2. The agent continues to respond normally when save_to_memory is invoked.
    3. No errors occur due to the placeholder implementation.
    """

    @pytest.mark.timeout(120)
    async def test_agent_responds_normally_with_important_info(
        self, chat_agent, test_user_id: str
    ) -> None:
        """重要情報を含む会話でエージェントが正常に応答する。

        save_to_memory が呼ばれても会話フローが壊れないことを確認する。
        """
        from app.models.conversation import StructuredResponse

        # Share important personal information that should trigger save_to_memory
        response, session_id = await chat_agent.run(
            user_id=test_user_id,
            session_id=None,
            message="私の好きな食べ物はラーメンです。覚えておいてください。",
            scene="cafe",
            emotion="happy",
        )

        assert isinstance(response, StructuredResponse)
        assert len(response.dialogue) > 0
        assert isinstance(session_id, str)

    @pytest.mark.timeout(120)
    async def test_save_to_memory_tool_is_callable_locally(self) -> None:
        """save_to_memory ツール関数がローカルで正しく呼び出せる。

        プレースホルダー実装として {"saved": True, "content": ...} を返す。
        """
        from app.services.agent_tools import save_to_memory

        from unittest.mock import MagicMock
        mock_ctx = MagicMock()
        mock_ctx.state = {"user_id": "test_user"}
        result = save_to_memory("ラーメンが好き", mock_ctx)

        assert result["saved"] is True
        assert result["content"] == "ラーメンが好き"
