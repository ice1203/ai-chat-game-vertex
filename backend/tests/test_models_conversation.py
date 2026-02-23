"""Tests for conversation data models (Task 2.1)."""
import pytest
from pydantic import ValidationError

from app.models.conversation import (
    ConversationRequest,
    ConversationResponse,
    Emotion,
    Scene,
    StructuredResponse,
)


# ---------------------------------------------------------------------------
# Enum Tests
# ---------------------------------------------------------------------------


class TestEmotionEnum:
    """Tests for Emotion enum."""

    def test_valid_emotions(self) -> None:
        """All eight emotion values should be valid."""
        assert Emotion.happy == "happy"
        assert Emotion.sad == "sad"
        assert Emotion.neutral == "neutral"
        assert Emotion.surprised == "surprised"
        assert Emotion.thoughtful == "thoughtful"
        assert Emotion.embarrassed == "embarrassed"
        assert Emotion.excited == "excited"
        assert Emotion.angry == "angry"

    def test_emotion_count(self) -> None:
        """Exactly 8 emotions should be defined."""
        assert len(Emotion) == 8

    def test_emotion_is_string(self) -> None:
        """Emotion should be usable as a string."""
        assert isinstance(Emotion.happy, str)


class TestSceneEnum:
    """Tests for Scene enum."""

    def test_valid_scenes(self) -> None:
        """All six scene values should be valid."""
        assert Scene.indoor == "indoor"
        assert Scene.outdoor == "outdoor"
        assert Scene.cafe == "cafe"
        assert Scene.park == "park"
        assert Scene.school == "school"
        assert Scene.home == "home"

    def test_scene_count(self) -> None:
        """Exactly 6 scenes should be defined."""
        assert len(Scene) == 6

    def test_scene_is_string(self) -> None:
        """Scene should be usable as a string."""
        assert isinstance(Scene.cafe, str)



# ---------------------------------------------------------------------------
# ConversationRequest Tests
# ---------------------------------------------------------------------------


class TestConversationRequest:
    """Tests for ConversationRequest model."""

    def test_valid_request(self) -> None:
        """Should create a valid request with required fields."""
        req = ConversationRequest(user_id="user_001", message="こんにちは")
        assert req.user_id == "user_001"
        assert req.message == "こんにちは"
        assert req.session_id is None

    def test_request_with_session_id(self) -> None:
        """Should accept optional session_id."""
        req = ConversationRequest(
            user_id="user_001",
            message="こんにちは",
            session_id="session_abc123",
        )
        assert req.session_id == "session_abc123"

    def test_message_max_length(self) -> None:
        """Message must not exceed 2000 characters."""
        long_message = "a" * 2001
        with pytest.raises(ValidationError):
            ConversationRequest(user_id="user_001", message=long_message)

    def test_message_max_length_boundary(self) -> None:
        """Message of exactly 2000 characters should be valid."""
        boundary_message = "a" * 2000
        req = ConversationRequest(user_id="user_001", message=boundary_message)
        assert len(req.message) == 2000

    def test_empty_message_rejected(self) -> None:
        """Empty message should be rejected."""
        with pytest.raises(ValidationError):
            ConversationRequest(user_id="user_001", message="")

    def test_user_id_required(self) -> None:
        """user_id is required."""
        with pytest.raises(ValidationError):
            ConversationRequest(message="こんにちは")  # type: ignore[call-arg]

    def test_message_required(self) -> None:
        """message is required."""
        with pytest.raises(ValidationError):
            ConversationRequest(user_id="user_001")  # type: ignore[call-arg]



# ---------------------------------------------------------------------------
# ConversationResponse Tests
# ---------------------------------------------------------------------------


class TestConversationResponse:
    """Tests for ConversationResponse model."""

    def _make_response(self, **kwargs: object) -> ConversationResponse:
        """Create a valid ConversationResponse with defaults."""
        defaults: dict[str, object] = {
            "session_id": "session_001",
            "dialogue": "こんにちは！",
            "narration": "彼女は笑顔で挨拶した。",
            "timestamp": "2026-02-23T10:00:00",
        }
        defaults.update(kwargs)
        return ConversationResponse(**defaults)  # type: ignore[arg-type]

    def test_valid_response(self) -> None:
        """Should create a valid response with required fields."""
        resp = self._make_response()
        assert resp.session_id == "session_001"
        assert resp.dialogue == "こんにちは！"
        assert resp.narration == "彼女は笑顔で挨拶した。"
        assert resp.image_path is None
        assert resp.timestamp == "2026-02-23T10:00:00"

    def test_image_path_when_generated(self) -> None:
        """Should accept image_path when image was generated."""
        resp = self._make_response(image_path="/images/happy_cafe_20260223120000.png")
        assert resp.image_path == "/images/happy_cafe_20260223120000.png"

    def test_required_fields(self) -> None:
        """All required fields must be present."""
        with pytest.raises(ValidationError):
            ConversationResponse(session_id="s1")  # type: ignore[call-arg]

    def test_no_emotion_field(self) -> None:
        """ConversationResponse must not expose emotion (backend-only concern)."""
        resp = self._make_response()
        assert not hasattr(resp, "emotion")

    def test_no_scene_field(self) -> None:
        """ConversationResponse must not expose scene (backend-only concern)."""
        resp = self._make_response()
        assert not hasattr(resp, "scene")

    def test_no_affinity_level_field(self) -> None:
        """ConversationResponse must not expose affinity_level (backend-only concern)."""
        resp = self._make_response()
        assert not hasattr(resp, "affinity_level")


# ---------------------------------------------------------------------------
# StructuredResponse Tests
# ---------------------------------------------------------------------------


class TestStructuredResponse:
    """Tests for StructuredResponse (LLM structured output schema).

    Task 3.1.5: affinityChange / isImportantEvent / eventSummary are removed.
    affinity_level (tool-reported current value) is added instead.
    """

    def _make_structured(self, **kwargs: object) -> StructuredResponse:
        """Create a valid StructuredResponse with defaults."""
        defaults: dict[str, object] = {
            "dialogue": "今日はいい天気ですね！",
            "narration": "彼女は窓の外を見た。",
            "emotion": Emotion.happy,
            "scene": Scene.indoor,
            "affinity_level": 50,
        }
        defaults.update(kwargs)
        return StructuredResponse(**defaults)  # type: ignore[arg-type]

    def test_valid_structured_response(self) -> None:
        """Should create a valid StructuredResponse."""
        resp = self._make_structured()
        assert resp.dialogue == "今日はいい天気ですね！"
        assert resp.emotion == Emotion.happy
        assert resp.scene == Scene.indoor
        assert resp.affinity_level == 50

    def test_affinity_level_at_zero(self) -> None:
        """affinity_level=0 (minimum boundary) should be valid."""
        resp = self._make_structured(affinity_level=0)
        assert resp.affinity_level == 0

    def test_affinity_level_at_max(self) -> None:
        """affinity_level=100 (maximum boundary) should be valid."""
        resp = self._make_structured(affinity_level=100)
        assert resp.affinity_level == 100

    def test_affinity_level_below_min_rejected(self) -> None:
        """affinity_level below 0 should be rejected."""
        with pytest.raises(ValidationError):
            self._make_structured(affinity_level=-1)

    def test_affinity_level_above_max_rejected(self) -> None:
        """affinity_level above 100 should be rejected."""
        with pytest.raises(ValidationError):
            self._make_structured(affinity_level=101)

    def test_all_emotions_valid(self) -> None:
        """All emotion values should be accepted."""
        for emotion in Emotion:
            resp = self._make_structured(emotion=emotion)
            assert resp.emotion == emotion

    def test_all_scenes_valid(self) -> None:
        """All scene values should be accepted."""
        for scene in Scene:
            resp = self._make_structured(scene=scene)
            assert resp.scene == scene

    def test_json_schema_generation(self) -> None:
        """Should be able to generate JSON schema (for ADK integration)."""
        schema = StructuredResponse.model_json_schema()
        assert "properties" in schema
        assert "dialogue" in schema["properties"]
        assert "affinity_level" in schema["properties"]

    def test_json_schema_no_removed_fields(self) -> None:
        """Removed fields should not appear in JSON schema."""
        schema = StructuredResponse.model_json_schema()
        assert "affinityChange" not in schema["properties"]
        assert "isImportantEvent" not in schema["properties"]
        assert "eventSummary" not in schema["properties"]
        assert "needsImageUpdate" not in schema["properties"]


