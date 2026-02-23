"""Tests for scripts/deploy_agent.py (Task 0.3)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# scripts/ ディレクトリをパスに追加してインポートできるようにする
_SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# load_character_config Tests
# ---------------------------------------------------------------------------


class TestLoadCharacterConfig:
    """Tests for load_character_config()."""

    def test_returns_character_config(self) -> None:
        """Should return a CharacterConfig with name, personality, appearance_prompt."""
        from deploy_agent import load_character_config
        from app.models.image import CharacterConfig

        config = load_character_config()

        assert isinstance(config, CharacterConfig)

    def test_config_has_name(self) -> None:
        """CharacterConfig should have a non-empty name."""
        from deploy_agent import load_character_config

        config = load_character_config()

        assert config.name

    def test_config_has_personality(self) -> None:
        """CharacterConfig should have a non-empty personality."""
        from deploy_agent import load_character_config

        config = load_character_config()

        assert config.personality

    def test_config_has_appearance_prompt(self) -> None:
        """CharacterConfig should have a non-empty appearance_prompt."""
        from deploy_agent import load_character_config

        config = load_character_config()

        assert config.appearance_prompt


# ---------------------------------------------------------------------------
# deploy() Tests (initial deploy)
# ---------------------------------------------------------------------------


class TestDeploy:
    """Tests for deploy() function."""

    @patch("deploy_agent.vertexai.agent_engines.create")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_calls_vertexai_init(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """deploy() should initialize vertexai with project/location."""
        from deploy_agent import deploy

        mock_deployed = MagicMock()
        mock_deployed.resource_name = "projects/p/locations/l/reasoningEngines/123"
        mock_create.return_value = mock_deployed

        deploy()

        mock_init.assert_called_once()

    @patch("deploy_agent.vertexai.agent_engines.create")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_calls_build_agent_with_custom_tools(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """deploy() should call build_agent with all three custom tools."""
        from deploy_agent import deploy
        from app.services.agent_tools import initialize_session, update_affinity, save_to_memory

        mock_deployed = MagicMock()
        mock_deployed.resource_name = "projects/p/locations/l/reasoningEngines/123"
        mock_create.return_value = mock_deployed

        deploy()

        mock_build.assert_called_once()
        kwargs = mock_build.call_args.kwargs
        assert initialize_session in kwargs["extra_tools"]
        assert update_affinity in kwargs["extra_tools"]
        assert save_to_memory in kwargs["extra_tools"]

    @patch("deploy_agent.vertexai.agent_engines.create")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_wraps_agent_with_adkapp(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """deploy() should wrap the agent with AdkApp."""
        from deploy_agent import deploy

        mock_deployed = MagicMock()
        mock_deployed.resource_name = "projects/p/locations/l/reasoningEngines/123"
        mock_create.return_value = mock_deployed

        deploy()

        mock_adkapp.assert_called_once_with(agent=mock_build.return_value)

    @patch("deploy_agent.vertexai.agent_engines.create")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_create_called_with_requirements(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """deploy() should call create() with the required packages."""
        from deploy_agent import deploy, REQUIREMENTS

        mock_deployed = MagicMock()
        mock_deployed.resource_name = "projects/p/locations/l/reasoningEngines/123"
        mock_create.return_value = mock_deployed

        deploy()

        mock_create.assert_called_once_with(
            mock_adkapp.return_value,
            requirements=REQUIREMENTS,
            extra_packages=["app"],
        )

    @patch("deploy_agent.vertexai.agent_engines.create")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_requirements_include_aiplatform(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """REQUIREMENTS should include google-cloud-aiplatform[agent_engines,adk]."""
        from deploy_agent import REQUIREMENTS

        assert any("google-cloud-aiplatform" in r for r in REQUIREMENTS)

    @patch("deploy_agent.vertexai.agent_engines.create")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_requirements_include_firestore(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """REQUIREMENTS should include google-cloud-firestore."""
        from deploy_agent import REQUIREMENTS

        assert any("google-cloud-firestore" in r for r in REQUIREMENTS)


# ---------------------------------------------------------------------------
# deploy(update=True) Tests
# ---------------------------------------------------------------------------


class TestDeployUpdate:
    """Tests for deploy(update=True) — re-deploy after code changes."""

    @patch("deploy_agent.vertexai.agent_engines.get")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_update_calls_agent_engines_get(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """deploy(update=True) should call vertexai.agent_engines.get()."""
        from deploy_agent import deploy

        deploy(update=True)

        mock_get.assert_called_once()

    @patch("deploy_agent.vertexai.agent_engines.get")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_update_calls_existing_update(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """deploy(update=True) should call existing.update(app)."""
        from deploy_agent import deploy

        mock_existing = MagicMock()
        mock_get.return_value = mock_existing

        deploy(update=True)

        mock_existing.update.assert_called_once_with(
            mock_adkapp.return_value, extra_packages=["app"]
        )

    @patch("deploy_agent.vertexai.agent_engines.create")
    @patch("deploy_agent.vertexai.agent_engines.get")
    @patch("deploy_agent.AdkApp")
    @patch("deploy_agent.build_agent")
    @patch("deploy_agent.vertexai.init")
    def test_update_does_not_call_create(
        self,
        mock_init: MagicMock,
        mock_build: MagicMock,
        mock_adkapp: MagicMock,
        mock_get: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """deploy(update=True) should NOT call vertexai.agent_engines.create()."""
        from deploy_agent import deploy

        deploy(update=True)

        mock_create.assert_not_called()
