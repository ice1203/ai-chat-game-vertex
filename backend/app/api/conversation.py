"""Conversation API router (Task 7.1, 7.2)."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.conversation import ConversationRequest, ConversationResponse, Message
from app.services.conversation import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversation", tags=["conversation"])


def get_conversation_service(request: Request) -> ConversationService:
    """FastAPI dependency: retrieve ConversationService from app.state.

    Returns HTTP 503 if the service was not initialized at startup
    (i.e. Agent Engine is unavailable).
    """
    svc: ConversationService | None = getattr(
        request.app.state, "conversation_service", None
    )
    if svc is None:
        raise HTTPException(
            status_code=503,
            detail="Agent Engine unavailable. Service not initialized.",
        )
    return svc


@router.post("/send", response_model=ConversationResponse)
async def send_message(
    body: ConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Send a user message and receive the agent's response.

    Delegates to ConversationService which orchestrates:
    - ChatAgent (Agent Engine)
    - ImageGenerationService (optional)

    Raises:
        HTTPException 503: Agent Engine error.
        HTTPException 422: Validation error (handled by FastAPI automatically).
    """
    try:
        return await service.send_message(body)
    except Exception as exc:
        logger.error(
            "send_message failed",
            exc_info=True,
            extra={"service": "ConversationRouter", "error_type": type(exc).__name__},
        )
        raise HTTPException(
            status_code=503,
            detail="Agent Engine unavailable. Please try again later.",
        ) from exc


@router.get("/history", response_model=list[Message])
async def get_history(
    session_id: str,
    limit: int = 50,
    service: ConversationService = Depends(get_conversation_service),
) -> list[Message]:
    """Retrieve conversation history for the given session.

    Args:
        session_id: Session identifier (required).
        limit: Maximum number of messages to return (default 50).

    Returns:
        List of Message objects (may be empty if session has no history).
    """
    return service.get_history(session_id, limit)
