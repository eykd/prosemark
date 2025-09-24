"""Tests for freewriting domain exceptions."""

from prosemark.freewriting.domain.exceptions import (
    ArgumentValidationError,
    CLIError,
    ConfigurationError,
    ContentError,
    DirectoryNotWritableError,
    FileSystemError,
    FreewriteError,
    NodeError,
    SessionError,
    ThemeNotFoundError,
    TUIError,
    ValidationError,
)


class TestFreewriteError:
    """Test the base FreewriteError exception."""

    def test_creates_error_with_message_only(self) -> None:
        """Test creating error with just a message."""
        message = 'Something went wrong'
        error = FreewriteError(message)

        assert error.message == message
        assert error.context == {}
        assert str(error) == message

    def test_creates_error_with_message_and_context(self) -> None:
        """Test creating error with message and context."""
        message = 'Something went wrong'
        context = {'user_id': '123', 'session_id': 'abc'}
        error = FreewriteError(message, context)

        assert error.message == message
        assert error.context == context

    def test_string_representation_without_context(self) -> None:
        """Test string representation when no context is provided."""
        message = 'Error message'
        error = FreewriteError(message)

        assert str(error) == 'Error message'

    def test_string_representation_with_context(self) -> None:
        """Test string representation when context is provided."""
        message = 'Error message'
        context = {'file': 'test.txt', 'line': '42'}
        error = FreewriteError(message, context)

        result = str(error)
        assert result.startswith('Error message (')
        assert 'file=test.txt' in result
        assert 'line=42' in result
        assert result.endswith(')')

    def test_string_representation_with_empty_context(self) -> None:
        """Test string representation when empty context is provided."""
        message = 'Error message'
        context: dict[str, str] = {}
        error = FreewriteError(message, context)

        assert str(error) == 'Error message'

    def test_inherits_from_exception(self) -> None:
        """Test that FreewriteError inherits from Exception."""
        error = FreewriteError('test')
        assert isinstance(error, Exception)

    def test_context_defaults_to_empty_dict_when_none(self) -> None:
        """Test that context defaults to empty dict when None is passed."""
        error = FreewriteError('test', None)
        assert error.context == {}


class TestValidationError:
    """Test the ValidationError exception."""

    def test_creates_validation_error_with_field_details(self) -> None:
        """Test creating validation error with field details."""
        error = ValidationError('username', 'invalid value', 'Must be alphanumeric')

        assert error.field_name == 'username'
        assert error.field_value == 'invalid value'
        assert error.validation_rule == 'Must be alphanumeric'
        assert isinstance(error, FreewriteError)

    def test_message_format(self) -> None:
        """Test that message is properly formatted."""
        error = ValidationError('age', '-5', 'Must be positive')

        expected_message = 'Validation failed for age: Must be positive'
        assert error.message == expected_message

    def test_inherits_from_freewrite_error(self) -> None:
        """Test that ValidationError inherits from FreewriteError."""
        error = ValidationError('field', 'value', 'rule')
        assert isinstance(error, FreewriteError)

    def test_with_custom_context(self) -> None:
        """Test creating validation error with custom context."""
        context = {'form': 'registration', 'step': '1'}
        error = ValidationError('email', 'not-email', 'Must be valid email', context)

        assert error.context == context


class TestFileSystemError:
    """Test the FileSystemError exception."""

    def test_creates_filesystem_error_with_basic_info(self) -> None:
        """Test creating filesystem error with operation and path."""
        error = FileSystemError('write', '/path/to/file.txt', 'Permission denied')

        assert error.operation == 'write'
        assert error.file_path == '/path/to/file.txt'
        assert error.system_error == 'Permission denied'
        assert isinstance(error, FreewriteError)

    def test_creates_filesystem_error_without_system_error(self) -> None:
        """Test creating filesystem error without system error."""
        error = FileSystemError('create', '/path/to/dir')

        assert error.operation == 'create'
        assert error.file_path == '/path/to/dir'
        assert error.system_error is None

    def test_message_format_with_system_error(self) -> None:
        """Test that message is properly formatted with system error."""
        error = FileSystemError('read', '/home/test/test.txt', 'File not found')

        expected_message = 'File system operation failed: read on /home/test/test.txt (File not found)'
        assert error.message == expected_message

    def test_message_format_without_system_error(self) -> None:
        """Test that message is properly formatted without system error."""
        error = FileSystemError('delete', '/var/log/app.log')

        expected_message = 'File system operation failed: delete on /var/log/app.log'
        assert error.message == expected_message

    def test_inherits_from_freewrite_error(self) -> None:
        """Test that FileSystemError inherits from FreewriteError."""
        error = FileSystemError('operation', '/path')
        assert isinstance(error, FreewriteError)


class TestNodeError:
    """Test the NodeError exception."""

    def test_creates_node_error_with_uuid(self) -> None:
        """Test creating node error with valid UUID."""
        error = NodeError('123e4567-e89b-12d3-a456-426614174000', 'read', 'Node not found')

        assert error.node_uuid == '123e4567-e89b-12d3-a456-426614174000'
        assert error.operation == 'read'
        assert error.reason == 'Node not found'
        assert isinstance(error, FreewriteError)

    def test_creates_node_error_without_uuid(self) -> None:
        """Test creating node error when UUID is None."""
        error = NodeError(None, 'validate', 'Invalid UUID format')

        assert error.node_uuid is None
        assert error.operation == 'validate'
        assert error.reason == 'Invalid UUID format'

    def test_message_format_with_uuid(self) -> None:
        """Test message format when UUID is provided."""
        uuid = '123e4567-e89b-12d3-a456-426614174000'
        error = NodeError(uuid, 'update', 'Permission denied')

        expected = f'Node operation failed: update on {uuid} - Permission denied'
        assert error.message == expected

    def test_message_format_without_uuid(self) -> None:
        """Test message format when UUID is None."""
        error = NodeError(None, 'parse', 'Invalid format')

        expected = 'Node operation failed: parse on invalid-uuid - Invalid format'
        assert error.message == expected


class TestSessionError:
    """Test the SessionError exception."""

    def test_creates_session_error_with_session_id(self) -> None:
        """Test creating session error with session ID."""
        error = SessionError('session_123', 'start', 'Connection failed')

        assert error.session_id == 'session_123'
        assert error.operation == 'start'
        assert error.reason == 'Connection failed'
        assert isinstance(error, FreewriteError)

    def test_creates_session_error_without_session_id(self) -> None:
        """Test creating session error when session ID is None."""
        error = SessionError(None, 'initialize', 'No active session')

        assert error.session_id is None
        assert error.operation == 'initialize'
        assert error.reason == 'No active session'

    def test_message_format_with_session_id(self) -> None:
        """Test message format when session ID is provided."""
        error = SessionError('session_789', 'save', 'Disk full')

        expected = 'Session operation failed: save on session_789 - Disk full'
        assert error.message == expected

    def test_message_format_without_session_id(self) -> None:
        """Test message format when session ID is None."""
        error = SessionError(None, 'load', 'No session available')

        expected = 'Session operation failed: load on unknown-session - No session available'
        assert error.message == expected


class TestTUIError:
    """Test the TUIError exception."""

    def test_creates_tui_error_with_all_params(self) -> None:
        """Test creating TUI error with all parameters."""
        error = TUIError('input_widget', 'key_press', 'Invalid key', recoverable=False)

        assert error.component == 'input_widget'
        assert error.operation == 'key_press'
        assert error.reason == 'Invalid key'
        assert error.recoverable is False
        assert isinstance(error, FreewriteError)

    def test_creates_tui_error_with_default_recoverable(self) -> None:
        """Test creating TUI error with default recoverable value."""
        error = TUIError('main_screen', 'render', 'Buffer overflow')

        assert error.component == 'main_screen'
        assert error.operation == 'render'
        assert error.reason == 'Buffer overflow'
        assert error.recoverable is True  # Default value

    def test_message_format(self) -> None:
        """Test that message is properly formatted."""
        error = TUIError('text_area', 'scroll', 'Out of bounds')

        expected = 'TUI operation failed: scroll in text_area - Out of bounds'
        assert error.message == expected


class TestCLIError:
    """Test the CLIError exception."""

    def test_creates_cli_error_with_argument(self) -> None:
        """Test creating CLI error with argument."""
        error = CLIError('write', '--theme', 'Theme not found', 2)

        assert error.command == 'write'
        assert error.argument == '--theme'
        assert error.reason == 'Theme not found'
        assert error.exit_code == 2
        assert isinstance(error, FreewriteError)

    def test_creates_cli_error_without_argument(self) -> None:
        """Test creating CLI error without argument."""
        error = CLIError('init', None, 'Project already exists')

        assert error.command == 'init'
        assert error.argument is None
        assert error.reason == 'Project already exists'
        assert error.exit_code == 1  # Default value

    def test_message_format_with_argument(self) -> None:
        """Test message format when argument is provided."""
        error = CLIError('validate', '--uuid', 'Invalid format')

        expected = 'CLI command failed: validate with argument --uuid - Invalid format'
        assert error.message == expected

    def test_message_format_without_argument(self) -> None:
        """Test message format when no argument is provided."""
        error = CLIError('status', None, 'No active session')

        expected = 'CLI command failed: status - No active session'
        assert error.message == expected

    def test_string_representation_returns_reason(self) -> None:
        """Test that __str__ returns just the reason for CLI errors."""
        error = CLIError('command', 'arg', 'Something failed')

        # CLIError overrides __str__ to return just the reason
        assert str(error) == 'Something failed'


class TestConfigurationError:
    """Test the ConfigurationError exception."""

    def test_creates_configuration_error(self) -> None:
        """Test creating configuration error."""
        error = ConfigurationError('theme', 'invalid', 'Theme does not exist')

        assert error.config_key == 'theme'
        assert error.config_value == 'invalid'
        assert error.reason == 'Theme does not exist'
        assert isinstance(error, FreewriteError)

    def test_message_format(self) -> None:
        """Test message format."""
        error = ConfigurationError('timeout', '-1', 'Must be positive')

        expected = 'Invalid configuration: timeout=-1 - Must be positive'
        assert error.message == expected


class TestContentError:
    """Test the ContentError exception."""

    def test_creates_content_error_with_short_preview(self) -> None:
        """Test creating content error with short content preview."""
        error = ContentError('encode', 'Hello world', 'Invalid encoding')

        assert error.operation == 'encode'
        assert error.content_preview == 'Hello world'
        assert error.reason == 'Invalid encoding'
        assert isinstance(error, FreewriteError)

    def test_creates_content_error_with_long_preview(self) -> None:
        """Test creating content error with long content that gets truncated."""
        long_content = 'a' * 100
        error = ContentError('validate', long_content, 'Too long')

        assert error.operation == 'validate'
        assert error.content_preview == long_content  # Original is preserved
        assert error.reason == 'Too long'

    def test_message_format_with_short_content(self) -> None:
        """Test message format with short content."""
        error = ContentError('parse', 'Short text', 'Invalid syntax')

        expected = 'Content operation failed: parse on "Short text" - Invalid syntax'
        assert error.message == expected

    def test_message_format_with_long_content(self) -> None:
        """Test message format with long content that gets truncated."""
        long_content = 'x' * 60
        error = ContentError('process', long_content, 'Format error')

        # Should truncate to 50 chars + "..."
        expected_preview = 'x' * 50 + '...'
        expected = f'Content operation failed: process on "{expected_preview}" - Format error'
        assert error.message == expected


class TestLegacyAliases:
    """Test the legacy exception aliases."""

    def test_argument_validation_error(self) -> None:
        """Test ArgumentValidationError legacy alias."""
        error = ArgumentValidationError('--count', 'invalid', 'Must be a number')

        assert error.command == 'validate'
        assert error.argument == '--count'
        assert error.reason == 'Must be a number'
        assert isinstance(error, CLIError)
        assert isinstance(error, FreewriteError)

    def test_theme_not_found_error(self) -> None:
        """Test ThemeNotFoundError legacy alias."""
        error = ThemeNotFoundError('theme', 'missing', 'Theme not available')

        assert error.command == 'configure'
        assert error.argument == 'theme'
        assert error.reason == 'Theme not available'
        assert isinstance(error, CLIError)

    def test_directory_not_writable_error(self) -> None:
        """Test DirectoryNotWritableError legacy alias."""
        error = DirectoryNotWritableError('write', '/readonly', 'Permission denied')

        assert error.command == 'write'
        assert error.argument == '/readonly'
        assert error.reason == 'Permission denied'
        assert isinstance(error, CLIError)


class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance."""

    def test_all_exceptions_inherit_from_freewrite_error(self) -> None:
        """Test that all domain exceptions inherit from FreewriteError."""
        exceptions = [
            ValidationError('field', 'value', 'rule'),
            FileSystemError('op', 'path'),
            NodeError('uuid', 'op', 'reason'),
            SessionError('session', 'op', 'reason'),
            TUIError('comp', 'op', 'reason'),
            CLIError('cmd', 'arg', 'reason'),
            ConfigurationError('key', 'value', 'reason'),
            ContentError('op', 'content', 'reason'),
        ]

        for exception in exceptions:
            assert isinstance(exception, FreewriteError)
            assert isinstance(exception, Exception)

    def test_all_exceptions_are_catchable_as_freewrite_error(self) -> None:
        """Test that all exceptions can be caught as FreewriteError."""
        exceptions = [
            ValidationError('field', 'value', 'rule'),
            FileSystemError('op', 'path'),
            NodeError('uuid', 'op', 'reason'),
            SessionError('session', 'op', 'reason'),
            TUIError('comp', 'op', 'reason'),
            CLIError('cmd', 'arg', 'reason'),
            ConfigurationError('key', 'value', 'reason'),
            ContentError('op', 'content', 'reason'),
        ]

        def _test_exception_catchability(exception: Exception) -> None:
            def _raise_specific_exception() -> None:
                raise exception

            caught = False
            try:
                _raise_specific_exception()
            except FreewriteError:
                caught = True

            assert caught, f'Exception {type(exception)} not caught as FreewriteError'

        for exception in exceptions:
            _test_exception_catchability(exception)

    def test_legacy_aliases_inherit_correctly(self) -> None:
        """Test that legacy aliases inherit from correct base classes."""
        arg_error = ArgumentValidationError('arg', 'val', 'reason')
        theme_error = ThemeNotFoundError('key', 'val', 'reason')
        dir_error = DirectoryNotWritableError('op', 'path', 'reason')

        # All should inherit from CLIError and FreewriteError
        for error in [arg_error, theme_error, dir_error]:
            assert isinstance(error, CLIError)
            assert isinstance(error, FreewriteError)
            assert isinstance(error, Exception)
