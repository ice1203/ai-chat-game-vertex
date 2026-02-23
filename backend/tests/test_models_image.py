"""Tests for image generation data models (Task 2.2)."""
import pytest
from pydantic import ValidationError

from app.models.conversation import Emotion, Scene
from app.models.image import CharacterConfig, ImageGenerationRequest


class TestImageGenerationRequest:
    """Tests for ImageGenerationRequest model."""

    def _make_request(self, **kwargs: object) -> ImageGenerationRequest:
        defaults: dict[str, object] = {
            "emotion": Emotion.happy,
            "scene": Scene.cafe,
            "affinity_level": 50,
        }
        defaults.update(kwargs)
        return ImageGenerationRequest(**defaults)  # type: ignore[arg-type]

    def test_valid_request(self) -> None:
        """Should create a valid request."""
        req = self._make_request()
        assert req.emotion == Emotion.happy
        assert req.scene == Scene.cafe
        assert req.affinity_level == 50

    def test_all_emotions_accepted(self) -> None:
        """All Emotion enum values should be accepted."""
        for emotion in Emotion:
            req = self._make_request(emotion=emotion)
            assert req.emotion == emotion

    def test_all_scenes_accepted(self) -> None:
        """All Scene enum values should be accepted."""
        for scene in Scene:
            req = self._make_request(scene=scene)
            assert req.scene == scene

    def test_affinity_level_min_boundary(self) -> None:
        """Affinity level of 0 should be valid."""
        req = self._make_request(affinity_level=0)
        assert req.affinity_level == 0

    def test_affinity_level_max_boundary(self) -> None:
        """Affinity level of 100 should be valid."""
        req = self._make_request(affinity_level=100)
        assert req.affinity_level == 100

    def test_affinity_level_below_min_rejected(self) -> None:
        """Affinity level below 0 should be rejected."""
        with pytest.raises(ValidationError):
            self._make_request(affinity_level=-1)

    def test_affinity_level_above_max_rejected(self) -> None:
        """Affinity level above 100 should be rejected."""
        with pytest.raises(ValidationError):
            self._make_request(affinity_level=101)

    def test_invalid_emotion_rejected(self) -> None:
        """Invalid emotion string should be rejected."""
        with pytest.raises(ValidationError):
            self._make_request(emotion="joyful")

    def test_invalid_scene_rejected(self) -> None:
        """Invalid scene string should be rejected."""
        with pytest.raises(ValidationError):
            self._make_request(scene="beach")

    def test_all_fields_required(self) -> None:
        """All fields are required."""
        with pytest.raises(ValidationError):
            ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe)  # type: ignore[call-arg]


class TestCharacterConfig:
    """Tests for CharacterConfig model."""

    def _make_config(self, **kwargs: object) -> CharacterConfig:
        defaults: dict[str, object] = {
            "name": "さくら",
            "personality": "明るく元気な女の子",
            "appearance_prompt": "anime style girl, long black hair, blue eyes, school uniform",
        }
        defaults.update(kwargs)
        return CharacterConfig(**defaults)  # type: ignore[arg-type]

    def test_valid_config(self) -> None:
        """Should create a valid character config."""
        config = self._make_config()
        assert config.name == "さくら"
        assert config.personality == "明るく元気な女の子"
        assert config.appearance_prompt == "anime style girl, long black hair, blue eyes, school uniform"

    def test_name_required(self) -> None:
        """name is required."""
        with pytest.raises(ValidationError):
            CharacterConfig(
                personality="明るく元気な女の子",
                appearance_prompt="anime style girl",
            )

    def test_personality_required(self) -> None:
        """personality is required."""
        with pytest.raises(ValidationError):
            CharacterConfig(
                name="さくら",
                appearance_prompt="anime style girl",
            )

    def test_appearance_prompt_required(self) -> None:
        """appearance_prompt is required."""
        with pytest.raises(ValidationError):
            CharacterConfig(
                name="さくら",
                personality="明るく元気な女の子",
            )

    def test_load_from_dict(self) -> None:
        """Should load from a dict (as when parsing character.json)."""
        data = {
            "name": "さくら",
            "personality": "明るく元気な女の子",
            "appearance_prompt": "anime style girl, long black hair",
        }
        config = CharacterConfig(**data)
        assert config.name == "さくら"
