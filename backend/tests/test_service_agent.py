"""Tests for ChatAgent service (Task 3.1) and build_agent (Task 3.1.5)."""
import pytest
from unittest.mock import MagicMock, patch

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

    def test_includes_affinity_level(self, character_config: CharacterConfig) -> None:
        """Context message should contain the affinity level."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        msg = agent._build_context_message(
            user_message="こんにちは",
            affinity_level=42,
            scene="cafe",
            emotion="happy",
        )

        assert "42" in msg

    def test_includes_scene(self, character_config: CharacterConfig) -> None:
        """Context message should contain the current scene."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        msg = agent._build_context_message(
            user_message="こんにちは",
            affinity_level=10,
            scene="cafe",
            emotion="neutral",
        )

        assert "cafe" in msg

    def test_includes_emotion(self, character_config: CharacterConfig) -> None:
        """Context message should contain the current emotion."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        msg = agent._build_context_message(
            user_message="こんにちは",
            affinity_level=10,
            scene="indoor",
            emotion="happy",
        )

        assert "happy" in msg

    def test_includes_user_message(self, character_config: CharacterConfig) -> None:
        """Context message should contain the original user message."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        user_msg = "好きな食べ物は何ですか？"
        msg = agent._build_context_message(
            user_message=user_msg,
            affinity_level=30,
            scene="cafe",
            emotion="happy",
        )

        assert user_msg in msg

    def test_different_affinity_levels(self, character_config: CharacterConfig) -> None:
        """Context message should correctly reflect different affinity levels."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        msg_low = agent._build_context_message("hello", 0, "indoor", "neutral")
        msg_high = agent._build_context_message("hello", 100, "indoor", "neutral")

        assert "0" in msg_low
        assert "100" in msg_high


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
        """System instructions must NOT include JSON schema syntax (degrades output quality).

        The response_schema in generate_content_config enforces structure at
        API level. Duplicating schema in prompt degrades output quality per
        official documentation.
        """
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        # No JSON schema syntax in instructions
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

        # Field names should appear with explanations (not as JSON schema)
        assert "dialogue" in instructions
        assert "emotion" in instructions

    def test_is_substantial(self, character_config: CharacterConfig) -> None:
        """System instructions should be substantial enough to guide the model."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert len(instructions) > 200


# ---------------------------------------------------------------------------
# ChatAgent Initialization Tests
# ---------------------------------------------------------------------------


class TestChatAgentInitialization:
    """Tests for ChatAgent constructor and initialize() method."""

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

    @patch("app.services.agent.VertexAiSessionService")
    @patch("app.services.agent.VertexAiMemoryBankService")
    @patch("app.services.agent.Runner")
    @patch("app.services.agent.Agent")
    def test_agent_uses_correct_model(
        self,
        mock_agent: object,
        mock_runner: object,
        mock_memory: object,
        mock_session: object,
        character_config: CharacterConfig,
    ) -> None:
        """Agent should be initialized with the specified model ID."""
        from app.services.agent import ChatAgent, MODEL_ID
        from unittest.mock import MagicMock

        chat_agent = ChatAgent(
            "test-project", "us-central1", "test-engine", character_config
        )
        chat_agent.initialize()

        assert isinstance(mock_agent, MagicMock)
        mock_agent.assert_called_once()  # type: ignore[attr-defined]
        assert mock_agent.call_args.kwargs["model"] == MODEL_ID  # type: ignore[attr-defined]

    @patch("app.services.agent.VertexAiSessionService")
    @patch("app.services.agent.VertexAiMemoryBankService")
    @patch("app.services.agent.Runner")
    @patch("app.services.agent.Agent")
    def test_agent_has_json_response_config(
        self,
        mock_agent: object,
        mock_runner: object,
        mock_memory: object,
        mock_session: object,
        character_config: CharacterConfig,
    ) -> None:
        """Agent should be configured with JSON response schema."""
        from app.services.agent import ChatAgent

        chat_agent = ChatAgent(
            "test-project", "us-central1", "test-engine", character_config
        )
        chat_agent.initialize()

        from unittest.mock import MagicMock

        assert isinstance(mock_agent, MagicMock)
        mock_agent.assert_called_once()  # type: ignore[attr-defined]
        config = mock_agent.call_args.kwargs["generate_content_config"]  # type: ignore[attr-defined]
        assert config.response_mime_type == "application/json"
        assert config.response_schema is not None

    @patch("app.services.agent.VertexAiSessionService")
    @patch("app.services.agent.VertexAiMemoryBankService")
    @patch("app.services.agent.Runner")
    @patch("app.services.agent.Agent")
    def test_agent_response_schema_matches_structured_response(
        self,
        mock_agent: object,
        mock_runner: object,
        mock_memory: object,
        mock_session: object,
        character_config: CharacterConfig,
    ) -> None:
        """Agent response schema should match StructuredResponse model schema."""
        from app.services.agent import ChatAgent
        from app.models.conversation import StructuredResponse

        chat_agent = ChatAgent(
            "test-project", "us-central1", "test-engine", character_config
        )
        chat_agent.initialize()

        from unittest.mock import MagicMock

        assert isinstance(mock_agent, MagicMock)
        config = mock_agent.call_args.kwargs["generate_content_config"]  # type: ignore[attr-defined]
        expected_schema = StructuredResponse.model_json_schema()
        assert config.response_schema == expected_schema

    @patch("app.services.agent.VertexAiSessionService")
    @patch("app.services.agent.VertexAiMemoryBankService")
    @patch("app.services.agent.Runner")
    @patch("app.services.agent.Agent")
    def test_agent_has_preload_memory_tool(
        self,
        mock_agent: object,
        mock_runner: object,
        mock_memory: object,
        mock_session: object,
        character_config: CharacterConfig,
    ) -> None:
        """Agent should have PreloadMemoryTool configured."""
        from app.services.agent import ChatAgent
        from google.adk.tools.preload_memory_tool import PreloadMemoryTool

        chat_agent = ChatAgent(
            "test-project", "us-central1", "test-engine", character_config
        )
        chat_agent.initialize()

        from unittest.mock import MagicMock

        assert isinstance(mock_agent, MagicMock)
        tools = mock_agent.call_args.kwargs["tools"]  # type: ignore[attr-defined]
        assert any(isinstance(t, PreloadMemoryTool) for t in tools)

    @patch("app.services.agent.VertexAiSessionService")
    @patch("app.services.agent.VertexAiMemoryBankService")
    @patch("app.services.agent.Runner")
    @patch("app.services.agent.Agent")
    def test_agent_has_load_memory_tool(
        self,
        mock_agent: object,
        mock_runner: object,
        mock_memory: object,
        mock_session: object,
        character_config: CharacterConfig,
    ) -> None:
        """Agent should have LoadMemoryTool configured."""
        from app.services.agent import ChatAgent
        from google.adk.tools.load_memory_tool import LoadMemoryTool

        chat_agent = ChatAgent(
            "test-project", "us-central1", "test-engine", character_config
        )
        chat_agent.initialize()

        from unittest.mock import MagicMock

        assert isinstance(mock_agent, MagicMock)
        tools = mock_agent.call_args.kwargs["tools"]  # type: ignore[attr-defined]
        assert any(isinstance(t, LoadMemoryTool) for t in tools)

    @patch("app.services.agent.VertexAiSessionService")
    @patch("app.services.agent.VertexAiMemoryBankService")
    @patch("app.services.agent.Runner")
    @patch("app.services.agent.Agent")
    def test_memory_service_initialized_with_config(
        self,
        mock_agent: object,
        mock_runner: object,
        mock_memory: object,
        mock_session: object,
        character_config: CharacterConfig,
    ) -> None:
        """VertexAiMemoryBankService should be initialized with project config."""
        from app.services.agent import ChatAgent
        from unittest.mock import MagicMock

        chat_agent = ChatAgent("my-project", "us-central1", "engine-abc", character_config)
        chat_agent.initialize()

        assert isinstance(mock_memory, MagicMock)
        mock_memory.assert_called_once_with(  # type: ignore[attr-defined]
            project="my-project",
            location="us-central1",
            agent_engine_id="engine-abc",
        )

    @patch("app.services.agent.VertexAiSessionService")
    @patch("app.services.agent.VertexAiMemoryBankService")
    @patch("app.services.agent.Runner")
    @patch("app.services.agent.Agent")
    def test_session_service_initialized_with_config(
        self,
        mock_agent: object,
        mock_runner: object,
        mock_memory: object,
        mock_session: object,
        character_config: CharacterConfig,
    ) -> None:
        """VertexAiSessionService should be initialized with project config."""
        from app.services.agent import ChatAgent
        from unittest.mock import MagicMock

        chat_agent = ChatAgent("my-project", "us-central1", "engine-abc", character_config)
        chat_agent.initialize()

        assert isinstance(mock_session, MagicMock)
        mock_session.assert_called_once_with(  # type: ignore[attr-defined]
            project="my-project",
            location="us-central1",
            agent_engine_id="engine-abc",
        )


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

    def test_includes_update_affinity_guideline(
        self, character_config: CharacterConfig
    ) -> None:
        """System instructions should guide the model to call update_affinity."""
        from app.services.agent import ChatAgent

        agent = ChatAgent("p", "l", "e", character_config)
        instructions = agent._build_system_instructions()

        assert "update_affinity" in instructions

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
        """build_agent() should use the configured MODEL_ID."""
        from app.services.agent import build_agent, MODEL_ID

        build_agent(character_config)

        assert mock_agent_cls.call_args.kwargs["model"] == MODEL_ID

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
    def test_has_json_response_config(
        self, mock_agent_cls: MagicMock, character_config: CharacterConfig
    ) -> None:
        """build_agent() should configure JSON response schema."""
        from app.services.agent import build_agent

        build_agent(character_config)

        config = mock_agent_cls.call_args.kwargs["generate_content_config"]
        assert config.response_mime_type == "application/json"
        assert config.response_schema is not None
