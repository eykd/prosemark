"""Tests for FakeLogger test double."""

import pytest

from prosemark.adapters.fake_logger import FakeLogger


class TestFakeLogger:
    """Test suite for FakeLogger functionality."""

    @pytest.fixture
    def logger(self) -> FakeLogger:
        """FakeLogger instance for testing."""
        return FakeLogger()

    def test_logger_starts_empty(self, logger: FakeLogger) -> None:
        """Test logger starts with no messages."""
        assert logger.log_count() == 0
        assert logger.get_logs() == []

    def test_debug_logging(self, logger: FakeLogger) -> None:
        """Test debug level logging."""
        logger.debug('Debug message')
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0] == ('debug', 'Debug message', (), {})

    def test_info_logging(self, logger: FakeLogger) -> None:
        """Test info level logging."""
        logger.info('Info message')
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0] == ('info', 'Info message', (), {})

    def test_warning_logging(self, logger: FakeLogger) -> None:
        """Test warning level logging."""
        logger.warning('Warning message')
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0] == ('warning', 'Warning message', (), {})

    def test_error_logging(self, logger: FakeLogger) -> None:
        """Test error level logging."""
        logger.error('Error message')
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0] == ('error', 'Error message', (), {})

    def test_logging_with_args(self, logger: FakeLogger) -> None:
        """Test logging with format arguments."""
        logger.info('Message with %s', 'args')
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0] == ('info', 'Message with %s', ('args',), {})

    def test_logging_with_kwargs(self, logger: FakeLogger) -> None:
        """Test logging with keyword arguments."""
        logger.info('Message', extra={'key': 'value'})
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0] == ('info', 'Message', (), {'extra': {'key': 'value'}})

    def test_get_logs_by_level(self, logger: FakeLogger) -> None:
        """Test filtering logs by level."""
        logger.debug('Debug')
        logger.info('Info')
        logger.warning('Warning')
        logger.error('Error')

        debug_logs = logger.get_logs_by_level('debug')
        assert len(debug_logs) == 1
        assert debug_logs[0][1] == 'Debug'

        info_logs = logger.get_logs_by_level('info')
        assert len(info_logs) == 1
        assert info_logs[0][1] == 'Info'

        error_logs = logger.get_logs_by_level('error')
        assert len(error_logs) == 1
        assert error_logs[0][1] == 'Error'

    def test_has_logged_partial_match(self, logger: FakeLogger) -> None:
        """Test has_logged with partial text matching."""
        logger.info('A longer message about something')
        assert logger.has_logged('info', 'longer message')
        assert logger.has_logged('info', 'about')
        assert not logger.has_logged('info', 'not found')
        assert not logger.has_logged('error', 'longer message')

    def test_clear_logs(self, logger: FakeLogger) -> None:
        """Test clearing all logs."""
        logger.info('Message 1')
        logger.error('Message 2')
        assert logger.log_count() == 2

        logger.clear_logs()
        assert logger.log_count() == 0
        assert logger.get_logs() == []

    def test_log_count_by_level(self, logger: FakeLogger) -> None:
        """Test counting logs by specific level."""
        logger.info('Info 1')
        logger.info('Info 2')
        logger.error('Error 1')
        logger.debug('Debug 1')

        assert logger.log_count_by_level('info') == 2
        assert logger.log_count_by_level('error') == 1
        assert logger.log_count_by_level('debug') == 1
        assert logger.log_count_by_level('warning') == 0

    def test_last_log(self, logger: FakeLogger) -> None:
        """Test getting the last logged message."""
        logger.info('First')
        logger.error('Second')
        logger.debug('Third')

        last = logger.last_log()
        assert last == ('debug', 'Third', (), {})

    def test_last_log_with_empty_logs(self, logger: FakeLogger) -> None:
        """Test last_log raises IndexError when no logs exist."""
        with pytest.raises(IndexError, match='No logs have been recorded'):
            logger.last_log()

    def test_multiple_logging_maintains_order(self, logger: FakeLogger) -> None:
        """Test that multiple log messages maintain insertion order."""
        logger.debug('First')
        logger.info('Second')
        logger.warning('Third')
        logger.error('Fourth')

        logs = logger.get_logs()
        assert len(logs) == 4
        assert logs[0][1] == 'First'
        assert logs[1][1] == 'Second'
        assert logs[2][1] == 'Third'
        assert logs[3][1] == 'Fourth'

    def test_get_logs_returns_copy(self, logger: FakeLogger) -> None:
        """Test that get_logs returns a copy of the internal list."""
        logger.info('Message')
        logs1 = logger.get_logs()
        logs2 = logger.get_logs()

        # They should be equal but not the same object
        assert logs1 == logs2
        assert logs1 is not logs2

        # Modifying one shouldn't affect the other
        logs1.append(('info', 'Modified', (), {}))
        assert len(logs2) == 1
