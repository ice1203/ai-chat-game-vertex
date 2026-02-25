"""Image generation service."""
import logging
from datetime import datetime, timedelta
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

REFERENCE_IMAGE_FILENAME = "reference.png"
REFERENCE_MAX_AGE_DAYS = 30


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
        # In-memory cache keyed by (emotion, scene).
        # Same combination reuses the existing image without calling the API again.
        self._cache: dict[tuple[str, str], str] = {}
        # Reference image for style consistency across generations.
        # Populated from the first successful generation and persisted to disk.
        self._reference_image_path = self.images_dir / REFERENCE_IMAGE_FILENAME
        self._reference_image_bytes: Optional[bytes] = None
        if self._reference_image_path.exists():
            age = datetime.now() - datetime.fromtimestamp(
                self._reference_image_path.stat().st_mtime
            )
            if age < timedelta(days=REFERENCE_MAX_AGE_DAYS):
                self._reference_image_bytes = self._reference_image_path.read_bytes()
                logger.debug("Loaded reference image from %s", self._reference_image_path)
            else:
                logger.info(
                    "Reference image expired (%d days old), will regenerate on next call",
                    age.days,
                )

    def build_prompt(self, request: ImageGenerationRequest, has_reference: bool = False) -> str:
        """Build a Gemini Image API prompt from request and character config.

        When a reference image is available, the prompt instructs the model to keep
        the character's appearance identical and vary only expression/scene/affinity.

        Args:
            request: Image generation parameters.
            has_reference: Whether a reference image will be passed to the API.

        Returns:
            Prompt string to send to the image generation API.
        """
        emotion_desc = self.character_config.emotion_prompts.get(
            request.emotion.value
        ) or EMOTION_PROMPTS[request.emotion]
        scene_desc = SCENE_PROMPTS[request.scene]
        affinity_key = "high" if request.affinity_level > 70 else "mid" if request.affinity_level > 30 else "low"
        affinity_desc = self.character_config.affinity_prompts.get(affinity_key) or _affinity_prompt(request.affinity_level)
        if has_reference:
            return (
                "Keep the character's appearance, hairstyle, eye color, and clothing "
                "exactly as shown in the reference image. "
                f"Change only the expression to: {emotion_desc}. "
                f"Background: {scene_desc}. {affinity_desc}."
            )
        return (
            f"{self.character_config.appearance_prompt}, "
            f"{emotion_desc}, {scene_desc}, {affinity_desc}"
        )

    def generate_image(self, request: ImageGenerationRequest) -> Optional[str]:
        """Generate an image via Gemini 3 Pro Image API and save it locally.

        Returns cached path if the same (emotion, scene) was generated before.
        Retries once on failure. Returns None if both attempts fail.
        After the first successful generation the image is saved as a style
        reference and passed to all subsequent API calls for visual consistency.

        Args:
            request: Image generation parameters (emotion, scene, affinity_level).

        Returns:
            URL path of the saved PNG, or None on failure.
        """
        cache_key = (request.emotion.value, request.scene.value)
        if cache_key in self._cache:
            logger.debug(
                "Image cache hit: %s/%s → %s",
                request.emotion.value,
                request.scene.value,
                self._cache[cache_key],
            )
            return self._cache[cache_key]

        prompt = self.build_prompt(request, has_reference=self._reference_image_bytes is not None)

        for attempt in range(2):
            try:
                image_bytes = self._call_image_api(prompt, self._reference_image_bytes)
                image_path = self._save_image(image_bytes, request.emotion, request.scene)
                self._cache[cache_key] = image_path
                if self._reference_image_bytes is None:
                    self._save_reference_image(image_bytes)
                return image_path
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

    def _save_reference_image(self, image_bytes: bytes) -> None:
        """Persist the first generated image as the style reference.

        Args:
            image_bytes: Raw PNG bytes of the reference image.
        """
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self._reference_image_path.write_bytes(image_bytes)
        self._reference_image_bytes = image_bytes
        logger.info("Saved style reference image to %s", self._reference_image_path)

    def _call_image_api(
        self, prompt: str, reference_image_bytes: Optional[bytes] = None
    ) -> bytes:
        """Call Vertex AI Gemini 3 Pro Image API and return raw PNG bytes.

        When reference_image_bytes is provided the image is included as the first
        part of a multimodal request so the model can maintain visual style consistency.

        Args:
            prompt: The image generation prompt built from character config and state.
            reference_image_bytes: Optional PNG bytes of a previously generated image
                used as a visual style anchor.

        Returns:
            Raw image bytes from the API response.

        Raises:
            RuntimeError: When the API returns no image data.
        """
        from google import genai  # type: ignore[import-untyped]
        from google.genai import types  # type: ignore[import-untyped]

        # Gemini 3 Pro Image is only available on the global endpoint.
        client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location="global",
        )

        if reference_image_bytes is not None:
            contents: object = [
                types.Part(
                    inline_data=types.Blob(data=reference_image_bytes, mime_type="image/png")
                ),
                types.Part(text=prompt),
            ]
        else:
            contents = prompt

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                system_instruction=self.character_config.appearance_prompt,
            ),
        )

        candidates = response.candidates
        if not candidates or candidates[0].content is None:
            raise RuntimeError("No candidates returned by Gemini Image API")

        for part in candidates[0].content.parts:
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
        # Return URL path served by FastAPI /images static mount
        return f"/images/{filename}"
