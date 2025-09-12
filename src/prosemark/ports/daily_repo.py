"""DailyRepo abstract base class for freewrite management.

This module defines the DailyRepo abstract base class which provides
the contract for creating timestamped freewrite files outside the
binder structure. Freewrites are standalone markdown files with
optional titles and UUIDv7 identifiers.
"""

from abc import ABC, abstractmethod


class DailyRepo(ABC):
    """Abstract base class for daily freewrite file management.

    The DailyRepo provides a simple interface for creating timestamped
    freewrite files that exist outside the binder hierarchy. These files
    offer frictionless writing opportunities with automatic timestamping
    and unique identification.

    Implementations should:
    - Generate filenames with format: YYYYMMDDTHHMM_<uuid7>.md
    - Support optional title in frontmatter
    - Create standalone files (no binder integration)
    - Use UUIDv7 for unique identification

    This abstract base class supports the hexagonal architecture by
    isolating freewrite file creation logic from the domain and
    application layers, enabling different storage mechanisms while
    maintaining consistent behavior.
    """

    @abstractmethod
    def write_freeform(self, title: str | None = None) -> str:
        """Create a new timestamped freewrite file.

        Creates a new markdown file with a timestamped filename and
        optional title in the frontmatter. The file is created as a
        standalone entity outside any binder structure.

        Args:
            title: Optional title to include in the file's frontmatter.
                   If provided, will be added as a 'title' field in the
                   YAML frontmatter block.

        Returns:
            The filename of the created freewrite file, following the
            format YYYYMMDDTHHMM_<uuid7>.md

        Raises:
            FilesystemError: If the file cannot be created due to I/O
                           errors, permission issues, or disk space
                           constraints.

        Example:
            >>> repo = FilesystemDailyRepo('/path/to/daily')
            >>> filename = repo.write_freeform('Morning Thoughts')
            >>> print(filename)
            "20250911T0830_01932c5a-7f3e-7000-8000-000000000001.md"

        """
