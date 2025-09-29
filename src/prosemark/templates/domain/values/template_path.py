"""TemplatePath value object for template path handling and validation."""

from pathlib import Path
from typing import Self

from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
)


class TemplatePath:
    """Immutable value object representing a validated template file path.

    This value object encapsulates a file system path that points to a template file,
    ensuring the path exists and meets basic template file requirements.
    """

    def __init__(self, path: Path | str) -> None:
        """Initialize a template path with validation.

        Args:
            path: File system path to a template file

        Raises:
            TemplateNotFoundError: If the path does not exist
            TemplateValidationError: If the path is not a valid template file

        """
        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            raise TemplateNotFoundError(
                template_name=path.name, search_path=str(path.parent) if path.parent != path else None
            )

        if not path.is_file():
            msg = f'Template path must point to a file, not a directory: {path}'
            raise TemplateValidationError(msg, template_path=str(path))

        if path.suffix != '.md':
            msg = f'Template files must have .md extension: {path}'
            raise TemplateValidationError(msg, template_path=str(path))

        self._path = path.resolve()

    @property
    def value(self) -> Path:
        """Get the absolute path to the template file."""
        return self._path

    @property
    def name(self) -> str:
        """Get the template name (filename without .md extension)."""
        return self._path.stem

    @property
    def exists(self) -> bool:
        """Check if the template file still exists on disk."""
        return self._path.exists()

    @property
    def is_readable(self) -> bool:
        """Check if the template file is readable."""
        try:
            return bool(self._path.is_file() and self._path.stat().st_mode & 0o400)
        except (OSError, PermissionError):  # pragma: no cover
            return False

    @property
    def parent_directory(self) -> Path:
        """Get the parent directory of the template file."""
        return self._path.parent

    def read_content(self) -> str:
        """Read the complete content of the template file.

        Returns:
            The full text content of the template file

        Raises:
            TemplateNotFoundError: If the file no longer exists
            PermissionError: If the file is not readable

        """
        if not self.exists:
            raise TemplateNotFoundError(template_name=self.name, search_path=str(self.parent_directory))

        try:
            return self._path.read_text(encoding='utf-8')
        except PermissionError as e:  # pragma: no cover
            msg = f'Cannot read template file: {self._path}'
            raise PermissionError(msg) from e

    def get_relative_path(self, base_directory: Path) -> Path:
        """Get the path relative to a base directory.

        Args:
            base_directory: The base directory to calculate relative path from

        Returns:
            Path relative to the base directory

        """
        try:
            return self._path.relative_to(base_directory)
        except ValueError:
            # Path is not relative to base_directory
            return self._path

    @classmethod
    def from_name_and_directory(cls, name: str, directory: Path) -> Self:
        """Create a TemplatePath from template name and directory.

        Args:
            name: Template name (without .md extension)
            directory: Directory containing the template

        Returns:
            New TemplatePath instance

        Raises:
            TemplateNotFoundError: If the template file does not exist
            TemplateValidationError: If the path is invalid

        """
        template_file = directory / f'{name}.md' if not name.endswith('.md') else directory / name

        return cls(template_file)

    def __str__(self) -> str:
        """String representation of the template path."""
        return str(self._path)

    def __repr__(self) -> str:
        """Developer representation of the template path."""
        return f'TemplatePath({self._path!r})'

    def __eq__(self, other: object) -> bool:
        """Check equality with another TemplatePath."""
        if not isinstance(other, TemplatePath):
            return NotImplemented
        return self._path == other._path

    def __hash__(self) -> int:
        """Hash based on the path value."""
        return hash(self._path)
