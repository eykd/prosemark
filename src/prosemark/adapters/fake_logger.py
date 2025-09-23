# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""In-memory fake implementation of Logger for testing."""

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
        self._logs: list[tuple[str, object, tuple[object, ...], dict[str, object]]] = []

    def debug(self, msg: object, *args: object, **kwargs: object) -> None:
        """Store debug message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('debug', msg, args, kwargs))

    def info(self, msg: object, *args: object, **kwargs: object) -> None:
        """Store info message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('info', msg, args, kwargs))

    def warning(self, msg: object, *args: object, **kwargs: object) -> None:
        """Store warning message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('warning', msg, args, kwargs))

    def error(self, msg: object, *args: object, **kwargs: object) -> None:
        """Store error message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('error', msg, args, kwargs))

    def exception(self, msg: object, *args: object, **kwargs: object) -> None:
        """Store exception message in log buffer.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for structured logging

        """
        self._logs.append(('exception', msg, args, kwargs))

    def get_logs(self) -> list[tuple[str, object, tuple[object, ...], dict[str, object]]]:
        """Return list of all logged messages.

        Returns:
            List of tuples containing (level, message, args, kwargs) in the order they were logged.

        """
        return self._logs.copy()

    def get_logs_by_level(self, level: str) -> list[tuple[str, object, tuple[object, ...], dict[str, object]]]:
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
        for log in level_logs:
            # Check raw message
            if text in str(log[1]):
                return True
            # Check formatted message if args are present
            if log[2]:  # args tuple is not empty
                try:
                    formatted_msg = str(log[1]) % log[2]
                    if text in formatted_msg:
                        return True
                except (TypeError, ValueError):  # pragma: no cover
                    # If formatting fails, continue to next log
                    pass
        return False

    def get_logged_messages(self) -> list[str]:
        """Get all logged messages formatted as strings.

        Returns:
            List of formatted log messages as strings.

        """
        messages = []
        for _level, msg, args, kwargs in self._logs:
            if args:
                try:
                    formatted_msg = str(msg) % args
                except (TypeError, ValueError):  # pragma: no cover
                    formatted_msg = f'{msg} {args}'
            else:
                formatted_msg = str(msg)

            # Append kwargs if present
            if kwargs:
                formatted_msg += f' {kwargs!r}'

            messages.append(formatted_msg)
        return messages

    def clear_logs(self) -> None:
        """Clear all stored log messages.

        Useful for resetting state between test cases.

        """
        self._logs.clear()

    def last_log(self) -> tuple[str, object, tuple[object, ...], dict[str, object]]:
        """Return the last logged message.

        Returns:
            Tuple containing (level, message, args, kwargs) for the most recent log entry.

        Raises:
            IndexError: If no messages have been logged.

        """
        if not self._logs:  # pragma: no cover
            msg = 'No logs have been recorded'
            raise IndexError(msg)  # pragma: no cover
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

    @property
    def info_messages(self) -> list[str]:
        """Get formatted info messages."""
        return [str(log[1]) % log[2] if log[2] else str(log[1]) for log in self.get_logs_by_level('info')]

    @property
    def error_messages(self) -> list[str]:
        """Get formatted error messages."""
        return [str(log[1]) % log[2] if log[2] else str(log[1]) for log in self.get_logs_by_level('error')]

    @property
    def debug_messages(self) -> list[str]:
        """Get formatted debug messages."""
        return [str(log[1]) % log[2] if log[2] else str(log[1]) for log in self.get_logs_by_level('debug')]

    @property
    def exception_messages(self) -> list[str]:
        """Get formatted exception messages."""
        return [str(log[1]) % log[2] if log[2] else str(log[1]) for log in self.get_logs_by_level('exception')]

    def clear(self) -> None:
        """Alias for clear_logs for convenience."""
        self.clear_logs()
