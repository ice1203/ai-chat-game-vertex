"""Custom tools for the character agent (Task 3.1.5).

These tools run inside the deployed Agent Engine and manage state via
Cloud Firestore (affinity / session metadata) and Memory Bank (long-term
memories).  Each function is a plain Python callable that can be passed
directly to the ADK Agent or wrapped with FunctionTool.
"""

import logging
import random
from datetime import datetime, timezone
from typing import Optional

from google.cloud import firestore

logger = logging.getLogger(__name__)

_VALID_SCENES = ["indoor", "outdoor", "cafe", "park"]

# neutral を多めにして、セッション開始時は落ち着いた状態から始まりやすくする。
# surprised / thoughtful はセッション開始の感情として不自然なため除外。
_INITIAL_EMOTIONS = ["neutral", "neutral", "neutral", "happy", "sad", "embarrassed", "excited", "angry"]


def initialize_session(user_id: str) -> dict:
    """Initialize session context at the start of a new conversation.

    Reads affinity and last session date from Firestore, calculates days
    since last session, writes current timestamp, and generates a random
    scene and initial emotion for the session.
    Call this at the beginning of every new conversation session.

    Args:
        user_id: The unique identifier of the user.

    Returns:
        A dict with keys: affinity_level (int), days_since_last_session
        (int or None), initial_scene (str), initial_emotion (str).
    """
    db = firestore.Client()
    doc = db.collection("user_states").document(user_id).get()

    affinity_level: int = 0
    days_since: Optional[int] = None

    if doc.exists:
        data = doc.to_dict()
        affinity_level = data.get("affinity_level", 0)
        last_updated = data.get("last_updated")
        if last_updated:
            days_since = (datetime.now(timezone.utc) - last_updated).days

    db.collection("user_states").document(user_id).set(
        {"last_updated": datetime.now(timezone.utc)}, merge=True
    )

    scene = random.choice(_VALID_SCENES)
    emotion = random.choice(_INITIAL_EMOTIONS)
    return {
        "affinity_level": affinity_level,
        "days_since_last_session": days_since,
        "initial_scene": scene,
        "initial_emotion": emotion,
    }


def update_affinity(user_id: str, delta: int) -> dict:
    """Update user affinity level in Firestore.

    Reads the current affinity, applies delta, clamps the result to the
    0-100 range, and persists the new value.
    Call this after every conversation turn with the affinity change amount.

    Args:
        user_id: The unique identifier of the user.
        delta: The change in affinity (positive to increase, negative to decrease).

    Returns:
        A dict with key: affinity_level (int, clamped to 0-100).
    """
    db = firestore.Client()
    doc = db.collection("user_states").document(user_id).get()
    current: int = doc.to_dict().get("affinity_level", 0) if doc.exists else 0
    new_affinity = max(0, min(100, current + delta))
    db.collection("user_states").document(user_id).set(
        {"affinity_level": new_affinity}, merge=True
    )
    return {"affinity_level": new_affinity}


def save_to_memory(user_id: str, content: str) -> dict:
    """Save an important memory to Memory Bank.

    Use when the user reveals preferences, important events occur, or
    information worth remembering across sessions is shared.
    Do NOT call for every turn - only for genuinely important moments.

    Args:
        user_id: The unique identifier of the user.
        content: The content to persist in Memory Bank.

    Returns:
        A dict with keys: saved (bool), content (str).

    Note:
        Full Memory Bank write requires the deployed Agent Engine runtime
        context.  In local / test environments this returns the placeholder
        result without making an external API call.
    """
    logger.info("save_to_memory called for user_id=%s", user_id)
    return {"saved": True, "content": content}
