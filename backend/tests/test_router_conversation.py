"""Tests for ConversationRouter (Task 7.1, 7.2)."""
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.models.conversation import ConversationResponse, Message


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_response(image_path: Optional[str] = None) -> ConversationResponse:
    return ConversationResponse(
        session_id="test-session-001",
        dialogue="こんにちは！",
        narration="彼女は微笑んだ。",
        image_path=image_path,
        timestamp="2026-02-24T00:00:00+00:00",
    )


@pytest.fixture
def mock_service():
    svc = MagicMock()
    svc.send_message = AsyncMock(return_value=_make_response())
    svc.get_history = MagicMock(return_value=[])
    return svc


@pytest.fixture
def client(mock_service):
    from app.main import app

    app.state.conversation_service = mock_service
    with TestClient(app) as c:
        yield c
    # cleanup
    if hasattr(app.state, "conversation_service"):
        del app.state.conversation_service


# ---------------------------------------------------------------------------
# Task 7.1: POST /api/conversation/send
# ---------------------------------------------------------------------------


class TestSendMessageEndpoint:
    def test_returns_200_on_success(self, client: TestClient) -> None:
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": "hello"},
        )
        assert resp.status_code == 200

    def test_response_has_session_id(self, client: TestClient) -> None:
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": "hello"},
        )
        assert resp.json()["session_id"] == "test-session-001"

    def test_response_has_dialogue(self, client: TestClient) -> None:
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": "hello"},
        )
        assert resp.json()["dialogue"] == "こんにちは！"

    def test_response_has_narration(self, client: TestClient) -> None:
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": "hello"},
        )
        assert resp.json()["narration"] == "彼女は微笑んだ。"

    def test_response_has_timestamp(self, client: TestClient) -> None:
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": "hello"},
        )
        assert "timestamp" in resp.json()

    def test_response_image_path_none_when_not_generated(self, client: TestClient) -> None:
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": "hello"},
        )
        assert resp.json()["image_path"] is None

    def test_response_image_path_when_generated(self, client: TestClient, mock_service) -> None:
        mock_service.send_message = AsyncMock(
            return_value=_make_response(image_path="/data/images/happy_cafe.png")
        )
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": "hello"},
        )
        assert resp.json()["image_path"] == "/data/images/happy_cafe.png"

    def test_passes_request_body_to_service(self, client: TestClient, mock_service) -> None:
        client.post(
            "/api/conversation/send",
            json={"user_id": "my-user", "message": "test msg", "session_id": "sess-1"},
        )
        call_args = mock_service.send_message.call_args
        req = call_args.args[0]
        assert req.user_id == "my-user"
        assert req.message == "test msg"
        assert req.session_id == "sess-1"

    def test_returns_422_on_empty_message(self, client: TestClient) -> None:
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": ""},
        )
        assert resp.status_code == 422

    def test_returns_422_on_missing_user_id(self, client: TestClient) -> None:
        resp = client.post(
            "/api/conversation/send",
            json={"message": "hello"},
        )
        assert resp.status_code == 422

    def test_returns_503_when_no_service(self) -> None:
        """Should return 503 when ConversationService is not initialized."""
        from app.main import app

        # Ensure no service is set
        if hasattr(app.state, "conversation_service"):
            del app.state.conversation_service

        with TestClient(app) as c:
            resp = c.post(
                "/api/conversation/send",
                json={"user_id": "u1", "message": "hello"},
            )
        assert resp.status_code == 503

    def test_returns_503_on_service_error(self, client: TestClient, mock_service) -> None:
        """Should return 503 when service.send_message raises."""
        mock_service.send_message = AsyncMock(side_effect=RuntimeError("Agent Engine error"))
        resp = client.post(
            "/api/conversation/send",
            json={"user_id": "u1", "message": "hello"},
        )
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Task 7.1: GET /api/conversation/history
# ---------------------------------------------------------------------------


class TestGetHistoryEndpoint:
    def test_returns_200_with_session_id(self, client: TestClient) -> None:
        resp = client.get("/api/conversation/history?session_id=sess-1")
        assert resp.status_code == 200

    def test_returns_list(self, client: TestClient) -> None:
        resp = client.get("/api/conversation/history?session_id=sess-1")
        assert isinstance(resp.json(), list)

    def test_returns_messages_from_service(self, client: TestClient, mock_service) -> None:
        mock_service.get_history = MagicMock(
            return_value=[
                Message(role="user", dialogue="hi", timestamp="2026-02-24T00:00:00Z"),
                Message(role="agent", dialogue="hello", narration="nar", timestamp="2026-02-24T00:00:01Z"),
            ]
        )
        resp = client.get("/api/conversation/history?session_id=sess-1")
        data = resp.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "agent"

    def test_passes_session_id_to_service(self, client: TestClient, mock_service) -> None:
        client.get("/api/conversation/history?session_id=my-session")
        mock_service.get_history.assert_called_once_with("my-session", 50)

    def test_limit_param_passed_to_service(self, client: TestClient, mock_service) -> None:
        client.get("/api/conversation/history?session_id=sess-1&limit=10")
        mock_service.get_history.assert_called_once_with("sess-1", 10)

    def test_returns_422_when_no_session_id(self, client: TestClient) -> None:
        resp = client.get("/api/conversation/history")
        assert resp.status_code == 422

    def test_returns_503_when_no_service(self) -> None:
        from app.main import app

        if hasattr(app.state, "conversation_service"):
            del app.state.conversation_service

        with TestClient(app) as c:
            resp = c.get("/api/conversation/history?session_id=sess-1")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Task 7.2: Health check with service status
# ---------------------------------------------------------------------------


class TestHealthCheckWithService:
    def test_health_returns_services_field(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert "services" in resp.json()

    def test_health_agent_engine_ok_when_service_initialized(
        self, client: TestClient
    ) -> None:
        resp = client.get("/health")
        assert resp.json()["services"]["agent_engine"] == "ok"

    def test_health_agent_engine_unavailable_when_no_service(self) -> None:
        from app.main import app

        if hasattr(app.state, "conversation_service"):
            del app.state.conversation_service

        with TestClient(app) as c:
            resp = c.get("/health")
        assert resp.json()["services"]["agent_engine"] == "unavailable"
