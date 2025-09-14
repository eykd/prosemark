"""In-memory fake implementation of Logger for testing."""
# ruff: noqa: ANN401 - Any types intentional for stdlib logging compatibility

from typing import Any

from prosemark.ports.logger import Logger


class FakeLogger(Logger):
    """In-memory fake implementation of Logger for testing.

    Provides complete logging functionality by collecting messages
    in memory instead of outputting them. Includes test helper methods
    for asserting logging behavior in tests.

    This fake stores all logged messages with their level and provides methods
    to inspect the logs for test assertions without exposing internal
    implementation details.

    Examples:
        >>> logger = FakeLogger()
        >>> logger.info('Operation completed')
        >>> logger.error('Failed to process %s', 'item')
        >>> logger.get_logs()
        [('info', 'Operation completed', (), {}), ('error', 'Failed to process %s', ('item',), {})]
        >>> logger.get_logs_by_level('info')
        [('info', 'Operation completed', (), {})]
        >>> logger.has_logged('error', 'Failed to process')
        True

    """

    def __init__(self) -> None:
        """Initialize empty fake logger."""
        self._logs: list[tuple[str, Any, tuple[Any, ...], dict[str, Any]]] = []

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Store debug message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('debug', msg, args, kwargs))

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Store info message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('info', msg, args, kwargs))

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Store warning message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('warning', msg, args, kwargs))

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Store error message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('error', msg, args, kwargs))

    def get_logs(self) -> list[tuple[str, Any, tuple[Any, ...], dict[str, Any]]]:
        """Return list of all logged messages.

        Returns:
            List of tuples containing (level, message, args, kwargs) in the order they were logged.

        """
        return self._logs.copy()

    def get_logs_by_level(self, level: str) -> list[tuple[str, Any, tuple[Any, ...], dict[str, Any]]]:
        """Return list of logged messages for a specific level.

        Args:
            level: Log level to filter by ('debug', 'info', 'warning', 'error')

        Returns:
            List of tuples containing (level, message, args, kwargs) for the specified level.

        """
        return [log for log in self._logs if log[0] == level]

    def has_logged(self, level: str, text: str) -> bool:
        """Check if any log message at the given level contains the text.

        Args:
            level: Log level to check ('debug', 'info', 'warning', 'error')
            text: Text to search for in log messages

        Returns:
            True if any message at the specified level contains the given text.

        """
        level_logs = self.get_logs_by_level(level)
        return any(text in str(log[1]) for log in level_logs)

    def clear_logs(self) -> None:
        """Clear all stored log messages.

        Useful for resetting state between test cases.

        """
        self._logs.clear()

    def last_log(self) -> tuple[str, Any, tuple[Any, ...], dict[str, Any]]:
        """Return the last logged message.

        Returns:
            Tuple containing (level, message, args, kwargs) for the most recent log entry.

        Raises:
            IndexError: If no messages have been logged.

        """
        if not self._logs:  # pragma: no cover
            raise IndexError('No logs have been recorded')  # pragma: no cover
        return self._logs[-1]  # pragma: no cover

    def log_count(self) -> int:
        """Return the total number of logged messages.

        Returns:
            Total count of all logged messages across all levels.

        """
        return len(self._logs)

    def log_count_by_level(self, level: str) -> int:
        """Return the count of logged messages for a specific level.

        Args:
            level: Log level to count ('debug', 'info', 'warning', 'error')

        Returns:
            Count of messages for the specified level.

        """
        return len(self.get_logs_by_level(level))
