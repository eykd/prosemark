"""Repository-related exceptions.

This module defines exceptions that can be raised by repository implementations.
"""


class RepositoryError(Exception):
    """Base exception for repository-related errors.

    This exception should be used as the base class for all repository-specific exceptions.
    """


class ProjectNotFoundError(RepositoryError):
    """Raised when a project cannot be found in the repository.

    This exception is raised when attempting to load or delete a project that does not exist.
    """

    def __init__(self) -> None:
        super().__init__('Project not found in repository')


class ProjectExistsError(RepositoryError):
    """Raised when attempting to create a project in a repository that already has one.

    This exception is raised when trying to create a project in a repository that
    already contains a project.
    """

    def __init__(self) -> None:
        super().__init__('A project already exists in this repository')
