"""File system port interface for freewriting feature.

This module defines the port interface for file system operations
required by the freewriting functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class FileSystemPort(ABC):
    """Port interface for file system operations.

    This port defines the contract for low-level file operations
    that the freewriting feature needs, including reading, writing,
    and directory management.
    """

    @abstractmethod
    def write_file(self, file_path: str, content: str, append: bool = False) -> None:  # noqa: FBT001, FBT002
        """Write content to file.

        Args:
            file_path: Target file path (should be absolute).
            content: Content to write.
            append: Whether to append (True) or overwrite (False).

        Raises:
            FileSystemError: If write operation fails.

        """

    @abstractmethod
    def read_file(self, file_path: str) -> str:
        """Read content from file.

        Args:
            file_path: Path to file to read.

        Returns:
            File content as string.

        Raises:
            FileSystemError: If read operation fails.

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
    def create_directory(self, directory_path: str, parents: bool = True) -> None:  # noqa: FBT001, FBT002
        """Create directory if it doesn't exist.

        Args:
            directory_path: Path to directory to create.
            parents: Whether to create parent directories if they don't exist.

        Raises:
            FileSystemError: If directory creation fails.

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

    @abstractmethod
    def get_absolute_path(self, path: str) -> str:
        """Convert path to absolute path.

        Args:
            path: Path to convert (can be relative or absolute).

        Returns:
            Absolute path string.

        """

    @abstractmethod
    def join_paths(self, *paths: str) -> str:
        """Join multiple path components into a single path.

        Args:
            *paths: Path components to join.

        Returns:
            Joined path string.

        """

    @abstractmethod
    def get_file_size(self, file_path: str) -> int:
        """Get size of file in bytes.

        Args:
            file_path: Path to file.

        Returns:
            File size in bytes.

        Raises:
            FileSystemError: If file doesn't exist or size cannot be determined.

        """

    @abstractmethod
    def backup_file(self, file_path: str, backup_suffix: str = '.bak') -> str:
        """Create backup copy of file.

        Args:
            file_path: Path to file to backup.
            backup_suffix: Suffix to add to backup file name.

        Returns:
            Path to backup file.

        Raises:
            FileSystemError: If backup creation fails.

        """

    @abstractmethod
    def ensure_parent_directory(self, file_path: str) -> None:
        """Ensure parent directory of file exists.

        Args:
            file_path: Path to file whose parent directory should exist.

        Raises:
            FileSystemError: If parent directory cannot be created.

        """

    @staticmethod
    def resolve_path(path: str) -> Path:  # pragma: no cover
        """Resolve path to pathlib.Path object.

        Args:
            path: Path string to resolve.

        Returns:
            Resolved Path object.

        """
        return Path(path).resolve()
