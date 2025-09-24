"""Port interfaces for freewriting domain operations.

This module defines the port interfaces that the freewriting domain uses
to interact with external systems. These ports define contracts that
adapters must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from datetime import datetime

    from prosemark.freewriting.domain.models import FreewriteSession, SessionConfig


class FreewriteServicePort(ABC):
    """Port interface for freewriting domain operations.

    This port defines the contract for core freewriting operations
    such as session management and content handling.
    """

    @abstractmethod
    def create_session(self, config: SessionConfig) -> FreewriteSession:
        """Create a new freewriting session with given configuration.

        Args:
            config: Session configuration from CLI.

        Returns:
            Initialized FreewriteSession.

        Raises:
            ValidationError: If configuration is invalid.
            FileSystemError: If target directory is not writable.

        """

    @abstractmethod
    def append_content(self, session: FreewriteSession, content: str) -> FreewriteSession:
        """Append content line to the session and persist immediately.

        Args:
            session: Current session state.
            content: Content line to append.

        Returns:
            Updated session with new content and word count.

        Raises:
            FileSystemError: If write operation fails.
            ValidationError: If content is invalid.

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
    def create_daily_filename(self, timestamp: datetime) -> str:
        """Generate filename for daily freewrite file.

        Args:
            timestamp: When the session started.

        Returns:
            Filename in YYYY-MM-DD-HHmm.md format.

        """

    @abstractmethod
    def get_session_stats(self, session: FreewriteSession) -> dict[str, int | float | bool]:
        """Calculate current session statistics.

        Args:
            session: Current session.

        Returns:
            Dictionary with word_count, elapsed_time, progress metrics.

        """


class NodeServicePort(ABC):
    """Port interface for node management operations.

    This port defines the contract for operations on prosemark nodes,
    including creation and content appending.
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

        Args:
            node_uuid: UUID for the new node.
            title: Optional title for the node.

        Returns:
            Path to created node file.

        Raises:
            ValidationError: If UUID is invalid.
            FileSystemError: If creation fails.

        """

    @abstractmethod
    def append_to_node(self, node_uuid: str, content: list[str], session_metadata: dict[str, str]) -> None:
        """Append freewriting content to existing node.

        Args:
            node_uuid: Target node UUID.
            content: Lines of content to append.
            session_metadata: Session info for context.

        Raises:
            FileSystemError: If write fails.
            ValidationError: If node doesn't exist.

        """


class FileSystemPort(ABC):
    """Port interface for file system operations.

    This port defines the contract for low-level file operations
    that the freewriting feature needs.
    """

    @abstractmethod
    def write_file(self, file_path: str, content: str, append: bool = False) -> None:  # noqa: FBT001, FBT002
        """Write content to file.

        Args:
            file_path: Target file path.
            content: Content to write.
            append: Whether to append (True) or overwrite (False).

        Raises:
            FileSystemError: If write operation fails.

        """

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists.

        Args:
            file_path: Path to check.

        Returns:
            True if file exists, False otherwise.

        """

    @abstractmethod
    def get_current_directory(self) -> str:
        """Get current working directory.

        Returns:
            Absolute path to current directory.

        """

    @abstractmethod
    def is_writable(self, directory_path: str) -> bool:
        """Check if directory is writable.

        Args:
            directory_path: Directory to check.

        Returns:
            True if writable, False otherwise.

        """
