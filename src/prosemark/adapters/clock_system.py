# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""System clock implementation for timestamp generation."""

from datetime import UTC, datetime

from prosemark.ports.clock import Clock


class ClockSystem(Clock):
    """Production clock implementation using system time.

    This implementation provides real system timestamps in ISO8601 UTC format.
    It uses Python's datetime module to generate consistent, UTC-based timestamps
    that can be used for:
    - Node frontmatter created/updated fields
    - Freeform content file timestamps
    - Any system-wide time tracking needs

    The generated timestamps are always in UTC timezone with 'Z' suffix
    for consistency and to avoid timezone-related issues.
    """

    def now_iso(self) -> str:
        """Generate current timestamp in ISO8601 UTC format.

        Returns:
            Current system time as ISO8601 formatted string in UTC with 'Z' suffix
            Format: "2025-09-20T15:30:45Z"

        """
        return datetime.now(UTC).isoformat().replace('+00:00', 'Z')
