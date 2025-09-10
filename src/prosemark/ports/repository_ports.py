"""Repository port protocols for data persistence."""

from typing import Any, Protocol, runtime_checkable

from prosemark.domain.aggregates import Binder
from prosemark.domain.value_objects import NodeId


@runtime_checkable
class BinderRepo(Protocol):
    """Repository protocol for binder persistence.

    Manages reading and writing the _binder.md file that contains
    the hierarchical structure of the project.
    """

    def load(self) -> Binder:
        """Load binder from persistent storage.

        Returns:
            Binder: The loaded binder structure

        Raises:
            FileNotFoundError: If binder file doesn't exist
            ValueError: If binder file is malformed

        """
        ...  # pragma: no cover

    def save(self, binder: Binder) -> None:
        """Save binder to persistent storage.

        Args:
            binder: The binder structure to save

        Raises:
            IOError: If unable to write to storage

        """
        ...  # pragma: no cover


@runtime_checkable
class NodeRepo(Protocol):
    """Repository protocol for node file management.

    Manages the individual node files ({id}.md and {id}.notes.md)
    including frontmatter parsing and editor integration.
    """

    def create(self, node_id: NodeId, title: str | None, synopsis: str | None) -> None:
        """Create new node files with frontmatter.

        Args:
            node_id: Unique identifier for the node
            title: Optional title for the node
            synopsis: Optional synopsis text

        Raises:
            FileExistsError: If node files already exist
            IOError: If unable to create files

        """
        ...  # pragma: no cover

    def read_frontmatter(self, node_id: NodeId) -> dict[str, Any]:
        """Read frontmatter from node's draft file.

        Args:
            node_id: Node identifier

        Returns:
            dict: Parsed frontmatter data

        Raises:
            FileNotFoundError: If node file doesn't exist
            ValueError: If frontmatter is malformed

        """
        ...  # pragma: no cover

    def write_frontmatter(self, node_id: NodeId, frontmatter: dict[str, Any]) -> None:
        """Write frontmatter to node's draft file.

        Args:
            node_id: Node identifier
            frontmatter: Frontmatter data to write

        Raises:
            FileNotFoundError: If node file doesn't exist
            IOError: If unable to write frontmatter

        """
        ...  # pragma: no cover

    def open_in_editor(self, node_id: NodeId, part: str) -> None:
        """Open node file in configured editor.

        Args:
            node_id: Node identifier
            part: Which part to edit ('draft' or 'notes')

        Raises:
            FileNotFoundError: If node file doesn't exist
            ValueError: If part is not 'draft' or 'notes'
            RuntimeError: If unable to launch editor

        """
        ...  # pragma: no cover

    def delete(self, node_id: NodeId, *, delete_files: bool) -> None:
        """Delete node files from storage.

        Args:
            node_id: Node identifier
            delete_files: Whether to actually delete files or just mark for removal

        Raises:
            FileNotFoundError: If node files don't exist
            IOError: If unable to delete files

        """
        ...  # pragma: no cover


@runtime_checkable
class DailyRepo(Protocol):
    """Repository protocol for daily freewrite management.

    Manages timestamped freewrite files that exist outside
    the main binder structure.
    """

    def write_freeform(self, title: str | None) -> str:
        """Create a new timestamped freewrite file.

        Args:
            title: Optional title for the freewrite

        Returns:
            str: Path to the created file

        Raises:
            IOError: If unable to create file

        """
        ...  # pragma: no cover
