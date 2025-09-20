"""File system implementation of NodeRepo for node file operations."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.exceptions import (
    EditorError,
    FileSystemError,
    FrontmatterFormatError,
    InvalidPartError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
)
from prosemark.ports.clock import Clock
from prosemark.ports.editor_port import EditorPort
from prosemark.ports.node_repo import NodeRepo

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import NodeId


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
            draft_content = self.frontmatter_codec.generate(frontmatter, '\n# Draft Content\n')
            draft_file.write_text(draft_content, encoding='utf-8')

            # Create notes file (minimal content, no frontmatter needed)
            notes_content = '# Notes\n'
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
