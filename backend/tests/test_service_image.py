"""Tests for ImageGenerationService prompt building (Task 5.1)."""
import pytest

from app.models.conversation import Emotion, Scene
from app.models.image import CharacterConfig, ImageGenerationRequest
from app.services.image import ImageGenerationService

CHARACTER_CONFIG = CharacterConfig(
    name="Hana",
    personality="明るく元気な女の子",
    appearance_prompt="anime style girl, long black hair, blue eyes, school uniform",
)


@pytest.fixture
def service() -> ImageGenerationService:
    return ImageGenerationService(character_config=CHARACTER_CONFIG)


class TestBuildPrompt:
    """Tests for ImageGenerationService.build_prompt()."""

    def test_prompt_contains_appearance(self, service: ImageGenerationService) -> None:
        """Prompt must contain character appearance_prompt."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        prompt = service.build_prompt(req)
        assert CHARACTER_CONFIG.appearance_prompt in prompt

    def test_prompt_contains_emotion(self, service: ImageGenerationService) -> None:
        """Prompt must contain emotion description."""
        req = ImageGenerationRequest(emotion=Emotion.embarrassed, scene=Scene.cafe, affinity_level=50)
        prompt = service.build_prompt(req)
        assert "embarrassed" in prompt or "blushing" in prompt

    def test_prompt_contains_scene(self, service: ImageGenerationService) -> None:
        """Prompt must contain scene description."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.park, affinity_level=50)
        prompt = service.build_prompt(req)
        assert "park" in prompt

    def test_all_emotions_have_mapping(self, service: ImageGenerationService) -> None:
        """Every Emotion value must produce a non-empty prompt."""
        for emotion in Emotion:
            req = ImageGenerationRequest(emotion=emotion, scene=Scene.indoor, affinity_level=50)
            prompt = service.build_prompt(req)
            assert len(prompt) > 0

    def test_all_scenes_have_mapping(self, service: ImageGenerationService) -> None:
        """Every Scene value must produce a non-empty prompt."""
        for scene in Scene:
            req = ImageGenerationRequest(emotion=Emotion.neutral, scene=scene, affinity_level=50)
            prompt = service.build_prompt(req)
            assert len(prompt) > 0

    def test_low_affinity_prompt(self, service: ImageGenerationService) -> None:
        """Low affinity (0-30) should produce solo/formal tone."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=10)
        prompt = service.build_prompt(req)
        assert "solo" in prompt
        assert any(word in prompt for word in ["formal", "reserved", "shy"])

    def test_mid_affinity_prompt(self, service: ImageGenerationService) -> None:
        """Mid affinity (31-70) should produce friendly/warm tone."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        prompt = service.build_prompt(req)
        assert any(word in prompt for word in ["friendly", "warm"])

    def test_high_affinity_prompt(self, service: ImageGenerationService) -> None:
        """High affinity (71-100) should produce intimate/close tone."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=100)
        prompt = service.build_prompt(req)
        assert any(word in prompt for word in ["intimate", "viewer", "soft gaze"])

    def test_affinity_boundary_30(self, service: ImageGenerationService) -> None:
        """Affinity 30 should be low tier."""
        req_30 = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=30)
        req_31 = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=31)
        assert service.build_prompt(req_30) != service.build_prompt(req_31)

    def test_affinity_boundary_70(self, service: ImageGenerationService) -> None:
        """Affinity 70 should be mid tier, 71 should be high tier."""
        req_70 = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=70)
        req_71 = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=71)
        assert service.build_prompt(req_70) != service.build_prompt(req_71)
