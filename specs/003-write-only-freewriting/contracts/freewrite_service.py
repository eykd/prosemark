"""Domain service contract for freewriting functionality.

This represents the port interface that adapters will implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FreewriteSession:
    """Domain model for a freewriting session."""

    session_id: str
    target_node: str | None
    title: str | None
    start_time: datetime
    word_count_goal: int | None
    time_limit: int | None
    current_word_count: int
    elapsed_time: int
    output_file_path: str
    content_lines: list[str]


@dataclass
class SessionConfig:
    """Configuration for a freewriting session."""

    target_node: str | None
    title: str | None
    word_count_goal: int | None
    time_limit: int | None
    theme: str
    current_directory: str


class FreewriteServicePort(ABC):
    """Port interface for freewriting domain operations."""

    @abstractmethod
    def create_session(self, config: SessionConfig) -> FreewriteSession:
        """Create a new freewriting session with given configuration.

        Args:
            config: Session configuration from CLI

        Returns:
            Initialized FreewriteSession

        Raises:
            ValidationError: If configuration is invalid
            FileSystemError: If target directory is not writable

        """

    @abstractmethod
    def append_content(self, session: FreewriteSession, content: str) -> FreewriteSession:
        """Append content line to the session and persist immediately.

        Args:
            session: Current session state
            content: Content line to append

        Returns:
            Updated session with new content and word count

        Raises:
            FileSystemError: If write operation fails
            ValidationError: If content is invalid

        """

    @abstractmethod
    def validate_node_uuid(self, node_uuid: str) -> bool:
        """Validate that a node UUID is properly formatted.

        Args:
            node_uuid: UUID string to validate

        Returns:
            True if valid UUID format, False otherwise

        """

    @abstractmethod
    def create_daily_filename(self, timestamp: datetime) -> str:
        """Generate filename for daily freewrite file.

        Args:
            timestamp: When the session started

        Returns:
            Filename in YYYY-MM-DD-HHmm.md format

        """

    @abstractmethod
    def get_session_stats(self, session: FreewriteSession) -> dict[str, int | float]:
        """Calculate current session statistics.

        Args:
            session: Current session

        Returns:
            Dictionary with word_count, elapsed_time, progress metrics

        """


class NodeServicePort(ABC):
    """Port interface for node management operations."""

    @abstractmethod
    def node_exists(self, node_uuid: str) -> bool:
        """Check if a node file exists.

        Args:
            node_uuid: UUID of the node to check

        Returns:
            True if node exists, False otherwise

        """

    @abstractmethod
    def create_node(self, node_uuid: str, title: str | None = None) -> str:
        """Create a new node file and add to binder.

        Args:
            node_uuid: UUID for the new node
            title: Optional title for the node

        Returns:
            Path to created node file

        Raises:
            ValidationError: If UUID is invalid
            FileSystemError: If creation fails

        """

    @abstractmethod
    def append_to_node(
        self, node_uuid: str, content: list[str], session_metadata: dict[str, str | int | datetime]
    ) -> None:
        """Append freewriting content to existing node.

        Args:
            node_uuid: Target node UUID
            content: Lines of content to append
            session_metadata: Session info for context

        Raises:
            FileSystemError: If write fails
            ValidationError: If node doesn't exist

        """


class FileSystemPort(ABC):
    """Port interface for file system operations."""

    @abstractmethod
    def write_file(self, file_path: str, content: str, *, append: bool = False) -> None:
        """Write content to file.

        Args:
            file_path: Target file path
            content: Content to write
            append: Whether to append (True) or overwrite (False)

        Raises:
            FileSystemError: If write operation fails

        """

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists.

        Args:
            file_path: Path to check

        Returns:
            True if file exists, False otherwise

        """

    @abstractmethod
    def get_current_directory(self) -> str:
        """Get current working directory.

        Returns:
            Absolute path to current directory

        """

    @abstractmethod
    def is_writable(self, directory_path: str) -> bool:
        """Check if directory is writable.

        Args:
            directory_path: Directory to check

        Returns:
            True if writable, False otherwise

        """


# Domain Exceptions
class FreewriteError(Exception):
    """Base exception for freewrite domain errors."""


class ValidationError(FreewriteError):
    """Raised when validation fails."""


class FileSystemError(FreewriteError):
    """Raised when file system operations fail."""


class NodeError(FreewriteError):
    """Raised when node operations fail."""
