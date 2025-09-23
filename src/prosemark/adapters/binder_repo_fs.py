# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""File system implementation of BinderRepo for _binder.md persistence."""

from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser
from prosemark.exceptions import BinderFormatError, BinderNotFoundError, FileSystemError
from prosemark.ports.binder_repo import BinderRepo

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import Binder


class BinderRepoFs(BinderRepo):
    """File system implementation of BinderRepo using _binder.md files.

    This adapter manages the persistence of Binder objects in markdown files
    with managed content blocks. It provides:
    - Round-trip preservation of content outside managed blocks
    - Proper parsing and generation of binder hierarchy from markdown lists
    - Robust error handling for file system operations
    - Integration with frontmatter and markdown parsing codecs

    File format (_binder.md):
    ```
    # Custom Project Notes
    Any content here is preserved outside managed blocks.

    <!-- BEGIN_MANAGED_BLOCK -->
    - [Chapter 1](0192f0c1-2345-7123-8abc-def012345678.md)
      - [Section 1.1](0192f0c1-2345-7456-8abc-def012345678.md)
    - [Chapter 2]()  # Placeholder
    <!-- END_MANAGED_BLOCK -->

    More custom content is preserved here too.
    ```

    The managed block contains the actual binder hierarchy that is parsed
    into domain objects, while preserving all other content.
    """

    MANAGED_BLOCK_START = '<!-- BEGIN_MANAGED_BLOCK -->'
    MANAGED_BLOCK_END = '<!-- END_MANAGED_BLOCK -->'

    def __init__(self, project_path: Path) -> None:
        """Initialize repository with project path.

        Args:
            project_path: Root directory containing _binder.md file

        """
        self.project_path = project_path
        self.binder_file = project_path / '_binder.md'
        self.parser = MarkdownBinderParser()
        self.frontmatter_codec = FrontmatterCodec()

    def load(self) -> 'Binder':
        """Load binder from storage.

        Returns:
            The loaded Binder aggregate

        Raises:
            BinderNotFoundError: If binder file doesn't exist
            FileSystemError: If file cannot be read
            BinderFormatError: If binder content cannot be parsed

        """
        if not self.binder_file.exists():
            msg = 'Binder file not found'
            raise BinderNotFoundError(msg, str(self.binder_file))

        try:
            content = self.binder_file.read_text(encoding='utf-8')
        except OSError as exc:
            msg = f'Cannot read binder file: {exc}'
            raise FileSystemError(msg) from exc

        try:
            # Extract managed block content
            managed_content = self._extract_managed_block(content)

            # Parse binder from managed content
            binder = self.parser.parse_to_binder(managed_content)

            # Store the complete original content for round-trip preservation
            binder.original_content = content  # Store for later saving
            binder.managed_content = managed_content
        except Exception as exc:
            msg = f'Failed to parse binder content: {exc}'
            raise BinderFormatError(msg) from exc
        else:
            return binder

    def save(self, binder: 'Binder') -> None:
        """Save binder to storage.

        Args:
            binder: The Binder aggregate to persist

        Raises:
            FileSystemError: If file cannot be written

        """
        try:
            # Generate managed block content from binder
            managed_content = self.parser.render_from_binder(binder)

            # Preserve existing content or create new structure
            if binder.original_content is not None:
                # Update existing file with preserved content
                updated_content = self._update_managed_block(binder.original_content, managed_content)
            else:
                # Create new file with managed block
                updated_content = self._create_new_content(managed_content)

            # Ensure parent directory exists
            self.binder_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            self.binder_file.write_text(updated_content, encoding='utf-8')

        except OSError as exc:
            msg = f'Cannot write binder file: {exc}'
            raise FileSystemError(msg) from exc

    def _extract_managed_block(self, content: str) -> str:
        """Extract content from managed block markers.

        Args:
            content: Full file content

        Returns:
            Content between managed block markers, or empty string if not found

        Raises:
            BinderFormatError: If managed block start found but no end marker

        """
        start_pos = content.find(self.MANAGED_BLOCK_START)
        if start_pos == -1:
            return ''

        end_pos = content.find(self.MANAGED_BLOCK_END, start_pos)
        if end_pos == -1:
            msg = 'Managed block start found but no end marker'
            raise BinderFormatError(msg)

        # Extract content between markers
        start_pos += len(self.MANAGED_BLOCK_START)
        return content[start_pos:end_pos].strip()

    def _update_managed_block(self, original_content: str, new_managed_content: str) -> str:
        """Update managed block content while preserving other content.

        Args:
            original_content: Original file content
            new_managed_content: New content for managed block

        Returns:
            Updated file content with new managed block

        """
        start_pos = original_content.find(self.MANAGED_BLOCK_START)
        end_pos = original_content.find(self.MANAGED_BLOCK_END)

        if start_pos == -1 or end_pos == -1:
            # No existing managed block, append one
            return self._create_new_content(new_managed_content)

        # Replace content between markers
        before = original_content[: start_pos + len(self.MANAGED_BLOCK_START)]
        after = original_content[end_pos:]

        return f'{before}\n{new_managed_content}\n{after}'

    def _create_new_content(self, managed_content: str) -> str:
        """Create new file content with managed block.

        Args:
            managed_content: Content for the managed block

        Returns:
            Complete file content with managed block structure

        """
        return f"""# Project Structure

{self.MANAGED_BLOCK_START}
{managed_content}
{self.MANAGED_BLOCK_END}
"""
