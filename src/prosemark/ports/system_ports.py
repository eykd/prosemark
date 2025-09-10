"""System integration port protocols."""

from typing import Protocol, runtime_checkable

from prosemark.domain.value_objects import NodeId


@runtime_checkable
class IdGenerator(Protocol):
    """Protocol for generating unique node identifiers.

    Generates UUIDv7 identifiers that are time-ordered and globally unique.
    """

    def new(self) -> NodeId:
        """Generate a new unique NodeId.

        Returns:
            NodeId: A new UUIDv7-based node identifier

        """
        ...


@runtime_checkable
class Clock(Protocol):
    """Protocol for time services.

    Provides UTC timestamps in ISO8601 format for tracking
    node creation and update times.
    """

    def now_iso(self) -> str:
        """Get current time as ISO8601 string.

        Returns:
            str: Current UTC time in ISO8601 format

        """
        ...


@runtime_checkable
class Logger(Protocol):
    """Protocol for structured logging services.

    Provides leveled logging capabilities for application
    events, errors, and debugging information.
    """

    def info(self, msg: str) -> None:
        """Log informational message.

        Args:
            msg: Message to log

        """
        ...

    def warn(self, msg: str) -> None:
        """Log warning message.

        Args:
            msg: Warning message to log

        """
        ...

    def error(self, msg: str) -> None:
        """Log error message.

        Args:
            msg: Error message to log

        """
        ...
