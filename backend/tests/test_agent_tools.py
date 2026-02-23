"""Tests for agent custom tools (Task 3.1.5).

user_id は ToolContext.state から取得するため、
テストでは _make_tool_context() ヘルパーでモックを作成して渡す。
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


def _make_tool_context(user_id: str = "user1") -> MagicMock:
    """Build a minimal ToolContext mock with state["user_id"] set."""
    ctx = MagicMock()
    ctx.state = {"user_id": user_id}
    return ctx


# ---------------------------------------------------------------------------
# initialize_session Tests
# ---------------------------------------------------------------------------


class TestInitializeSession:
    """Tests for initialize_session tool."""

    def _make_db_mock(self, doc_exists: bool, doc_data: dict | None = None) -> MagicMock:
        """Helper to build a mock Firestore DB."""
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = doc_exists
        if doc_data is not None:
            mock_doc.to_dict.return_value = doc_data
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        return mock_db

    @patch("app.services.agent_tools.firestore.Client")
    def test_first_time_returns_zero_affinity(self, mock_client: MagicMock) -> None:
        """First-time call (no Firestore doc) should return affinity_level=0."""
        from app.services.agent_tools import initialize_session

        mock_client.return_value = self._make_db_mock(doc_exists=False)

        result = initialize_session(_make_tool_context())

        assert result["affinity_level"] == 0

    @patch("app.services.agent_tools.firestore.Client")
    def test_first_time_returns_none_days_since(self, mock_client: MagicMock) -> None:
        """First-time call should return days_since_last_session=None."""
        from app.services.agent_tools import initialize_session

        mock_client.return_value = self._make_db_mock(doc_exists=False)

        result = initialize_session(_make_tool_context())

        assert result["days_since_last_session"] is None

    @patch("app.services.agent_tools.firestore.Client")
    def test_first_time_writes_last_updated(self, mock_client: MagicMock) -> None:
        """initialize_session should write last_updated to Firestore."""
        from app.services.agent_tools import initialize_session

        mock_db = self._make_db_mock(doc_exists=False)
        mock_client.return_value = mock_db

        initialize_session(_make_tool_context())

        mock_db.collection.return_value.document.return_value.set.assert_called_once()

    @patch("app.services.agent_tools.firestore.Client")
    def test_returns_valid_scene(self, mock_client: MagicMock) -> None:
        """Should return a scene from the valid set."""
        from app.services.agent_tools import initialize_session

        mock_client.return_value = self._make_db_mock(doc_exists=False)

        result = initialize_session(_make_tool_context())

        assert result["initial_scene"] in ["indoor", "outdoor", "cafe", "park"]

    @patch("app.services.agent_tools.firestore.Client")
    def test_returns_valid_initial_emotion(self, mock_client: MagicMock) -> None:
        """Should return an emotion from the valid session-start pool."""
        from app.services.agent_tools import initialize_session, _INITIAL_EMOTIONS

        mock_client.return_value = self._make_db_mock(doc_exists=False)

        result = initialize_session(_make_tool_context())

        assert result["initial_emotion"] in _INITIAL_EMOTIONS

    @patch("app.services.agent_tools.firestore.Client")
    def test_initial_emotion_excludes_surprised_and_thoughtful(
        self, mock_client: MagicMock
    ) -> None:
        """surprised / thoughtful should not appear as initial emotions."""
        from app.services.agent_tools import _INITIAL_EMOTIONS

        assert "surprised" not in _INITIAL_EMOTIONS
        assert "thoughtful" not in _INITIAL_EMOTIONS

    @patch("app.services.agent_tools.firestore.Client")
    def test_existing_user_returns_saved_affinity(self, mock_client: MagicMock) -> None:
        """Existing user should get their saved affinity_level from Firestore."""
        from app.services.agent_tools import initialize_session

        mock_client.return_value = self._make_db_mock(
            doc_exists=True,
            doc_data={"affinity_level": 50, "last_updated": None},
        )

        result = initialize_session(_make_tool_context())

        assert result["affinity_level"] == 50

    @patch("app.services.agent_tools.firestore.Client")
    def test_calculates_days_since_last_session(self, mock_client: MagicMock) -> None:
        """Should calculate days since last session from last_updated timestamp."""
        from app.services.agent_tools import initialize_session

        last_updated = datetime.now(timezone.utc) - timedelta(days=3)
        mock_client.return_value = self._make_db_mock(
            doc_exists=True,
            doc_data={"affinity_level": 30, "last_updated": last_updated},
        )

        result = initialize_session(_make_tool_context())

        assert result["days_since_last_session"] == 3

    @patch("app.services.agent_tools.firestore.Client")
    def test_no_last_updated_returns_none_days_since(self, mock_client: MagicMock) -> None:
        """If last_updated is None in Firestore, days_since should be None."""
        from app.services.agent_tools import initialize_session

        mock_client.return_value = self._make_db_mock(
            doc_exists=True,
            doc_data={"affinity_level": 20, "last_updated": None},
        )

        result = initialize_session(_make_tool_context())

        assert result["days_since_last_session"] is None

    @patch("app.services.agent_tools.firestore.Client")
    def test_uses_user_id_from_state(self, mock_client: MagicMock) -> None:
        """initialize_session should use user_id from tool_context.state."""
        from app.services.agent_tools import initialize_session

        mock_db = self._make_db_mock(doc_exists=False)
        mock_client.return_value = mock_db

        initialize_session(_make_tool_context(user_id="specific_user"))

        # Verify Firestore was called with the correct user_id
        mock_db.collection.return_value.document.assert_called_with("specific_user")


# ---------------------------------------------------------------------------
# update_affinity Tests
# ---------------------------------------------------------------------------


class TestUpdateAffinity:
    """Tests for update_affinity tool."""

    def _make_db_mock(self, doc_exists: bool, affinity: int = 0) -> MagicMock:
        """Helper to build a Firestore DB mock for update_affinity tests."""
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = doc_exists
        mock_doc.to_dict.return_value = {"affinity_level": affinity}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        return mock_db

    @patch("app.services.agent_tools.firestore.Client")
    def test_adds_delta_to_affinity(self, mock_client: MagicMock) -> None:
        """Should add delta to the current affinity."""
        from app.services.agent_tools import update_affinity

        mock_client.return_value = self._make_db_mock(doc_exists=True, affinity=30)

        result = update_affinity(10, _make_tool_context())

        assert result["affinity_level"] == 40

    @patch("app.services.agent_tools.firestore.Client")
    def test_subtracts_negative_delta(self, mock_client: MagicMock) -> None:
        """Negative delta should decrease affinity."""
        from app.services.agent_tools import update_affinity

        mock_client.return_value = self._make_db_mock(doc_exists=True, affinity=50)

        result = update_affinity(-15, _make_tool_context())

        assert result["affinity_level"] == 35

    @patch("app.services.agent_tools.firestore.Client")
    def test_clamps_at_100(self, mock_client: MagicMock) -> None:
        """Should clamp result at maximum of 100."""
        from app.services.agent_tools import update_affinity

        mock_client.return_value = self._make_db_mock(doc_exists=True, affinity=95)

        result = update_affinity(20, _make_tool_context())

        assert result["affinity_level"] == 100

    @patch("app.services.agent_tools.firestore.Client")
    def test_clamps_at_0(self, mock_client: MagicMock) -> None:
        """Should clamp result at minimum of 0."""
        from app.services.agent_tools import update_affinity

        mock_client.return_value = self._make_db_mock(doc_exists=True, affinity=5)

        result = update_affinity(-20, _make_tool_context())

        assert result["affinity_level"] == 0

    @patch("app.services.agent_tools.firestore.Client")
    def test_saves_new_affinity_to_firestore(self, mock_client: MagicMock) -> None:
        """Should persist the new affinity to Firestore."""
        from app.services.agent_tools import update_affinity

        mock_db = self._make_db_mock(doc_exists=True, affinity=30)
        mock_client.return_value = mock_db

        update_affinity(5, _make_tool_context())

        mock_db.collection.return_value.document.return_value.set.assert_called_once()

    @patch("app.services.agent_tools.firestore.Client")
    def test_no_existing_doc_uses_zero_as_base(self, mock_client: MagicMock) -> None:
        """When no Firestore doc exists, base affinity should be 0."""
        from app.services.agent_tools import update_affinity

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        mock_client.return_value = mock_db

        result = update_affinity(15, _make_tool_context())

        assert result["affinity_level"] == 15

    @patch("app.services.agent_tools.firestore.Client")
    def test_returns_dict_with_affinity_level_key(self, mock_client: MagicMock) -> None:
        """Result dict should contain the 'affinity_level' key."""
        from app.services.agent_tools import update_affinity

        mock_client.return_value = self._make_db_mock(doc_exists=True, affinity=40)

        result = update_affinity(0, _make_tool_context())

        assert "affinity_level" in result

    @patch("app.services.agent_tools.firestore.Client")
    def test_uses_user_id_from_state(self, mock_client: MagicMock) -> None:
        """update_affinity should use user_id from tool_context.state."""
        from app.services.agent_tools import update_affinity

        mock_db = self._make_db_mock(doc_exists=True, affinity=10)
        mock_client.return_value = mock_db

        update_affinity(5, _make_tool_context(user_id="specific_user"))

        mock_db.collection.return_value.document.assert_called_with("specific_user")


# ---------------------------------------------------------------------------
# save_to_memory Tests
# ---------------------------------------------------------------------------


class TestSaveToMemory:
    """Tests for save_to_memory tool."""

    def test_returns_saved_true(self) -> None:
        """Should return saved=True."""
        from app.services.agent_tools import save_to_memory

        result = save_to_memory("ユーザーは猫が好き", _make_tool_context())

        assert result["saved"] is True

    def test_returns_content_in_result(self) -> None:
        """Should echo the content back in the result."""
        from app.services.agent_tools import save_to_memory

        content = "今日はとても楽しかった"
        result = save_to_memory(content, _make_tool_context())

        assert result["content"] == content

    def test_accepts_various_content(self) -> None:
        """Should handle any string content."""
        from app.services.agent_tools import save_to_memory

        for content in ["short", "a" * 500, "日本語のコンテンツ"]:
            result = save_to_memory(content, _make_tool_context())
            assert result["saved"] is True
            assert result["content"] == content
