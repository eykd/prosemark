# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Fake configuration adapter for testing config management."""

from pathlib import Path

from prosemark.ports.config_port import ConfigPort, ProsemarkConfig


class FakeConfigPort(ConfigPort):
    """In-memory fake implementation of ConfigPort for testing.

    Provides minimal configuration management functionality using memory
    storage instead of filesystem. Tracks which configuration files have
    been created and provides default configuration values.

    This fake maintains a set of paths where configs have been created
    and returns a minimal valid configuration dictionary. It does not
    perform actual file I/O operations.

    Examples:
        >>> config = FakeConfigPort()
        >>> path = Path('/test/.prosemark.yml')
        >>> config.create_default_config(path)
        >>> config.config_exists(path)
        True
        >>> config.get_default_config_values()
        {'editor': 'vim', 'daily_dir': 'daily', 'binder_file': '_binder.md'}

    """

    def __init__(self) -> None:
        """Initialize empty fake configuration port."""
        self._created_configs: set[Path] = set()

    def create_default_config(self, config_path: Path) -> None:
        """Record that a configuration was created at the given path.

        Args:
            config_path: Path where configuration would be created.

        """
        self._created_configs.add(config_path)

    def config_exists(self, config_path: Path) -> bool:
        """Check if configuration was created at the given path.

        Args:
            config_path: Path to check for configuration.

        Returns:
            True if create_default_config was called with this path.

        """
        return config_path in self._created_configs

    def get_default_config_values(self) -> ProsemarkConfig:
        """Return minimal valid default configuration values.

        Returns:
            Dictionary with minimal configuration for testing.

        """
        return {
            'editor': 'vim',
            'daily_dir': 'daily',
            'binder_file': '_binder.md',
        }
