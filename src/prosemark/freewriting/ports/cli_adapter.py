"""CLI adapter port interfaces for freewriting command interface.

This module defines the port interfaces for the command-line interface
components of the freewriting feature.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.freewriting.domain.models import SessionConfig
    from prosemark.freewriting.ports.tui_adapter import TUIAdapterPort, TUIConfig


class CLIAdapterPort(ABC):
    """Port interface for CLI operations.

    This port defines the contract for command-line interface operations
    such as argument parsing and TUI launching.
    """

    @property
    @abstractmethod
    def tui_adapter(self) -> TUIAdapterPort:
        """TUI adapter instance for launching interface.

        Returns:
            The TUI adapter instance used by this CLI adapter.

        """

    @abstractmethod
    def parse_arguments(
        self,
        node: str | None,
        title: str | None,
        word_count_goal: int | None,
        time_limit: int | None,
        theme: str,
        current_directory: str | None,
    ) -> SessionConfig:
        """Parse and validate CLI arguments into session configuration.

        Args:
            node: Optional UUID of target node.
            title: Optional session title.
            word_count_goal: Optional word count target.
            time_limit: Optional time limit in seconds.
            theme: UI theme name.
            current_directory: Working directory override.

        Returns:
            Validated SessionConfig object.

        Raises:
            ValidationError: If any arguments are invalid.

        """

    @abstractmethod
    def validate_node_argument(self, node: str | None) -> str | None:
        """Validate node UUID argument.

        Args:
            node: Node UUID string to validate.

        Returns:
            Validated UUID string or None.

        Raises:
            ValidationError: If UUID format is invalid.

        """

    @abstractmethod
    def create_tui_config(self, theme: str) -> TUIConfig:
        """Create TUI configuration from CLI arguments.

        Args:
            theme: Theme name from CLI.

        Returns:
            TUIConfig object with appropriate settings.

        Raises:
            ValidationError: If theme is not available.

        """

    @abstractmethod
    def launch_tui(self, session_config: SessionConfig, tui_config: TUIConfig) -> int:
        """Launch the TUI interface with given configuration.

        Args:
            session_config: Session configuration.
            tui_config: TUI configuration.

        Returns:
            Exit code (0 for success, non-zero for error).

        """

    @abstractmethod
    def handle_cli_error(self, error: Exception) -> int:
        """Handle CLI-level errors and display appropriate messages.

        Args:
            error: The exception that occurred.

        Returns:
            Appropriate exit code.

        """


class CommandValidationPort(ABC):
    """Port interface for command validation operations.

    This port defines the contract for validating command arguments
    and checking system capabilities.
    """

    @abstractmethod
    def validate_write_command_args(
        self,
        node: str | None,
        title: str | None,
        word_count_goal: int | None,
        time_limit: int | None,
    ) -> dict[str, str | int | bool]:
        """Validate arguments for the write command.

        Args:
            node: Optional node UUID.
            title: Optional title.
            word_count_goal: Optional word count goal.
            time_limit: Optional time limit.

        Returns:
            Dictionary of validation results and normalized values.

        Raises:
            ValidationError: If validation fails.

        """

    @abstractmethod
    def get_available_themes(self) -> list[str]:
        """Get list of available UI themes.

        Returns:
            List of theme names.

        """

    @abstractmethod
    def get_current_working_directory(self) -> str:
        """Get current working directory.

        Returns:
            Absolute path to current directory.

        """

    @abstractmethod
    def check_directory_writable(self, directory: str) -> bool:
        """Check if directory is writable.

        Args:
            directory: Directory path to check.

        Returns:
            True if writable, False otherwise.

        """


# CLI-specific data structures
@dataclass(frozen=True)
class CLIContext:
    """Context information for CLI operations."""

    command_name: str
    arguments: dict[str, str | int | bool]
    working_directory: str
    user_config: dict[str, str]
    debug_mode: bool


@dataclass(frozen=True)
class ValidationResult:
    """Result of argument validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    normalized_values: dict[str, str | int | bool]


@dataclass(frozen=True)
class CLIResponse:
    """Response from CLI operations."""

    exit_code: int
    message: str | None
    error_details: dict[str, str] | None
