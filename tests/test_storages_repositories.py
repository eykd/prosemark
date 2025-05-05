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
    loaded_project = repo.load()

    # Verify it's the same project
    assert loaded_project is project
    assert loaded_project.name == 'Test Project'
    assert loaded_project.description == 'A test project'


def test_repository_exists() -> None:
    """Test that a repository can check if a project exists."""
    repo = InMemoryProjectRepository()

    # Initially, no project exists
    assert not repo.exists()

    # Create a project
    project = Project(name='Test Project')
    repo.save(project)

    # Now a project exists
    assert repo.exists()


def test_repository_create() -> None:
    """Test that a repository can create a new project."""
    repo = InMemoryProjectRepository()

    # Create a project
    project = repo.create('New Project', 'A new project')

    # Verify the project was created
    assert project.name == 'New Project'
    assert project.description == 'A new project'
    assert project.root_node is not None

    # Verify it exists in the repository
    assert repo.exists()


def test_repository_delete() -> None:
    """Test that a repository can delete a project."""
    repo = InMemoryProjectRepository()

    # Create a project
    repo.create('Temporary Project', 'A project to delete')

    # Verify it exists
    assert repo.exists()

    # Delete the project
    repo.delete()

    # Verify it was deleted
    assert not repo.exists()


def test_repository_project_not_found() -> None:
    """Test that appropriate errors are raised when a project is not found."""
    repo = InMemoryProjectRepository()

    # Try to load a non-existent project
    with pytest.raises(ProjectNotFoundError):
        repo.load()

    # Try to delete a non-existent project
    with pytest.raises(ProjectNotFoundError):
        repo.delete()


def test_repository_project_already_exists() -> None:
    """Test that appropriate errors are raised when a project already exists."""
    repo = InMemoryProjectRepository()

    # Create a project
    repo.create('Existing Project')

    # Try to create another project
    with pytest.raises(ProjectExistsError):
        repo.create('Another Project')
