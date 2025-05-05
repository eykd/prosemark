"""Repository interfaces for the prosemark domain.

This module defines the repository interfaces for persisting domain objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.projects import Project


class ProjectRepository(Protocol):
    """Interface for project persistence operations.

    This interface defines the contract for storing and retrieving a single Project object.
    Concrete implementations will handle the actual persistence mechanism.
    """

    def save(self, project: Project) -> None:  # pragma: no cover
        """Save the project to the repository.

        Args:
            project: The project to save.

        Raises:
            RepositoryError: If the project cannot be saved.

        """
        ...

    def load(self) -> Project:  # pragma: no cover
        """Load the project from the repository.

        Returns:
            The loaded project.

        Raises:
            ProjectNotFoundError: If the project cannot be found.
            RepositoryError: If the project cannot be loaded.

        """
        ...

    def exists(self) -> bool:  # pragma: no cover
        """Check if a project exists in the repository.

        Returns:
            True if a project exists, False otherwise.

        """
        ...

    def create(self, name: str, description: str = '') -> Project:  # pragma: no cover
        """Create a new project in the repository.

        Args:
            name: The name of the new project.
            description: An optional description of the project.

        Returns:
            The newly created project.

        Raises:
            ProjectExistsError: If a project already exists in the repository.
            RepositoryError: If the project cannot be created.

        """
        ...

    def delete(self) -> None:  # pragma: no cover
        """Delete the project from the repository.

        Raises:
            ProjectNotFoundError: If the project cannot be found.
            RepositoryError: If the project cannot be deleted.

        """
        ...
