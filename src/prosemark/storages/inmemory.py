"""In-memory storage adapter for Markdown nodes.

This module provides a storage adapter that stores Markdown nodes in memory,
useful for testing and temporary storage scenarios.
"""

from prosemark.storages.base import NodeStoragePort


class InMemoryNodeStorage(NodeStoragePort):
    """In-memory storage adapter for Markdown nodes.

    This adapter stores node content in memory using a dictionary,
    making it suitable for testing and temporary storage scenarios.

    Attributes:
        _nodes: A dictionary mapping node IDs to their content.

    """

    def __init__(self) -> None:
        """Initialize the storage adapter."""
        self._nodes: dict[str, str] = {}

    def read(self, node_id: str) -> str:
        """Read the content of a node by ID.

        Args:
            node_id: The unique identifier for the node.

        Returns:
            The content of the node as a string, or empty string if not found.

        """
        return self._nodes.get(node_id, '')

    def write(self, node_id: str, content: str) -> None:
        """Write content to a node by ID.

        Args:
            node_id: The unique identifier for the node.
            content: The content to write to the node.

        """
        self._nodes[node_id] = content

    def get_binder(self) -> str:
        """Read the content of the special _binder node.

        The _binder node contains metadata about the project structure.

        Returns:
            The content of the _binder node as a string, or empty string if not found.

        """
        return self.read('_binder')

    def delete(self, node_id: str) -> None:
        """Delete the entry for a node by ID if it exists."""
        if node_id in self._nodes:
            del self._nodes[node_id]
