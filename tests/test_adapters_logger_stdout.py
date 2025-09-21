"""Tests for LoggerStdout adapter."""

import io

import pytest

from prosemark.adapters.logger_stdout import LoggerStdout


class TestLoggerStdout:
    """Test LoggerStdout adapter methods."""

    @pytest.fixture
    def stdout_capture(self) -> io.StringIO:
        """Create a StringIO buffer to capture stdout."""
        return io.StringIO()

    @pytest.fixture
    def stderr_capture(self) -> io.StringIO:
        """Create a StringIO buffer to capture stderr."""
        return io.StringIO()

    @pytest.fixture
    def logger(self, stdout_capture: io.StringIO, stderr_capture: io.StringIO) -> LoggerStdout:
        """Create a LoggerStdout instance with captured streams."""
        return LoggerStdout(info_stream=stdout_capture, error_stream=stderr_capture)

    def test_warning_with_message_only(self, logger: LoggerStdout, stderr_capture: io.StringIO) -> None:
        """Test warning method with message only."""
        # Act
        logger.warning('This is a warning')

        # Assert
        output = stderr_capture.getvalue()
        assert output == '[WARNING] This is a warning\n'

    def test_warning_with_formatting_args(self, logger: LoggerStdout, stderr_capture: io.StringIO) -> None:
        """Test warning method with formatting arguments."""
        # Act
        logger.warning('Warning: %s failed with code %d', 'operation', 42)

        # Assert
        output = stderr_capture.getvalue()
        assert output == '[WARNING] Warning: operation failed with code 42\n'

    def test_warning_with_no_args(self, logger: LoggerStdout, stderr_capture: io.StringIO) -> None:
        """Test warning method without formatting arguments."""
        # Act
        logger.warning('Simple warning message')

        # Assert
        output = stderr_capture.getvalue()
        assert output == '[WARNING] Simple warning message\n'

    def test_warning_with_complex_object(self, logger: LoggerStdout, stderr_capture: io.StringIO) -> None:
        """Test warning method with complex object that gets converted to string."""
        # Act
        logger.warning({'error': 'test', 'code': 404})

        # Assert
        output = stderr_capture.getvalue()
        assert output == "[WARNING] {'error': 'test', 'code': 404}\n"

    def test_warning_writes_to_error_stream(self) -> None:
        """Test that warning output goes to error stream, not stdout."""
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        logger = LoggerStdout(info_stream=stdout_buf, error_stream=stderr_buf)

        # Act
        logger.warning('Test warning')

        # Assert
        assert stdout_buf.getvalue() == ''  # Nothing to stdout
        assert stderr_buf.getvalue() == '[WARNING] Test warning\n'  # Warning to stderr
