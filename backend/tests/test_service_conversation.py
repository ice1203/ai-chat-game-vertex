"""Tests for ConversationService (Task 6.1, 6.2)."""
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.conversation import ConversationRequest, Emotion, Scene, StructuredResponse
from app.models.image import CharacterConfig, ImageGenerationRequest


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def character_config() -> CharacterConfig:
    return CharacterConfig(
        name="あかり",
        personality="明るく元気な女の子",
        appearance_prompt="anime style girl, long black hair, blue eyes",
    )


def _make_structured(
    emotion: Emotion = Emotion.neutral,
    scene: Scene = Scene.indoor,
    affinity_level: int = 0,
) -> StructuredResponse:
    return StructuredResponse(
        dialogue="こんにちは！",
        narration="あかりは微笑んだ。",
        emotion=emotion,
        scene=scene,
        affinity_level=affinity_level,
    )


def _make_chat_agent_mock(
    structured: Optional[StructuredResponse] = None,
    session_id: str = "session-abc",
) -> MagicMock:
    if structured is None:
        structured = _make_structured()
    mock = MagicMock()
    mock.run = AsyncMock(return_value=(structured, session_id))
    return mock


def _make_image_service_mock(image_path: Optional[str] = "/data/images/test.png") -> MagicMock:
    mock = MagicMock()
    mock.generate_image = MagicMock(return_value=image_path)
    return mock


# ---------------------------------------------------------------------------
# Task 6.1: Construction
# ---------------------------------------------------------------------------


class TestConversationServiceConstruction:
    def test_stores_chat_agent(self) -> None:
        from app.services.conversation import ConversationService

        agent = _make_chat_agent_mock()
        image = _make_image_service_mock()
        svc = ConversationService(chat_agent=agent, image_service=image)
        assert svc.chat_agent is agent

    def test_stores_image_service(self) -> None:
        from app.services.conversation import ConversationService

        svc = ConversationService(chat_agent=_make_chat_agent_mock(), image_service=_make_image_service_mock())
        assert svc.image_service is not None

    def test_session_context_initially_empty(self) -> None:
        from app.services.conversation import ConversationService

        svc = ConversationService(chat_agent=_make_chat_agent_mock(), image_service=_make_image_service_mock())
        assert svc._session_context == {}


# ---------------------------------------------------------------------------
# Task 6.1: send_message — agent call and context passing
# ---------------------------------------------------------------------------


class TestSendMessageOrchestration:
    async def test_calls_chat_agent_run(self) -> None:
        from app.services.conversation import ConversationService

        mock_agent = _make_chat_agent_mock()
        svc = ConversationService(chat_agent=mock_agent, image_service=_make_image_service_mock(None))
        await svc.send_message(ConversationRequest(user_id="u", message="hello"))
        mock_agent.run.assert_called_once()

    async def test_passes_user_id_to_agent(self) -> None:
        from app.services.conversation import ConversationService

        mock_agent = _make_chat_agent_mock()
        svc = ConversationService(chat_agent=mock_agent, image_service=_make_image_service_mock(None))
        await svc.send_message(ConversationRequest(user_id="my-user", message="hi"))
        assert mock_agent.run.call_args.kwargs.get("user_id") == "my-user"

    async def test_passes_message_to_agent(self) -> None:
        from app.services.conversation import ConversationService

        mock_agent = _make_chat_agent_mock()
        svc = ConversationService(chat_agent=mock_agent, image_service=_make_image_service_mock(None))
        await svc.send_message(ConversationRequest(user_id="u", message="test message"))
        assert mock_agent.run.call_args.kwargs.get("message") == "test message"

    async def test_passes_session_id_to_agent(self) -> None:
        from app.services.conversation import ConversationService

        mock_agent = _make_chat_agent_mock()
        svc = ConversationService(chat_agent=mock_agent, image_service=_make_image_service_mock(None))
        await svc.send_message(ConversationRequest(user_id="u", message="m", session_id="sid-123"))
        assert mock_agent.run.call_args.kwargs.get("session_id") == "sid-123"

    async def test_first_turn_passes_default_scene(self) -> None:
        from app.services.conversation import ConversationService

        mock_agent = _make_chat_agent_mock()
        svc = ConversationService(chat_agent=mock_agent, image_service=_make_image_service_mock(None))
        await svc.send_message(ConversationRequest(user_id="u", message="m"))
        assert mock_agent.run.call_args.kwargs.get("scene") == "indoor"

    async def test_first_turn_passes_default_emotion(self) -> None:
        from app.services.conversation import ConversationService

        mock_agent = _make_chat_agent_mock()
        svc = ConversationService(chat_agent=mock_agent, image_service=_make_image_service_mock(None))
        await svc.send_message(ConversationRequest(user_id="u", message="m"))
        assert mock_agent.run.call_args.kwargs.get("emotion") == "neutral"

    async def test_second_turn_passes_previous_scene(self) -> None:
        from app.services.conversation import ConversationService

        first = _make_structured(scene=Scene.cafe, emotion=Emotion.happy)
        mock_agent = _make_chat_agent_mock(structured=first)
        svc = ConversationService(chat_agent=mock_agent, image_service=_make_image_service_mock(None))
        await svc.send_message(ConversationRequest(user_id="u", message="first"))

        mock_agent.run = AsyncMock(return_value=(_make_structured(), "s"))
        await svc.send_message(ConversationRequest(user_id="u", message="second"))
        assert mock_agent.run.call_args.kwargs.get("scene") == "cafe"

    async def test_second_turn_passes_previous_emotion(self) -> None:
        from app.services.conversation import ConversationService

        first = _make_structured(emotion=Emotion.happy, scene=Scene.cafe)
        mock_agent = _make_chat_agent_mock(structured=first)
        svc = ConversationService(chat_agent=mock_agent, image_service=_make_image_service_mock(None))
        await svc.send_message(ConversationRequest(user_id="u", message="first"))

        mock_agent.run = AsyncMock(return_value=(_make_structured(), "s"))
        await svc.send_message(ConversationRequest(user_id="u", message="second"))
        assert mock_agent.run.call_args.kwargs.get("emotion") == "happy"

    async def test_response_fields(self) -> None:
        from app.services.conversation import ConversationService

        structured = StructuredResponse(
            dialogue="やあ！", narration="彼女は笑った。",
            emotion=Emotion.happy, scene=Scene.cafe, affinity_level=10,
        )
        svc = ConversationService(
            chat_agent=_make_chat_agent_mock(structured=structured, session_id="s-99"),
            image_service=_make_image_service_mock(None),
        )
        resp = await svc.send_message(ConversationRequest(user_id="u", message="m"))
        assert resp.session_id == "s-99"
        assert resp.dialogue == "やあ！"
        assert resp.narration == "彼女は笑った。"
        assert resp.timestamp

    async def test_context_updated_after_turn(self) -> None:
        from app.services.conversation import ConversationService

        structured = _make_structured(emotion=Emotion.happy, scene=Scene.park, affinity_level=30)
        svc = ConversationService(
            chat_agent=_make_chat_agent_mock(structured=structured),
            image_service=_make_image_service_mock(None),
        )
        await svc.send_message(ConversationRequest(user_id="user1", message="m"))
        ctx = svc._session_context["user1"]
        assert ctx["emotion"] == "happy"
        assert ctx["scene"] == "park"
        assert ctx["affinity_level"] == 30


# ---------------------------------------------------------------------------
# Task 6.2: Image generation trigger (programmatic state change only)
# ---------------------------------------------------------------------------


class TestImageGenerationTrigger:
    """Trigger = emotion_change OR scene_change OR affinity_change >= 10."""

    async def _run(
        self,
        structured: StructuredResponse,
        prev: Optional[dict[str, Any]] = None,
        image_path: Optional[str] = "/img/test.png",
    ) -> tuple[object, MagicMock]:
        from app.services.conversation import ConversationService

        mock_agent = _make_chat_agent_mock(structured=structured)
        mock_image = _make_image_service_mock(image_path=image_path)
        svc = ConversationService(chat_agent=mock_agent, image_service=mock_image)
        if prev:
            svc._session_context["u"] = prev
        resp = await svc.send_message(ConversationRequest(user_id="u", message="m"))
        return resp, mock_image

    async def test_generates_when_emotion_changes(self) -> None:
        structured = _make_structured(emotion=Emotion.happy, scene=Scene.indoor, affinity_level=0)
        _, mock_image = await self._run(
            structured, prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0}
        )
        mock_image.generate_image.assert_called_once()

    async def test_generates_when_scene_changes(self) -> None:
        structured = _make_structured(emotion=Emotion.neutral, scene=Scene.cafe, affinity_level=0)
        _, mock_image = await self._run(
            structured, prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0}
        )
        mock_image.generate_image.assert_called_once()

    async def test_generates_when_affinity_exceeds_threshold(self) -> None:
        structured = _make_structured(emotion=Emotion.neutral, scene=Scene.indoor, affinity_level=10)
        _, mock_image = await self._run(
            structured, prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0}
        )
        mock_image.generate_image.assert_called_once()

    async def test_generates_when_affinity_decreases_by_threshold(self) -> None:
        structured = _make_structured(emotion=Emotion.neutral, scene=Scene.indoor, affinity_level=0)
        _, mock_image = await self._run(
            structured, prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 10}
        )
        mock_image.generate_image.assert_called_once()

    async def test_no_image_when_nothing_changes(self) -> None:
        structured = _make_structured(emotion=Emotion.neutral, scene=Scene.indoor, affinity_level=5)
        _, mock_image = await self._run(
            structured, prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0}
        )
        mock_image.generate_image.assert_not_called()

    async def test_no_image_when_affinity_change_below_threshold(self) -> None:
        structured = _make_structured(emotion=Emotion.neutral, scene=Scene.indoor, affinity_level=9)
        _, mock_image = await self._run(
            structured, prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0}
        )
        mock_image.generate_image.assert_not_called()

    async def test_exact_threshold_10_triggers(self) -> None:
        structured = _make_structured(emotion=Emotion.neutral, scene=Scene.indoor, affinity_level=10)
        _, mock_image = await self._run(
            structured, prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0}
        )
        mock_image.generate_image.assert_called_once()

    async def test_returns_image_path_when_generated(self) -> None:
        from app.models.conversation import ConversationResponse

        structured = _make_structured(emotion=Emotion.happy)
        resp, _ = await self._run(
            structured,
            prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0},
            image_path="/data/happy_cafe.png",
        )
        assert isinstance(resp, ConversationResponse)
        assert resp.image_path == "/data/happy_cafe.png"

    async def test_image_path_none_when_not_triggered(self) -> None:
        from app.models.conversation import ConversationResponse

        structured = _make_structured()
        resp, _ = await self._run(
            structured,
            prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0},
            image_path=None,
        )
        assert isinstance(resp, ConversationResponse)
        assert resp.image_path is None

    async def test_fallback_none_on_generation_failure(self) -> None:
        from app.models.conversation import ConversationResponse

        structured = _make_structured(emotion=Emotion.happy)
        resp, _ = await self._run(
            structured,
            prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0},
            image_path=None,
        )
        assert isinstance(resp, ConversationResponse)
        assert resp.image_path is None

    async def test_passes_correct_params_to_image_service(self) -> None:
        structured = _make_structured(emotion=Emotion.sad, scene=Scene.park, affinity_level=55)
        _, mock_image = await self._run(
            structured, prev={"emotion": "neutral", "scene": "indoor", "affinity_level": 0}
        )
        req: ImageGenerationRequest = mock_image.generate_image.call_args.args[0]
        assert req.emotion == Emotion.sad
        assert req.scene == Scene.park
        assert req.affinity_level == 55
