"""ChatAgent service and build_agent factory using ADK framework (Task 3.1, 3.1.5, 3.2)."""
import json
import logging
import os
import time
from typing import Any, Optional

import vertexai
import vertexai.agent_engines  # ensure submodule is loaded for vertexai.agent_engines.get()
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import Gemini
from google.adk.tools.load_memory_tool import LoadMemoryTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import Client
from google.genai import types as genai_types

from app.core.logging import setup_logging
from app.models.conversation import Emotion, Scene, StructuredResponse
from app.models.image import CharacterConfig

logger = setup_logging("agent")

MODEL_ID = "gemini-3-flash-preview"


class _Gemini3Global(Gemini):
    """Gemini 3 wrapper that forces the global endpoint.

    Agent Engine overrides GOOGLE_CLOUD_LOCATION to the deployment region
    (e.g. us-central1), but Gemini 3 models are only available on the global
    endpoint.  By overriding api_client we bypass the environment variable and
    always connect to location='global'.

    Reference: https://github.com/google/adk-python/issues/3628#issuecomment-…
    """

    @property
    def api_client(self) -> Client:
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID", "")
        return Client(
            project=project,
            location="global",
            http_options=genai_types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
            ),
        )


async def _noop_after_agent_callback(callback_context: CallbackContext) -> None:
    """No-op after-agent callback.

    State management (affinity, memory) is handled by the custom tools
    (initialize_session, update_affinity, save_to_memory) running inside
    the Agent Engine, so no post-run callback work is needed here.
    """
    return None


def _build_system_instructions(character_config: CharacterConfig) -> str:
    """Build system instructions for the character agent.

    Includes character settings, field meaning explanations, and tool usage
    guidelines.  JSON schema syntax is intentionally excluded because
    output_schema enforces structure at the API level; duplicating schema
    in the prompt degrades output quality.

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
- affinity_level: コンテキストメッセージの「親密度」を基に、今回の会話の流れを反映した新しい値を設定してください（楽しい会話は+3〜+5、普通は+0〜+2、ネガティブは-3〜-1）。0-100の範囲で返してください。

## ツールの使い方

- セッション開始時は必ずinitialize_sessionを呼んでください（親密度・シーン・感情の初期状態を取得します）。
- {char.name}として覚えておきたいユーザーの好みや印象的な出来事があればsave_to_memoryを呼んでください。保存する内容は必ず**日本語**で書いてください（例：「ユーザーはプログラミングにハマっており、恋愛シミュレーションゲームを作っている」）。

## 重要な注意事項

- 毎ターンのメッセージに現在のシーン・感情・親密度が渡されます。それを参考に応答してください。
- 親密度レベルに応じて口調を変えてください（0〜30: 敬語・よそよそしい、31〜70: 友好的・自然、71〜100: 親しみやすい・フレンドリー）。
- 常にキャラクターとして振る舞い、AIであることを明かさないでください。
"""


def _parse_response(response_text: str) -> StructuredResponse:
    """Parse JSON response text into StructuredResponse with fallback defaults.

    Args:
        response_text: Raw text from the agent's final response event.

    Returns:
        Parsed StructuredResponse, or a safe default on any parse failure.
    """
    try:
        data = json.loads(response_text)
        return StructuredResponse(**data)
    except Exception:
        logger.error("Failed to parse agent response: %.200s", response_text)
        return StructuredResponse(
            dialogue=response_text or "...",
            narration="",
            emotion=Emotion.neutral,
            scene=Scene.indoor,
            affinity_level=0,
        )


def build_agent(
    character_config: CharacterConfig,
    extra_tools: Optional[list] = None,
) -> Agent:
    """Build and return a configured ADK Agent instance.

    This module-level factory is used both by ChatAgent (via deploy_agent.py)
    and by scripts/deploy_agent.py so that the same agent definition is shared
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
        model=_Gemini3Global(model=MODEL_ID),
        instruction=_build_system_instructions(character_config),
        after_agent_callback=_noop_after_agent_callback,
        tools=tools,
        output_schema=StructuredResponse,
    )


class ChatAgent:
    """ADK-based chat agent backed by a deployed Vertex AI Agent Engine.

    Responsibilities:
    - Connect to the deployed Agent Engine via vertexai.agent_engines.get()
    - Manage Sessions (create on first turn, reuse on subsequent turns)
    - Build context-enriched user messages (scene/emotion per turn)
    - Parse structured JSON responses into StructuredResponse

    Note: State updates (affinity, memory) are handled by custom tools
    (initialize_session, update_affinity, save_to_memory) running inside
    the deployed Agent Engine.
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

        self._adk_app: Optional[Any] = None

    def initialize(self) -> None:
        """Connect to the deployed Agent Engine.

        Calls vertexai.init() and then retrieves the deployed AgentEngine
        object via vertexai.agent_engines.get().  Must be called before run().
        """
        vertexai.init(project=self.project_id, location=self.location)
        self._adk_app = vertexai.agent_engines.get(self.agent_engine_id)

    def _build_system_instructions(self) -> str:
        """Build system instructions for this agent's character config.

        Delegates to the module-level _build_system_instructions() so that
        tests on the ChatAgent instance continue to work unchanged.
        """
        return _build_system_instructions(self.character_config)

    def _build_context_message(
        self,
        user_message: str,
        scene: str,
        emotion: str,
        affinity_level: int,
    ) -> str:
        """Build context-enriched user message.

        Dynamic state (scene, emotion, affinity_level) is injected into the
        message each turn so the LLM can reference the current relationship
        level when composing the response and updating affinity_level.

        Args:
            user_message: The original message from the user.
            scene: Current scene identifier (e.g. "cafe", "indoor").
            emotion: Current emotion identifier (e.g. "happy", "neutral").
            affinity_level: Current affinity level (0-100).

        Returns:
            Formatted message combining state context and user message.
        """
        return f"""[現在の状態]
シーン: {scene} / 感情: {emotion} / 親密度: {affinity_level}

[ユーザーメッセージ]
{user_message}"""

    async def run(
        self,
        user_id: str,
        session_id: Optional[str],
        message: str,
        scene: str,
        emotion: str,
        affinity_level: int = 0,
    ) -> tuple[StructuredResponse, str]:
        """Run one conversation turn against the deployed Agent Engine.

        Creates a new session on the first turn (session_id=None) and reuses
        the existing session on subsequent turns.

        Args:
            user_id: The user identifier.
            session_id: Existing session ID, or None to create a new session.
            message: The user's raw message text.
            scene: Current scene identifier (passed as context).
            emotion: Current emotion identifier (passed as context).

        Returns:
            Tuple of (StructuredResponse, session_id).
        """
        assert self._adk_app is not None, "Call initialize() before run()"

        # Create a new session on the first turn.
        # user_id is stored in session state so tools can retrieve it via
        # ToolContext.state["user_id"] without relying on LLM-generated args.
        if session_id is None:
            session = await self._adk_app.async_create_session(
                user_id=user_id,
                state={"user_id": user_id},
            )
            # The deployed Agent Engine returns a dict; local SDK returns a Pydantic model
            session_id = session["id"] if isinstance(session, dict) else session.id

        context_message = self._build_context_message(
            user_message=message,
            scene=scene,
            emotion=emotion,
            affinity_level=affinity_level,
        )

        # Collect the final model text from the streaming response.
        # Deployed Agent Engine events with text from the model have
        # "model_version" at the top level (no content.role=="model").
        response_text = ""
        _t0 = time.perf_counter()
        async for event in self._adk_app.async_stream_query(
            user_id=user_id,
            session_id=session_id,
            message=context_message,
        ):
            if not isinstance(event, dict):
                logger.debug("[stream] non-dict event: %r", event)
                continue

            # --- DEBUG: log every event to diagnose memory/tool issues ---
            _author = event.get("author", "")
            _content = event.get("content", {})
            _parts = _content.get("parts", []) if isinstance(_content, dict) else []
            for _part in _parts:
                if not isinstance(_part, dict):
                    continue
                if "function_call" in _part:
                    _fc = _part["function_call"]
                    logger.debug(
                        "[tool_call] %s args=%s",
                        _fc.get("name"),
                        _fc.get("args"),
                    )
                elif "function_response" in _part:
                    _fr = _part["function_response"]
                    logger.debug(
                        "[tool_response] %s result=%.300s",
                        _fr.get("name"),
                        _fr.get("response"),
                    )
                elif "text" in _part and _author not in ("user",):
                    logger.debug("[text:%s] %.200s", _author, _part["text"])
            # --- END DEBUG ---

            # Model text events carry "model_version"; skip error events
            if "model_version" not in event:
                continue
            logger.info("model_version=%s", event["model_version"])
            for part in event.get("content", {}).get("parts", []):
                if isinstance(part, dict) and "text" in part:
                    response_text = part["text"]

        _elapsed = time.perf_counter() - _t0
        logger.info("Agent Engine call: %.2fs (user=%s)", _elapsed, user_id)

        structured = _parse_response(response_text)
        assert session_id is not None
        return structured, session_id
