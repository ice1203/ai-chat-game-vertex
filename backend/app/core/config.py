"""Configuration management using pydantic-settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GCP settings (required)
    gcp_project_id: str
    vertex_ai_location: str
    agent_engine_id: str

    # Vertex AI staging bucket
    staging_bucket: str = ""

    # Application settings
    app_name: str = "ai-chat-game-vertex"
    user_id: str = "demo_user_001"

    # Server settings
    backend_host: str = "localhost"
    backend_port: int = 8000
    frontend_port: int = 3000


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
