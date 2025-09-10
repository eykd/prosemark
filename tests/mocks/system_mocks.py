"""Mock implementations for system protocols."""

from datetime import UTC, datetime

from uuid_extension import uuid7

from prosemark.domain.value_objects import NodeId


class MockIdGenerator:
    """Mock implementation of IdGenerator for testing."""

    def __init__(self, fixed_ids: list[str] | None = None) -> None:
        """Initialize with optional fixed ID sequence.

        Args:
            fixed_ids: If provided, will return these IDs in order, then generate random ones

        """
        self._fixed_ids = fixed_ids or []
        self._fixed_index = 0
        self.new_called = 0
        self._generated_ids: list[str] = []

    def new(self) -> NodeId:
        """Generate a new NodeId."""
        self.new_called += 1

        if self._fixed_index < len(self._fixed_ids):
            # Return fixed ID
            node_id_str = self._fixed_ids[self._fixed_index]
            self._fixed_index += 1
        else:
            # Generate UUIDv7
            node_id_str = str(uuid7())

        self._generated_ids.append(node_id_str)
        return NodeId(node_id_str)

    def get_generated_ids(self) -> list[str]:
        """Get list of all generated IDs."""
        return self._generated_ids.copy()


class MockClock:
    """Mock implementation of Clock for testing."""

    def __init__(self, fixed_time: str | None = None) -> None:
        """Initialize with optional fixed time.

        Args:
            fixed_time: If provided, will always return this time

        """
        self._fixed_time = fixed_time
        self._call_times: list[str] = []
        self.now_iso_called = 0

    def now_iso(self) -> str:
        """Get current time as ISO8601 string."""
        self.now_iso_called += 1

        timestamp = self._fixed_time or datetime.now(UTC).isoformat()

        self._call_times.append(timestamp)
        return timestamp

    def get_call_times(self) -> list[str]:
        """Get list of all returned timestamps."""
        return self._call_times.copy()

    def set_fixed_time(self, time_str: str) -> None:
        """Set a fixed time to return."""
        self._fixed_time = time_str

    def clear_fixed_time(self) -> None:
        """Clear fixed time, return to real time."""
        self._fixed_time = None


class MockLogger:
    """Mock implementation of Logger for testing."""

    def __init__(self) -> None:
        """Initialize empty logger."""
        self._logs: list[tuple[str, str]] = []  # (level, message) pairs
        self.info_called = 0
        self.warn_called = 0
        self.error_called = 0

    def info(self, msg: str) -> None:
        """Log info message."""
        self.info_called += 1
        self._logs.append(('info', msg))

    def warn(self, msg: str) -> None:
        """Log warning message."""
        self.warn_called += 1
        self._logs.append(('warn', msg))

    def error(self, msg: str) -> None:
        """Log error message."""
        self.error_called += 1
        self._logs.append(('error', msg))

    def get_logs(self) -> list[tuple[str, str]]:
        """Get all logged messages as (level, message) pairs."""
        return self._logs.copy()

    def get_logs_by_level(self, level: str) -> list[str]:
        """Get all messages for a specific level."""
        return [msg for log_level, msg in self._logs if log_level == level]

    def clear_logs(self) -> None:
        """Clear all logged messages."""
        self._logs.clear()
        self.info_called = 0
        self.warn_called = 0
        self.error_called = 0

    def has_log_containing(self, text: str, level: str | None = None) -> bool:
        """Check if any log message contains the given text.

        Args:
            text: Text to search for in log messages
            level: Optional level filter

        Returns:
            bool: True if any message contains the text

        """
        logs_to_check = self._logs
        if level:
            logs_to_check = [(log_level, msg) for log_level, msg in self._logs if log_level == level]

        return any(text in msg for _, msg in logs_to_check)
