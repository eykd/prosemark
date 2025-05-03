"""Tests for the repository interfaces."""

from __future__ import annotations

import pytest

from prosemark.domain.projects import Project
from prosemark.domain.repositories import ProjectRepository


# Define a simple in-memory implementation for testing
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
            raise ValueError(f'Project {project_id} not found')
        return self.projects[project_id]

    def list_projects(self) -> list[dict[str, str]]:
        """List all available projects in the repository."""
        return [{'id': name, 'name': name} for name in self.projects]

    def create_project(self, name: str, description: str = '') -> Project:
        """Create a new project in the repository."""
        if name in self.projects:
            raise ValueError(f'Project {name} already exists')
        project = Project(name=name, description=description)
        self.projects[name] = project
        return project

    def delete_project(self, project_id: str) -> None:
        """Delete a project from the repository."""
        if project_id not in self.projects:
            raise ValueError(f'Project {project_id} not found')
        del self.projects[project_id]


# Type check to ensure InMemoryProjectRepository implements ProjectRepository
_: ProjectRepository = InMemoryProjectRepository()  # type: ignore


def test_repository_save_and_load() -> None:
    """Test that a repository can save and load a project."""
    repo = InMemoryProjectRepository()
    project = Project(name='Test Project', description='A test project')

    # Save the project
    repo.save(project)

    # Load the project
    loaded_project = repo.load('Test Project')

    # Verify it's the same project
    assert loaded_project is project
    assert loaded_project.name == 'Test Project'
    assert loaded_project.description == 'A test project'


def test_repository_list_projects() -> None:
    """Test that a repository can list all projects."""
    repo = InMemoryProjectRepository()

    # Create some projects
    project1 = repo.create_project('Project 1', 'First project')
    project2 = repo.create_project('Project 2', 'Second project')

    # List projects
    projects = repo.list_projects()

    # Verify the list
    assert len(projects) == 2
    assert {'id': 'Project 1', 'name': 'Project 1'} in projects
    assert {'id': 'Project 2', 'name': 'Project 2'} in projects


def test_repository_create_project() -> None:
    """Test that a repository can create a new project."""
    repo = InMemoryProjectRepository()

    # Create a project
    project = repo.create_project('New Project', 'A new project')

    # Verify the project was created
    assert project.name == 'New Project'
    assert project.description == 'A new project'
    assert project.root_node is not None

    # Verify it was added to the repository
    assert 'New Project' in [p['id'] for p in repo.list_projects()]


def test_repository_delete_project() -> None:
    """Test that a repository can delete a project."""
    repo = InMemoryProjectRepository()

    # Create a project
    repo.create_project('Temporary Project', 'A project to delete')

    # Verify it exists
    assert 'Temporary Project' in [p['id'] for p in repo.list_projects()]

    # Delete the project
    repo.delete_project('Temporary Project')

    # Verify it was deleted
    assert 'Temporary Project' not in [p['id'] for p in repo.list_projects()]


def test_repository_project_not_found() -> None:
    """Test that appropriate errors are raised when a project is not found."""
    repo = InMemoryProjectRepository()

    # Try to load a non-existent project
    with pytest.raises(ValueError):
        repo.load('Non-existent Project')

    # Try to delete a non-existent project
    with pytest.raises(ValueError):
        repo.delete_project('Non-existent Project')


def test_repository_project_already_exists() -> None:
    """Test that appropriate errors are raised when a project already exists."""
    repo = InMemoryProjectRepository()

    # Create a project
    repo.create_project('Existing Project')

    # Try to create a project with the same name
    with pytest.raises(ValueError):
        repo.create_project('Existing Project')
