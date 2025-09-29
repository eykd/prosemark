"""DirectoryPath value object for template directory handling and validation."""

from pathlib import Path
from typing import Self

from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateDirectoryNotFoundError,
    TemplateValidationError,
)


class DirectoryPath:
    """Immutable value object representing a validated template directory path.

    This value object encapsulates a directory path and provides template-specific
    directory operations and validation.
    """

    def __init__(self, path: Path | str) -> None:
        """Initialize a directory path with validation.

        Args:
            path: File system path to a directory

        Raises:
            TemplateDirectoryNotFoundError: If the directory does not exist
            TemplateValidationError: If the path is not a valid directory

        """
        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            raise TemplateDirectoryNotFoundError(str(path))

        if not path.is_dir():
            msg = f'Path must point to a directory, not a file: {path}'
            raise TemplateValidationError(msg, template_path=str(path))

        self._path = path.resolve()

    @property
    def value(self) -> Path:
        """Get the absolute path to the directory."""
        return self._path

    @property
    def name(self) -> str:
        """Get the directory name."""
        return self._path.name

    @property
    def exists(self) -> bool:
        """Check if the directory still exists."""
        return self._path.exists() and self._path.is_dir()

    @property
    def template_count(self) -> int:
        """Count the number of .md files in this directory (non-recursive)."""
        if not self.exists:
            return 0

        try:
            return len([f for f in self._path.iterdir() if f.is_file() and f.suffix == '.md'])
        except (OSError, PermissionError):  # pragma: no cover
            return 0

    @property
    def total_template_count(self) -> int:
        """Count all .md files in this directory recursively."""
        if not self.exists:
            return 0

        try:
            return len(list(self._path.rglob('*.md')))
        except (OSError, PermissionError):  # pragma: no cover
            return 0

    @property
    def subdirectory_count(self) -> int:
        """Count the number of subdirectories in this directory."""
        if not self.exists:
            return 0

        try:
            return len([d for d in self._path.iterdir() if d.is_dir()])
        except (OSError, PermissionError):  # pragma: no cover
            return 0

    @property
    def is_valid_template_directory(self) -> bool:
        """Check if this directory is a valid template directory.

        A valid template directory either:
        1. Contains at least one .md file directly, OR
        2. Contains subdirectories that contain .md files
        """
        if not self.exists:
            return False

        # Check for direct .md files
        if self.template_count > 0:
            return True

        # Check for .md files in subdirectories
        return self.total_template_count > self.template_count

    def list_template_files(self, *, recursive: bool = False) -> list[Path]:
        """List all .md files in the directory.

        Args:
            recursive: If True, search subdirectories recursively

        Returns:
            List of paths to .md files

        Raises:
            TemplateDirectoryNotFoundError: If directory no longer exists

        """
        if not self.exists:
            raise TemplateDirectoryNotFoundError(str(self._path))

        try:
            if recursive:
                return sorted(self._path.rglob('*.md'))
            return sorted([f for f in self._path.iterdir() if f.is_file() and f.suffix == '.md'])
        except (OSError, PermissionError) as e:  # pragma: no cover
            msg = f'Cannot access directory: {self._path}'
            raise TemplateDirectoryNotFoundError(msg) from e

    def list_subdirectories(self) -> list[Path]:
        """List all subdirectories.

        Returns:
            List of paths to subdirectories

        Raises:
            TemplateDirectoryNotFoundError: If directory no longer exists

        """
        if not self.exists:
            raise TemplateDirectoryNotFoundError(str(self._path))

        try:
            return sorted([d for d in self._path.iterdir() if d.is_dir()])
        except (OSError, PermissionError) as e:  # pragma: no cover
            msg = f'Cannot access directory: {self._path}'
            raise TemplateDirectoryNotFoundError(msg) from e

    def find_template_file(self, template_name: str) -> Path | None:
        """Find a template file by name in this directory.

        Args:
            template_name: Name of template (with or without .md extension)

        Returns:
            Path to template file if found, None otherwise

        """
        if not self.exists:
            return None

        # Ensure .md extension
        if not template_name.endswith('.md'):
            template_name = f'{template_name}.md'

        template_file = self._path / template_name
        return template_file if template_file.is_file() else None

    def find_subdirectory(self, directory_name: str) -> Path | None:
        """Find a subdirectory by name.

        Args:
            directory_name: Name of subdirectory

        Returns:
            Path to subdirectory if found, None otherwise

        """
        if not self.exists:
            return None

        subdirectory = self._path / directory_name
        return subdirectory if subdirectory.is_dir() else None

    def get_relative_path_to(self, target_path: Path) -> Path | None:
        """Get relative path from this directory to a target path.

        Args:
            target_path: Target path to calculate relative path to

        Returns:
            Relative path if possible, None if paths are not related

        """
        try:
            return target_path.relative_to(self._path)
        except ValueError:
            return None

    def contains_path(self, path: Path) -> bool:
        """Check if a path is contained within this directory.

        Args:
            path: Path to check

        Returns:
            True if path is within this directory

        """
        return self.get_relative_path_to(path) is not None

    @classmethod
    def create_if_not_exists(cls, path: Path | str) -> Self:
        """Create directory if it doesn't exist and return DirectoryPath.

        Args:
            path: Path to directory to create

        Returns:
            New DirectoryPath instance

        Raises:
            TemplateValidationError: If path exists but is not a directory
            OSError: If directory cannot be created

        """
        if isinstance(path, str):
            path = Path(path)

        if path.exists() and not path.is_dir():
            msg = f'Path exists but is not a directory: {path}'
            raise TemplateValidationError(msg, template_path=str(path))

        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        return cls(path)

    def __str__(self) -> str:
        """String representation of the directory path."""
        return str(self._path)

    def __repr__(self) -> str:
        """Developer representation of the directory path."""
        return f'DirectoryPath({self._path!r})'

    def __eq__(self, other: object) -> bool:
        """Check equality with another DirectoryPath."""
        if not isinstance(other, DirectoryPath):
            return NotImplemented
        return self._path == other._path

    def __hash__(self) -> int:
        """Hash based on the path value."""
        return hash(self._path)
