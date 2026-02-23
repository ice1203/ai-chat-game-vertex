"""Tests for ChatAgent service (Task 3.1, 3.1.5, 3.2, 3.3)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.image import CharacterConfig


@pytest.fixture
def character_config() -> CharacterConfig:
    """Sample character config for testing."""
    return CharacterConfig(
        name="あかり",
        personality="明るく元気な女の子。好奇心旺盛で、新しいことに挑戦するのが好き。",
        appearance_prompt="anime style girl, long black hair, blue eyes, school uniform",
    )


# ---------------------------------------------------------------------------
# _build_context_message Tests
# ---------------------------------------------------------------------------


class TestBuildContextMessage:
    """Tests for _build_context_message method."""

    def _build(self, character_config: CharacterConfig, **kwargs: object) -> str:
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        defaults = dict(user_message="hello", scene="cafe", emotion="neutral", affinity_level=0)
        defaults.update(kwargs)
        return agent._build_context_message(**defaults)  # type: ignore[arg-type]

    def test_includes_scene(self, character_config: CharacterConfig) -> None:
        """Context message should contain the current scene."""
        assert "cafe" in self._build(character_config, scene="cafe")

    def test_includes_emotion(self, character_config: CharacterConfig) -> None:
        """Context message should contain the current emotion."""
        assert "happy" in self._build(character_config, emotion="happy")

    def test_includes_affinity_level(self, character_config: CharacterConfig) -> None:
        """Context message should contain the current affinity level."""
        assert "42" in self._build(character_config, affinity_level=42)

    def test_includes_user_message(self, character_config: CharacterConfig) -> None:
        """Context message should contain the original user message."""
        user_msg = "好きな食べ物は何ですか？"
        assert user_msg in self._build(character_config, user_message=user_msg)

    def test_returns_string(self, character_config: CharacterConfig) -> None:
        """Context message should be a plain string (not types.Content)."""
        assert isinstance(self._build(character_config), str)

    def test_does_not_include_user_id(self, character_config: CharacterConfig) -> None:
        """Context message should NOT include user_id (stored in session state instead)."""
        assert "ユーザーID" not in self._build(character_config)


# ---------------------------------------------------------------------------
# _build_system_instructions Tests
# ---------------------------------------------------------------------------


class TestBuildSystemInstructions:
    """Tests for _build_system_instructions method."""

    def test_includes_character_name(self, character_config: CharacterConfig) -> None:
        """System instructions should include the character name."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "あかり" in instructions

    def test_includes_personality(self, character_config: CharacterConfig) -> None:
        """System instructions should include personality description."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "明るく元気な女の子" in instructions

    def test_does_not_contain_json_schema_syntax(
        self, character_config: CharacterConfig
    ) -> None:
        """System instructions must NOT include JSON schema syntax."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert '"dialogue":' not in instructions
        assert '"needsImageUpdate":' not in instructions
        assert '"isImportantEvent":' not in instructions
        assert "response_schema" not in instructions

    def test_includes_field_name_explanations(
        self, character_config: CharacterConfig
    ) -> None:
        """System instructions should explain what each field represents."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "dialogue" in instructions
        assert "emotion" in instructions

    def test_is_substantial(self, character_config: CharacterConfig) -> None:
        """System instructions should be substantial enough to guide the model."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert len(instructions) > 200


# ---------------------------------------------------------------------------
# ChatAgent Constructor Tests
# ---------------------------------------------------------------------------


class TestChatAgentConstruction:
    """Tests for ChatAgent constructor."""

    def test_stores_project_id(self, character_config: CharacterConfig) -> None:
        """ChatAgent should store project_id."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("my-project", "us-central1", "engine-123", character_config)
        assert agent.project_id == "my-project"

    def test_stores_location(self, character_config: CharacterConfig) -> None:
        """ChatAgent should store location."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "us-central1", "e", character_config)
        assert agent.location == "us-central1"

    def test_stores_agent_engine_id(self, character_config: CharacterConfig) -> None:
        """ChatAgent should store agent_engine_id."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "engine-123", character_config)
        assert agent.agent_engine_id == "engine-123"

    def test_stores_character_config(self, character_config: CharacterConfig) -> None:
        """ChatAgent should store character_config."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        assert agent.character_config == character_config

    def test_adk_app_initially_none(self, character_config: CharacterConfig) -> None:
        """_adk_app should be None before initialize() is called."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        assert agent._adk_app is None


# ---------------------------------------------------------------------------
# ChatAgent.initialize() Tests (Task 3.2)
# ---------------------------------------------------------------------------


class TestChatAgentInitialize:
    """Tests for the refactored initialize() using vertexai.agent_engines."""

    @patch("app.services.agent.vertexai")
    def test_calls_vertexai_init_with_project_and_location(
        self, mock_vertexai: MagicMock, character_config: CharacterConfig
    ) -> None:
        """initialize() should call vertexai.init with project and location."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("my-project", "us-central1", "engine-123", character_config)
        agent.initialize()

        mock_vertexai.init.assert_called_once_with(
            project="my-project",
            location="us-central1",
        )

    @patch("app.services.agent.vertexai")
    def test_calls_agent_engines_get_with_id(
        self, mock_vertexai: MagicMock, character_config: CharacterConfig
    ) -> None:
        """initialize() should call vertexai.agent_engines.get with agent_engine_id."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "engine-999", character_config)
        agent.initialize()

        mock_vertexai.agent_engines.get.assert_called_once_with("engine-999")

    @patch("app.services.agent.vertexai")
    def test_stores_adk_app_reference(
        self, mock_vertexai: MagicMock, character_config: CharacterConfig
    ) -> None:
        """initialize() should store the AgentEngine object as _adk_app."""
        from app.services.agent import ChatAgent

        mock_app = MagicMock()
        mock_vertexai.agent_engines.get.return_value = mock_app

        agent = ChatAgent("p", "l", "e", character_config)
        agent.initialize()

        assert agent._adk_app is mock_app


# ---------------------------------------------------------------------------
# ChatAgent.run() Tests (Task 3.2)
# ---------------------------------------------------------------------------


async def _async_gen(*events: dict):  # type: ignore[return]
    """Helper: async generator that yields given dicts as stream events."""
    for event in events:
        yield event


class TestChatAgentRun:
    """Tests for the new run() method using async_stream_query."""

    def _make_agent(self, character_config: CharacterConfig) -> "ChatAgent":  # type: ignore[name-defined]
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        return agent

    def _make_adk_app(
        self,
        session_id: str = "session-123",
        events: list | None = None,
    ) -> MagicMock:
        """Build a mock adk_app with preset session and stream events."""
        mock_session = MagicMock()
        mock_session.id = session_id

        mock_adk_app = MagicMock()
        mock_adk_app.async_create_session = AsyncMock(return_value=mock_session)
        mock_adk_app.async_stream_query = lambda **kw: _async_gen(*(events or []))
        return mock_adk_app

    async def test_creates_new_session_when_session_id_is_none(
        self, character_config: CharacterConfig
    ) -> None:
        """run() should call async_create_session when no session_id provided."""
        agent = self._make_agent(character_config)
        agent._adk_app = self._make_adk_app(session_id="new-session")

        _, returned_session_id = await agent.run(
            user_id="user-1",
            session_id=None,
            message="hello",
            scene="cafe",
            emotion="happy",
        )

        agent._adk_app.async_create_session.assert_called_once_with(
            user_id="user-1", state={"user_id": "user-1"}
        )
        assert returned_session_id == "new-session"

    async def test_does_not_create_session_when_id_provided(
        self, character_config: CharacterConfig
    ) -> None:
        """run() should NOT call async_create_session when session_id is given."""
        agent = self._make_agent(character_config)
        agent._adk_app = self._make_adk_app()

        await agent.run(
            user_id="user-1",
            session_id="existing-session",
            message="hello",
            scene="cafe",
            emotion="happy",
        )

        agent._adk_app.async_create_session.assert_not_called()

    async def test_returns_provided_session_id_unchanged(
        self, character_config: CharacterConfig
    ) -> None:
        """run() should return the same session_id that was passed in."""
        agent = self._make_agent(character_config)
        agent._adk_app = self._make_adk_app()

        _, returned_id = await agent.run(
            user_id="user-1",
            session_id="keep-me",
            message="hello",
            scene="indoor",
            emotion="neutral",
        )

        assert returned_id == "keep-me"

    async def test_returns_structured_response_from_model_event(
        self, character_config: CharacterConfig
    ) -> None:
        """run() should parse the model event text into StructuredResponse."""
        import json
        from app.models.conversation import StructuredResponse

        payload = json.dumps(
            {
                "dialogue": "こんにちは！",
                "narration": "あかりは微笑んだ。",
                "emotion": "happy",
                "scene": "cafe",
                "affinity_level": 30,
            }
        )
        # Deployed Agent Engine format: model events carry "model_version"
        model_event = {"model_version": "gemini-3.1-pro-preview", "content": {"parts": [{"text": payload}]}}

        agent = self._make_agent(character_config)
        agent._adk_app = self._make_adk_app(events=[model_event])

        response, _ = await agent.run(
            user_id="user-1",
            session_id="s",
            message="hello",
            scene="cafe",
            emotion="happy",
        )

        assert isinstance(response, StructuredResponse)
        assert response.dialogue == "こんにちは！"
        assert response.affinity_level == 30

    async def test_ignores_non_model_events(
        self, character_config: CharacterConfig
    ) -> None:
        """run() should ignore tool-call and other non-model events."""
        import json
        from app.models.conversation import StructuredResponse

        payload = json.dumps(
            {
                "dialogue": "返答です",
                "narration": "",
                "emotion": "neutral",
                "scene": "indoor",
                "affinity_level": 10,
            }
        )
        events = [
            # non-model event (function_response): has role="user", no model_version
            {"content": {"role": "user", "parts": [{"text": "tool call"}]}},
            # model text event: has model_version, no role in content
            {"model_version": "gemini-3.1-pro-preview", "content": {"parts": [{"text": payload}]}},
        ]

        agent = self._make_agent(character_config)
        agent._adk_app = self._make_adk_app(events=events)

        response, _ = await agent.run(
            user_id="u", session_id="s", message="hi", scene="indoor", emotion="neutral"
        )

        assert isinstance(response, StructuredResponse)
        assert response.dialogue == "返答です"

    async def test_fallback_on_empty_stream(
        self, character_config: CharacterConfig
    ) -> None:
        """run() should return fallback StructuredResponse when stream has no model event."""
        from app.models.conversation import StructuredResponse

        agent = self._make_agent(character_config)
        agent._adk_app = self._make_adk_app(events=[])

        response, _ = await agent.run(
            user_id="u", session_id="s", message="hi", scene="indoor", emotion="neutral"
        )

        assert isinstance(response, StructuredResponse)


# ---------------------------------------------------------------------------
# System Instructions - Tool Guidelines Tests (Task 3.1.5)
# ---------------------------------------------------------------------------


class TestSystemInstructionsToolGuidelines:
    """Tests that system instructions include tool usage guidelines (Task 3.1.5)."""

    def test_includes_initialize_session_guideline(
        self, character_config: CharacterConfig
    ) -> None:
        """System instructions should guide the model to call initialize_session."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "initialize_session" in instructions

    def test_does_not_include_update_affinity_tool(
        self, character_config: CharacterConfig
    ) -> None:
        """update_affinity is handled by ConversationService — not a tool anymore."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "update_affinity" not in instructions

    def test_includes_save_to_memory_guideline(
        self, character_config: CharacterConfig
    ) -> None:
        """System instructions should guide the model to call save_to_memory."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "save_to_memory" in instructions

    def test_includes_affinity_level_field(
        self, character_config: CharacterConfig
    ) -> None:
        """System instructions should mention the affinity_level response field."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "affinity_level" in instructions

    def test_does_not_include_removed_fields(
        self, character_config: CharacterConfig
    ) -> None:
        """System instructions must NOT mention fields removed in Task 3.1.5."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "affinityChange" not in instructions
        assert "isImportantEvent" not in instructions
        assert "eventSummary" not in instructions


# ---------------------------------------------------------------------------
# build_agent Tests (Task 3.1.5)
# ---------------------------------------------------------------------------


class TestBuildAgent:
    """Tests for the module-level build_agent() exportable function."""

    @patch("app.services.agent.Agent")
    def test_returns_agent_instance(
        self, mock_agent_cls: MagicMock, character_config: CharacterConfig
    ) -> None:
        """build_agent() should call Agent() and return its instance."""
        from app.services.agent import build_agent

        build_agent(character_config)

        mock_agent_cls.assert_called_once()

    @patch("app.services.agent.Agent")
    def test_uses_correct_model(
        self, mock_agent_cls: MagicMock, character_config: CharacterConfig
    ) -> None:
        """build_agent() should use _Gemini3Global wrapping the configured MODEL_ID."""
        from app.services.agent import build_agent, MODEL_ID, _Gemini3Global

        build_agent(character_config)

        model_arg = mock_agent_cls.call_args.kwargs["model"]
        assert isinstance(model_arg, _Gemini3Global)
        assert model_arg.model == MODEL_ID

    @patch("app.services.agent.Agent")
    def test_includes_preload_memory_tool(
        self, mock_agent_cls: MagicMock, character_config: CharacterConfig
    ) -> None:
        """build_agent() should include PreloadMemoryTool in tools."""
        from app.services.agent import build_agent
        from google.adk.tools.preload_memory_tool import PreloadMemoryTool

        build_agent(character_config)

        tools = mock_agent_cls.call_args.kwargs["tools"]
        assert any(isinstance(t, PreloadMemoryTool) for t in tools)

    @patch("app.services.agent.Agent")
    def test_extra_tools_appended(
        self, mock_agent_cls: MagicMock, character_config: CharacterConfig
    ) -> None:
        """build_agent() should append extra_tools to the default tool list."""
        from app.services.agent import build_agent

        def dummy_tool(x: str) -> dict:
            """Dummy tool."""
            return {"x": x}

        build_agent(character_config, extra_tools=[dummy_tool])

        tools = mock_agent_cls.call_args.kwargs["tools"]
        assert dummy_tool in tools

    @patch("app.services.agent.Agent")
    def test_no_extra_tools_by_default(
        self, mock_agent_cls: MagicMock, character_config: CharacterConfig
    ) -> None:
        """build_agent() without extra_tools should only have default tools."""
        from app.services.agent import build_agent
        from google.adk.tools.preload_memory_tool import PreloadMemoryTool
        from google.adk.tools.load_memory_tool import LoadMemoryTool

        build_agent(character_config)

        tools = mock_agent_cls.call_args.kwargs["tools"]
        assert len(tools) == 2
        assert any(isinstance(t, PreloadMemoryTool) for t in tools)
        assert any(isinstance(t, LoadMemoryTool) for t in tools)

    @patch("app.services.agent.Agent")
    def test_uses_output_schema(
        self, mock_agent_cls: MagicMock, character_config: CharacterConfig
    ) -> None:
        """build_agent() should use output_schema=StructuredResponse (not generate_content_config)."""
        from app.services.agent import build_agent
        from app.models.conversation import StructuredResponse

        build_agent(character_config)

        assert mock_agent_cls.call_args.kwargs["output_schema"] is StructuredResponse
        assert "generate_content_config" not in mock_agent_cls.call_args.kwargs


# ---------------------------------------------------------------------------
# _parse_response Tests (Task 3.3)
# ---------------------------------------------------------------------------


class TestParseResponse:
    """Direct tests for the module-level _parse_response() function."""

    def test_valid_json_returns_structured_response(self) -> None:
        """Valid JSON should be parsed into a StructuredResponse."""
        import json
        from app.services.agent import _parse_response
        from app.models.conversation import StructuredResponse

        payload = json.dumps(
            {
                "dialogue": "こんにちは",
                "narration": "微笑む",
                "emotion": "happy",
                "scene": "cafe",
                "affinity_level": 42,
            }
        )

        result = _parse_response(payload)

        assert isinstance(result, StructuredResponse)
        assert result.dialogue == "こんにちは"
        assert result.narration == "微笑む"
        assert result.affinity_level == 42

    def test_valid_json_preserves_emotion(self) -> None:
        """Parsed response should preserve the emotion field."""
        import json
        from app.services.agent import _parse_response
        from app.models.conversation import Emotion

        payload = json.dumps(
            {
                "dialogue": "x",
                "narration": "",
                "emotion": "sad",
                "scene": "indoor",
                "affinity_level": 10,
            }
        )

        result = _parse_response(payload)
        assert result.emotion == Emotion.sad

    def test_valid_json_preserves_scene(self) -> None:
        """Parsed response should preserve the scene field."""
        import json
        from app.services.agent import _parse_response
        from app.models.conversation import Scene

        payload = json.dumps(
            {
                "dialogue": "x",
                "narration": "",
                "emotion": "neutral",
                "scene": "park",
                "affinity_level": 0,
            }
        )

        result = _parse_response(payload)
        assert result.scene == Scene.park

    def test_invalid_json_returns_fallback(self) -> None:
        """Non-JSON string should trigger fallback StructuredResponse."""
        from app.services.agent import _parse_response
        from app.models.conversation import StructuredResponse

        result = _parse_response("this is not json")

        assert isinstance(result, StructuredResponse)

    def test_fallback_emotion_is_neutral(self) -> None:
        """Fallback response should have emotion=neutral."""
        from app.services.agent import _parse_response
        from app.models.conversation import Emotion

        result = _parse_response("invalid json")

        assert result.emotion == Emotion.neutral

    def test_fallback_scene_is_indoor(self) -> None:
        """Fallback response should have scene=indoor."""
        from app.services.agent import _parse_response
        from app.models.conversation import Scene

        result = _parse_response("invalid json")

        assert result.scene == Scene.indoor

    def test_fallback_affinity_level_is_zero(self) -> None:
        """Fallback response should have affinity_level=0."""
        from app.services.agent import _parse_response

        result = _parse_response("invalid json")

        assert result.affinity_level == 0

    def test_empty_string_returns_fallback(self) -> None:
        """Empty string should trigger fallback with '...' as dialogue."""
        from app.services.agent import _parse_response

        result = _parse_response("")

        assert result.dialogue == "..."

    def test_invalid_json_uses_text_as_dialogue(self) -> None:
        """Non-JSON text should be used as dialogue in the fallback."""
        from app.services.agent import _parse_response

        result = _parse_response("エラーテキスト")

        assert result.dialogue == "エラーテキスト"

    def test_missing_required_field_returns_fallback(self) -> None:
        """JSON missing required fields should trigger fallback."""
        import json
        from app.services.agent import _parse_response
        from app.models.conversation import Emotion

        # 'affinity_level' is required but omitted
        payload = json.dumps(
            {"dialogue": "hi", "narration": "", "emotion": "happy", "scene": "cafe"}
        )

        result = _parse_response(payload)

        assert result.emotion == Emotion.neutral  # fallback

    def test_out_of_range_affinity_returns_fallback(self) -> None:
        """affinity_level outside 0-100 should fail validation → fallback."""
        import json
        from app.services.agent import _parse_response

        payload = json.dumps(
            {
                "dialogue": "hi",
                "narration": "",
                "emotion": "happy",
                "scene": "cafe",
                "affinity_level": 999,
            }
        )

        result = _parse_response(payload)

        assert result.affinity_level == 0  # fallback

    def test_logs_error_on_parse_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Parse failure should emit an error-level log."""
        import logging
        from app.services.agent import _parse_response

        with caplog.at_level(logging.ERROR, logger="app.services.agent"):
            _parse_response("not valid json at all")

        assert any("Failed to parse" in r.message for r in caplog.records)
