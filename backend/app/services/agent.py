"""ChatAgent service and build_agent factory using ADK framework (Task 3.1, 3.1.5)."""
import logging
from typing import Optional

from google.adk import Agent, Runner
from google.adk.agents.callback_context import CallbackContext
from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService
from google.adk.tools.load_memory_tool import LoadMemoryTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.models.conversation import StructuredResponse
from app.models.image import CharacterConfig

logger = logging.getLogger(__name__)

MODEL_ID = "gemini-3.1-pro-preview"


async def _noop_after_agent_callback(_callback_context: CallbackContext) -> None:
    """No-op after-agent callback.

    State management (affinity, memory) is handled by the custom tools
    (initialize_session, update_affinity, save_to_memory) running inside
    the Agent Engine, so no post-run callback work is needed here.
    """
    return None


def _build_system_instructions(character_config: CharacterConfig) -> str:
    """Build system instructions for the character agent.

    Includes character settings, field meaning explanations, and tool usage
    guidelines.  JSON schema syntax is intentionally excluded because the
    response_schema in generate_content_config enforces structure at the API
    level; duplicating schema in the prompt degrades output quality.

    Args:
        character_config: Character configuration (name, personality, etc.).

    Returns:
        System instruction string.
    """
    char = character_config
    return f"""あなたは「{char.name}」というキャラクターです。

## キャラクター設定

名前: {char.name}
性格・背景: {char.personality}

## 応答フィールドの説明

- dialogue: {char.name}として、ユーザーへのセリフを日本語で書いてください。一人称でナチュラルに話してください。
- narration: 三人称の短い情景描写を書いてください（例: 「{char.name}は微笑みながら答えた。」）。
- emotion: このターンの{char.name}の感情を1つ選んでください（happy / sad / neutral / surprised / thoughtful / embarrassed / excited / angry）。
- scene: 現在の場所を1つ選んでください（indoor / outdoor / cafe / park / school / home）。
- affinity_level: update_affinityツールを呼んだ後の現在の親密度レベル（0-100）を入れてください。

## ツールの使い方

- セッション開始時は必ずinitialize_sessionを呼んでください（親密度・シーン・感情の初期状態を取得します）。
- 毎ターン最後にupdate_affinityを呼んでください（delta: 楽しい会話は+3〜+5、普通は0〜+2、ネガティブは-3〜-1）。
- {char.name}として覚えておきたいユーザーの好みや印象的な出来事があればsave_to_memoryを呼んでください。

## 重要な注意事項

- 毎ターンのメッセージに現在の親密度・シーン・感情が渡されます。それを参考に応答してください。
- 親密度レベルに応じて口調を変えてください（0〜30: 敬語・よそよそしい、31〜70: 友好的・自然、71〜100: 親しみやすい・フレンドリー）。
- 常にキャラクターとして振る舞い、AIであることを明かさないでください。
"""


def build_agent(
    character_config: CharacterConfig,
    extra_tools: Optional[list] = None,
) -> Agent:
    """Build and return a configured ADK Agent instance.

    This module-level factory is used both by ChatAgent.initialize() and by
    scripts/deploy_agent.py so that the same agent definition is shared
    between local (Runner-based) and cloud (Agent Engine) contexts.

    Args:
        character_config: Character configuration used for system instructions.
        extra_tools: Additional callable tools to add (e.g. initialize_session,
                     update_affinity, save_to_memory).  Each item may be a
                     plain Python callable or an ADK BaseTool instance.

    Returns:
        Configured ADK Agent ready for use with Runner or deployment.
    """
    tools: list = [PreloadMemoryTool(), LoadMemoryTool()]
    if extra_tools:
        tools.extend(extra_tools)

    return Agent(
        name="character_agent",
        model=MODEL_ID,
        instruction=_build_system_instructions(character_config),
        after_agent_callback=_noop_after_agent_callback,
        tools=tools,
        generate_content_config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=StructuredResponse.model_json_schema(),
        ),
    )


class ChatAgent:
    """ADK-based chat agent with Memory Bank and Session integration.

    Responsibilities:
    - Initialize ADK Agent via build_agent() with correct model, tools, and
      response schema
    - Build context-enriched user messages (affinity/scene/emotion per turn)

    Note: Session management is handled by VertexAiSessionService (Runner).
    State updates (affinity, memory) are handled by custom tools inside the
    deployed Agent Engine.
    """

    def __init__(
        self,
        project_id: str,
        location: str,
        agent_engine_id: str,
        character_config: CharacterConfig,
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.agent_engine_id = agent_engine_id
        self.character_config = character_config

        self._agent: Optional[Agent] = None
        self._runner: Optional[Runner] = None
        self._session_service: Optional[VertexAiSessionService] = None
        self._memory_service: Optional[VertexAiMemoryBankService] = None

    def initialize(self) -> None:
        """Initialize ADK agent, runner, and cloud services.

        Creates VertexAiMemoryBankService and VertexAiSessionService, then
        builds the Agent via build_agent() and wires all three into Runner.
        """
        self._memory_service = VertexAiMemoryBankService(
            project=self.project_id,
            location=self.location,
            agent_engine_id=self.agent_engine_id,
        )
        self._session_service = VertexAiSessionService(
            project=self.project_id,
            location=self.location,
            agent_engine_id=self.agent_engine_id,
        )
        self._agent = build_agent(self.character_config)
        self._runner = Runner(
            agent=self._agent,
            session_service=self._session_service,
            memory_service=self._memory_service,
        )

    def _build_system_instructions(self) -> str:
        """Build system instructions for this agent's character config.

        Delegates to the module-level _build_system_instructions() so that
        tests on the ChatAgent instance continue to work unchanged.
        """
        return _build_system_instructions(self.character_config)

    def _build_context_message(
        self,
        user_message: str,
        affinity_level: int,
        scene: str,
        emotion: str,
    ) -> str:
        """Build context-enriched user message.

        Dynamic state (affinity, scene, emotion) is injected into the message
        each turn rather than into the system prompt, since these values change
        during the conversation.

        Args:
            user_message: The original message from the user.
            affinity_level: Current affinity level (0-100).
            scene: Current scene identifier (e.g. "cafe", "indoor").
            emotion: Current emotion identifier (e.g. "happy", "neutral").

        Returns:
            Formatted message combining state context and user message.
        """
        return f"""[現在の状態]
親密度: {affinity_level} / シーン: {scene} / 感情: {emotion}

[ユーザーメッセージ]
{user_message}"""
