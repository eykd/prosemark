"""In-memory implementation of the ProjectRepository interface."""

from prosemark.domain.projects import Project
from prosemark.storages.repositories.exceptions import ProjectExistsError, ProjectNotFoundError


class InMemoryProjectRepository:
    """A simple in-memory implementation of ProjectRepository for testing."""

    def __init__(self) -> None:
        self.projects: dict[str, Project] = {}

    def save(self, project: Project) -> None:
        """Save a project to the repository."""
        self.projects[project.name] = project

    def load(self, project_id: str) -> Project:
        """Load a project from the repository."""
        if project_id not in self.projects:
            raise ProjectNotFoundError(project_id)
        return self.projects[project_id]

    def list_projects(self) -> list[dict[str, str]]:
        """List all available projects in the repository."""
        return [{'id': name, 'name': name} for name in self.projects]

    def create_project(self, name: str, description: str = '') -> Project:
        """Create a new project in the repository."""
        if name in self.projects:
            raise ProjectExistsError(name)
        project = Project(name=name, description=description)
        self.projects[name] = project
        return project

    def delete_project(self, project_id: str) -> None:
        """Delete a project from the repository."""
        if project_id not in self.projects:
            raise ProjectNotFoundError(project_id)
        del self.projects[project_id]
