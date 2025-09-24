"""CLI adapter implementation using Typer framework.

This module provides the concrete implementation of the CLI ports
using the Typer framework for command-line interface operations.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import typer

from prosemark.freewriting.adapters.title_handler import process_title
from prosemark.freewriting.domain.exceptions import CLIError, ValidationError
from prosemark.freewriting.domain.models import SessionConfig

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.freewriting.adapters.tui_adapter import TextualTUIAdapter
    from prosemark.freewriting.ports.tui_adapter import TUIConfig

from prosemark.freewriting.ports.cli_adapter import (
    CLIAdapterPort,
    CommandValidationPort,
)
from prosemark.freewriting.ports.tui_adapter import TUIConfig


class TyperCLIAdapter(CLIAdapterPort, CommandValidationPort):
    """Concrete implementation of CLI ports using Typer framework."""

    def __init__(self, tui_adapter: TextualTUIAdapter) -> None:
        """Initialize the Typer CLI adapter.

        Args:
            tui_adapter: TUI adapter instance for launching interface.

        """
        self._tui_adapter = tui_adapter
        self.available_themes = ['dark', 'light', 'auto']

    @property
    def tui_adapter(self) -> TextualTUIAdapter:
        """TUI adapter instance for launching interface.

        Returns:
            The TUI adapter instance used by this CLI adapter.

        """
        return self._tui_adapter

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

        def _validate_directory(directory: str) -> str:
            """Internal helper to validate directory."""
            if not TyperCLIAdapter.check_directory_writable(directory):
                msg = 'Directory is not writable'
                raise ValidationError('current_directory', directory, msg)
            return directory

        def _validate_theme(theme_name: str) -> str:
            """Internal helper to validate theme."""
            if theme_name not in self.available_themes:
                msg = f'Invalid theme. Available themes: {self.available_themes}'
                raise ValidationError('theme', theme_name, msg)
            return theme_name

        try:
            # Validate node UUID if provided
            validated_node = TyperCLIAdapter.validate_node_argument(node)

            # Use current directory if not specified
            current_directory = current_directory or TyperCLIAdapter.get_current_working_directory()

            # Apply validation
            current_directory = _validate_directory(current_directory)
            theme = _validate_theme(theme)

            # Process title for integration test requirements
            if title:
                process_title(title)

            # Create session configuration
            return SessionConfig(
                target_node=validated_node,
                title=title,
                word_count_goal=word_count_goal,
                time_limit=time_limit,
                theme=theme,
                current_directory=current_directory,
            )

        except ValidationError:
            raise
        except Exception as e:
            msg = f'Failed to parse arguments: {e}'
            raise CLIError('freewrite', 'arguments', msg) from e

    @staticmethod
    def validate_node_argument(node: str | None) -> str | None:
        """Validate node UUID argument.

        Args:
            node: Node UUID string to validate.

        Returns:
            Validated UUID string or None.

        Raises:
            ValidationError: If UUID format is invalid.

        """

        def _validate_uuid(uuid_str: str) -> str:
            """Validate UUID format."""
            try:
                parsed_uuid = UUID(uuid_str)
                return str(parsed_uuid)
            except ValueError as e:
                raise ValidationError('node', uuid_str, 'Invalid UUID format') from e

        return _validate_uuid(node) if node is not None else None

    def create_tui_config(self, theme: str) -> TUIConfig:
        """Create TUI configuration from CLI arguments.

        Args:
            theme: Theme name from CLI.

        Returns:
            TUIConfig object with appropriate settings.

        Raises:
            ValidationError: If theme is not available.

        """
        if theme not in self.available_themes:
            msg = f'Theme not available. Available themes: {self.available_themes}'
            raise ValidationError('theme', theme, msg)

        return TUIConfig(
            theme=theme,
            content_height_percent=80,
            input_height_percent=20,
            show_word_count=True,
            show_timer=True,
            auto_scroll=True,
            max_display_lines=1000,
        )

    def launch_tui(self, session_config: SessionConfig, tui_config: TUIConfig) -> int:
        """Launch the TUI interface with given configuration.

        Args:
            session_config: Session configuration.
            tui_config: TUI configuration.

        Returns:
            Exit code (0 for success, non-zero for error).

        """
        try:
            return self.tui_adapter.run_tui(session_config, tui_config)
        except (ValidationError, CLIError) as e:
            return TyperCLIAdapter.handle_cli_error(e)
        except RuntimeError as e:
            # More specific error handling for TUI-related runtime errors
            msg = f'TUI Runtime Error: {e}'
            typer.echo(msg, err=True)
            return 1  # Runtime error
        except KeyboardInterrupt:
            # Handle graceful interruption
            typer.echo('TUI interrupted by user', err=True)
            return 2  # Interrupted

    @staticmethod
    def handle_cli_error(error: Exception) -> int:
        """Handle CLI-level errors and display appropriate messages.

        Args:
            error: The exception that occurred.

        Returns:
            Appropriate exit code.

        """
        # Determine error type and exit code
        if isinstance(error, ValidationError):
            typer.echo(f'Validation Error: {error}', err=True)
            return 2  # Invalid arguments
        if isinstance(error, CLIError):
            typer.echo(f'CLI Error: {error}', err=True)
            return error.exit_code
        typer.echo(f'Unexpected Error: {error}', err=True)
        return 1  # General error

    @staticmethod
    def validate_write_command_args(
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
        errors = []
        normalized_values: dict[str, str | int | bool] = {}

        # Validate node UUID
        if node is not None:
            try:
                validated_node = TyperCLIAdapter.validate_node_argument(node)
                normalized_values['node'] = validated_node or ''
            except ValidationError as e:
                errors.append(f'node: {e.validation_rule}')

        # Validate word count goal
        if word_count_goal is not None:
            if word_count_goal <= 0:
                errors.append('word_count_goal: must be positive')
            else:
                normalized_values['word_count_goal'] = word_count_goal

        # Validate time limit
        if time_limit is not None:
            if time_limit <= 0:
                errors.append('time_limit: must be positive')
            else:
                normalized_values['time_limit'] = time_limit

        # Validate title (optional, but if present should not be empty)
        if title is not None:
            if not title.strip():
                errors.append('title: cannot be empty if provided')
            else:
                normalized_values['title'] = title.strip()

        if errors:
            error_msg = '; '.join(errors)
            raise ValidationError('command_args', str(locals()), error_msg)

        return normalized_values

    def get_available_themes(self) -> list[str]:
        """Get list of available UI themes.

        Returns:
            List of theme names.

        """
        return self.available_themes.copy()

    @staticmethod
    def get_current_working_directory() -> str:
        """Get current working directory.

        Returns:
            Absolute path to current directory.

        """
        return str(Path.cwd())

    @staticmethod
    def check_directory_writable(directory: str) -> bool:
        """Check if directory is writable.

        Args:
            directory: Directory path to check.

        Returns:
            True if writable, False otherwise.

        """

        def _check_create_directory(path: Path) -> bool:
            """Check if directory can be created."""
            try:
                path.mkdir(parents=True, exist_ok=True)
                # If directory was successfully created
                if path.exists():  # pragma: no branch
                    path.rmdir()
            except OSError:
                return False
            return True

        def _check_write_permission(path: Path) -> bool:
            """Check if directory is writable."""
            test_file = path / '.cli_write_test'
            try:
                test_file.write_text('test', encoding='utf-8')
                test_file.unlink()
            except OSError:
                return False
            return True

        try:
            path = Path(directory)

            # If directory doesn't exist, check if we can create it
            if not path.exists():
                return _check_create_directory(path)

            # Test write permission with a temporary file
            return _check_write_permission(path)

        except OSError:  # pragma: no cover
            return False


def create_freewrite_command(
    cli_adapter: TyperCLIAdapter,
) -> typer.Typer:
    """Create the freewrite command using Typer.

    Args:
        cli_adapter: CLI adapter instance.

    Returns:
        Configured Typer application.

    """
    app = typer.Typer(
        name='freewrite',
        help='Write-only freewriting interface for prosemark',
        add_completion=False,
    )

    @app.command()
    def write(
        node: str | None = typer.Argument(
            None,
            help='Target node UUID (optional, creates daily file if not specified)',
        ),
        title: str | None = typer.Option(
            None,
            '--title',
            '-t',
            help='Optional title for the session',
        ),
        word_count_goal: int | None = typer.Option(
            None,
            '--words',
            '-w',
            help='Word count goal for the session',
            min=1,
        ),
        time_limit: int | None = typer.Option(
            None,
            '--time',
            '-m',
            help='Time limit for session in minutes',
            min=1,
        ),
        theme: str = typer.Option(
            'dark',
            '--theme',
            help='UI theme (dark, light, auto)',
        ),
        directory: str | None = typer.Option(
            None,
            '--directory',
            '-d',
            help='Working directory (defaults to current directory)',
        ),
    ) -> None:
        """Start a freewriting session with write-only TUI interface."""
        try:
            # Convert time limit from minutes to seconds
            time_limit_seconds = time_limit * 60 if time_limit else None

            # Validate all arguments
            cli_adapter.validate_write_command_args(node, title, word_count_goal, time_limit_seconds)

            # Parse arguments into session configuration
            session_config = cli_adapter.parse_arguments(
                node=node,
                title=title,
                word_count_goal=word_count_goal,
                time_limit=time_limit_seconds,
                theme=theme,
                current_directory=directory,
            )

            # Create TUI configuration
            tui_config = cli_adapter.create_tui_config(theme)

            # Launch the TUI interface
            exit_code = cli_adapter.launch_tui(session_config, tui_config)

            # Exit with the code returned by TUI
            typer.Exit(exit_code)  # pragma: no cover

        except (ValidationError, CLIError) as e:
            # Let the CLI adapter handle the error and determine exit code
            exit_code = TyperCLIAdapter.handle_cli_error(e)
            raise typer.Exit(exit_code) from e
        except Exception as e:
            # Handle unexpected errors
            exit_code = TyperCLIAdapter.handle_cli_error(e)
            raise typer.Exit(exit_code) from e

    return app


def main() -> None:
    """Main entry point for CLI testing.

    This function is primarily for development and testing.
    In production, the CLI integration would be handled by
    the main prosemark CLI application.

    Note: This function creates minimal stub dependencies for testing.
    Real usage would inject proper implementations from the main app.
    """
    try:
        typer.echo('Error: This CLI requires proper dependency injection from main app')
        typer.echo('Use this adapter through the main prosemark CLI application')
        sys.exit(1)

    except (OSError, KeyboardInterrupt) as e:  # pragma: no cover
        typer.echo(f'Failed to start CLI: {e}', err=True)  # pragma: no cover
        sys.exit(1)  # pragma: no cover


if __name__ == '__main__':  # pragma: no cover
    main()  # pragma: no cover
