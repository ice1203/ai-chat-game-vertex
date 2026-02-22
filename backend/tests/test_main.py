"""Tests for FastAPI app entry point (TDD RED phase - written before implementation)."""
from fastapi.testclient import TestClient


def test_health_endpoint_returns_200() -> None:
    """Health check endpoint should return HTTP 200."""
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_status_ok() -> None:
    """Health check response should contain status=ok."""
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_app_has_correct_title() -> None:
    """FastAPI app should have the project title."""
    from app.main import app
    assert app.title == "AI Chat Game - Vertex AI Edition"


def test_app_has_cors_middleware() -> None:
    """App should allow requests from frontend origin."""
    from app.main import app
    from starlette.middleware.cors import CORSMiddleware
    # Verify CORSMiddleware is registered in user_middleware
    middleware_classes = [m.cls for m in app.user_middleware]
    assert CORSMiddleware in middleware_classes
