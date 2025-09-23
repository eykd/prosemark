# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""File system implementation of DailyRepo for freeform writing files."""

from datetime import datetime
from pathlib import Path

from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.exceptions import FileSystemError
from prosemark.ports.clock import Clock
from prosemark.ports.daily_repo import DailyRepo
from prosemark.ports.id_generator import IdGenerator


class DailyRepoFs(DailyRepo):
    """File system implementation of DailyRepo for freeform writing files.

    This adapter manages the creation of timestamped freeform writing files
    outside the binder structure with:
    - Filename format: YYYYMMDDTHHMM_<uuid7>.md
    - Optional title in YAML frontmatter
    - Standalone markdown files for quick writing
    - Configurable daily directory for organization

    Example file structure:
    ```
    daily/
    ├── 20250920T0830_0192f0c1-2345-7123-8abc-def012345678.md
    ├── 20250920T1430_0192f0c1-2345-7456-8abc-def012345678.md
    └── ...
    ```

    File content format:
    ```yaml
    ---
    title: "Morning Thoughts"
    id: "0192f0c1-2345-7123-8abc-def012345678"
    created: "2025-09-20T08:30:00Z"
    ---
    # Freeform Writing

    Content goes here...
    ```

    The adapter ensures:
    - Unique filenames with timestamp and UUID components
    - Consistent frontmatter structure
    - Directory creation as needed
    - Proper error handling for file system operations
    """

    def __init__(
        self,
        daily_path: Path,
        id_generator: IdGenerator,
        clock: Clock,
    ) -> None:
        """Initialize repository with daily directory and dependencies.

        Args:
            daily_path: Directory for storing daily freeform files
            id_generator: ID generator for creating unique identifiers
            clock: Clock for timestamp generation

        """
        self.daily_path = daily_path
        self.id_generator = id_generator
        self.clock = clock
        self.frontmatter_codec = FrontmatterCodec()

    def write_freeform(self, title: str | None = None) -> str:
        """Create a new timestamped freewrite file.

        Args:
            title: Optional title to include in the file's frontmatter

        Returns:
            The filename of the created freewrite file

        Raises:
            FileSystemError: If the file cannot be created

        """
        try:
            # Generate unique ID and timestamp
            unique_id = self.id_generator.new()
            now_iso = self.clock.now_iso()

            # Create timestamp prefix for filename
            # Parse ISO format to extract timestamp components
            timestamp = datetime.fromisoformat(now_iso)
            timestamp_prefix = timestamp.strftime('%Y%m%dT%H%M')

            # Build filename
            filename = f'{timestamp_prefix}_{unique_id}.md'
            file_path = self.daily_path / filename

            # Ensure directory exists
            self.daily_path.mkdir(parents=True, exist_ok=True)

            # Prepare frontmatter
            frontmatter = {
                'id': str(unique_id),
                'created': now_iso,
            }

            if title:
                frontmatter['title'] = title

            # Create content with frontmatter
            content_body = '\n# Freeform Writing\n\n'
            full_content = self.frontmatter_codec.generate(frontmatter, content_body)

            # Write file
            file_path.write_text(full_content, encoding='utf-8')
        except OSError as exc:
            msg = f'Cannot create freeform file: {exc}'
            raise FileSystemError(msg) from exc
        else:
            return filename
