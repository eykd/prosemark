# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Fake clock adapter for testing time-dependent operations."""

from prosemark.ports.clock import Clock


class FakeClock(Clock):
    """In-memory fake implementation of Clock for testing.

    Provides deterministic timestamp generation for tests by returning
    a fixed ISO8601 timestamp. Can be initialized with a specific
    timestamp or uses a default value.

    This fake always returns the same timestamp value, ensuring
    reproducible test behavior for time-dependent operations.

    Examples:
        >>> clock = FakeClock()
        >>> clock.now_iso()
        '2025-09-13T12:00:00Z'
        >>> custom_clock = FakeClock('2025-01-01T00:00:00Z')
        >>> custom_clock.now_iso()
        '2025-01-01T00:00:00Z'

    """

    def __init__(self, fixed_time: str = '2025-09-13T12:00:00Z') -> None:
        """Initialize fake clock with a fixed timestamp.

        Args:
            fixed_time: ISO8601 formatted timestamp to always return.
                Defaults to '2025-09-13T12:00:00Z'.

        """
        self._fixed_time = fixed_time

    def now_iso(self) -> str:
        """Return the fixed timestamp.

        Returns:
            The fixed ISO8601 timestamp provided at initialization.

        """
        return self._fixed_time
