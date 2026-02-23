"""Tests for ImageGenerationService.generate_image() - Task 5.2."""
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from app.models.conversation import Emotion, Scene
from app.models.image import CharacterConfig, ImageGenerationRequest
from app.services.image import ImageGenerationService

CHARACTER_CONFIG = CharacterConfig(
    name="Hana",
    personality="明るく元気な女の子",
    appearance_prompt="anime style girl, long black hair, blue eyes, school uniform",
)


@pytest.fixture
def images_dir(tmp_path: Path) -> Path:
    d = tmp_path / "images"
    d.mkdir()
    return d


@pytest.fixture
def service(images_dir: Path) -> ImageGenerationService:
    return ImageGenerationService(
        character_config=CHARACTER_CONFIG,
        project_id="test-project",
        location="us-central1",
        images_dir=images_dir,
    )


class TestGenerateImage:
    """Tests for ImageGenerationService.generate_image()."""

    def test_returns_file_path_string(self, service: ImageGenerationService) -> None:
        """generate_image should return a str file path on success."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        with patch.object(service, "_call_image_api", return_value=b"png_data"):
            result = service.generate_image(req)
        assert isinstance(result, str)

    def test_file_has_png_extension(self, service: ImageGenerationService) -> None:
        """Returned file path must end with .png."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        with patch.object(service, "_call_image_api", return_value=b"png_data"):
            result = service.generate_image(req)
        assert result is not None
        assert result.endswith(".png")

    def test_filename_starts_with_emotion_underscore_scene(
        self, service: ImageGenerationService
    ) -> None:
        """Filename must follow {emotion}_{scene}_{timestamp}.png convention."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.park, affinity_level=50)
        with patch.object(service, "_call_image_api", return_value=b"png_data"):
            result = service.generate_image(req)
        assert result is not None
        filename = Path(result).name
        assert filename.startswith("happy_park_")

    def test_filename_timestamp_is_14_digits(self, service: ImageGenerationService) -> None:
        """Timestamp part of filename must be 14 digits (YYYYMMDDHHMMSS)."""
        req = ImageGenerationRequest(emotion=Emotion.sad, scene=Scene.indoor, affinity_level=20)
        with patch.object(service, "_call_image_api", return_value=b"png_data"):
            result = service.generate_image(req)
        assert result is not None
        stem = Path(result).stem  # e.g. "sad_indoor_20260223120000"
        # emotion and scene have no underscore, so split on first two '_' safely
        parts = stem.split("_")
        # parts = ["sad", "indoor", "20260223120000"]
        timestamp = parts[-1]
        assert timestamp.isdigit()
        assert len(timestamp) == 14

    def test_file_is_saved_to_disk_with_correct_content(
        self, service: ImageGenerationService
    ) -> None:
        """Image bytes must be written to the returned file path."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        image_bytes = b"\x89PNG_fake_data"
        with patch.object(service, "_call_image_api", return_value=image_bytes):
            result = service.generate_image(req)
        assert result is not None
        saved_path = Path(result)
        assert saved_path.exists()
        assert saved_path.read_bytes() == image_bytes

    def test_creates_images_dir_if_missing(self, tmp_path: Path) -> None:
        """images_dir is created automatically if it does not exist."""
        missing_dir = tmp_path / "new_images"
        assert not missing_dir.exists()
        svc = ImageGenerationService(
            character_config=CHARACTER_CONFIG,
            project_id="test-project",
            location="us-central1",
            images_dir=missing_dir,
        )
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        with patch.object(svc, "_call_image_api", return_value=b"png_data"):
            result = svc.generate_image(req)
        assert missing_dir.exists()
        assert result is not None

    def test_retries_exactly_once_on_api_error(self, service: ImageGenerationService) -> None:
        """On API error, _call_image_api is called a total of 2 times (original + 1 retry)."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        call_count = 0

        def always_fails(*args: object, **kwargs: object) -> bytes:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("API error")

        with patch.object(service, "_call_image_api", side_effect=always_fails):
            service.generate_image(req)
        assert call_count == 2

    def test_returns_none_after_both_attempts_fail(self, service: ImageGenerationService) -> None:
        """Returns None when both the original attempt and retry fail."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        with patch.object(service, "_call_image_api", side_effect=RuntimeError("API error")):
            result = service.generate_image(req)
        assert result is None

    def test_returns_path_when_retry_succeeds(self, service: ImageGenerationService) -> None:
        """Returns a valid file path when the retry (second attempt) succeeds."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        call_count = 0

        def fail_then_succeed(*args: object, **kwargs: object) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first attempt fails")
            return b"png_data"

        with patch.object(service, "_call_image_api", side_effect=fail_then_succeed):
            result = service.generate_image(req)
        assert call_count == 2
        assert result is not None
        assert result.endswith(".png")

    def test_logs_error_on_each_failed_attempt(
        self, service: ImageGenerationService, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An ERROR log must be emitted for each failed API attempt."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        with caplog.at_level(logging.ERROR):
            with patch.object(service, "_call_image_api", side_effect=RuntimeError("boom")):
                service.generate_image(req)
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1

    def test_no_file_created_when_generation_fails(
        self, service: ImageGenerationService, images_dir: Path
    ) -> None:
        """No PNG file should exist in images_dir when generation fails."""
        req = ImageGenerationRequest(emotion=Emotion.happy, scene=Scene.cafe, affinity_level=50)
        with patch.object(service, "_call_image_api", side_effect=RuntimeError("API error")):
            service.generate_image(req)
        png_files = list(images_dir.glob("*.png"))
        assert len(png_files) == 0
