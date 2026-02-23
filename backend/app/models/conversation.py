"""Conversation and message data models."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Emotion(str, Enum):
    """Character emotion states."""

    happy = "happy"
    sad = "sad"
    neutral = "neutral"
    surprised = "surprised"
    thoughtful = "thoughtful"
    embarrassed = "embarrassed"
    excited = "excited"
    angry = "angry"


class Scene(str, Enum):
    """Scene/location types."""

    indoor = "indoor"
    outdoor = "outdoor"
    cafe = "cafe"
    park = "park"
    school = "school"
    home = "home"



class ConversationRequest(BaseModel):
    """Request model for sending a message."""

    user_id: str
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


class ConversationResponse(BaseModel):
    """FastAPI エンドポイントがフロントエンドに返すレスポンス。表示に必要な情報のみ含む。"""

    session_id: str
    dialogue: str
    narration: str
    image_path: Optional[str] = None
    timestamp: str


class StructuredResponse(BaseModel):
    """LLM（ADK経由）が返す構造化JSONのスキーマ。バックエンド内部処理専用。フロントには返さない。"""

    dialogue: str
    narration: str
    emotion: Emotion
    scene: Scene
    needsImageUpdate: bool
    affinityChange: int
    isImportantEvent: bool
    eventSummary: str
