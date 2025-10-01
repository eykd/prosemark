"""File-based template repository adapter for template storage and retrieval."""

from pathlib import Path
from typing import Any

from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.entities.template_directory import TemplateDirectory
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidTemplateDirectoryError,
    TemplateDirectoryNotFoundError,
    TemplateNotFoundError,
    TemplateParseError,
    TemplateValidationError,
)
from prosemark.templates.domain.values.template_path import TemplatePath
from prosemark.templates.ports.template_repository_port import TemplateRepositoryPort


class FileTemplateRepository(TemplateRepositoryPort):
    """File-based implementation of template repository."""

    def __init__(self, templates_root: Path | str) -> None:
        """Initialize repository with templates root directory.

        Args:
            templates_root: Path to the root templates directory

        Raises:
            TemplateDirectoryNotFoundError: If root directory doesn't exist

        """
        self._templates_root = Path(templates_root)
        if not self._templates_root.exists():
            msg = f'Templates root directory not found: {self._templates_root}'
            raise TemplateDirectoryNotFoundError(msg)
        if not self._templates_root.is_dir():
            msg = f'Templates root path is not a directory: {self._templates_root}'
            raise TemplateDirectoryNotFoundError(msg)

    def get_template(self, template_name: str) -> Template:
        """Load a single template by name.

        Args:
            template_name: Name of the template (without .md extension)

        Returns:
            Template object

        Raises:
            TemplateNotFoundError: If template file doesn't exist

        """
        # Look for template file directly in templates root
        template_file = self._templates_root / f'{template_name}.md'

        if not template_file.exists():
            raise TemplateNotFoundError(template_name=template_name, search_path=str(self._templates_root))

        try:
            template_path = TemplatePath(template_file)
            return Template.from_file(template_path.value)
        except OSError as e:
            # File system errors should be treated as template not found
            raise TemplateNotFoundError(template_name=template_name, search_path=str(self._templates_root)) from e
        # Let validation errors bubble up as they are

    def get_template_directory(self, directory_name: str) -> TemplateDirectory:
        """Load a template directory by name.

        Args:
            directory_name: Name of the template directory

        Returns:
            TemplateDirectory object

        Raises:
            TemplateDirectoryNotFoundError: If directory doesn't exist

        """
        directory_path = self._templates_root / directory_name

        if not directory_path.exists():
            msg = f"Template directory '{directory_name}' not found in {self._templates_root}"
            raise TemplateDirectoryNotFoundError(msg)

        if not directory_path.is_dir():
            msg = f"Template directory path '{directory_path}' is not a directory"
            raise TemplateDirectoryNotFoundError(msg)

        try:
            return TemplateDirectory.from_directory(directory_path)
        except Exception as e:
            # Re-raise as TemplateDirectoryNotFoundError for consistency
            msg = f"Failed to load template directory '{directory_name}': {e}"
            raise TemplateDirectoryNotFoundError(msg) from e

    @classmethod
    def list_templates(cls, search_path: Path) -> list[Template]:
        """List all individual templates in the search path.

        Args:
            search_path: Directory path to search for templates

        Returns:
            List of Template instances (excludes directory templates)

        Raises:
            TemplateDirectoryNotFoundError: If search_path does not exist

        """
        if not search_path.exists():  # pragma: no cover
            msg = f'Search path does not exist: {search_path}'
            raise TemplateDirectoryNotFoundError(msg)

        if not search_path.is_dir():
            msg = f'Search path is not a directory: {search_path}'
            raise TemplateDirectoryNotFoundError(msg)

        templates = []

        # Find all .md files directly in the search path
        for template_file in search_path.glob('*.md'):
            if template_file.is_file():  # pragma: no branch
                try:
                    template_path = TemplatePath(template_file)
                    template = Template.from_file(template_path.value)
                    templates.append(template)
                except (TemplateParseError, TemplateValidationError) as e:
                    # Log the error but skip invalid template files
                    import logging

                    logging.getLogger(__name__).warning('Skipping invalid template file %s: %s', template_file, e)
                    continue

        return sorted(templates, key=lambda t: t.name)

    def list_template_directories(self, search_path: Path) -> list[TemplateDirectory]:
        """List all template directories in the search path.

        Args:
            search_path: Directory path to search for template directories

        Returns:
            List of TemplateDirectory instances

        Raises:
            TemplateDirectoryNotFoundError: If search_path does not exist

        """
        if not search_path.exists():  # pragma: no cover
            msg = f'Search path does not exist: {search_path}'
            raise TemplateDirectoryNotFoundError(msg)

        if not search_path.is_dir():
            msg = f'Search path is not a directory: {search_path}'
            raise TemplateDirectoryNotFoundError(msg)

        directories = []

        # Find all directories in search path that contain .md files
        for item in search_path.iterdir():
            if item.is_dir() and self._directory_contains_templates(item):
                try:
                    template_directory = TemplateDirectory.from_directory(item)
                    directories.append(template_directory)
                except (TemplateParseError, TemplateValidationError, InvalidTemplateDirectoryError) as e:
                    # Log the error but skip invalid template directories
                    import logging

                    logging.getLogger(__name__).warning('Skipping invalid template directory %s: %s', item, e)
                    continue

        return sorted(directories, key=lambda d: d.name)

    def list_all_template_names(self) -> list[str]:
        """List all single template names available in the templates root.

        Returns:
            List of template names (without .md extension)

        """
        # Find all .md files directly in the templates root
        template_names = [
            template_file.stem for template_file in self._templates_root.glob('*.md') if template_file.is_file()
        ]

        return sorted(template_names)

    def list_all_template_directory_names(self) -> list[str]:
        """List all template directory names available in the templates root.

        Returns:
            List of template directory names

        """
        # Find all directories in templates root that contain .md files using list comprehension
        directory_names = [
            item.name
            for item in self._templates_root.iterdir()
            if item.is_dir() and self._directory_contains_templates(item)
        ]

        return sorted(directory_names)

    @classmethod
    def find_template_by_name(cls, name: str, search_path: Path) -> Template | None:
        """Find a template by name in the given search path.

        Args:
            name: Template name (without .md extension)
            search_path: Directory path to search for templates

        Returns:
            Template instance if found, None otherwise

        Raises:
            TemplateDirectoryNotFoundError: If search_path does not exist

        """
        if not search_path.exists():  # pragma: no cover
            msg = f'Search path does not exist: {search_path}'
            raise TemplateDirectoryNotFoundError(msg)

        if not search_path.is_dir():
            msg = f'Search path is not a directory: {search_path}'
            raise TemplateDirectoryNotFoundError(msg)

        template_file = search_path / f'{name}.md'
        if template_file.exists() and template_file.is_file():
            try:
                template_path = TemplatePath(template_file)
                return Template.from_file(template_path.value)
            except (TemplateParseError, TemplateValidationError):
                return None
        return None  # pragma: no cover

    def find_template_directory(self, name: str, search_path: Path) -> TemplateDirectory | None:
        """Find a template directory by name.

        Args:
            name: Directory name
            search_path: Parent directory to search in

        Returns:
            TemplateDirectory instance if found, None otherwise

        Raises:
            TemplateDirectoryNotFoundError: If search_path does not exist

        """
        if not search_path.exists():  # pragma: no cover
            msg = f'Search path does not exist: {search_path}'
            raise TemplateDirectoryNotFoundError(msg)

        if not search_path.is_dir():
            msg = f'Search path is not a directory: {search_path}'
            raise TemplateDirectoryNotFoundError(msg)

        directory_path = search_path / name
        if directory_path.exists() and directory_path.is_dir() and self._directory_contains_templates(directory_path):
            try:
                return TemplateDirectory.from_directory(directory_path)
            except (TemplateParseError, TemplateValidationError, InvalidTemplateDirectoryError):
                return None
        return None  # pragma: no cover

    @classmethod
    def load_template_content(cls, template_path: Path) -> str:
        """Load raw content from a template file.

        Args:
            template_path: Absolute path to template file

        Returns:
            Raw template content as string

        Raises:
            TemplateNotFoundError: If template file does not exist
            PermissionError: If template file is not readable

        """
        if not template_path.exists():
            raise TemplateNotFoundError(template_name=template_path.stem, search_path=str(template_path.parent))

        try:  # pragma: no cover
            return template_path.read_text(encoding='utf-8')
        except PermissionError as e:  # pragma: no cover
            msg = f'Cannot read template file: {template_path}'
            raise PermissionError(msg) from e

    @classmethod
    def validate_template_path(cls, path: Path) -> bool:
        """Validate that a path points to a valid template location.

        Args:
            path: Path to validate

        Returns:
            True if path is valid for template operations

        """
        return path.exists() and path.is_file() and path.suffix == '.md'

    def template_exists(self, template_name: str) -> bool:
        """Check if a single template exists.

        Args:
            template_name: Name of the template

        Returns:
            True if template exists, False otherwise

        """
        template_file = self._templates_root / f'{template_name}.md'
        return template_file.exists() and template_file.is_file()

    def template_directory_exists(self, directory_name: str) -> bool:
        """Check if a template directory exists.

        Args:
            directory_name: Name of the template directory

        Returns:
            True if directory exists and contains templates, False otherwise

        """
        directory_path = self._templates_root / directory_name
        return (
            directory_path.exists() and directory_path.is_dir() and self._directory_contains_templates(directory_path)
        )

    def get_templates_root(self) -> Path:
        """Get the root directory for templates.

        Returns:
            Path to templates root directory

        """
        return self._templates_root

    @staticmethod
    def _directory_contains_templates(directory_path: Path) -> bool:
        """Check if a directory contains any template files.

        Args:
            directory_path: Path to directory to check

        Returns:
            True if directory contains .md files, False otherwise

        """
        try:
            # Check for .md files recursively
            return any(template_file.is_file() for template_file in directory_path.rglob('*.md'))
        except (OSError, PermissionError):  # pragma: no cover
            return False

    def get_template_info(self, template_name: str) -> dict[str, Any]:
        """Get metadata about a template without fully loading it.

        Args:
            template_name: Name of the template

        Returns:
            Dictionary with template metadata

        Raises:
            TemplateNotFoundError: If template doesn't exist

        """
        template_file = self._templates_root / f'{template_name}.md'

        if not template_file.exists():
            raise TemplateNotFoundError(template_name=template_name, search_path=str(self._templates_root))

        try:  # pragma: no cover
            # Get file stats
            stat = template_file.stat()

            return {
                'name': template_name,
                'file_path': str(template_file),
                'file_size': stat.st_size,
                'modified_time': stat.st_mtime,
                'is_directory_template': False,
            }
        except (OSError, PermissionError) as e:  # pragma: no cover
            raise TemplateNotFoundError(template_name=template_name, search_path=str(self._templates_root)) from e

    def get_template_directory_info(self, directory_name: str) -> dict[str, Any]:
        """Get metadata about a template directory without fully loading it.

        Args:
            directory_name: Name of the template directory

        Returns:
            Dictionary with directory metadata

        Raises:
            TemplateDirectoryNotFoundError: If directory doesn't exist

        """
        directory_path = self._templates_root / directory_name

        if not directory_path.exists() or not directory_path.is_dir():
            msg = f"Template directory '{directory_name}' not found in {self._templates_root}"
            raise TemplateDirectoryNotFoundError(msg)

        try:  # pragma: no cover
            # Count template files
            template_count = sum(1 for f in directory_path.rglob('*.md') if f.is_file())

            # Get directory stats
            stat = directory_path.stat()

            return {
                'name': directory_name,
                'directory_path': str(directory_path),
                'template_count': template_count,
                'modified_time': stat.st_mtime,
                'is_directory_template': True,
            }
        except (OSError, PermissionError) as e:  # pragma: no cover
            msg = f"Failed to get info for template directory '{directory_name}': {e}"
            raise TemplateDirectoryNotFoundError(msg) from e
