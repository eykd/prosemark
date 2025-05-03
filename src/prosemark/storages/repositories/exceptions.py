"""Repository-related exceptions.

This module defines exceptions that can be raised by repository implementations.
"""


class RepositoryError(Exception):
    """Base exception for repository-related errors.

    This exception should be used as the base class for all repository-specific exceptions.
    """


class ProjectNotFoundError(RepositoryError):
    """Raised when a requested project cannot be found in the repository.

    This exception is raised when attempting to load or delete a project that does not exist.

    Attributes:
        project_id: The identifier of the project that was not found.

    """

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(f'Project {project_id} not found')


class ProjectExistsError(RepositoryError):
    """Raised when attempting to create a project that already exists.

    This exception is raised when trying to create a project with a name that is already
    in use by another project in the repository.

    Attributes:
        project_name: The name of the project that already exists.

    """

    def __init__(self, project_name: str) -> None:
        self.project_name = project_name
        super().__init__(f'Project {project_name} already exists')
