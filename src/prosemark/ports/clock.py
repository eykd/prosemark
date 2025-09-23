"""Abstract base class for timestamp management."""

from abc import ABC, abstractmethod


class Clock(ABC):
    """Abstract base class for timestamp management.

    Defines the minimal interface for generating ISO8601 UTC timestamps
    used throughout the system. This abstract base class enables:

    * Consistent timestamp formatting across all operations
    * Testable time-dependent behavior through dependency injection
    * Support for different time sources (system clock, fixed time for tests)
    * Hexagonal architecture compliance by isolating system time concerns

    The MVP uses UTC timestamps in ISO8601 format for created/updated frontmatter
    fields and freewrite filenames. Expected format examples:
    - "2025-09-10T10:00:00-07:00" (with timezone offset)
    - "2025-09-10T17:00:00Z" (UTC timezone)

    Examples:
        >>> class TestClock(Clock):
        ...     def now_iso(self) -> str:
        ...         return '2025-09-10T17:00:00Z'
        >>> clock = TestClock()
        >>> timestamp = clock.now_iso()
        >>> isinstance(timestamp, str)
        True

    """

    @abstractmethod
    def now_iso(self) -> str:
        """Generate current timestamp in ISO8601 UTC format.

        This method must be implemented by concrete subclasses to provide
        specific timestamp generation strategies (system clock, fixed time, etc.).

        Returns:
            Current timestamp as ISO8601 formatted string in UTC.
            Expected formats: "2025-09-10T17:00:00Z" or "2025-09-10T10:00:00-07:00"

        Raises:
            NotImplementedError: If not implemented by a concrete subclass

        """
        msg = 'Subclasses must implement the now_iso() method'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover
