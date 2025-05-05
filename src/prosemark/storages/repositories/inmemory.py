"""In-memory implementation of the ProjectRepository interface."""

from prosemark.domain.projects import Project
from prosemark.storages.repositories.exceptions import ProjectExistsError, ProjectNotFoundError


class InMemoryProjectRepository:
    """A simple in-memory implementation of ProjectRepository for testing."""

    def __init__(self) -> None:
        """Initialize an empty in-memory project repository."""
        self._project: Project | None = None

    def save(self, project: Project) -> None:
        """Save the project to the repository.

        Args:
            project: The project to save.

        """
        self._project = project

    def load(self) -> Project:
        """Load the project from the repository.

        Returns:
            The loaded project.

        Raises:
            ProjectNotFoundError: If no project exists in the repository.

        """
        if self._project is None:
            raise ProjectNotFoundError
        return self._project

    def exists(self) -> bool:
        """Check if a project exists in the repository.

        Returns:
            True if a project exists, False otherwise.

        """
        return self._project is not None

    def create(self, name: str, description: str = '') -> Project:
        """Create a new project in the repository.

        Args:
            name: The name of the project.
            description: An optional description of the project.

        Returns:
            The newly created project.

        Raises:
            ProjectExistsError: If a project already exists in the repository.

        """
        if self._project is not None:
            raise ProjectExistsError

        self._project = Project(name=name, description=description)
        return self._project

    def delete(self) -> None:
        """Delete the project from the repository.

        Raises:
            ProjectNotFoundError: If no project exists in the repository.

        """
        if self._project is None:
            raise ProjectNotFoundError
        self._project = None
