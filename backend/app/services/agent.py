"""ChatAgent service using ADK framework (Task 3.1)."""
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
    """No-op callback.

    Memory Bank saving is handled by ConversationService after inspecting
    the structured response (affinityChange, isImportantEvent).
    Running this callback every turn would cause unnecessary API costs.
    """
    return None


class ChatAgent:
    """ADK-based chat agent with Memory Bank and Session integration.

    Responsibilities:
    - Initialize ADK Agent with correct model, tools, and response schema
    - Build system instructions (character config + field meanings + response rules)
    - Build context-enriched user messages (affinity/scene/emotion injected per turn)

    Note: Session management and Memory Bank saving are handled by
    VertexAiSessionService (via Runner) and ConversationService respectively.
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

        Creates VertexAiMemoryBankService and VertexAiSessionService for
        Memory Bank and Session management respectively, then wires them
        into the ADK Runner.
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
        self._agent = Agent(
            name="character_agent",
            model=MODEL_ID,
            instruction=self._build_system_instructions(),
            tools=[PreloadMemoryTool(), LoadMemoryTool()],
            after_agent_callback=_noop_after_agent_callback,
            generate_content_config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StructuredResponse.model_json_schema(),
            ),
        )
        self._runner = Runner(
            agent=self._agent,
            session_service=self._session_service,
            memory_service=self._memory_service,
        )

    def _build_system_instructions(self) -> str:
        """Build system instructions for the character agent.

        Includes only character settings, field meaning explanations, and
        response rules. JSON schema syntax is intentionally excluded because
        the response_schema in generate_content_config enforces structure at
        the API level. Duplicating schema descriptions in the prompt degrades
        output quality per official documentation.
        """
        char = self.character_config
        return f"""あなたは「{char.name}」というキャラクターです。

## キャラクター設定

名前: {char.name}
性格・背景: {char.personality}

## 応答フィールドの説明

- dialogue: {char.name}として、ユーザーへのセリフを日本語で書いてください。一人称でナチュラルに話してください。
- narration: 三人称の短い情景描写を書いてください（例: 「{char.name}は微笑みながら答えた。」）。
- emotion: このターンの{char.name}の感情を1つ選んでください（happy / sad / neutral / surprised / thoughtful / embarrassed / excited / angry）。
- scene: 現在の場所を1つ選んでください（indoor / outdoor / cafe / park / school / home）。
- affinityChange: このターンの会話によって親密度がどれだけ変わったかを整数で返してください（通常は-5〜+10の範囲）。
- isImportantEvent: ユーザーの好みや重要な出来事が判明した場合はtrue、そうでなければfalseを返してください。
- eventSummary: isImportantEventがtrueの場合、記憶すべき出来事を1〜2文で要約してください。falseの場合は空文字列にしてください。

## 重要な注意事項

- 毎ターンのメッセージに現在の親密度・シーン・感情が渡されます。それを参考に応答してください。
- 親密度レベルに応じて口調を変えてください（0〜30: 敬語・よそよそしい、31〜70: 友好的・自然、71〜100: 親しみやすい・フレンドリー）。
- 常にキャラクターとして振る舞い、AIであることを明かさないでください。
"""

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
