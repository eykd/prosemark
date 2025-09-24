"""File system adapter implementation for freewriting feature.

This module provides concrete implementation of the FileSystemPort
using standard Python file operations.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from prosemark.freewriting.domain.exceptions import FileSystemError
from prosemark.freewriting.ports.file_system import FileSystemPort


class FileSystemAdapter(FileSystemPort):
    """Concrete implementation of FileSystemPort using standard file operations.

    This adapter provides file system operations using Python's built-in
    file handling capabilities and pathlib for path management.
    """

    def write_file(self, file_path: str, content: str, append: bool = False) -> None:  # noqa: FBT001, FBT002
        """Write content to file.

        Args:
            file_path: Target file path (should be absolute).
            content: Content to write.
            append: Whether to append (True) or overwrite (False).

        Raises:
            FileSystemError: If write operation fails.

        """
        try:
            # Ensure parent directory exists
            self.ensure_parent_directory(file_path)

            mode = 'a' if append else 'w'
            with Path(file_path).open(mode, encoding='utf-8') as f:
                f.write(content)

        except OSError as e:  # pragma: no cover
            raise FileSystemError('write', file_path, str(e)) from e

    @classmethod
    def read_file(cls, file_path: str) -> str:
        """Read content from file.

        Args:
            file_path: Path to file to read.

        Returns:
            File content as string.

        Raises:
            FileSystemError: If read operation fails.

        """
        try:
            with Path(file_path).open('r', encoding='utf-8') as f:
                return f.read()

        except OSError as e:
            raise FileSystemError('read', file_path, str(e)) from e

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if file exists.

        Args:
            file_path: Path to check.

        Returns:
            True if file exists, False otherwise.

        """
        return Path(file_path).exists()

    @classmethod
    def create_directory(cls, directory_path: str, parents: bool = True) -> None:  # noqa: FBT001, FBT002
        """Create directory if it doesn't exist.

        Args:
            directory_path: Path to directory to create.
            parents: Whether to create parent directories if they don't exist.

        Raises:
            FileSystemError: If directory creation fails.

        """
        try:
            Path(directory_path).mkdir(parents=parents, exist_ok=True)

        except OSError as e:
            raise FileSystemError('create_directory', directory_path, str(e)) from e

    @staticmethod
    def get_current_directory() -> str:
        """Get current working directory.

        Returns:
            Absolute path to current directory.

        """
        return str(Path.cwd())

    def is_writable(self, directory_path: str) -> bool:
        """Check if directory is writable.

        Args:
            directory_path: Directory to check.

        Returns:
            True if writable, False otherwise.

        """
        try:
            path = Path(directory_path)

            # If directory doesn't exist, check if we can create it
            if not path.exists():
                try:
                    # Try to create it temporarily
                    path.mkdir(parents=True, exist_ok=True)
                    # If creation succeeded, remove it and check parent
                    if path.exists():
                        path.rmdir()
                        return self.is_writable(str(path.parent))
                except OSError:
                    return False
                else:
                    # If creation succeeded but directory doesn't exist (race condition)
                    return False  # pragma: no cover

            # Check if we can write by creating a temporary file
            test_file = path / '.write_test'
            try:
                with test_file.open('w', encoding='utf-8') as f:
                    f.write('test')
                test_file.unlink()
            except OSError:
                return False
            else:
                return True

        except OSError:
            return False

    @staticmethod
    def get_absolute_path(path: str) -> str:
        """Convert path to absolute path.

        Args:
            path: Path to convert (can be relative or absolute).

        Returns:
            Absolute path string.

        """
        return str(Path(path).resolve())

    @staticmethod
    def join_paths(*paths: str) -> str:
        """Join multiple path components into a single path.

        Args:
            *paths: Path components to join.

        Returns:
            Joined path string.

        """
        if not paths:
            return ''

        result = Path(paths[0])
        for path in paths[1:]:
            result /= path
        return str(result)

    @classmethod
    def get_file_size(cls, file_path: str) -> int:
        """Get size of file in bytes.

        Args:
            file_path: Path to file.

        Returns:
            File size in bytes.

        Raises:
            FileSystemError: If file doesn't exist or size cannot be determined.

        """
        try:
            return Path(file_path).stat().st_size

        except OSError as e:
            raise FileSystemError('stat', file_path, str(e)) from e

    @classmethod
    def backup_file(cls, file_path: str, backup_suffix: str = '.bak') -> str:
        """Create backup copy of file.

        Args:
            file_path: Path to file to backup.
            backup_suffix: Suffix to add to backup file name.

        Returns:
            Path to backup file.

        Raises:
            FileSystemError: If backup creation fails.

        """
        try:
            source_path = Path(file_path)
            backup_path = source_path.with_suffix(source_path.suffix + backup_suffix)

            # Copy the file to backup location
            shutil.copy2(source_path, backup_path)

            return str(backup_path)

        except (OSError, shutil.Error) as e:
            raise FileSystemError('backup', file_path, str(e)) from e

    @classmethod
    def ensure_parent_directory(cls, file_path: str) -> None:
        """Ensure parent directory of file exists.

        Args:
            file_path: Path to file whose parent directory should exist.

        Raises:
            FileSystemError: If parent directory cannot be created.

        """
        try:
            parent_dir = Path(file_path).parent
            if not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)

        except OSError as e:
            raise FileSystemError('ensure_parent', str(Path(file_path).parent), str(e)) from e

    @staticmethod
    def sanitize_title(title: str) -> str:
        """Sanitize a title string for use in filenames.

        Args:
            title: The title string to sanitize.

        Returns:
            Sanitized title safe for use in filenames.

        """
        # Replace potentially problematic characters with underscores
        sanitized = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_')
        sanitized = sanitized.replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_')
        sanitized = sanitized.replace('|', '_')

        # Remove leading/trailing whitespace and convert to clean format
        sanitized = sanitized.strip()

        # Collapse multiple underscores into single ones
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')

        # Remove leading/trailing underscores
        return sanitized.strip('_')
