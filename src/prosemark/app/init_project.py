"""InitProject use case for creating new prosemark projects."""

from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import Binder

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.logger import Logger


class InitProject:
    """Initialize a new prosemark writing project."""

    def __init__(
        self,
        *,
        binder_repo: 'BinderRepo',
        console: 'ConsolePort',
        logger: 'Logger',
    ) -> None:
        """Initialize the InitProject use case.

        Args:
            binder_repo: Repository for binder operations.
            console: Console output port.
            logger: Logger port.

        """
        self.binder_repo = binder_repo
        self.console = console
        self.logger = logger

    def execute(self, *, project_title: str, project_path: Path | None = None) -> None:
        """Initialize a new prosemark project.

        Args:
            project_title: Title for the new project.
            project_path: Optional path for project, defaults to current directory.

        """
        project_path = project_path or Path.cwd()
        self.logger.info('Initializing project: %s at %s', project_title, project_path)

        # Check if binder already exists
        binder_path = project_path / '_binder.md'
        if binder_path.exists():
            self.console.print_error(f'Binder already exists at {binder_path}')
            return

        # Create new binder
        binder = Binder(roots=[])

        # Save the binder
        self.binder_repo.save(binder)

        self.console.print_success(f'Project "{project_title}" initialized successfully')
        self.console.print_info(f'Created {binder_path}')
        self.logger.info('Project initialized: %s', project_title)
