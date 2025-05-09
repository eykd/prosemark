"""Base interfaces for storage adapters.

This module defines the abstract base classes that all storage adapters must implement.
"""

from abc import ABC, abstractmethod


class NodeStoragePort(ABC):
    """Abstract base class defining the interface for node storage."""

    @abstractmethod
    def read(self, node_id: str) -> str:
        """Read the content of a node by ID.

        Args:
            node_id: The unique identifier for the node.

        Returns:
            The content of the node as a string, or empty string if not found.

        """

    @abstractmethod
    def write(self, node_id: str, content: str) -> None:
        """Write content to a node by ID.

        Args:
            node_id: The unique identifier for the node.
            content: The content to write to the node.

        """

    @abstractmethod
    def get_binder(self) -> str:
        """Read the content of the special _binder node.

        The _binder node contains metadata about the project structure.

        Returns:
            The content of the _binder node as a string, or empty string if not found.

        """
