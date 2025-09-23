"""Abstract base class for configuration file management."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypedDict


class ProsemarkConfig(TypedDict, total=False):
    """Type definition for prosemark configuration values."""

    editor: str
    daily_dir: str
    binder_file: str


class ConfigPort(ABC):
    """Abstract base class for configuration file management.

    Defines the contract for creating and managing prosemark configuration files.
    This abstract base class enables:

    * Clean separation between business logic and configuration I/O
    * Testable configuration operations through dependency injection
    * Support for different configuration storage mechanisms
    * Hexagonal architecture compliance by isolating configuration concerns
    * Future extensibility to different configuration formats or sources

    The MVP uses this for creating default .prosemark.yml configuration files
    during project initialization with standard YAML format and default values.

    Examples:
        >>> class TestConfigPort(ConfigPort):
        ...     def create_default_config(self, config_path: Path) -> None:
        ...         # Test implementation
        ...         pass
        >>> config = TestConfigPort()
        >>> config.create_default_config(Path('.prosemark.yml'))

    """

    @abstractmethod
    def create_default_config(self, config_path: Path) -> None:
        """Create default .prosemark.yml configuration file.

        Writes a new configuration file with default values for all
        prosemark settings. The configuration includes editor settings,
        file naming patterns, binder management markers, and other
        project-specific defaults.

        Args:
            config_path: Path where configuration file should be created

        Raises:
            FilesystemError: If configuration file cannot be written
            NotImplementedError: If not implemented by a concrete subclass

        """
        msg = 'Subclasses must implement create_default_config()'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

    @abstractmethod
    def config_exists(self, config_path: Path) -> bool:
        """Check if configuration file already exists.

        Determines whether a prosemark configuration file is present
        at the specified path. Used during project initialization to
        detect existing projects and prevent conflicts.

        Args:
            config_path: Path to check for configuration file existence

        Returns:
            True if configuration file exists, False otherwise

        Raises:
            NotImplementedError: If not implemented by a concrete subclass

        """
        msg = 'Subclasses must implement config_exists()'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

    @abstractmethod
    def get_default_config_values(self) -> ProsemarkConfig:
        """Return default configuration values as dictionary.

        Provides the standard default configuration values that would be
        written to a new .prosemark.yml file. Useful for testing and
        validation of configuration content.

        Returns:
            Dictionary containing default configuration key-value pairs

        Raises:
            NotImplementedError: If not implemented by a concrete subclass

        """
        msg = 'Subclasses must implement get_default_config_values()'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover
