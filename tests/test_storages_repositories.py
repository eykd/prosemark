"""Tests for the repository interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prosemark.domain.projects import Project
from prosemark.storages.repositories.exceptions import ProjectExistsError, ProjectNotFoundError
from prosemark.storages.repositories.inmemory import InMemoryProjectRepository

if TYPE_CHECKING:
    from prosemark.storages.repositories.base import ProjectRepository

# Type check to ensure InMemoryProjectRepository implements ProjectRepository
_: ProjectRepository = InMemoryProjectRepository()


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
    repo.create_project('Project 1', 'First project')
    repo.create_project('Project 2', 'Second project')

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
    with pytest.raises(ProjectNotFoundError) as exc_info:
        repo.load('Non-existent Project')
    assert exc_info.value.project_id == 'Non-existent Project'

    # Try to delete a non-existent project
    with pytest.raises(ProjectNotFoundError) as exc_info:
        repo.delete_project('Non-existent Project')
    assert exc_info.value.project_id == 'Non-existent Project'


def test_repository_project_already_exists() -> None:
    """Test that appropriate errors are raised when a project already exists."""
    repo = InMemoryProjectRepository()

    # Create a project
    repo.create_project('Existing Project')

    # Try to create a project with the same name
    with pytest.raises(ProjectExistsError) as exc_info:
        repo.create_project('Existing Project')
    assert exc_info.value.project_name == 'Existing Project'
