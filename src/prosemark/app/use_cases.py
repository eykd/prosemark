"""Use case interactors for prosemark application layer."""

from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import Binder
from prosemark.exceptions import BinderIntegrityError

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.clock import Clock
    from prosemark.ports.config_port import ConfigPort
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.logger import Logger


class InitProject:
    """Use case interactor for initializing a new prosemark project.

    Orchestrates the creation of a new prosemark project by setting up
    the necessary file structure, configuration, and initial binder state.
    Follows hexagonal architecture principles with pure business logic
    that delegates all I/O operations to injected port implementations.

    The initialization process:
    1. Validates the target directory is suitable for project creation
    2. Checks for existing project files to prevent conflicts
    3. Creates an empty binder structure with proper managed blocks
    4. Generates default configuration file (.prosemark.yml)
    5. Logs operational details and provides user feedback

    Args:
        binder_repo: Port for binder persistence operations
        config_port: Port for configuration file management
        console_port: Port for user output and messaging
        logger: Port for operational logging and audit trails
        clock: Port for timestamp generation

    Examples:
        >>> # With dependency injection
        >>> interactor = InitProject(
        ...     binder_repo=file_binder_repo,
        ...     config_port=yaml_config_port,
        ...     console_port=terminal_console,
        ...     logger=production_logger,
        ...     clock=system_clock,
        ... )
        >>> interactor.execute(Path('/path/to/new/project'))

    """

    def __init__(
        self,
        binder_repo: 'BinderRepo',
        config_port: 'ConfigPort',
        console_port: 'ConsolePort',
        logger: 'Logger',
        clock: 'Clock',
    ) -> None:
        """Initialize InitProject with injected dependencies.

        Args:
            binder_repo: Port for binder persistence operations
            config_port: Port for configuration file management
            console_port: Port for user output and messaging
            logger: Port for operational logging and audit trails
            clock: Port for timestamp generation

        """
        self._binder_repo = binder_repo
        self._config_port = config_port
        self._console_port = console_port
        self._logger = logger
        self._clock = clock

    def execute(self, project_path: Path) -> None:
        """Execute project initialization workflow.

        Creates a new prosemark project at the specified path with default
        configuration and empty binder structure. Validates that the target
        directory doesn't already contain a prosemark project.

        Args:
            project_path: Directory where project should be initialized

        Raises:
            BinderIntegrityError: If project is already initialized (_binder.md exists)
            FilesystemError: If files cannot be created (propagated from ports)

        """
        self._logger.info('Starting project initialization at %s', project_path)

        # Validation Phase - Check for existing project
        binder_path = project_path / '_binder.md'
        config_path = project_path / '.prosemark.yml'

        if binder_path.exists():
            self._logger.error('Project initialization failed: project already exists at %s', binder_path)
            raise BinderIntegrityError('Project already initialized', str(binder_path))

        self._logger.debug('Validation passed: no existing project found')

        # Creation Phase - Set up project structure
        self._clock.now_iso()
        self._create_initial_binder()
        self._create_default_config(config_path)

        # User Feedback - Confirm successful initialization
        self._console_port.print(f'Initialized prosemark project at {project_path}')
        self._logger.info('Project initialization completed successfully at %s', project_path)

    def _create_initial_binder(self) -> None:
        """Create initial empty binder structure.

        Creates a new Binder aggregate with empty roots list and saves it
        through the binder repository. This establishes the foundational
        hierarchy structure for the project.

        """
        self._logger.debug('Creating initial empty binder structure')
        initial_binder = Binder(roots=[])
        self._binder_repo.save(initial_binder)
        self._logger.info('Initial binder structure created and saved')

    def _create_default_config(self, config_path: Path) -> None:
        """Create default configuration file.

        Delegates configuration file creation to the config port, which
        handles the specific format and default values according to the
        MVP specification.

        Args:
            config_path: Path where configuration file should be created

        """
        self._logger.debug('Creating default configuration at %s', config_path)
        self._config_port.create_default_config(config_path)
        self._logger.info('Default configuration created at %s', config_path)
