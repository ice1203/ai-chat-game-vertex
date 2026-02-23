"""Image generation service."""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.conversation import Emotion, Scene
from app.models.image import CharacterConfig, ImageGenerationRequest

logger = logging.getLogger(__name__)

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

    def __init__(
        self,
        character_config: CharacterConfig,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        images_dir: Optional[Path] = None,
    ) -> None:
        self.character_config = character_config
        self.project_id = project_id
        self.location = location
        self.images_dir = Path(images_dir) if images_dir is not None else Path("data/images")

    def build_prompt(self, request: ImageGenerationRequest) -> str:
        """Build a Gemini Image API prompt from request and character config."""
        emotion_desc = EMOTION_PROMPTS[request.emotion]
        scene_desc = SCENE_PROMPTS[request.scene]
        affinity_desc = _affinity_prompt(request.affinity_level)
        return (
            f"{self.character_config.appearance_prompt}, "
            f"{emotion_desc}, {scene_desc}, {affinity_desc}"
        )

    def generate_image(self, request: ImageGenerationRequest) -> Optional[str]:
        """Generate an image via Gemini 3 Pro Image API and save it locally.

        Retries once on failure. Returns the saved file path on success,
        or None if both attempts fail.

        Args:
            request: Image generation parameters (emotion, scene, affinity_level).

        Returns:
            Absolute file path of the saved PNG, or None on failure.
        """
        prompt = self.build_prompt(request)

        for attempt in range(2):
            try:
                image_bytes = self._call_image_api(prompt)
                return self._save_image(image_bytes, request.emotion, request.scene)
            except Exception as exc:
                logger.error(
                    "Image generation failed (attempt %d/2): %s: %s",
                    attempt + 1,
                    type(exc).__name__,
                    exc,
                    extra={
                        "service": "ImageGenerationService",
                        "error_type": type(exc).__name__,
                        "attempt": attempt + 1,
                    },
                )

        return None

    def _call_image_api(self, prompt: str) -> bytes:
        """Call Vertex AI Gemini 3 Pro Image API and return raw PNG bytes.

        Args:
            prompt: The image generation prompt built from character config and state.

        Returns:
            Raw image bytes from the API response.

        Raises:
            RuntimeError: When the API returns no image data.
        """
        from google import genai  # type: ignore[import-untyped]
        from google.genai import types  # type: ignore[import-untyped]

        client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
        )
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                system_instruction=self.character_config.appearance_prompt,
            ),
        )

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                return bytes(part.inline_data.data)

        raise RuntimeError("No image data returned by Gemini Image API")

    def _save_image(self, image_bytes: bytes, emotion: Emotion, scene: Scene) -> str:
        """Save image bytes to the images directory with proper naming convention.

        File name format: {emotion}_{scene}_{YYYYMMDDHHMMSS}.png

        Args:
            image_bytes: Raw PNG bytes to save.
            emotion: Current character emotion (used in filename).
            scene: Current scene (used in filename).

        Returns:
            Absolute file path of the saved image.
        """
        self.images_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{emotion.value}_{scene.value}_{timestamp}.png"
        file_path = self.images_dir / filename
        file_path.write_bytes(image_bytes)
        return str(file_path)
