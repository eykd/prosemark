"""Tests for ConfigPort abstract base class."""

from pathlib import Path

import pytest

from prosemark.ports.config_port import ConfigPort, ProsemarkConfig


class TestConfigPort:
    """Test ConfigPort abstract base class contract."""

    def test_config_port_is_abstract(self) -> None:
        """Test ConfigPort cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ConfigPort()  # type: ignore[abstract]

    def test_config_port_requires_create_default_config_implementation(self) -> None:
        """Test concrete subclass must implement create_default_config."""

        class IncompleteConfigPort(ConfigPort):
            def config_exists(self, config_path: Path) -> bool:
                return False

            def get_default_config_values(self) -> ProsemarkConfig:
                return {}

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteConfigPort()  # type: ignore[abstract]

    def test_config_port_requires_config_exists_implementation(self) -> None:
        """Test concrete subclass must implement config_exists."""

        class IncompleteConfigPort(ConfigPort):
            def create_default_config(self, config_path: Path) -> None:
                pass

            def get_default_config_values(self) -> ProsemarkConfig:
                return {}

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteConfigPort()  # type: ignore[abstract]

    def test_config_port_requires_get_default_config_values_implementation(self) -> None:
        """Test concrete subclass must implement get_default_config_values."""

        class IncompleteConfigPort(ConfigPort):
            def create_default_config(self, config_path: Path) -> None:
                pass

            def config_exists(self, config_path: Path) -> bool:
                return False

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteConfigPort()  # type: ignore[abstract]

    def test_config_port_can_be_implemented(self) -> None:
        """Test complete implementation can be instantiated."""

        class CompleteConfigPort(ConfigPort):
            def create_default_config(self, config_path: Path) -> None:
                pass

            def config_exists(self, config_path: Path) -> bool:
                return False

            def get_default_config_values(self) -> ProsemarkConfig:
                return {}

        # Should not raise
        config_port = CompleteConfigPort()
        assert isinstance(config_port, ConfigPort)
