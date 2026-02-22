"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging

# Setup logging
logger = setup_logging("main")

# Create FastAPI app
app = FastAPI(
    title="AI Chat Game - Vertex AI Edition",
    description="Stateful dialogue app using Vertex AI Agent Engine",
    version="0.1.0",
)

# CORS configuration (loaded lazily to avoid startup errors in tests)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.frontend_port}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "ok", "version": app.version}
