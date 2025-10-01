"""Template Repository Port Contract.

Defines the interface for template storage and retrieval operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.entities.template_directory import TemplateDirectory


class TemplateRepositoryPort(ABC):
    """Port for template storage and retrieval operations."""

    @abstractmethod
    def find_template_by_name(self, name: str, search_path: Path) -> Template | None:
        """Find a template by name in the given search path.

        Args:
            name: Template name (without .md extension)
            search_path: Directory path to search for templates

        Returns:
            Template instance if found, None otherwise

        Raises:
            TemplateDirectoryNotFoundError: If search_path does not exist

        """

    @abstractmethod
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

    @abstractmethod
    def get_templates_root(self) -> Path:
        """Get the root directory for templates.

        Returns:
            Path to templates root directory

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_template(self, template_name: str) -> Template:
        """Load a single template by name from the templates root.

        Args:
            template_name: Name of the template (without .md extension)

        Returns:
            Template instance

        Raises:
            TemplateNotFoundError: If template doesn't exist

        """

    @abstractmethod
    def get_template_directory(self, directory_name: str) -> TemplateDirectory:
        """Load a template directory by name from the templates root.

        Args:
            directory_name: Name of the template directory

        Returns:
            TemplateDirectory instance

        Raises:
            TemplateDirectoryNotFoundError: If directory doesn't exist

        """

    @abstractmethod
    def list_templates(self, search_path: Path) -> list[Template]:
        """List all individual templates in the search path.

        Args:
            search_path: Directory path to search for templates

        Returns:
            List of Template instances (excludes directory templates)

        Raises:
            TemplateDirectoryNotFoundError: If search_path does not exist

        """

    @abstractmethod
    def list_template_directories(self, search_path: Path) -> list[TemplateDirectory]:
        """List all template directories in the search path.

        Args:
            search_path: Directory path to search for template directories

        Returns:
            List of TemplateDirectory instances

        Raises:
            TemplateDirectoryNotFoundError: If search_path does not exist

        """

    @abstractmethod
    def load_template_content(self, template_path: Path) -> str:
        """Load raw content from a template file.

        Args:
            template_path: Absolute path to template file

        Returns:
            Raw template content as string

        Raises:
            TemplateNotFoundError: If template file does not exist
            FilePermissionError: If template file is not readable

        """

    @abstractmethod
    def validate_template_path(self, path: Path) -> bool:
        """Validate that a path points to a valid template location.

        Args:
            path: Path to validate

        Returns:
            True if path is valid for template operations

        """
