# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""In-memory fake implementation of NodeRepo for testing."""

from prosemark.domain.models import NodeId
from prosemark.exceptions import NodeIdentityError, NodeNotFoundError
from prosemark.ports.node_repo import NodeRepo


class FakeNodeRepo(NodeRepo):
    """In-memory fake implementation of NodeRepo for testing.

    Provides complete node file management functionality using memory storage
    instead of filesystem operations. Maintains the same interface contract as
    production implementations but without actual file I/O.

    This fake stores node frontmatter and tracks file creation/deletion for
    test assertions. It simulates all NodeRepo operations including editor
    integration (tracked but not executed).

    Examples:
        >>> from prosemark.domain.models import NodeId
        >>> repo = FakeNodeRepo()
        >>> node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        >>> repo.create(node_id, 'Test Title', 'Test synopsis')
        >>> frontmatter = repo.read_frontmatter(node_id)
        >>> frontmatter['title']
        'Test Title'

    """

    def __init__(self) -> None:
        """Initialize empty fake repository."""
        self._nodes: dict[str, dict[str, str | None]] = {}
        self._editor_calls: list[tuple[str, str]] = []
        self._delete_calls: list[tuple[str, bool]] = []
        self._open_in_editor_exception: Exception | None = None
        self._existing_files: set[str] = set()
        self._existing_notes_files: set[str] = set()
        self._frontmatter_mismatches: dict[str, str] = {}

    def create(self, node_id: 'NodeId', title: str | None, synopsis: str | None) -> None:
        """Create new node files with initial frontmatter.

        Args:
            node_id: Unique identifier for the node
            title: Optional title for the node
            synopsis: Optional synopsis/summary for the node

        Raises:
            NodeIdentityError: If node with this ID already exists

        """
        node_key = str(node_id)
        if node_key in self._nodes:  # pragma: no cover
            msg = 'Node already exists'
            raise NodeIdentityError(msg, node_key)

        # Store frontmatter with current timestamp placeholders
        # In real implementation, these would come from Clock port
        self._nodes[node_key] = {
            'id': node_key,
            'title': title,
            'synopsis': synopsis,
            'created': '2025-09-14T12:00:00Z',  # Placeholder timestamp
            'updated': '2025-09-14T12:00:00Z',  # Placeholder timestamp
        }

        # Auto-add to existing files for audit testing
        self._existing_files.add(node_key)
        self._existing_notes_files.add(node_key)

    def read_frontmatter(self, node_id: 'NodeId') -> dict[str, str | None]:
        """Read frontmatter from node draft file.

        Args:
            node_id: NodeId to read frontmatter for

        Returns:
            Dictionary containing frontmatter fields

        Raises:
            NodeNotFoundError: If node file doesn't exist

        """
        node_key = str(node_id)
        if node_key not in self._nodes:  # pragma: no cover
            msg = 'Node not found'
            raise NodeNotFoundError(msg, node_key)

        frontmatter = self._nodes[node_key].copy()

        # Apply frontmatter mismatch if configured for testing
        if node_key in self._frontmatter_mismatches:
            frontmatter['id'] = self._frontmatter_mismatches[node_key]

        return frontmatter

    def write_frontmatter(self, node_id: 'NodeId', fm: dict[str, str | None]) -> None:  # pragma: no cover
        """Update frontmatter in node draft file.

        Args:
            node_id: NodeId to update frontmatter for
            fm: Dictionary containing frontmatter fields to write

        Raises:
            NodeNotFoundError: If node file doesn't exist

        """
        node_key = str(node_id)
        if node_key not in self._nodes:  # pragma: no cover
            msg = 'Node not found'
            raise NodeNotFoundError(msg, node_key)

        # Update the stored frontmatter
        self._nodes[node_key] = fm.copy()

    def open_in_editor(self, node_id: 'NodeId', part: str) -> None:
        """Open specified node part in editor.

        Args:
            node_id: NodeId to open in editor
            part: Which part to open ('draft', 'notes', 'synopsis')

        Raises:
            NodeNotFoundError: If node file doesn't exist
            ValueError: If part is not a valid option

        """
        node_key = str(node_id)
        if node_key not in self._nodes:  # pragma: no cover
            msg = 'Node not found'
            raise NodeNotFoundError(msg, node_key)

        if part not in {'draft', 'notes', 'synopsis'}:  # pragma: no cover
            msg = 'Invalid part specification'
            raise ValueError(msg, part)

        # Track editor calls for test assertions (before potential exception)
        self._editor_calls.append((node_key, part))

        # Check if exception should be raised (for testing)
        if self._open_in_editor_exception is not None:
            exception_to_raise = self._open_in_editor_exception
            self._open_in_editor_exception = None  # Reset after raising
            raise exception_to_raise

    def delete(self, node_id: 'NodeId', *, delete_files: bool) -> None:
        """Remove node from system.

        Args:
            node_id: NodeId to delete
            delete_files: If True, simulates file deletion

        Raises:
            NodeNotFoundError: If node doesn't exist

        """
        node_key = str(node_id)
        if node_key not in self._nodes:  # pragma: no cover
            msg = 'Node not found'
            raise NodeNotFoundError(msg, node_key)

        # Track delete calls for test assertions
        self._delete_calls.append((node_key, delete_files))

        # Remove from memory storage
        del self._nodes[node_key]

    def node_exists(self, node_id: 'NodeId') -> bool:
        """Check if node exists in repository.

        Helper method for test assertions.

        Args:
            node_id: NodeId to check

        Returns:
            True if node exists, False otherwise

        """
        return str(node_id) in self._nodes

    def get_editor_calls(self) -> list[tuple[str, str]]:  # pragma: no cover
        """Get list of editor calls for test assertions.

        Returns:
            List of tuples containing (node_id, part) for each editor call

        """
        return self._editor_calls.copy()

    def clear_editor_calls(self) -> None:  # pragma: no cover
        """Clear editor call history.

        Useful for resetting state between test cases.

        """
        self._editor_calls.clear()

    def get_delete_calls(self) -> list[tuple[str, bool]]:
        """Get list of delete calls for test assertions.

        Returns:
            List of tuples containing (node_id, delete_files) for each delete call

        """
        return self._delete_calls.copy()

    def delete_called_with(self, node_id: 'NodeId', *, delete_files: bool) -> bool:
        """Check if delete was called with specific parameters.

        Args:
            node_id: NodeId to check
            delete_files: delete_files parameter to check

        Returns:
            True if delete was called with these parameters

        """
        return (str(node_id), delete_files) in self._delete_calls

    def clear_delete_calls(self) -> None:
        """Clear delete call history.

        Useful for resetting state between test cases.

        """
        self._delete_calls.clear()

    def get_node_count(self) -> int:  # pragma: no cover
        """Get total number of nodes in repository.

        Returns:
            Count of nodes currently stored

        """
        return len(self._nodes)

    def set_open_in_editor_exception(self, exception: Exception | None) -> None:
        """Set an exception to be raised on next open_in_editor call.

        Args:
            exception: Exception to raise, or None to clear

        """
        self._open_in_editor_exception = exception

    @property
    def open_in_editor_calls(self) -> list[tuple['NodeId', str]]:
        """Get list of open_in_editor calls for test assertions.

        Returns:
            List of tuples containing (node_id, part) for each editor call

        """
        return [(NodeId(node_key), part) for node_key, part in self._editor_calls]

    @open_in_editor_calls.setter
    def open_in_editor_calls(self, value: list[tuple['NodeId', str]]) -> None:
        """Set the open_in_editor_calls list (for test reset).

        Args:
            value: New list value

        """
        self._editor_calls = [(str(node_id), part) for node_id, part in value]

    def set_existing_files(self, file_ids: list[str]) -> None:
        """Set which node files exist for audit testing.

        Args:
            file_ids: List of node ID strings that should be considered as existing files

        """
        self._existing_files = set(file_ids)

    def set_existing_notes_files(self, file_ids: list[str]) -> None:
        """Set which node notes files exist for audit testing.

        Args:
            file_ids: List of node ID strings that should be considered as having existing notes files

        """
        self._existing_notes_files = set(file_ids)

    def get_existing_files(self) -> set['NodeId']:
        """Get all existing node file IDs for audit testing.

        Returns:
            Set of NodeIds that exist as files

        """
        # Filter out invalid node IDs to match real file system behavior
        valid_node_ids = set()
        for file_id in self._existing_files:
            try:
                valid_node_ids.add(NodeId(file_id))
            except (ValueError, NodeIdentityError):
                # Skip invalid node IDs (similar to real file system behavior)
                continue
        return valid_node_ids

    def get_existing_notes_files(self) -> set[str]:
        """Get all existing notes file IDs for audit testing.

        Returns:
            Set of node ID strings that exist as notes files

        """
        return self._existing_notes_files.copy()

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
        if file_type not in {'draft', 'notes'}:
            msg = f'Invalid file_type: {file_type}. Must be "draft" or "notes"'
            raise ValueError(msg)

        node_key = str(node_id)

        if file_type == 'draft':
            # Check if the main .md file exists (tracked in _existing_files)
            return node_key in self._existing_files
        # Check if the notes file exists (tracked in _existing_notes_files)
        return node_key in self._existing_notes_files

    def set_frontmatter_mismatch(self, file_id: str, frontmatter_id: str) -> None:
        """Set a frontmatter ID mismatch for audit testing.

        Args:
            file_id: The file's actual node ID
            frontmatter_id: The mismatched ID in the file's frontmatter

        """
        self._frontmatter_mismatches[file_id] = frontmatter_id

    def create_notes_file(self, node_id: 'NodeId') -> None:
        """Create only the notes file for an existing node.

        Creates the {id}.notes.md file with obsidian-style link to the node.
        This is used when the draft file exists but the notes file is missing.

        Args:
            node_id: NodeId for the node that needs a notes file

        Raises:
            FileSystemError: If notes file cannot be created

        """
        # In fake implementation, just mark that notes file exists
        node_key = str(node_id)
        if node_key not in self._existing_notes_files:
            self._existing_notes_files.add(node_key)
