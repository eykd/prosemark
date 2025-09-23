"""Tests for FakeLogger adapter."""

from prosemark.adapters.fake_logger import FakeLogger


class TestFakeLogger:
    """Test the FakeLogger implementation."""

    def test_logging_with_complex_formatting(self) -> None:
        """Test logging messages with complex formatting."""
        logger = FakeLogger()

        # Test logging with complex formatting that doesn't match exactly
        logger.info('User %s logged in with ID %d', 'John', 42, extra={'ip': '127.0.0.1'})

        # Retrieve logged messages
        logged_messages = logger.get_logged_messages()

        # Assert that the message was logged with all information
        assert any('User John logged in with ID 42' in msg for msg in logged_messages)
        assert any("{'extra': {'ip': '127.0.0.1'}}" in msg for msg in logged_messages)

        # Clear logs and verify
        logger.clear_logs()
        assert logger.log_count() == 0

    def test_logging_with_tuple_args(self) -> None:
        """Test logging with a tuple of arguments that doesn't match exactly."""
        logger = FakeLogger()

        # Deliberately mismatch format and args
        logger.error('Failed to process %s', ('data', 'extra'))

        # Retrieve logged messages
        logged_messages = logger.get_logged_messages()

        # Assert that the message was logged, handling imperfect formatting
        assert any('Failed to process' in msg for msg in logged_messages)
        assert any("('data', 'extra')" in msg for msg in logged_messages)

    def test_log_level_methods(self) -> None:
        """Test different log level methods."""
        logger = FakeLogger()

        # Log messages at different levels
        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')

        # Check log counts by level
        assert logger.log_count_by_level('debug') == 1
        assert logger.log_count_by_level('info') == 1
        assert logger.log_count_by_level('warning') == 1
        assert logger.log_count_by_level('error') == 1

        # Check has_logged method
        assert logger.has_logged('debug', 'Debug')
        assert logger.has_logged('info', 'Info')
        assert logger.has_logged('warning', 'Warning')
        assert logger.has_logged('error', 'Error')

        # Get last log
        last_log = logger.last_log()
        assert last_log[0] == 'error'
        assert last_log[1] == 'Error message'

    def test_last_log_exception(self) -> None:
        """Test that last_log raises IndexError on empty logs."""
        logger = FakeLogger()

        # Verify last_log raises IndexError when no logs exist
        import pytest

        with pytest.raises(IndexError, match='No logs have been recorded'):
            logger.last_log()

    def test_has_logged_formatting_failures(self) -> None:
        """Test logging with malformed formatting."""
        logger = FakeLogger()
        logger.debug('Test %s %s', 'value', 'extra')
        assert not logger.has_logged('debug', 'unrelated')

    def test_has_logged_kwargs_path(self) -> None:
        """Test logging with kwargs."""
        logger = FakeLogger()
        logger.debug('Test message: %s', {'key': 'value'})
        assert logger.has_logged('debug', 'message')
