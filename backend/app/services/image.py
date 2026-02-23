"""Image generation service."""
from app.models.conversation import Emotion, Scene
from app.models.image import CharacterConfig, ImageGenerationRequest

EMOTION_PROMPTS: dict[Emotion, str] = {
    Emotion.happy: "happy expression, bright smile",
    Emotion.sad: "sad expression, downcast eyes",
    Emotion.neutral: "neutral expression, calm",
    Emotion.surprised: "surprised expression, wide eyes",
    Emotion.thoughtful: "thoughtful expression, looking away",
    Emotion.embarrassed: "embarrassed expression, blushing cheeks",
    Emotion.excited: "excited expression, sparkling eyes",
    Emotion.angry: "angry expression, furrowed brows",
}

SCENE_PROMPTS: dict[Scene, str] = {
    Scene.indoor: "indoor background, cozy room",
    Scene.outdoor: "outdoor background, clear sky",
    Scene.cafe: "cafe background, warm lighting",
    Scene.park: "park background, green trees",
    Scene.school: "school background, classroom",
    Scene.home: "home room background, comfortable",
}


def _affinity_prompt(affinity_level: int) -> str:
    if affinity_level <= 30:
        return "solo, formal atmosphere, reserved, shy"
    elif affinity_level <= 70:
        return "solo, friendly and warm atmosphere, natural smile"
    else:
        return "solo, close and intimate, warm smile directed at viewer, soft gaze"


class ImageGenerationService:
    """Handles image prompt building and generation via Gemini Image API."""

    def __init__(self, character_config: CharacterConfig) -> None:
        self.character_config = character_config

    def build_prompt(self, request: ImageGenerationRequest) -> str:
        """Build a Gemini Image API prompt from request and character config."""
        emotion_desc = EMOTION_PROMPTS[request.emotion]
        scene_desc = SCENE_PROMPTS[request.scene]
        affinity_desc = _affinity_prompt(request.affinity_level)
        return (
            f"{self.character_config.appearance_prompt}, "
            f"{emotion_desc}, {scene_desc}, {affinity_desc}"
        )
