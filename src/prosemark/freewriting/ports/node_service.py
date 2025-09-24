"""Node service port interface for freewriting feature.

This module defines the port interface for node management operations
specific to the freewriting functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class NodeServicePort(ABC):
    """Port interface for node management operations.

    This port defines the contract for operations on prosemark nodes,
    including creation, existence checking, and content appending.
    """

    @abstractmethod
    def node_exists(self, node_uuid: str) -> bool:
        """Check if a node file exists.

        Args:
            node_uuid: UUID of the node to check.

        Returns:
            True if node exists, False otherwise.

        """

    @abstractmethod
    def create_node(self, node_uuid: str, title: str | None = None) -> str:
        """Create a new node file and add to binder.

        Creates a new prosemark node file with the given UUID and optionally
        adds it to the project binder for organization.

        Args:
            node_uuid: UUID for the new node.
            title: Optional title for the node.

        Returns:
            Path to created node file.

        Raises:
            ValidationError: If UUID is invalid.
            FileSystemError: If creation fails.
            NodeError: If node creation fails.

        """

    @abstractmethod
    def append_to_node(self, node_uuid: str, content: list[str], session_metadata: dict[str, str]) -> None:
        """Append freewriting content to existing node.

        Appends the given content lines to the specified node, adding
        session metadata to provide context about when and how the
        content was added.

        Args:
            node_uuid: Target node UUID.
            content: Lines of content to append.
            session_metadata: Session info for context (timestamp, word count, etc.).

        Raises:
            FileSystemError: If write fails.
            ValidationError: If node doesn't exist.
            NodeError: If node operations fail.

        """

    @abstractmethod
    def get_node_path(self, node_uuid: str) -> str:
        """Get file path for a node UUID.

        Args:
            node_uuid: UUID of the node.

        Returns:
            Absolute path to the node file.

        Raises:
            ValidationError: If UUID format is invalid.

        """

    @staticmethod
    @abstractmethod
    def validate_node_uuid(node_uuid: str) -> bool:
        """Validate that a node UUID is properly formatted.

        Args:
            node_uuid: UUID string to validate.

        Returns:
            True if valid UUID format, False otherwise.

        """

    @abstractmethod
    def add_to_binder(self, node_uuid: str, title: str | None = None) -> None:
        """Add node to the project binder.

        Args:
            node_uuid: UUID of the node to add.
            title: Optional title for the binder entry.

        Raises:
            FileSystemError: If binder update fails.
            NodeError: If node addition fails.

        """
