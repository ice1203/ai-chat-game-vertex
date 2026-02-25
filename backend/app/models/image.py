"""Image generation data models."""
from pydantic import BaseModel, Field

from app.models.conversation import Emotion, Scene


class ImageGenerationRequest(BaseModel):
    """Request model for image generation passed to ImageGenerationService."""

    emotion: Emotion
    scene: Scene
    affinity_level: int = Field(..., ge=0, le=100)


class CharacterConfig(BaseModel):
    """Character configuration loaded from data/characters/character.json."""

    name: str
    personality: str
    appearance_prompt: str
    emotion_prompts: dict[str, str] = Field(default_factory=dict)
    affinity_prompts: dict[str, str] = Field(default_factory=dict)
