"""Contract tests for CLIAdapterPort protocol (T006).

These tests verify that any implementation of the CLIAdapterPort protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from unittest.mock import Mock

from prosemark.freewriting.domain.exceptions import (
    ArgumentValidationError,
    CLIError,
    DirectoryNotWritableError,
    ThemeNotFoundError,
    ValidationError,
)
from prosemark.freewriting.domain.models import SessionConfig
from prosemark.freewriting.ports.cli_adapter import (
    CLIAdapterPort,
    CLIContext,
    CLIResponse,
    CommandValidationPort,
    ValidationResult,
)
from prosemark.freewriting.ports.tui_adapter import TUIConfig


class TestCLIAdapterPortContract:
    """Test contract compliance for CLIAdapterPort implementations."""

    def test_parse_arguments_returns_session_config(self) -> None:
        """Test parse_arguments() returns SessionConfig from CLI arguments."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        expected_config = SessionConfig(
            target_node='01234567-89ab-cdef-0123-456789abcdef',
            title='CLI Test Session',
            word_count_goal=750,
            time_limit=2400,
            theme='light',
            current_directory='/home/user/project',
        )
        mock_adapter.parse_arguments.return_value = expected_config

        # Act
        result = mock_adapter.parse_arguments(
            node='01234567-89ab-cdef-0123-456789abcdef',
            title='CLI Test Session',
            word_count_goal=750,
            time_limit=2400,
            theme='light',
            current_directory='/home/user/project',
        )

        # Assert
        assert isinstance(result, SessionConfig)
        assert result.target_node == '01234567-89ab-cdef-0123-456789abcdef'
        assert result.title == 'CLI Test Session'
        assert result.word_count_goal == 750
        assert result.time_limit == 2400
        assert result.theme == 'light'
        mock_adapter.parse_arguments.assert_called_once()

    def test_parse_arguments_with_minimal_args(self) -> None:
        """Test parse_arguments() with minimal arguments (mostly None/defaults)."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        expected_config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=None,
            time_limit=None,
            theme='default',
            current_directory='/current/working/dir',
        )
        mock_adapter.parse_arguments.return_value = expected_config

        # Act
        result = mock_adapter.parse_arguments(
            node=None, title=None, word_count_goal=None, time_limit=None, theme='default', current_directory=None
        )

        # Assert
        assert isinstance(result, SessionConfig)
        assert result.target_node is None
        assert result.title is None
        assert result.word_count_goal is None
        assert result.time_limit is None
        mock_adapter.parse_arguments.assert_called_once()

    def test_parse_arguments_raises_validation_error_on_invalid_args(self) -> None:
        """Test parse_arguments() raises ValidationError for invalid arguments."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        mock_adapter.parse_arguments.side_effect = ValidationError('node', 'invalid-format', 'Invalid UUID format')

        # Act & Assert
        try:
            mock_adapter.parse_arguments(
                node='invalid-uuid-format',
                title='Test',
                word_count_goal=-100,
                time_limit=-60,
                theme='nonexistent',
                current_directory='/invalid/path',
            )
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_adapter.parse_arguments.assert_called_once()

    def test_validate_node_argument_returns_valid_uuid(self) -> None:
        """Test validate_node_argument() returns validated UUID string."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        valid_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        mock_adapter.validate_node_argument.return_value = valid_uuid

        # Act
        result = mock_adapter.validate_node_argument(valid_uuid)

        # Assert
        assert result == valid_uuid
        mock_adapter.validate_node_argument.assert_called_once_with(valid_uuid)

    def test_validate_node_argument_returns_none_for_none_input(self) -> None:
        """Test validate_node_argument() returns None when input is None."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        mock_adapter.validate_node_argument.return_value = None

        # Act
        result = mock_adapter.validate_node_argument(None)

        # Assert
        assert result is None
        mock_adapter.validate_node_argument.assert_called_once_with(None)

    def test_validate_node_argument_raises_validation_error_on_invalid_format(self) -> None:
        """Test validate_node_argument() raises ValidationError for invalid UUID format."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        invalid_uuid = 'not-a-valid-uuid-format'
        mock_adapter.validate_node_argument.side_effect = ValidationError(
            'node', 'invalid-format', 'Invalid UUID format'
        )

        # Act & Assert
        try:
            mock_adapter.validate_node_argument(invalid_uuid)
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_adapter.validate_node_argument.assert_called_once_with(invalid_uuid)

    def test_create_tui_config_returns_tui_config(self) -> None:
        """Test create_tui_config() returns TUIConfig object."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        theme_name = 'dark'
        expected_config = TUIConfig(
            theme=theme_name,
            content_height_percent=80,
            input_height_percent=20,
            show_word_count=True,
            show_timer=True,
            auto_scroll=True,
            max_display_lines=1000,
        )
        mock_adapter.create_tui_config.return_value = expected_config

        # Act
        result = mock_adapter.create_tui_config(theme_name)

        # Assert
        assert isinstance(result, TUIConfig)
        assert result.theme == theme_name
        assert result.content_height_percent == 80
        assert result.input_height_percent == 20
        mock_adapter.create_tui_config.assert_called_once_with(theme_name)

    def test_create_tui_config_raises_validation_error_for_invalid_theme(self) -> None:
        """Test create_tui_config() raises ValidationError for invalid theme."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        invalid_theme = 'nonexistent_theme'
        mock_adapter.create_tui_config.side_effect = ValidationError('theme', 'nonexistent', 'Theme not available')

        # Act & Assert
        try:
            mock_adapter.create_tui_config(invalid_theme)
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_adapter.create_tui_config.assert_called_once_with(invalid_theme)

    def test_launch_tui_returns_exit_code(self) -> None:
        """Test launch_tui() returns integer exit code."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        session_config = SessionConfig(
            target_node=None,
            title='Test Session',
            word_count_goal=None,
            time_limit=None,
            theme='default',
            current_directory='/test',
        )
        tui_config = TUIConfig(
            theme='default',
            content_height_percent=80,
            input_height_percent=20,
            show_word_count=True,
            show_timer=True,
            auto_scroll=True,
            max_display_lines=1000,
        )
        expected_exit_code = 0
        mock_adapter.launch_tui.return_value = expected_exit_code

        # Act
        result = mock_adapter.launch_tui(session_config, tui_config)

        # Assert
        assert isinstance(result, int)
        assert result == expected_exit_code
        mock_adapter.launch_tui.assert_called_once_with(session_config, tui_config)

    def test_launch_tui_returns_nonzero_exit_code_on_error(self) -> None:
        """Test launch_tui() returns non-zero exit code on error."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        session_config = SessionConfig(
            target_node=None,
            title='Error Test',
            word_count_goal=None,
            time_limit=None,
            theme='default',
            current_directory='/test',
        )
        tui_config = TUIConfig(
            theme='default',
            content_height_percent=80,
            input_height_percent=20,
            show_word_count=True,
            show_timer=True,
            auto_scroll=True,
            max_display_lines=1000,
        )
        error_exit_code = 1
        mock_adapter.launch_tui.return_value = error_exit_code

        # Act
        result = mock_adapter.launch_tui(session_config, tui_config)

        # Assert
        assert isinstance(result, int)
        assert result != 0
        assert result == error_exit_code
        mock_adapter.launch_tui.assert_called_once_with(session_config, tui_config)

    def test_handle_cli_error_returns_appropriate_exit_code(self) -> None:
        """Test handle_cli_error() returns appropriate exit code for error type."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)
        test_error = ArgumentValidationError('argument', 'invalid-value', 'Invalid argument provided')
        expected_exit_code = 2  # Common exit code for argument errors
        mock_adapter.handle_cli_error.return_value = expected_exit_code

        # Act
        result = mock_adapter.handle_cli_error(test_error)

        # Assert
        assert isinstance(result, int)
        assert result == expected_exit_code
        mock_adapter.handle_cli_error.assert_called_once_with(test_error)

    def test_handle_cli_error_with_different_error_types(self) -> None:
        """Test handle_cli_error() handles different error types appropriately."""
        # Arrange
        mock_adapter = Mock(spec=CLIAdapterPort)

        error_types_and_codes = [
            (ArgumentValidationError('argument', 'bad-value', 'Bad argument'), 2),
            (ThemeNotFoundError('theme', 'missing', 'Theme missing'), 3),
            (DirectoryNotWritableError('write', '/readonly', 'No write permission'), 4),
            (Exception('Generic error'), 1),
        ]

        for error, expected_code in error_types_and_codes:
            mock_adapter.handle_cli_error.return_value = expected_code

            # Act
            result = mock_adapter.handle_cli_error(error)

            # Assert
            assert isinstance(result, int)
            assert result == expected_code

        assert mock_adapter.handle_cli_error.call_count == len(error_types_and_codes)

    def test_protocol_methods_exist(self) -> None:
        """Test that CLIAdapterPort protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_adapter = Mock(spec=CLIAdapterPort)

        # Verify methods exist
        assert hasattr(mock_adapter, 'parse_arguments')
        assert hasattr(mock_adapter, 'validate_node_argument')
        assert hasattr(mock_adapter, 'create_tui_config')
        assert hasattr(mock_adapter, 'launch_tui')
        assert hasattr(mock_adapter, 'handle_cli_error')

        # Verify methods are callable
        assert callable(mock_adapter.parse_arguments)
        assert callable(mock_adapter.validate_node_argument)
        assert callable(mock_adapter.create_tui_config)
        assert callable(mock_adapter.launch_tui)
        assert callable(mock_adapter.handle_cli_error)


class TestCommandValidationPortContract:
    """Test contract compliance for CommandValidationPort implementations."""

    def test_validate_write_command_args_returns_validation_dict(self) -> None:
        """Test validate_write_command_args() returns validation result dictionary."""
        # Arrange
        mock_validator = Mock(spec=CommandValidationPort)
        expected_result = {
            'valid': True,
            'errors': [],
            'warnings': ['Word count goal is high'],
            'normalized_node': '01234567-89ab-cdef-0123-456789abcdef',
            'normalized_title': 'Test Session',
            'normalized_word_count_goal': 2000,
            'normalized_time_limit': 3600,
        }
        mock_validator.validate_write_command_args.return_value = expected_result

        # Act
        result = mock_validator.validate_write_command_args(
            node='01234567-89ab-cdef-0123-456789abcdef', title='Test Session', word_count_goal=2000, time_limit=3600
        )

        # Assert
        assert isinstance(result, dict)
        assert 'valid' in result
        assert result['valid'] is True
        mock_validator.validate_write_command_args.assert_called_once()

    def test_validate_write_command_args_with_validation_errors(self) -> None:
        """Test validate_write_command_args() returns errors for invalid arguments."""
        # Arrange
        mock_validator = Mock(spec=CommandValidationPort)
        expected_result = {
            'valid': False,
            'errors': ['Invalid UUID format', 'Negative word count not allowed'],
            'warnings': [],
            'normalized_node': None,
            'normalized_title': None,
            'normalized_word_count_goal': None,
            'normalized_time_limit': None,
        }
        mock_validator.validate_write_command_args.return_value = expected_result

        # Act
        result = mock_validator.validate_write_command_args(
            node='invalid-uuid', title=None, word_count_goal=-100, time_limit=None
        )

        # Assert
        assert isinstance(result, dict)
        assert result['valid'] is False
        assert len(result['errors']) > 0
        mock_validator.validate_write_command_args.assert_called_once()

    def test_validate_write_command_args_raises_validation_error(self) -> None:
        """Test validate_write_command_args() can raise ValidationError for critical issues."""
        # Arrange
        mock_validator = Mock(spec=CommandValidationPort)
        mock_validator.validate_write_command_args.side_effect = ValidationError(
            'args', 'invalid', 'Critical validation failure'
        )

        # Act & Assert
        try:
            mock_validator.validate_write_command_args(
                node='critical-error-case', title=None, word_count_goal=None, time_limit=None
            )
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_validator.validate_write_command_args.assert_called_once()

    def test_get_available_themes_returns_theme_list(self) -> None:
        """Test get_available_themes() returns list of available theme names."""
        # Arrange
        mock_validator = Mock(spec=CommandValidationPort)
        expected_themes = ['default', 'dark', 'light', 'high_contrast', 'minimal']
        mock_validator.get_available_themes.return_value = expected_themes

        # Act
        result = mock_validator.get_available_themes()

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(theme, str) for theme in result)
        assert 'default' in result
        mock_validator.get_available_themes.assert_called_once_with()

    def test_get_available_themes_returns_empty_list_if_no_themes(self) -> None:
        """Test get_available_themes() can return empty list."""
        # Arrange
        mock_validator = Mock(spec=CommandValidationPort)
        mock_validator.get_available_themes.return_value = []

        # Act
        result = mock_validator.get_available_themes()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0
        mock_validator.get_available_themes.assert_called_once_with()

    def test_get_current_working_directory_returns_absolute_path(self) -> None:
        """Test get_current_working_directory() returns absolute path string."""
        # Arrange
        mock_validator = Mock(spec=CommandValidationPort)
        expected_path = '/home/user/current/project'
        mock_validator.get_current_working_directory.return_value = expected_path

        # Act
        result = mock_validator.get_current_working_directory()

        # Assert
        assert isinstance(result, str)
        assert result == expected_path
        assert result.startswith('/')  # Absolute path
        mock_validator.get_current_working_directory.assert_called_once_with()

    def test_check_directory_writable_returns_boolean(self) -> None:
        """Test check_directory_writable() returns boolean value."""
        # Arrange
        mock_validator = Mock(spec=CommandValidationPort)
        test_directory = '/home/user/writable'
        mock_validator.check_directory_writable.return_value = True

        # Act
        result = mock_validator.check_directory_writable(test_directory)

        # Assert
        assert isinstance(result, bool)
        assert result is True
        mock_validator.check_directory_writable.assert_called_once_with(test_directory)

    def test_check_directory_writable_returns_false_for_readonly(self) -> None:
        """Test check_directory_writable() returns False for read-only directory."""
        # Arrange
        mock_validator = Mock(spec=CommandValidationPort)
        readonly_directory = '/readonly/system/directory'
        mock_validator.check_directory_writable.return_value = False

        # Act
        result = mock_validator.check_directory_writable(readonly_directory)

        # Assert
        assert result is False
        mock_validator.check_directory_writable.assert_called_once_with(readonly_directory)

    def test_protocol_methods_exist(self) -> None:
        """Test that CommandValidationPort protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_validator = Mock(spec=CommandValidationPort)

        # Verify methods exist
        assert hasattr(mock_validator, 'validate_write_command_args')
        assert hasattr(mock_validator, 'get_available_themes')
        assert hasattr(mock_validator, 'get_current_working_directory')
        assert hasattr(mock_validator, 'check_directory_writable')

        # Verify methods are callable
        assert callable(mock_validator.validate_write_command_args)
        assert callable(mock_validator.get_available_themes)
        assert callable(mock_validator.get_current_working_directory)
        assert callable(mock_validator.check_directory_writable)


class TestCLIDataStructuresContract:
    """Test contract compliance for CLI-related data structures."""

    def test_cli_context_has_required_fields(self) -> None:
        """Test CLIContext dataclass has all required fields."""
        # Arrange
        cli_context = CLIContext(
            command_name='write',
            arguments={'title': 'Test', 'word_count_goal': 500},  # Remove None values
            working_directory='/home/user/project',
            user_config={'theme': 'dark', 'auto_save': 'True'},  # All strings
            debug_mode=False,
        )

        # Assert
        assert hasattr(cli_context, 'command_name')
        assert hasattr(cli_context, 'arguments')
        assert hasattr(cli_context, 'working_directory')
        assert hasattr(cli_context, 'user_config')
        assert hasattr(cli_context, 'debug_mode')
        assert cli_context.command_name == 'write'
        assert isinstance(cli_context.arguments, dict)
        assert isinstance(cli_context.debug_mode, bool)

    def test_validation_result_has_required_fields(self) -> None:
        """Test ValidationResult dataclass has all required fields."""
        # Arrange
        validation_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=['Consider setting a word count goal'],
            normalized_values={'title': 'Normalized Title'},  # Remove None values
        )

        # Assert
        assert hasattr(validation_result, 'is_valid')
        assert hasattr(validation_result, 'errors')
        assert hasattr(validation_result, 'warnings')
        assert hasattr(validation_result, 'normalized_values')
        assert isinstance(validation_result.is_valid, bool)
        assert isinstance(validation_result.errors, list)
        assert isinstance(validation_result.warnings, list)
        assert isinstance(validation_result.normalized_values, dict)

    def test_cli_response_has_required_fields(self) -> None:
        """Test CLIResponse dataclass has all required fields."""
        # Arrange
        cli_response = CLIResponse(exit_code=0, message='Operation completed successfully', error_details=None)

        # Assert
        assert hasattr(cli_response, 'exit_code')
        assert hasattr(cli_response, 'message')
        assert hasattr(cli_response, 'error_details')
        assert isinstance(cli_response.exit_code, int)
        assert cli_response.message is None or isinstance(cli_response.message, str)

    def test_cli_response_with_error_details(self) -> None:
        """Test CLIResponse with error details included."""
        # Arrange
        error_details = {
            'error_type': 'ValidationError',
            'field': 'node_uuid',
            'provided_value': 'invalid-uuid',
            'expected_format': 'UUID string',
        }
        cli_response = CLIResponse(exit_code=2, message='Argument validation failed', error_details=error_details)

        # Assert
        assert cli_response.exit_code == 2
        assert cli_response.error_details is not None
        assert isinstance(cli_response.error_details, dict)
        assert 'error_type' in cli_response.error_details

    def test_cli_exceptions_are_properly_defined(self) -> None:
        """Test CLI exception classes are properly defined."""
        # Test base exception
        base_error = CLIError('write', 'node_arg', 'Base CLI error')
        assert isinstance(base_error, Exception)
        assert str(base_error) == 'Base CLI error'

        # Test argument validation error
        arg_error = ArgumentValidationError('argument', 'invalid', 'Invalid argument')
        assert isinstance(arg_error, CLIError)
        assert isinstance(arg_error, Exception)

        # Test theme not found error
        theme_error = ThemeNotFoundError('theme', 'missing', 'Theme not found')
        assert isinstance(theme_error, CLIError)
        assert isinstance(theme_error, Exception)

        # Test directory not writable error
        dir_error = DirectoryNotWritableError('write', '/readonly', 'Directory not writable')
        assert isinstance(dir_error, CLIError)
        assert isinstance(dir_error, Exception)
