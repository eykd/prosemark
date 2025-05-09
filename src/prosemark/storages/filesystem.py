"""Filesystem storage adapter for Markdown nodes.

This module provides a storage adapter that reads and writes Markdown files
from the filesystem, using a timestamp-based ID system for filenames.
"""

from pathlib import Path
from typing import Protocol


class NodeStoragePort(Protocol):
    """Port defining the interface for node storage."""

    def read(self, node_id: str) -> str:
        """Read the content of a node by ID.

        Args:
            node_id: The unique identifier for the node.

        Returns:
            The content of the node as a string, or empty string if not found.

        """
        ...  # pragma: no cover

    def write(self, node_id: str, content: str) -> None:
        """Write content to a node by ID.

        Args:
            node_id: The unique identifier for the node.
            content: The content to write to the node.

        """
        ...  # pragma: no cover


class FilesystemMdNodeStorage:
    """Filesystem storage adapter for Markdown nodes.

    This adapter reads and writes Markdown files from the filesystem,
    using a timestamp-based ID system for filenames.

    Attributes:
        base_path: The base directory where node files are stored.

    """

    def __init__(self, base_path: Path) -> None:
        """Initialize the storage adapter.

        Args:
            base_path: The base directory where node files are stored.

        """
        self.base_path = base_path
        # Ensure the directory exists
        base_path.mkdir(parents=True, exist_ok=True)

    def read(self, node_id: str) -> str:
        """Read the content of a node by ID.

        Args:
            node_id: The unique identifier for the node.

        Returns:
            The content of the node as a string, or empty string if not found.

        """
        file_path = self._get_file_path(node_id)
        if not file_path.exists():
            return ''

        try:
            return file_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            # Return empty string if file can't be read or decoded
            return ''

    def write(self, node_id: str, content: str) -> None:
        """Write content to a node by ID.

        Args:
            node_id: The unique identifier for the node.
            content: The content to write to the node.

        """
        file_path = self._get_file_path(node_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')

    def _get_file_path(self, node_id: str) -> Path:
        """Get the file path for a node ID.

        Args:
            node_id: The unique identifier for the node.

        Returns:
            The Path object for the node's file.

        """
        return self.base_path / f'{node_id}.md'

    def get_binder(self) -> str:
        """Read the content of the special _binder node.
        
        The _binder node contains metadata about the project structure.
        
        Returns:
            The content of the _binder node as a string, or empty string if not found.

        """
        return self.read('_binder')
