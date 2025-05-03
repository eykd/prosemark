"""Repository interfaces for the prosemark domain.

This module defines the repository interfaces for persisting domain objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.projects import Project


class ProjectRepository(Protocol):
    """Interface for project persistence operations.

    This interface defines the contract for storing and retrieving Project objects.
    Concrete implementations will handle the actual persistence mechanism.
    """

    def save(self, project: Project) -> None:  # pragma: no cover
        """Save a project to the repository.

        Args:
            project: The project to save.

        Raises:
            RepositoryError: If the project cannot be saved.

        """
        ...

    def load(self, project_id: str) -> Project:  # pragma: no cover
        """Load a project from the repository.

        Args:
            project_id: The identifier of the project to load.

        Returns:
            The loaded project.

        Raises:
            ProjectNotFoundError: If the project cannot be found.
            RepositoryError: If the project cannot be loaded.

        """
        ...

    def list_projects(self) -> list[dict[str, str]]:  # pragma: no cover
        """List all available projects in the repository.

        Returns:
            A list of dictionaries containing project metadata.
            Each dictionary should contain at least 'id' and 'name' keys.

        Raises:
            RepositoryError: If the projects cannot be listed.

        """
        ...

    def create_project(self, name: str, description: str = '') -> Project:  # pragma: no cover
        """Create a new project in the repository.

        Args:
            name: The name of the new project.
            description: An optional description of the project.

        Returns:
            The newly created project.

        Raises:
            ProjectExistsError: If a project with the same name already exists.
            RepositoryError: If the project cannot be created.

        """
        ...

    def delete_project(self, project_id: str) -> None:  # pragma: no cover
        """Delete a project from the repository.

        Args:
            project_id: The identifier of the project to delete.

        Raises:
            ProjectNotFoundError: If the project cannot be found.
            RepositoryError: If the project cannot be deleted.

        """
        ...
