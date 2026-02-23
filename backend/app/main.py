"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging

# Setup logging
logger = setup_logging("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize services at startup, clean up at shutdown."""
    settings = get_settings()
    try:
        from app.models.image import CharacterConfig
        from app.services.agent import ChatAgent
        from app.services.conversation import ConversationService
        from app.services.image import ImageGenerationService

        char_path = Path("data/characters/character.json")
        character_config = CharacterConfig.model_validate_json(char_path.read_text())

        chat_agent = ChatAgent(
            project_id=settings.gcp_project_id,
            location=settings.vertex_ai_location,
            agent_engine_id=settings.agent_engine_id,
            character_config=character_config,
        )
        chat_agent.initialize()

        image_service = ImageGenerationService(
            character_config=character_config,
            project_id=settings.gcp_project_id,
            location=settings.vertex_ai_location,
        )

        app.state.conversation_service = ConversationService(
            chat_agent=chat_agent,
            image_service=image_service,
        )
        logger.info("Services initialized successfully")
    except Exception as exc:
        logger.error(
            "Service initialization failed — running in degraded mode",
            exc_info=True,
            extra={"service": "main", "error_type": type(exc).__name__},
        )
        # Continue without services; endpoints return 503 until fixed

    yield
    # Shutdown cleanup (nothing needed for this demo)


# Create FastAPI app
app = FastAPI(
    title="AI Chat Game - Vertex AI Edition",
    description="Stateful dialogue app using Vertex AI Agent Engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.frontend_port}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.conversation import router as conversation_router  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

app.include_router(conversation_router)

# Serve generated images from data/images/ at /images
_images_dir = Path("data/images")
_images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(_images_dir)), name="images")


@app.get("/debug/memory/{user_id}")
async def debug_memory(user_id: str, q: str = "ユーザー") -> dict:
    """Debug endpoint: query Memory Bank directly for a user.

    Returns raw memories stored via save_to_memory to verify that
    PreloadMemoryTool has something to load.

    Example:
        GET /debug/memory/user123
    """
    from google.adk.memory import VertexAiMemoryBankService

    cfg = get_settings()
    project = cfg.gcp_project_id
    location = cfg.vertex_ai_location
    agent_engine_id = cfg.agent_engine_id

    if not agent_engine_id:
        return {"error": "AGENT_ENGINE_ID not set", "memories": []}

    memory_service = VertexAiMemoryBankService(
        project=project,
        location=location,
        agent_engine_id=agent_engine_id,
    )

    try:
        result = await memory_service.search_memory(
            app_name="character_agent",
            user_id=user_id,
            query=q,
        )
        memories = [
            {
                "content": m.content.parts[0].text
                if m.content and m.content.parts
                else str(m),
                "score": getattr(m, "score", None),
            }
            for m in (result.memories if hasattr(result, "memories") else [])
        ]
        logger.info("debug_memory: user=%s count=%d", user_id, len(memories))
        return {"user_id": user_id, "count": len(memories), "memories": memories}
    except Exception as exc:
        logger.error("debug_memory failed: %s", exc, exc_info=True)
        return {"error": str(exc), "memories": []}


@app.get("/health")
async def health_check(request: Request) -> dict:
    """Health check endpoint.

    Reports initialization status of Agent Engine / Conversation service.
    Always returns HTTP 200; check `services.agent_engine` for actual status.
    """
    svc = getattr(request.app.state, "conversation_service", None)
    agent_ok = svc is not None

    logger.info("Health check requested")
    return {
        "status": "ok",
        "version": app.version,
        "services": {
            "agent_engine": "ok" if agent_ok else "unavailable",
        },
    }
