"""ConversationService: orchestrates one conversation turn (Task 6.1, 6.2)."""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from google.cloud import firestore

from app.models.conversation import (
    ConversationRequest,
    ConversationResponse,
    Message,
    StructuredResponse,
)
from app.core.logging import setup_logging
from app.models.image import ImageGenerationRequest

if TYPE_CHECKING:
    from app.services.agent import ChatAgent
    from app.services.image import ImageGenerationService

logger = setup_logging("conversation")

# Emotion categories for image generation trigger.
# Image is generated only when the category changes, not on every emotion shift.
_EMOTION_CATEGORY: dict[str, str] = {
    "happy":       "positive",
    "excited":     "positive",
    "neutral":     "neutral",
    "thoughtful":  "neutral",
    "sad":         "negative",
    "angry":       "negative",
    "surprised":   "expressive",
    "embarrassed": "expressive",
}

_DEFAULT_CONTEXT: dict[str, Any] = {
    "emotion": "neutral",
    "scene": "indoor",
    "affinity_level": 0,
}


class ConversationService:
    """Orchestrates a single conversation turn.

    Responsibilities:
    1. Pass previous scene/emotion context to ChatAgent each turn
    2. Delegate to ChatAgent for LLM response (StructuredResponse)
    3. Evaluate image generation trigger: needsImageUpdate AND state change
    4. Call ImageGenerationService when triggered
    5. Update in-memory session context with latest state
    6. Return ConversationResponse

    State notes:
    - Persistent state (affinity, memory, sessions) is managed by the
      deployed Agent Engine tools.
    - _session_context holds the latest emotion/scene/affinity_level
      per user_id in memory, used solely for image trigger comparison
      and agent context injection.
    """

    def __init__(
        self,
        chat_agent: "ChatAgent",
        image_service: "ImageGenerationService",
    ) -> None:
        self.chat_agent = chat_agent
        self.image_service = image_service
        self._session_context: dict[str, dict[str, Any]] = {}
        # session_id -> list of messages (user + agent alternating)
        self._history: dict[str, list[Message]] = {}
        self._db = firestore.Client()

    async def send_message(self, request: ConversationRequest) -> ConversationResponse:
        """Orchestrate one conversation turn.

        Args:
            request: Conversation request (user_id, message, session_id).

        Returns:
            ConversationResponse with dialogue, narration, optional image_url,
            session_id and timestamp.
        """
        # --- 1. Retrieve previous context (defaults on first turn) ---
        prev = self._session_context.get(request.user_id, _DEFAULT_CONTEXT)

        # --- 2. Call Agent Engine ---
        structured_response: StructuredResponse
        session_id: str
        structured_response, session_id = await self.chat_agent.run(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            scene=prev["scene"],
            emotion=prev["emotion"],
            affinity_level=prev["affinity_level"],
        )

        logger.info(
            "turn: emotion=%s scene=%s affinity=%d",
            structured_response.emotion.value,
            structured_response.scene.value,
            structured_response.affinity_level,
        )

        # --- 3. Image generation trigger (Task 6.2) ---
        # Trigger when emotion, scene, or affinity_level changed significantly.
        image_path: Optional[str] = None
        if self._validate_image_trigger(structured_response, prev):
            logger.debug("Image trigger fired for user=%s", request.user_id)
            image_path = self.image_service.generate_image(
                ImageGenerationRequest(
                    emotion=structured_response.emotion,
                    scene=structured_response.scene,
                    affinity_level=structured_response.affinity_level,
                )
            )

        # --- 4. Persist affinity to Firestore (replaces update_affinity tool) ---
        self._update_affinity_firestore(request.user_id, structured_response.affinity_level)

        # --- 5. Update in-memory context ---
        self._session_context[request.user_id] = {
            "emotion": structured_response.emotion.value,
            "scene": structured_response.scene.value,
            "affinity_level": structured_response.affinity_level,
        }

        # --- 6. Append to history (per session_id) ---
        now = datetime.now(timezone.utc).isoformat()
        history = self._history.setdefault(session_id, [])
        history.append(Message(role="user", dialogue=request.message, timestamp=now))
        history.append(
            Message(
                role="agent",
                dialogue=structured_response.dialogue,
                narration=structured_response.narration,
                timestamp=now,
            )
        )

        # --- 6. Build response ---
        return ConversationResponse(
            session_id=session_id,
            dialogue=structured_response.dialogue,
            narration=structured_response.narration,
            image_path=image_path,
            timestamp=now,
        )

    def _update_affinity_firestore(self, user_id: str, affinity_level: int) -> None:
        """Persist the latest affinity_level to Firestore.

        Called after each turn instead of the update_affinity Agent Engine tool,
        removing one LLM roundtrip per conversation turn.
        """
        try:
            self._db.collection("user_states").document(user_id).set(
                {"affinity_level": affinity_level}, merge=True
            )
        except Exception as exc:
            logger.error(
                "Failed to update affinity in Firestore: %s",
                exc,
                extra={"service": "ConversationService", "error_type": type(exc).__name__},
            )

    def get_history(self, session_id: str, limit: int = 50) -> list[Message]:
        """Return message history for the given session, newest last.

        Args:
            session_id: Session identifier.
            limit: Maximum number of messages to return (0 = all).

        Returns:
            List of Message objects, capped to `limit`.
        """
        messages = self._history.get(session_id, [])
        return messages[-limit:] if limit > 0 else messages

    def _validate_image_trigger(
        self,
        response: StructuredResponse,
        prev: dict[str, Any],
    ) -> bool:
        """Validate whether a state change justifies image generation.

        Returns True when:
        - Emotion CATEGORY changed (e.g. neutral → positive, not happy → excited)
        - Scene changed
        - Affinity level changed by >= 10 points
        """
        prev_category = _EMOTION_CATEGORY.get(prev["emotion"], "neutral")
        new_category = _EMOTION_CATEGORY.get(response.emotion.value, "neutral")
        if new_category != prev_category:
            return True
        if response.scene.value != prev["scene"]:
            return True
        if abs(response.affinity_level - prev["affinity_level"]) >= 10:
            return True
        return False
