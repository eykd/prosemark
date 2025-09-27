# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""File system implementation of NodeRepo for node file operations."""

from pathlib import Path
from typing import Any, ClassVar

from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.domain.models import NodeId
from prosemark.exceptions import (
    EditorError,
    FileSystemError,
    FrontmatterFormatError,
    InvalidPartError,
    NodeAlreadyExistsError,
    NodeIdentityError,
    NodeNotFoundError,
)
from prosemark.ports.clock import Clock
from prosemark.ports.editor_port import EditorPort
from prosemark.ports.node_repo import NodeRepo


class NodeRepoFs(NodeRepo):
    """File system implementation of NodeRepo for managing node files.

    This adapter manages the persistence of individual node files with:
    - {id}.md files for draft content with YAML frontmatter
    - {id}.notes.md files for notes (optional frontmatter)
    - Frontmatter parsing and generation using FrontmatterCodec
    - Editor integration for opening specific node parts
    - Proper error handling for file system operations

    Frontmatter structure in {id}.md:
    ```yaml
    ---
    id: "0192f0c1-2345-7123-8abc-def012345678"
    title: "Node Title"
    synopsis: "Brief description"
    created: "2025-09-20T15:30:00Z"
    updated: "2025-09-20T16:00:00Z"
    ---
    # Node Content
    ```

    The adapter ensures:
    - Consistent frontmatter format across all node files
    - Automatic timestamp management (created on create, updated on modify)
    - Editor integration with proper part handling
    - Robust file system error handling
    """

    VALID_PARTS: ClassVar[set[str]] = {'draft', 'notes', 'synopsis'}

    # UUID7 format constants
    UUID7_LENGTH = 36  # Total length of UUID7 string (8-4-4-4-12)
    UUID7_PARTS_COUNT = 5  # Number of hyphen-separated parts
    MIN_NODE_ID_LENGTH = 3  # Minimum length for reasonable node ID

    def __init__(
        self,
        project_path: Path,
        editor: EditorPort,
        clock: Clock,
    ) -> None:
        """Initialize repository with project path and dependencies.

        Args:
            project_path: Root directory containing node files
            editor: Editor port for launching external editor
            clock: Clock port for timestamp generation

        """
        self.project_path = project_path
        self.editor = editor
        self.clock = clock
        self.frontmatter_codec = FrontmatterCodec()

    def create(self, node_id: 'NodeId', title: str | None, synopsis: str | None) -> None:
        """Create new node files with initial frontmatter.

        Args:
            node_id: Unique identifier for the node
            title: Optional title for the node
            synopsis: Optional synopsis/summary for the node

        Raises:
            NodeAlreadyExistsError: If node with this ID already exists
            FileSystemError: If files cannot be created

        """
        draft_file = self.project_path / f'{node_id}.md'
        notes_file = self.project_path / f'{node_id}.notes.md'

        # Check if files already exist
        if draft_file.exists() or notes_file.exists():
            msg = f'Node files already exist for {node_id}'
            raise NodeAlreadyExistsError(msg)

        try:
            # Create timestamp
            now = self.clock.now_iso()

            # Prepare frontmatter
            frontmatter = {
                'id': str(node_id),
                'title': title,
                'synopsis': synopsis,
                'created': now,
                'updated': now,
            }

            # Create draft file with frontmatter
            draft_content = self.frontmatter_codec.generate(frontmatter, '')
            draft_file.write_text(draft_content, encoding='utf-8')

            # Create notes file with obsidian-style link to node file
            notes_content = f'# Notes\n\n[[{node_id}]]\n'
            notes_file.write_text(notes_content, encoding='utf-8')

        except OSError as exc:
            msg = f'Cannot create node files: {exc}'
            raise FileSystemError(msg) from exc

    def read_frontmatter(self, node_id: 'NodeId') -> dict[str, Any]:
        """Read frontmatter from node draft file.

        Args:
            node_id: NodeId to read frontmatter for

        Returns:
            Dictionary containing frontmatter fields

        Raises:
            NodeNotFoundError: If node file doesn't exist
            FileSystemError: If file cannot be read
            FrontmatterFormatError: If frontmatter format is invalid

        """
        draft_file = self.project_path / f'{node_id}.md'

        if not draft_file.exists():
            msg = f'Node file not found: {draft_file}'
            raise NodeNotFoundError(msg)

        try:
            content = draft_file.read_text(encoding='utf-8')
        except OSError as exc:
            msg = f'Cannot read node file: {exc}'
            raise FileSystemError(msg) from exc

        try:
            frontmatter, _ = self.frontmatter_codec.parse(content)
        except Exception as exc:
            msg = f'Invalid frontmatter in {draft_file}'
            raise FrontmatterFormatError(msg) from exc
        else:
            return frontmatter

    def write_frontmatter(self, node_id: 'NodeId', frontmatter: dict[str, Any]) -> None:
        """Update frontmatter in node draft file.

        Args:
            node_id: NodeId to update frontmatter for
            frontmatter: Dictionary containing frontmatter fields to write

        Raises:
            NodeNotFoundError: If node file doesn't exist
            FileSystemError: If file cannot be written

        """
        draft_file = self.project_path / f'{node_id}.md'

        if not draft_file.exists():
            msg = f'Node file not found: {draft_file}'
            raise NodeNotFoundError(msg)

        try:
            # Read existing content
            content = draft_file.read_text(encoding='utf-8')

            # Update timestamp
            updated_frontmatter = frontmatter.copy()
            updated_frontmatter['updated'] = self.clock.now_iso()

            # Update frontmatter
            updated_content = self.frontmatter_codec.update_frontmatter(content, updated_frontmatter)

            # Write back
            draft_file.write_text(updated_content, encoding='utf-8')

        except OSError as exc:
            msg = f'Cannot write node file: {exc}'
            raise FileSystemError(msg) from exc

    def open_in_editor(self, node_id: 'NodeId', part: str) -> None:
        """Open specified node part in editor.

        Args:
            node_id: NodeId to open in editor
            part: Which part to open ('draft', 'notes', 'synopsis')

        Raises:
            NodeNotFoundError: If node file doesn't exist
            InvalidPartError: If part is not a valid option
            EditorError: If editor cannot be launched

        """
        if part not in self.VALID_PARTS:
            msg = f'Invalid part: {part}. Must be one of {self.VALID_PARTS}'
            raise InvalidPartError(msg)

        # Determine which file to open
        if part == 'notes':
            file_path = self.project_path / f'{node_id}.notes.md'
        else:
            # Both 'draft' and 'synopsis' open the main draft file
            file_path = self.project_path / f'{node_id}.md'

        if not file_path.exists():
            msg = f'Node file not found: {file_path}'
            raise NodeNotFoundError(msg)

        try:
            # For synopsis, provide cursor hint to focus on frontmatter area
            cursor_hint = '1' if part == 'synopsis' else None
            self.editor.open(str(file_path), cursor_hint=cursor_hint)

        except Exception as exc:
            msg = f'Failed to open editor for {file_path}'
            raise EditorError(msg) from exc

    def delete(self, node_id: 'NodeId', *, delete_files: bool = True) -> None:
        """Remove node from system.

        Args:
            node_id: NodeId to delete
            delete_files: If True, delete actual files from filesystem

        Raises:
            FileSystemError: If files cannot be deleted (when delete_files=True)

        """
        if not delete_files:
            # No-op for file system implementation when not deleting files
            return

        draft_file = self.project_path / f'{node_id}.md'
        notes_file = self.project_path / f'{node_id}.notes.md'

        try:
            # Delete files if they exist
            if draft_file.exists():
                draft_file.unlink()

            if notes_file.exists():
                notes_file.unlink()

        except OSError as exc:
            msg = f'Cannot delete node files: {exc}'
            raise FileSystemError(msg) from exc

    def get_existing_files(self) -> set['NodeId']:
        """Get all existing node files from the filesystem.

        Scans the project directory for node files ({id}.md) and returns
        the set of NodeIds that have existing files.

        Returns:
            Set of NodeIds for files that exist on disk

        Raises:
            FileSystemError: If directory cannot be scanned

        """
        try:
            existing_files = set()
            for md_file in self.project_path.glob('*.md'):
                # Skip non-node files like _binder.md and README.md
                if md_file.stem.startswith('_') or not self._is_valid_node_id(md_file.stem):
                    continue

                # Skip .notes.md files as they are secondary files
                if md_file.stem.endswith('.notes'):  # pragma: no cover
                    continue  # pragma: no cover

                # The filename should be the NodeId
                try:
                    node_id = NodeId(md_file.stem)
                    existing_files.add(node_id)
                except NodeIdentityError:
                    # Skip files that aren't valid NodeIds
                    continue

        except OSError as exc:
            msg = f'Cannot scan directory for node files: {exc}'
            raise FileSystemError(msg) from exc
        else:
            return existing_files

    def _is_valid_node_id(self, filename: str) -> bool:
        """Check if a filename looks like a valid NodeId.

        A valid NodeId should be a UUID7 format string, but we'll also
        accept any reasonable identifier for audit purposes.

        Args:
            filename: The filename (without extension) to check

        Returns:
            True if the filename appears to be a valid NodeId

        """
        # Skip empty filenames
        if not filename:
            return False

        # Check for UUID7 format first
        if self._is_uuid7_format(filename):
            return True

        # Also accept other reasonable node IDs for audit purposes
        return self._is_reasonable_node_id(filename)

    def _is_uuid7_format(self, filename: str) -> bool:
        """Check if filename matches UUID7 format (8-4-4-4-12).

        Returns:
            True if filename matches UUID7 format, False otherwise

        """
        if len(filename) != self.UUID7_LENGTH:
            return False

        parts = filename.split('-')
        if len(parts) != self.UUID7_PARTS_COUNT:
            return False

        expected_lengths = [8, 4, 4, 4, 12]
        if not all(
            len(part) == expected_length for part, expected_length in zip(parts, expected_lengths, strict=False)
        ):
            return False

        # Check if all characters are valid hex
        try:
            for part in parts:
                int(part, 16)
        except ValueError:
            return False
        else:
            return True

    def _is_reasonable_node_id(self, filename: str) -> bool:
        """Check if filename is a reasonable node ID for audit purposes.

        Returns:
            True if filename appears to be a reasonable node ID

        """
        # Must be at least 3 characters, alphanumeric plus hyphens/underscores
        if len(filename) < self.MIN_NODE_ID_LENGTH or not all(c.isalnum() or c in '-_' for c in filename):
            return False

        # Must not be a reserved name
        reserved_names = {'readme', 'license', 'changelog', 'todo', 'notes'}
        return filename.lower() not in reserved_names

    def file_exists(self, node_id: 'NodeId', file_type: str) -> bool:
        """Check if a specific node file exists.

        Args:
            node_id: NodeId to check
            file_type: Type of file to check ('draft' for {id}.md, 'notes' for {id}.notes.md)

        Returns:
            True if the file exists, False otherwise

        Raises:
            ValueError: If file_type is not valid

        """
        if file_type == 'draft':
            file_path = self.project_path / f'{node_id}.md'
        elif file_type == 'notes':
            file_path = self.project_path / f'{node_id}.notes.md'
        else:
            msg = f'Invalid file_type: {file_type}. Must be "draft" or "notes"'
            raise ValueError(msg)

        return file_path.exists()

    def create_notes_file(self, node_id: 'NodeId') -> None:
        """Create only the notes file for an existing node.

        Creates the {id}.notes.md file with obsidian-style link to the node.
        This is used when the draft file exists but the notes file is missing.

        Args:
            node_id: NodeId for the node that needs a notes file

        Raises:
            FileSystemError: If notes file cannot be created

        """
        notes_file = self.project_path / f'{node_id}.notes.md'

        try:
            # Create notes file with obsidian-style link to node file
            notes_content = f'# Notes\n\n[[{node_id}]]\n'
            notes_file.write_text(notes_content, encoding='utf-8')

        except OSError as exc:  # pragma: no cover
            msg = f'Cannot create notes file: {exc}'
            raise FileSystemError(msg) from exc
