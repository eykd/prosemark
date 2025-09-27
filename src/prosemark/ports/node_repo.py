"""NodeRepo abstract base class for node file operations."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import NodeId


class NodeRepo(ABC):
    """Abstract base class for node file operations.

    The NodeRepo defines the contract for managing node files ({id}.md and {id}.notes.md).
    It handles frontmatter operations, file lifecycle, and editor integration.

    All implementations must handle:
    - Node file creation with proper frontmatter structure
    - Reading and writing frontmatter metadata
    - Editor integration for different node parts
    - Node deletion with configurable file removal

    File Structure:
    - {id}.md: Node draft content with frontmatter
    - {id}.notes.md: Node notes content (may or may not have frontmatter)

    Frontmatter Format:
    The frontmatter should be in YAML format with these fields:
    - id: NodeId as string (required)
    - title: Optional title string
    - synopsis: Optional synopsis string
    - created: ISO 8601 timestamp string (required)
    - updated: ISO 8601 timestamp string (required, auto-updated)
    """

    @abstractmethod
    def create(self, node_id: 'NodeId', title: str | None, synopsis: str | None) -> None:
        """Create new node files with initial frontmatter.

        Creates both {id}.md and {id}.notes.md files with appropriate
        frontmatter and initial content structure.

        Args:
            node_id: Unique identifier for the node
            title: Optional title for the node
            synopsis: Optional synopsis/summary for the node

        Raises:
            FilesystemError: If files cannot be created
            NodeIdentityError: If node with this ID already exists

        """

    @abstractmethod
    def read_frontmatter(self, node_id: 'NodeId') -> dict[str, str | None]:
        """Read frontmatter from node draft file.

        Parses the YAML frontmatter from the {id}.md file and returns
        it as a dictionary.

        Args:
            node_id: NodeId to read frontmatter for

        Returns:
            Dictionary containing frontmatter fields:
            - id: NodeId as string
            - title: Title string or None
            - synopsis: Synopsis string or None
            - created: ISO 8601 timestamp string
            - updated: ISO 8601 timestamp string

        Raises:
            NodeNotFoundError: If node file doesn't exist
            FilesystemError: If file cannot be read
            ValueError: If frontmatter format is invalid

        """

    @abstractmethod
    def write_frontmatter(self, node_id: 'NodeId', fm: dict[str, str | None]) -> None:
        """Update frontmatter in node draft file.

        Updates the YAML frontmatter in the {id}.md file. The 'updated'
        timestamp should be automatically set to the current time.

        Args:
            node_id: NodeId to update frontmatter for
            fm: Dictionary containing frontmatter fields to write

        Raises:
            NodeNotFoundError: If node file doesn't exist
            FilesystemError: If file cannot be written
            ValueError: If frontmatter data is invalid

        """

    @abstractmethod
    def open_in_editor(self, node_id: 'NodeId', part: str) -> None:
        """Open specified node part in editor.

        Launches the configured editor to edit the specified part of the node.

        Args:
            node_id: NodeId to open in editor
            part: Which part to open - must be one of:
                  - 'draft': Open {id}.md file
                  - 'notes': Open {id}.notes.md file
                  - 'synopsis': Open {id}.md file focused on synopsis

        Raises:
            NodeNotFoundError: If node file doesn't exist
            ValueError: If part is not a valid option
            FilesystemError: If editor cannot be launched

        """

    @abstractmethod
    def delete(self, node_id: 'NodeId', *, delete_files: bool) -> None:
        """Remove node from system.

        Removes the node from the system, optionally deleting the actual
        files from the filesystem.

        Args:
            node_id: NodeId to delete
            delete_files: If True, delete actual {id}.md and {id}.notes.md files.
                         If False, just remove from any internal tracking.

        Raises:
            NodeNotFoundError: If node doesn't exist
            FilesystemError: If files cannot be deleted (when delete_files=True)

        """

    @abstractmethod
    def get_existing_files(self) -> set['NodeId']:
        """Get all existing node files from the filesystem.

        Scans the project directory for node files ({id}.md) and returns
        the set of NodeIds that have existing files.

        Returns:
            Set of NodeIds for files that exist on disk

        Raises:
            FileSystemError: If directory cannot be scanned

        """

    @abstractmethod
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

    @abstractmethod
    def create_notes_file(self, node_id: 'NodeId') -> None:
        """Create only the notes file for an existing node.

        Creates the {id}.notes.md file with obsidian-style link to the node.
        This is used when the draft file exists but the notes file is missing.

        Args:
            node_id: NodeId for the node that needs a notes file

        Raises:
            FileSystemError: If notes file cannot be created

        """
