"""Tests for JSON structured logging (TDD RED phase - written before implementation)."""
import json
import logging


def test_json_formatter_outputs_valid_json() -> None:
    """JSONFormatter should produce valid JSON output."""
    from app.core.logging import JSONFormatter
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test-service",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_json_formatter_has_required_fields() -> None:
    """Log output must contain timestamp, level, service, message fields."""
    from app.core.logging import JSONFormatter
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="my-service",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="something happened",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)

    assert "timestamp" in parsed
    assert "level" in parsed
    assert "service" in parsed
    assert "message" in parsed
    assert parsed["level"] == "WARNING"
    assert parsed["service"] == "my-service"
    assert parsed["message"] == "something happened"


def test_json_formatter_includes_error_type_on_exception() -> None:
    """Log output should include error_type field when an exception is attached."""
    from app.core.logging import JSONFormatter
    formatter = JSONFormatter()
    try:
        raise ValueError("test error")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="error-service",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="an error occurred",
        args=(),
        exc_info=exc_info,
    )
    output = formatter.format(record)
    parsed = json.loads(output)

    assert "error_type" in parsed
    assert parsed["error_type"] == "ValueError"


def test_setup_logging_returns_logger() -> None:
    """setup_logging() should return a configured Logger instance."""
    from app.core.logging import setup_logging
    logger = setup_logging("test-app")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test-app"
