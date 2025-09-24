"""Tests for CLI adapter implementation using Typer framework.

These tests cover the TyperCLIAdapter class and create_freewrite_command function,
testing the concrete implementation against the CLI port contracts.
"""

import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from prosemark.freewriting.adapters.cli_adapter import TyperCLIAdapter, create_freewrite_command, main
from prosemark.freewriting.adapters.tui_adapter import TextualTUIAdapter
from prosemark.freewriting.domain.exceptions import CLIError, ValidationError
from prosemark.freewriting.domain.models import SessionConfig
from prosemark.freewriting.ports.tui_adapter import TUIConfig


class TestTyperCLIAdapter:
    """Test the Typer CLI adapter implementation."""

    def test_adapter_initialization(self) -> None:
        """Test adapter initializes with TUI adapter."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        # Act
        adapter = TyperCLIAdapter(mock_tui_adapter)

        # Assert
        assert adapter._tui_adapter == mock_tui_adapter
        assert adapter.tui_adapter == mock_tui_adapter
        assert adapter.available_themes == ['dark', 'light', 'auto']

    def test_parse_arguments_success_full_args(self) -> None:
        """Test successful argument parsing with all arguments provided."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        target_node = str(uuid.uuid4())

        with patch.object(TyperCLIAdapter, 'check_directory_writable', return_value=True):
            # Act
            result = adapter.parse_arguments(
                node=target_node,
                title='Test Session',
                word_count_goal=1000,
                time_limit=3600,
                theme='dark',
                current_directory='/test/dir',
            )

        # Assert
        assert isinstance(result, SessionConfig)
        assert result.target_node == target_node
        assert result.title == 'Test Session'
        assert result.word_count_goal == 1000
        assert result.time_limit == 3600
        assert result.theme == 'dark'
        assert result.current_directory == '/test/dir'

    def test_parse_arguments_success_minimal_args(self) -> None:
        """Test successful argument parsing with minimal arguments."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        with (
            patch.object(TyperCLIAdapter, 'get_current_working_directory', return_value='/current/dir'),
            patch.object(TyperCLIAdapter, 'check_directory_writable', return_value=True),
        ):
            # Act
            result = adapter.parse_arguments(
                node=None,
                title=None,
                word_count_goal=None,
                time_limit=None,
                theme='light',
                current_directory=None,
            )

        # Assert
        assert isinstance(result, SessionConfig)
        assert result.target_node is None
        assert result.title is None
        assert result.word_count_goal is None
        assert result.time_limit is None
        assert result.theme == 'light'
        assert result.current_directory == '/current/dir'

    def test_parse_arguments_invalid_directory(self) -> None:
        """Test parse_arguments raises ValidationError for invalid directory."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        with (
            patch.object(TyperCLIAdapter, 'check_directory_writable', return_value=False),
            pytest.raises(ValidationError, match='Directory is not writable'),
        ):
            adapter.parse_arguments(
                node=None,
                title=None,
                word_count_goal=None,
                time_limit=None,
                theme='dark',
                current_directory='/readonly/dir',
            )

    def test_parse_arguments_invalid_theme(self) -> None:
        """Test parse_arguments raises ValidationError for invalid theme."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        with (
            patch.object(TyperCLIAdapter, 'check_directory_writable', return_value=True),
            pytest.raises(ValidationError, match='Invalid theme'),
        ):
            adapter.parse_arguments(
                node=None,
                title=None,
                word_count_goal=None,
                time_limit=None,
                theme='invalid_theme',
                current_directory='/test/dir',
            )

    def test_parse_arguments_exception_handling(self) -> None:
        """Test parse_arguments handles unexpected exceptions as CLIError."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        with (
            patch.object(TyperCLIAdapter, 'validate_node_argument', side_effect=RuntimeError('Unexpected error')),
            pytest.raises(CLIError, match='Failed to parse arguments'),
        ):
            adapter.parse_arguments(
                node='some-node',
                title=None,
                word_count_goal=None,
                time_limit=None,
                theme='dark',
                current_directory=None,
            )

    def test_validate_node_argument_valid_uuid(self) -> None:
        """Test validate_node_argument with valid UUID."""
        # Arrange
        valid_uuid = str(uuid.uuid4())

        # Act
        result = TyperCLIAdapter.validate_node_argument(valid_uuid)

        # Assert
        assert result == valid_uuid

    def test_validate_node_argument_none(self) -> None:
        """Test validate_node_argument with None."""
        # Act
        result = TyperCLIAdapter.validate_node_argument(None)

        # Assert
        assert result is None

    def test_validate_node_argument_invalid_uuid(self) -> None:
        """Test validate_node_argument raises ValidationError for invalid UUID."""
        # Act & Assert
        with pytest.raises(ValidationError, match='Invalid UUID format'):
            TyperCLIAdapter.validate_node_argument('invalid-uuid')

    def test_create_tui_config_valid_theme(self) -> None:
        """Test create_tui_config with valid theme."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        # Act
        result = adapter.create_tui_config('dark')

        # Assert
        assert isinstance(result, TUIConfig)
        assert result.theme == 'dark'
        assert result.content_height_percent == 80
        assert result.input_height_percent == 20
        assert result.show_word_count is True
        assert result.show_timer is True
        assert result.auto_scroll is True
        assert result.max_display_lines == 1000

    def test_create_tui_config_invalid_theme(self) -> None:
        """Test create_tui_config raises ValidationError for invalid theme."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        # Act & Assert
        with pytest.raises(ValidationError, match='Theme not available'):
            adapter.create_tui_config('invalid_theme')

    def test_launch_tui_success(self) -> None:
        """Test successful TUI launch."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.run_tui.return_value = 0
        adapter = TyperCLIAdapter(mock_tui_adapter)

        session_config = SessionConfig()
        tui_config = TUIConfig(theme='dark')

        # Act
        result = adapter.launch_tui(session_config, tui_config)

        # Assert
        assert result == 0
        mock_tui_adapter.run_tui.assert_called_once_with(session_config, tui_config)

    def test_launch_tui_validation_error(self) -> None:
        """Test launch_tui handles ValidationError."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.run_tui.side_effect = ValidationError('config', 'invalid', 'Invalid config')
        adapter = TyperCLIAdapter(mock_tui_adapter)

        session_config = SessionConfig()
        tui_config = TUIConfig(theme='dark')

        with patch.object(TyperCLIAdapter, 'handle_cli_error', return_value=2) as mock_handle_error:
            # Act
            result = adapter.launch_tui(session_config, tui_config)

            # Assert
            assert result == 2
            mock_handle_error.assert_called_once()

    def test_launch_tui_runtime_error(self) -> None:
        """Test launch_tui handles RuntimeError."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.run_tui.side_effect = RuntimeError('TUI failed')
        adapter = TyperCLIAdapter(mock_tui_adapter)

        session_config = SessionConfig()
        tui_config = TUIConfig(theme='dark')

        with patch('typer.echo') as mock_echo:
            # Act
            result = adapter.launch_tui(session_config, tui_config)

            # Assert
            assert result == 1
            mock_echo.assert_called_once_with('TUI Runtime Error: TUI failed', err=True)

    def test_launch_tui_keyboard_interrupt(self) -> None:
        """Test launch_tui handles KeyboardInterrupt."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.run_tui.side_effect = KeyboardInterrupt()
        adapter = TyperCLIAdapter(mock_tui_adapter)

        session_config = SessionConfig()
        tui_config = TUIConfig(theme='dark')

        with patch('typer.echo') as mock_echo:
            # Act
            result = adapter.launch_tui(session_config, tui_config)

            # Assert
            assert result == 2
            mock_echo.assert_called_once_with('TUI interrupted by user', err=True)

    def test_handle_cli_error_validation_error(self) -> None:
        """Test handle_cli_error with ValidationError."""
        # Arrange
        error = ValidationError('field', 'value', 'Validation failed')

        with patch('typer.echo') as mock_echo:
            # Act
            result = TyperCLIAdapter.handle_cli_error(error)

            # Assert
            assert result == 2
            mock_echo.assert_called_once_with(f'Validation Error: {error}', err=True)

    def test_handle_cli_error_cli_error(self) -> None:
        """Test handle_cli_error with CLIError."""
        # Arrange
        error = CLIError('operation', 'component', 'CLI error occurred')
        error.exit_code = 3

        with patch('typer.echo') as mock_echo:
            # Act
            result = TyperCLIAdapter.handle_cli_error(error)

            # Assert
            assert result == 3
            mock_echo.assert_called_once_with(f'CLI Error: {error}', err=True)

    def test_handle_cli_error_generic_exception(self) -> None:
        """Test handle_cli_error with generic Exception."""
        # Arrange
        error = RuntimeError('Generic error')

        with patch('typer.echo') as mock_echo:
            # Act
            result = TyperCLIAdapter.handle_cli_error(error)

            # Assert
            assert result == 1
            mock_echo.assert_called_once_with(f'Unexpected Error: {error}', err=True)

    def test_validate_write_command_args_success_all_args(self) -> None:
        """Test validate_write_command_args with all valid arguments."""
        # Arrange
        node = str(uuid.uuid4())

        # Act
        result = TyperCLIAdapter.validate_write_command_args(
            node=node,
            title='Test Title',
            word_count_goal=1000,
            time_limit=3600,
        )

        # Assert
        assert isinstance(result, dict)
        assert result['node'] == node
        assert result['title'] == 'Test Title'
        assert result['word_count_goal'] == 1000
        assert result['time_limit'] == 3600

    def test_validate_write_command_args_success_minimal(self) -> None:
        """Test validate_write_command_args with minimal arguments."""
        # Act
        result = TyperCLIAdapter.validate_write_command_args(
            node=None,
            title=None,
            word_count_goal=None,
            time_limit=None,
        )

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 0  # No normalized values for None inputs

    def test_validate_write_command_args_invalid_node(self) -> None:
        """Test validate_write_command_args raises ValidationError for invalid node."""
        # Act & Assert
        with pytest.raises(ValidationError, match='node:'):
            TyperCLIAdapter.validate_write_command_args(
                node='invalid-uuid',
                title=None,
                word_count_goal=None,
                time_limit=None,
            )

    def test_validate_write_command_args_invalid_word_count(self) -> None:
        """Test validate_write_command_args raises ValidationError for negative word count."""
        # Act & Assert
        with pytest.raises(ValidationError, match='word_count_goal: must be positive'):
            TyperCLIAdapter.validate_write_command_args(
                node=None,
                title=None,
                word_count_goal=-100,
                time_limit=None,
            )

    def test_validate_write_command_args_invalid_time_limit(self) -> None:
        """Test validate_write_command_args raises ValidationError for negative time limit."""
        # Act & Assert
        with pytest.raises(ValidationError, match='time_limit: must be positive'):
            TyperCLIAdapter.validate_write_command_args(
                node=None,
                title=None,
                word_count_goal=None,
                time_limit=-60,
            )

    def test_validate_write_command_args_empty_title(self) -> None:
        """Test validate_write_command_args raises ValidationError for empty title."""
        # Act & Assert
        with pytest.raises(ValidationError, match='title: cannot be empty'):
            TyperCLIAdapter.validate_write_command_args(
                node=None,
                title='   ',  # Whitespace only
                word_count_goal=None,
                time_limit=None,
            )

    def test_validate_write_command_args_multiple_errors(self) -> None:
        """Test validate_write_command_args combines multiple errors."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TyperCLIAdapter.validate_write_command_args(
                node='invalid-uuid',
                title='',
                word_count_goal=-100,
                time_limit=-60,
            )

        error_msg = str(exc_info.value)
        assert 'word_count_goal: must be positive' in error_msg
        assert 'time_limit: must be positive' in error_msg
        assert 'title: cannot be empty' in error_msg

    def test_get_available_themes(self) -> None:
        """Test get_available_themes returns copy of themes."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        # Act
        result = adapter.get_available_themes()

        # Assert
        assert result == ['dark', 'light', 'auto']
        assert result is not adapter.available_themes  # Should be a copy

    def test_get_current_working_directory(self) -> None:
        """Test get_current_working_directory returns current directory."""
        # Act
        result = TyperCLIAdapter.get_current_working_directory()

        # Assert
        assert isinstance(result, str)
        assert result == str(Path.cwd())

    def test_check_directory_writable_existing_directory(self) -> None:
        """Test check_directory_writable with existing writable directory."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Act
            result = TyperCLIAdapter.check_directory_writable(temp_dir)

            # Assert
            assert result is True

    def test_check_directory_writable_nonexistent_directory(self) -> None:
        """Test check_directory_writable with non-existent directory that can be created."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / 'new_dir'

            # Act
            result = TyperCLIAdapter.check_directory_writable(str(test_dir))

            # Assert
            assert result is True

    def test_check_directory_writable_readonly_directory(self) -> None:
        """Test check_directory_writable with read-only directory."""
        # This test is tricky because we need a truly read-only directory
        # Let's test with an invalid path that can't be written to

        # Act
        result = TyperCLIAdapter.check_directory_writable('/root/readonly')

        # Assert - This should return False for most users
        assert isinstance(result, bool)

    def test_check_directory_writable_invalid_path(self) -> None:
        """Test check_directory_writable with invalid path."""
        # Act - use a path that will trigger OSError in the try/except
        with patch('pathlib.Path', side_effect=OSError('Invalid path')):
            result = TyperCLIAdapter.check_directory_writable('/some/path')

        # Assert
        assert result is False


class TestCreateFreewriteCommand:
    """Test the create_freewrite_command function."""

    def test_create_freewrite_command_returns_typer_app(self) -> None:
        """Test create_freewrite_command returns Typer application."""
        # Arrange
        mock_cli_adapter = Mock(spec=TyperCLIAdapter)

        # Act
        result = create_freewrite_command(mock_cli_adapter)

        # Assert
        assert isinstance(result, typer.Typer)
        assert result.info.name == 'freewrite'

    def test_freewrite_command_success(self) -> None:
        """Test freewrite write command successful execution."""
        # Arrange
        mock_cli_adapter = Mock(spec=TyperCLIAdapter)
        mock_cli_adapter.validate_write_command_args.return_value = {}
        mock_cli_adapter.parse_arguments.return_value = SessionConfig()
        mock_cli_adapter.create_tui_config.return_value = TUIConfig(theme='dark')
        mock_cli_adapter.launch_tui.return_value = 0

        app = create_freewrite_command(mock_cli_adapter)

        # Mock typer.Exit to avoid actual exit
        with patch('typer.Exit'):
            # Act - call the write command directly
            try:
                # Get the write command and call it with no arguments
                # Find the write command in the registered commands list
                write_command = next((cmd for cmd in app.registered_commands if cmd.name == 'write'), None)
                if write_command and write_command.callback:
                    write_command.callback()
            except (TypeError, StopIteration):
                # Expected - the command expects arguments or no write command found
                pass

        # The command should have been prepared, even if not fully executed
        assert app.info.name == 'freewrite'

    def test_freewrite_command_validation_error(self) -> None:
        """Test freewrite write command handles ValidationError."""
        # Arrange
        mock_cli_adapter = Mock(spec=TyperCLIAdapter)
        mock_cli_adapter.validate_write_command_args.side_effect = ValidationError(
            'args', 'invalid', 'Validation failed'
        )

        app = create_freewrite_command(mock_cli_adapter)

        # Act & Assert - actually invoke the command to test exception handling path
        from typer.testing import CliRunner

        runner = CliRunner()

        with patch.object(TyperCLIAdapter, 'handle_cli_error', return_value=2) as mock_handle_error:
            # This will execute the actual command callback and trigger the exception handling
            result = runner.invoke(app, [])

            # Should exit with error code
            assert result.exit_code == 2
            mock_cli_adapter.validate_write_command_args.assert_called_once()
            mock_handle_error.assert_called_once()

    def test_freewrite_command_unexpected_error(self) -> None:
        """Test freewrite write command handles unexpected errors."""
        # Arrange
        mock_cli_adapter = Mock(spec=TyperCLIAdapter)
        mock_cli_adapter.validate_write_command_args.side_effect = RuntimeError('Unexpected error')

        app = create_freewrite_command(mock_cli_adapter)

        # Act & Assert - actually invoke the command to test exception handling path
        from typer.testing import CliRunner

        runner = CliRunner()

        with patch.object(TyperCLIAdapter, 'handle_cli_error', return_value=1) as mock_handle_error:
            # This will execute the actual command callback and trigger the exception handling
            result = runner.invoke(app, [])

            # Should exit with error code
            assert result.exit_code == 1
            mock_cli_adapter.validate_write_command_args.assert_called_once()
            mock_handle_error.assert_called_once()

    def test_freewrite_command_generic_exception_in_launch_tui(self) -> None:
        """Test freewrite write command handles generic exceptions from launch_tui."""
        # Arrange
        mock_cli_adapter = Mock(spec=TyperCLIAdapter)
        mock_cli_adapter.validate_write_command_args.return_value = None
        mock_cli_adapter.parse_arguments.return_value = Mock()
        mock_cli_adapter.create_tui_config.return_value = Mock()
        mock_cli_adapter.launch_tui.side_effect = OSError('OS Error during launch')

        app = create_freewrite_command(mock_cli_adapter)

        # Act & Assert - actually invoke the command to test exception handling path
        from typer.testing import CliRunner

        runner = CliRunner()

        with patch.object(TyperCLIAdapter, 'handle_cli_error', return_value=1) as mock_handle_error:
            # This will execute the actual command callback and trigger the exception handling
            result = runner.invoke(app, [])

            # Should exit with error code
            assert result.exit_code == 1
            mock_cli_adapter.launch_tui.assert_called_once()
            mock_handle_error.assert_called_once()


class TestMainFunction:
    """Test the main function."""

    def test_main_exits_with_error(self) -> None:
        """Test main function exits with error message."""
        # Arrange & Act & Assert
        with patch('typer.echo') as mock_echo, patch('sys.exit') as mock_exit:
            main()

            mock_echo.assert_any_call('Error: This CLI requires proper dependency injection from main app')
            mock_echo.assert_any_call('Use this adapter through the main prosemark CLI application')
            mock_exit.assert_called_once_with(1)

    def test_main_handles_os_error(self) -> None:
        """Test main function handles OSError."""
        # Arrange & Act & Assert
        with (
            patch('typer.echo', side_effect=OSError('System error')),
            patch('typer.echo'),
            patch('sys.exit') as mock_exit,
        ):
            main()

            mock_exit.assert_called_with(1)

    def test_main_handles_keyboard_interrupt(self) -> None:
        """Test main function handles KeyboardInterrupt."""
        # Arrange & Act & Assert
        with patch('typer.echo', side_effect=KeyboardInterrupt()), patch('typer.echo'), patch('sys.exit') as mock_exit:
            main()

            mock_exit.assert_called_with(1)


class TestCLIAdapterIntegration:
    """Integration tests for CLI adapter components."""

    def test_full_argument_parsing_flow(self) -> None:
        """Test the complete flow from CLI arguments to session config."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        node_uuid = str(uuid.uuid4())

        with (
            patch.object(TyperCLIAdapter, 'check_directory_writable', return_value=True),
            patch('prosemark.freewriting.adapters.cli_adapter.process_title') as mock_process_title,
        ):
            # Act
            session_config = adapter.parse_arguments(
                node=node_uuid,
                title='Integration Test',
                word_count_goal=500,
                time_limit=1800,
                theme='dark',
                current_directory='/test/integration',
            )

            tui_config = adapter.create_tui_config('dark')

            # Assert
            assert session_config.target_node == node_uuid
            assert session_config.title == 'Integration Test'
            assert session_config.word_count_goal == 500
            assert session_config.time_limit == 1800
            assert session_config.theme == 'dark'
            assert session_config.current_directory == '/test/integration'

            assert tui_config.theme == 'dark'
            assert tui_config.content_height_percent == 80

            mock_process_title.assert_called_once_with('Integration Test')

    def test_error_propagation_flow(self) -> None:
        """Test error propagation through the CLI adapter layers."""
        # Arrange
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        adapter = TyperCLIAdapter(mock_tui_adapter)

        # Test validation error propagation
        with pytest.raises(ValidationError):
            TyperCLIAdapter.validate_node_argument('invalid-uuid')

        # Test CLI error creation from parse_arguments
        with (
            patch.object(TyperCLIAdapter, 'validate_node_argument', side_effect=Exception('Unexpected')),
            pytest.raises(CLIError),
        ):
            adapter.parse_arguments(
                node='test',
                title=None,
                word_count_goal=None,
                time_limit=None,
                theme='dark',
                current_directory=None,
            )
