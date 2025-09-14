"""Use case interactors for prosemark application layer."""

from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import BinderIntegrityError, NodeNotFoundError

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.clock import Clock
    from prosemark.ports.config_port import ConfigPort
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.id_generator import IdGenerator
    from prosemark.ports.logger import Logger
    from prosemark.ports.node_repo import NodeRepo


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


class AddNode:
    """Use case interactor for adding new nodes to the binder structure.

    Orchestrates the creation of new nodes by generating unique identifiers,
    creating node files with proper frontmatter, and updating the binder
    hierarchy. Follows hexagonal architecture principles with pure business
    logic that delegates all I/O operations to injected port implementations.

    The node creation process:
    1. Generates unique NodeId for the new node
    2. Creates node draft file ({id}.md) with YAML frontmatter
    3. Creates node notes file ({id}.notes.md) as empty file
    4. Validates parent node exists when specified
    5. Adds BinderItem to binder structure at specified position
    6. Updates and saves binder changes to _binder.md
    7. Logs all operations with NodeId for traceability

    Args:
        binder_repo: Port for binder persistence operations
        node_repo: Port for node file creation and management
        id_generator: Port for generating unique NodeId values
        logger: Port for operational logging and audit trails
        clock: Port for timestamp generation

    Examples:
        >>> # With dependency injection
        >>> interactor = AddNode(
        ...     binder_repo=file_binder_repo,
        ...     node_repo=file_node_repo,
        ...     id_generator=uuid_generator,
        ...     logger=production_logger,
        ...     clock=system_clock,
        ... )
        >>> node_id = interactor.execute(title='Chapter One', synopsis='The beginning', parent_id=None, position=None)

    """

    def __init__(
        self,
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        id_generator: 'IdGenerator',
        logger: 'Logger',
        clock: 'Clock',
    ) -> None:
        """Initialize AddNode with injected dependencies.

        Args:
            binder_repo: Port for binder persistence operations
            node_repo: Port for node file creation and management
            id_generator: Port for generating unique NodeId values
            logger: Port for operational logging and audit trails
            clock: Port for timestamp generation

        """
        self._binder_repo = binder_repo
        self._node_repo = node_repo
        self._id_generator = id_generator
        self._logger = logger
        self._clock = clock

    def execute(
        self,
        title: str | None,
        synopsis: str | None,
        parent_id: NodeId | None,
        position: int | None,
    ) -> NodeId:
        """Execute node creation workflow.

        Creates a new node with the specified metadata and adds it to the
        binder hierarchy. The node is added at the root level if no parent
        is specified, or under the specified parent node.

        Args:
            title: Optional title for the node (used as display_title)
            synopsis: Optional synopsis/summary for the node
            parent_id: Optional parent NodeId for nested placement
            position: Optional position for insertion order (None = append)

        Returns:
            NodeId of the created node

        Raises:
            NodeNotFoundError: If specified parent_id doesn't exist in binder
            BinderIntegrityError: If binder integrity is violated after addition
            FilesystemError: If node files cannot be created (propagated from ports)

        """
        self._logger.info('Starting node creation with title=%s, parent_id=%s', title, parent_id)

        # Generation Phase - Create unique identity
        node_id = self._id_generator.new()
        self._logger.debug('Generated new NodeId: %s', node_id)

        # Creation Phase - Set up node files with proper metadata
        self._clock.now_iso()
        self._node_repo.create(node_id, title, synopsis)
        self._logger.debug('Created node files for NodeId: %s', node_id)

        # Integration Phase - Add to binder structure
        binder = self._binder_repo.load()
        self._add_node_to_binder(binder, node_id, title, parent_id, position)
        self._binder_repo.save(binder)
        self._logger.debug('Added node to binder and saved changes for NodeId: %s', node_id)

        # Completion
        self._logger.info('Node creation completed successfully for NodeId: %s', node_id)
        return node_id

    def _add_node_to_binder(
        self,
        binder: Binder,
        node_id: NodeId,
        title: str | None,
        parent_id: NodeId | None,
        position: int | None,
    ) -> None:
        """Add the new node to the binder hierarchy.

        Creates a BinderItem for the node and adds it to the appropriate
        location in the binder tree structure.

        Args:
            binder: Binder instance to modify
            node_id: NodeId of the new node
            title: Title to use as display_title (or empty string if None)
            parent_id: Optional parent NodeId for nested placement
            position: Optional position for insertion order

        Raises:
            NodeNotFoundError: If parent_id is specified but doesn't exist

        """
        # Create BinderItem for the new node
        display_title = title if title is not None else ''
        new_item = BinderItem(id=node_id, display_title=display_title, children=[])

        if parent_id is None:
            # Add to root level
            self._logger.debug('Adding node to binder roots for NodeId: %s', node_id)
            if position is None:
                binder.roots.append(new_item)
            else:
                binder.roots.insert(position, new_item)
        else:
            # Add under specified parent
            self._logger.debug('Adding node under parent %s for NodeId: %s', parent_id, node_id)
            parent_item = binder.find_by_id(parent_id)
            if parent_item is None:
                self._logger.error('Parent node not found in binder: %s', parent_id)
                raise NodeNotFoundError('Parent node not found', str(parent_id))

            if position is None:
                parent_item.children.append(new_item)
            else:
                parent_item.children.insert(position, new_item)

        # Validate binder integrity after modification
        binder.validate_integrity()  # pragma: no cover
