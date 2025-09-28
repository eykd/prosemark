"""Use case interactors for prosemark application layer."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import (
    AlreadyMaterializedError,
    BinderIntegrityError,
    EditorLaunchError,
    FileSystemError,
    NodeIdentityError,
    NodeNotFoundError,
    PlaceholderNotFoundError,
)

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.clock import Clock
    from prosemark.ports.config_port import ConfigPort
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.daily_repo import DailyRepo
    from prosemark.ports.editor_port import EditorPort
    from prosemark.ports.id_generator import IdGenerator
    from prosemark.ports.logger import Logger
    from prosemark.ports.node_repo import NodeRepo


@dataclass(frozen=True)
class PlaceholderIssue:
    """Represents a placeholder item found during audit."""

    display_title: str
    position: str  # Human-readable position like "[0][1]"


@dataclass(frozen=True)
class MissingIssue:
    """Represents a missing node file found during audit."""

    node_id: NodeId
    expected_path: str


@dataclass(frozen=True)
class OrphanIssue:
    """Represents an orphaned node file found during audit."""

    node_id: NodeId
    file_path: str


@dataclass(frozen=True)
class MismatchIssue:
    """Represents a frontmatter ID mismatch found during audit."""

    file_path: str
    expected_id: NodeId
    actual_id: NodeId


@dataclass
class AuditReport:
    """Contains the results of a binder audit operation."""

    placeholders: list[PlaceholderIssue] = field(default_factory=list)
    missing: list[MissingIssue] = field(default_factory=list)
    orphans: list[OrphanIssue] = field(default_factory=list)
    mismatches: list[MismatchIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        """Check if the audit found no issues.

        Placeholders are not considered errors - they are informational items
        that indicate planned content without actual implementation.

        Returns:
            True if no issues were found, False otherwise

        """
        return not self.missing and not self.orphans and not self.mismatches

    def format_report(self) -> str:
        """Format the audit results as a human-readable report.

        Returns:
            Formatted string report with issues organized by type

        """
        if self.is_clean() and not self.placeholders:
            return 'Audit Results:\n============\n✓ Clean (no issues found)'

        lines = ['Issues Found:' if not self.is_clean() else 'Audit Results:', '============']

        if self.placeholders:
            lines.append(f'PLACEHOLDERS ({len(self.placeholders)}):')
            lines.extend(
                f'  - "{placeholder.display_title}" at position {placeholder.position}'
                for placeholder in self.placeholders
            )
            lines.append('')

        if self.missing:
            lines.append(f'MISSING ({len(self.missing)}):')
            lines.extend(
                f'  - Node {missing.expected_path} referenced in binder but file missing' for missing in self.missing
            )
            lines.append('')

        if self.orphans:
            lines.append(f'ORPHANS ({len(self.orphans)}):')
            lines.extend(f'  - Node {orphan.file_path} exists but not in binder' for orphan in self.orphans)
            lines.append('')

        if self.mismatches:
            lines.append(f'MISMATCHES ({len(self.mismatches)}):')
            lines.extend(
                f'  - File {mismatch.file_path} has frontmatter id: {mismatch.actual_id}'
                for mismatch in self.mismatches
            )
            lines.append('')

        return '\n'.join(lines).rstrip()

    def to_json(self) -> str:
        """Convert audit results to JSON format.

        Returns:
            JSON string representation of the audit results

        """
        data = {
            'placeholders': [
                {
                    'display_title': p.display_title,
                    'position': p.position,
                }
                for p in self.placeholders
            ],
            'missing': [
                {
                    'node_id': str(m.node_id),
                    'expected_path': m.expected_path,
                }
                for m in self.missing
            ],
            'orphans': [
                {
                    'node_id': str(o.node_id),
                    'file_path': o.file_path,
                }
                for o in self.orphans
            ],
            'mismatches': [
                {
                    'file_path': m.file_path,
                    'expected_id': str(m.expected_id),
                    'actual_id': str(m.actual_id),
                }
                for m in self.mismatches
            ],
        }
        return json.dumps(data, indent=2)


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
            FileSystemError: If files cannot be created (propagated from ports)

        """
        self._logger.info('Starting project initialization at %s', project_path)

        # Validation Phase - Check for existing project
        binder_path = project_path / '_binder.md'
        config_path = project_path / '.prosemark.yml'

        if binder_path.exists():
            self._logger.error('Project initialization failed: project already exists at %s', binder_path)
            msg = 'Project already initialized'
            raise BinderIntegrityError(msg, str(binder_path))

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
            FileSystemError: If node files cannot be created (propagated from ports)

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
        display_title = title if title is not None else '(untitled)'
        new_item = BinderItem(display_title=display_title, node_id=node_id, children=[])

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
                msg = 'Parent node not found'
                raise NodeNotFoundError(msg, str(parent_id))

            if position is None:
                parent_item.children.append(new_item)
            else:
                parent_item.children.insert(position, new_item)

        # Validate binder integrity after modification
        binder.validate_integrity()  # pragma: no cover


class EditPart:
    """Use case interactor for editing node parts in external editor.

    Orchestrates the opening of node parts (draft, notes, synopsis) in the
    configured external editor. Follows hexagonal architecture principles
    with pure business logic that delegates all I/O operations to injected
    port implementations.

    The edit process:
    1. Validates that the specified node exists in the binder
    2. Validates that the requested part is valid (draft, notes, synopsis)
    3. Opens the appropriate file part in the external editor
    4. Logs the editor operation for traceability

    Args:
        binder_repo: Port for binder persistence operations (validation)
        node_repo: Port for node file operations and editor integration
        logger: Port for operational logging and audit trails

    Examples:
        >>> # With dependency injection
        >>> interactor = EditPart(
        ...     binder_repo=file_binder_repo,
        ...     node_repo=file_node_repo,
        ...     logger=production_logger,
        ... )
        >>> interactor.execute(node_id=node_id, part='draft')

    """

    def __init__(
        self,
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        logger: 'Logger',
    ) -> None:
        """Initialize EditPart with injected dependencies.

        Args:
            binder_repo: Port for binder persistence operations (validation)
            node_repo: Port for node file operations and editor integration
            logger: Port for operational logging and audit trails

        """
        self._binder_repo = binder_repo
        self._node_repo = node_repo
        self._logger = logger

    def execute(self, node_id: NodeId, part: str) -> None:
        """Execute part editing workflow.

        Opens the specified part of the node in the external editor.
        Validates that both the node and part are valid before proceeding.

        Args:
            node_id: NodeId of the node to edit
            part: Which part to edit - must be one of:
                  - 'draft': Edit the main content in {id}.md
                  - 'notes': Edit the notes in {id}.notes.md
                  - 'synopsis': Edit the synopsis field in {id}.md frontmatter

        Raises:
            NodeNotFoundError: If node_id doesn't exist in binder
            ValueError: If part is not a valid option
            FileSystemError: If editor cannot be launched or files don't exist

        """
        self._logger.info('Starting edit operation for NodeId: %s, part: %s', node_id, part)

        # Validation Phase - Check node exists in binder
        binder = self._binder_repo.load()
        target_item = binder.find_by_id(node_id)
        if target_item is None:
            self._logger.error('Node not found in binder: %s', node_id)
            msg = 'Node not found in binder'
            raise NodeNotFoundError(msg, str(node_id))

        # Validation Phase - Check part is valid
        valid_parts = {'draft', 'notes', 'synopsis'}
        if part not in valid_parts:
            self._logger.error('Invalid part specified: %s (valid: %s)', part, valid_parts)
            msg = f'Invalid part: {part}. Must be one of: {", ".join(sorted(valid_parts))}'
            raise ValueError(msg)

        self._logger.debug('Validation passed: node exists and part is valid')

        # Editor Launch Phase - Open file in external editor
        self._logger.debug('Opening %s part of node %s in editor', part, node_id)
        self._node_repo.open_in_editor(node_id, part)

        self._logger.info('Edit operation completed successfully for NodeId: %s, part: %s', node_id, part)


class MoveNode:
    """Use case interactor for moving nodes within the binder hierarchy.

    Orchestrates the movement of existing nodes by updating the binder
    structure while preserving node identity and files. Follows hexagonal
    architecture principles with pure business logic that delegates all I/O
    operations to injected port implementations.

    The node movement process:
    1. Validates source node exists in binder hierarchy
    2. Validates target parent exists when specified
    3. Checks for circular dependencies using ancestor traversal
    4. Removes node from current location in binder tree
    5. Adds node to new location at specified position
    6. Updates and saves binder changes to _binder.md
    7. Logs all operations with NodeId details for traceability

    Node files remain unchanged during move operations - only the binder
    hierarchy structure is modified.

    Args:
        binder_repo: Port for binder persistence operations
        logger: Port for operational logging and audit trails

    Examples:
        >>> # With dependency injection
        >>> interactor = MoveNode(
        ...     binder_repo=file_binder_repo,
        ...     logger=production_logger,
        ... )
        >>> interactor.execute(node_id=node_id, parent_id=new_parent_id, position=0)

    """

    def __init__(
        self,
        binder_repo: 'BinderRepo',
        logger: 'Logger',
    ) -> None:
        """Initialize MoveNode with injected dependencies.

        Args:
            binder_repo: Port for binder persistence operations
            logger: Port for operational logging and audit trails

        """
        self._binder_repo = binder_repo
        self._logger = logger

    def execute(
        self,
        node_id: NodeId,
        parent_id: NodeId | None,
        position: int | None,
    ) -> None:
        """Execute node movement workflow.

        Moves the specified node to a new location in the binder hierarchy.
        The node is moved to the root level if no parent is specified, or
        under the specified parent node at the given position.

        Args:
            node_id: NodeId of the node to move
            parent_id: Optional target parent NodeId (None = move to root)
            position: Optional position for insertion order (None = append)

        Raises:
            NodeNotFoundError: If node_id or parent_id doesn't exist in binder
            BinderIntegrityError: If move would create circular dependency
            FileSystemError: If binder file cannot be saved (propagated from ports)

        """
        self._logger.info(
            'Starting move node operation for NodeId: %s to parent: %s position: %s',
            node_id,
            parent_id,
            position,
        )

        # Load and validate binder structure
        binder = self._binder_repo.load()
        self._logger.debug('Validating source and target nodes')

        # Validate source node exists
        source_item = binder.find_by_id(node_id)
        if source_item is None:
            self._logger.error('Source node not found in binder: %s', node_id)
            msg = 'Source node not found in binder'
            raise NodeNotFoundError(msg, str(node_id))

        # Validate target parent exists (if specified)
        if parent_id is not None:
            target_parent = binder.find_by_id(parent_id)
            if target_parent is None:
                self._logger.error('Target parent not found in binder: %s', parent_id)
                msg = 'Target parent not found in binder'
                raise NodeNotFoundError(msg, str(parent_id))

        # Check for circular dependencies
        self._logger.debug('Checking for circular dependencies')
        if MoveNode._would_create_circular_dependency(binder, node_id, parent_id):
            self._logger.error(
                'Circular dependency detected: cannot move %s under %s',
                node_id,
                parent_id,
            )
            msg = 'Move would create circular dependency'
            raise BinderIntegrityError(
                msg,
                str(node_id),
                str(parent_id),
            )

        # Perform the move operation
        self._remove_node_from_current_location(binder, source_item)
        self._add_node_to_new_location(binder, source_item, parent_id, position)

        # Save updated binder
        self._binder_repo.save(binder)

        self._logger.info('Move node operation completed successfully for NodeId: %s', node_id)

    @staticmethod
    def _would_create_circular_dependency(
        binder: Binder,
        node_id: NodeId,
        parent_id: NodeId | None,
    ) -> bool:
        """Check if moving node under parent would create circular dependency.

        Uses ancestor traversal approach: walks up from target parent to see
        if the source node is an ancestor.

        Args:
            binder: Binder instance to check
            node_id: NodeId of node being moved
            parent_id: Target parent NodeId (None means root level)

        Returns:
            True if move would create circular dependency, False otherwise

        """
        # Moving to root level cannot create circular dependency
        if parent_id is None:
            return False

        # Check if source node is an ancestor of target parent
        return MoveNode._is_ancestor(binder, node_id, parent_id)

    @staticmethod
    def _is_ancestor(binder: Binder, potential_ancestor_id: NodeId, descendant_id: NodeId) -> bool:
        """Check if potential_ancestor_id is an ancestor of descendant_id.

        Traverses up the tree from descendant to see if potential_ancestor
        is found in the ancestry chain.

        Args:
            binder: Binder instance to traverse
            potential_ancestor_id: NodeId that might be an ancestor
            descendant_id: NodeId to check ancestry for

        Returns:
            True if potential_ancestor_id is an ancestor of descendant_id

        """
        current_id: NodeId | None = descendant_id

        while current_id is not None:
            # Find parent of current node
            parent_item = MoveNode._find_parent_of_node(binder, current_id)

            if parent_item is None:
                # Reached root level, no more ancestors
                return False

            if parent_item.id == potential_ancestor_id:
                # Found the potential ancestor in ancestry chain
                return True

            # Continue up the tree
            current_id = parent_item.id

        return False  # pragma: no cover

    @staticmethod
    def _find_parent_of_node(binder: Binder, node_id: NodeId) -> BinderItem | None:
        """Find the parent BinderItem of the specified node.

        Args:
            binder: Binder instance to search
            node_id: NodeId to find parent for

        Returns:
            Parent BinderItem or None if node is at root level

        """

        def _search_for_parent(item: BinderItem) -> BinderItem | None:
            """Recursively search for parent of node_id."""
            # Check if any direct child matches the target node_id
            for child in item.children:
                if child.id == node_id:
                    return item

            # Recursively search in children
            for child in item.children:
                result = _search_for_parent(child)
                if result is not None:
                    return result

            return None

        # Search through all root items
        for root_item in binder.roots:
            if root_item.id == node_id:
                # Node is at root level, no parent
                return None

            result = _search_for_parent(root_item)
            if result is not None:
                return result

        return None  # pragma: no cover

    def _remove_node_from_current_location(self, binder: Binder, source_item: BinderItem) -> None:
        """Remove the source node from its current location in the binder.

        Args:
            binder: Binder instance to modify
            source_item: BinderItem to remove

        """
        self._logger.debug('Removing node from current location: %s', source_item.id)

        # Source item must have a valid NodeId to be moved
        if source_item.id is None:
            msg = 'Cannot remove item without NodeId'
            raise BinderIntegrityError(msg, source_item)

        # Find parent and remove from its children list
        parent_item = MoveNode._find_parent_of_node(binder, source_item.id)

        if parent_item is None:
            # Node is at root level
            binder.roots.remove(source_item)
        else:
            # Node is under a parent
            parent_item.children.remove(source_item)

    def _add_node_to_new_location(
        self,
        binder: Binder,
        source_item: BinderItem,
        parent_id: NodeId | None,
        position: int | None,
    ) -> None:
        """Add the source node to its new location in the binder.

        Args:
            binder: Binder instance to modify
            source_item: BinderItem to add
            parent_id: Target parent NodeId (None = root level)
            position: Position for insertion (None = append, out-of-bounds = append)

        """
        self._logger.debug('Adding node to new location: %s under parent: %s', source_item.id, parent_id)

        if parent_id is None:
            # Add to root level
            target_list = binder.roots
        else:
            # Add under specified parent
            parent_item = binder.find_by_id(parent_id)
            if parent_item is None:
                msg = 'Parent item not found'
                raise NodeNotFoundError(msg, parent_id)
            target_list = parent_item.children

        # Insert at specified position or append
        if position is None or position >= len(target_list):
            target_list.append(source_item)
        else:
            # Ensure position is not negative (treat as 0)
            position = max(0, position)
            target_list.insert(position, source_item)


class RemoveNode:
    """Use case interactor for removing nodes from the binder structure.

    Orchestrates the removal of nodes by updating the binder hierarchy while
    optionally deleting associated files. Follows hexagonal architecture
    principles with pure business logic that delegates all I/O operations
    to injected port implementations.

    The node removal process:
    1. Validates node exists in binder hierarchy
    2. Handles child nodes by promoting them to removed node's parent level
    3. Removes node from binder structure (from parent or root level)
    4. Optionally deletes node files using NodeRepo when delete_files=True
    5. Updates and saves binder changes to _binder.md
    6. Logs removal operations with NodeId and file deletion status
    7. Preserves binder integrity after node removal

    Child nodes are promoted to maintain hierarchy consistency - when a parent
    node is removed, its children are moved to the grandparent level rather
    than being orphaned or automatically removed.

    Args:
        binder_repo: Port for binder persistence operations
        node_repo: Port for node file deletion when delete_files=True
        logger: Port for operational logging and audit trails

    Examples:
        >>> # With dependency injection
        >>> interactor = RemoveNode(
        ...     binder_repo=file_binder_repo,
        ...     node_repo=file_node_repo,
        ...     logger=production_logger,
        ... )
        >>> interactor.execute(node_id=node_id, delete_files=False)

    """

    def __init__(
        self,
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        logger: 'Logger',
    ) -> None:
        """Initialize RemoveNode with injected dependencies.

        Args:
            binder_repo: Port for binder persistence operations
            node_repo: Port for node file deletion when delete_files=True
            logger: Port for operational logging and audit trails

        """
        self._binder_repo = binder_repo
        self._node_repo = node_repo
        self._logger = logger

    def execute(self, node_id: NodeId, *, delete_files: bool = False) -> None:
        """Execute node removal workflow.

        Removes the specified node from the binder hierarchy and optionally
        deletes the associated files. Child nodes are promoted to the parent
        level to maintain hierarchy consistency.

        Args:
            node_id: NodeId of the node to remove
            delete_files: If True, delete {id}.md and {id}.notes.md files

        Raises:
            NodeNotFoundError: If node_id doesn't exist in binder
            FileSystemError: If binder or node files cannot be updated

        """
        self._logger.info(
            'Starting node removal for NodeId: %s with delete_files=%s',
            node_id,
            delete_files,
        )

        # Load and validate binder structure
        binder = self._binder_repo.load()
        self._logger.debug('Validating node exists in binder')

        # Validate node exists
        target_item = binder.find_by_id(node_id)
        if target_item is None:
            self._logger.error('Node not found in binder: %s', node_id)
            msg = 'Node not found in binder'
            raise NodeNotFoundError(msg, str(node_id))

        # Find parent for child promotion logic
        parent_item = RemoveNode._find_parent_of_node(binder, node_id)

        # Promote children before removing node
        if target_item.children:
            self._logger.debug(
                'Promoting %d children of node %s to parent level',
                len(target_item.children),
                node_id,
            )
            self._promote_children_to_parent_level(binder, target_item, parent_item)

        # Remove node from binder structure
        self._remove_node_from_binder(binder, target_item, parent_item)

        # Delete files if requested
        if delete_files:
            self._logger.debug('Deleting node files for NodeId: %s', node_id)
            self._node_repo.delete(node_id, delete_files=True)

        # Save updated binder
        self._binder_repo.save(binder)

        self._logger.info(
            'Node removal completed successfully for NodeId: %s (files deleted: %s)',
            node_id,
            delete_files,
        )

    @staticmethod
    def _find_parent_of_node(binder: Binder, node_id: NodeId) -> BinderItem | None:
        """Find the parent BinderItem of the specified node.

        Args:
            binder: Binder instance to search
            node_id: NodeId to find parent for

        Returns:
            Parent BinderItem or None if node is at root level

        """

        def _search_for_parent(item: BinderItem) -> BinderItem | None:
            """Recursively search for parent of node_id."""
            # Check if any direct child matches the target node_id
            for child in item.children:
                if child.id == node_id:
                    return item

            # Recursively search in children
            for child in item.children:
                result = _search_for_parent(child)
                if result is not None:
                    return result

            return None

        # Search through all root items
        for root_item in binder.roots:
            if root_item.id == node_id:
                # Node is at root level, no parent
                return None

            result = _search_for_parent(root_item)
            if result is not None:
                return result

        return None  # pragma: no cover

    def _promote_children_to_parent_level(
        self,
        binder: Binder,
        target_item: BinderItem,
        parent_item: BinderItem | None,
    ) -> None:
        """Promote children of target node to parent level.

        Args:
            binder: Binder instance to modify
            target_item: BinderItem being removed
            parent_item: Parent of target item (None if at root level)

        """
        self._logger.debug('Preparing to promote children')
        children_to_promote = target_item.children.copy()
        self._logger.debug('Promoting %d children of %s', len(children_to_promote), target_item.id)

        if parent_item is None:
            # Target is at root level, promote children to root
            target_index = binder.roots.index(target_item)
            # Insert children at the target's position
            for i, child in enumerate(children_to_promote):
                binder.roots.insert(target_index + i, child)
        else:
            # Target is under a parent, promote children to parent level
            target_index = parent_item.children.index(target_item)
            # Insert children at the target's position under parent
            for i, child in enumerate(children_to_promote):
                parent_item.children.insert(target_index + i, child)

    def _remove_node_from_binder(
        self,
        binder: Binder,
        target_item: BinderItem,
        parent_item: BinderItem | None,
    ) -> None:
        """Remove the target node from the binder structure.

        Args:
            binder: Binder instance to modify
            target_item: BinderItem to remove
            parent_item: Parent of target item (None if at root level)

        """
        self._logger.debug('Removing node from binder structure: %s', target_item.id)

        if parent_item is None:
            # Node is at root level
            binder.roots.remove(target_item)
        else:
            # Node is under a parent
            parent_item.children.remove(target_item)


class WriteFreeform:
    """Use case interactor for creating timestamped freewrite files.

    Creates standalone markdown files with optional titles and UUIDv7 identifiers
    outside the binder structure for frictionless writing. This interactor supports
    spontaneous idea capture without structural constraints and can launch the
    created file in the user's preferred editor.

    The freewrite creation process:
    1. Generates a unique timestamped filename with UUIDv7 identifier
    2. Creates the file with optional title in YAML frontmatter
    3. Opens the file in external editor for immediate writing
    4. Logs the operation for reference and session tracking
    5. Returns the filename for confirmation or further operations

    Args:
        daily_repo: Port for freewrite file creation and management
        editor_port: Port for launching external editor
        logger: Port for operational logging and audit trails
        clock: Port for timestamp generation

    Examples:
        >>> # With dependency injection
        >>> interactor = WriteFreeform(
        ...     daily_repo=filesystem_daily_repo,
        ...     editor_port=system_editor_port,
        ...     logger=production_logger,
        ...     clock=system_clock,
        ... )
        >>> filename = interactor.execute(title='Morning Thoughts')
        >>> print(filename)
        "20250911T0830_01932c5a-7f3e-7000-8000-000000000001.md"

    """

    def __init__(
        self,
        daily_repo: 'DailyRepo',
        editor_port: 'EditorPort',
        logger: 'Logger',
        clock: 'Clock',
    ) -> None:
        """Initialize WriteFreeform with injected dependencies.

        Args:
            daily_repo: Port for freewrite file creation and management
            editor_port: Port for launching external editor
            logger: Port for operational logging and audit trails
            clock: Port for timestamp generation

        """
        self._daily_repo = daily_repo
        self._editor_port = editor_port
        self._logger = logger
        self._clock = clock

    def execute(self, title: str | None = None) -> str:
        """Execute freewrite creation workflow.

        Creates a new timestamped freewrite file with optional title,
        opens it in the external editor, and returns the filename for
        confirmation. Handles editor launch failures gracefully.

        Args:
            title: Optional title to include in the file's frontmatter.
                   If provided, will be added as a 'title' field in the
                   YAML frontmatter block.

        Returns:
            The filename of the created freewrite file, following the
            format YYYYMMDDTHHMM_<uuid7>.md

        Raises:
            FileSystemError: If the file cannot be created due to I/O
                           errors, permission issues, or disk space
                           constraints (propagated from DailyRepo).

        """
        # Log start of freewrite creation
        if title:
            self._logger.info('Starting freewrite creation with title: %s', title)
        else:
            self._logger.info('Starting freewrite creation without title')

        try:
            # Create the freewrite file
            filename = self._daily_repo.write_freeform(title=title)
            self._logger.info('Created freewrite file: %s', filename)

            # Attempt to open in editor
            try:
                self._editor_port.open(filename)
                self._logger.debug('Opened freewrite file in editor: %s', filename)
            except EditorLaunchError as exc:
                # Editor failure shouldn't prevent the freewrite from being created
                self._logger.warning('Failed to open freewrite file in editor: %s (file still created)', str(exc))
                return filename
            else:
                return filename

        except FileSystemError:
            self._logger.exception('Failed to create freewrite file')
            raise  # Re-raise filesystem errors as they're critical


class ShowStructure:
    """Use case interactor for displaying the hierarchical structure of the binder.

    Provides a read-only view of the binder hierarchy, supporting both full
    structure display and subtree filtering. Formats the tree structure using
    ASCII art for console display with proper indentation and tree characters.

    The structure display process:
    1. Loads the current binder structure from storage
    2. Validates subtree root node exists when node_id is specified
    3. Filters to subtree or shows full structure based on parameters
    4. Formats the hierarchy using tree drawing characters (├─, └─, │)
    5. Shows placeholders with distinctive visual markers
    6. Returns formatted string representation for console output
    7. Logs operation details for traceability and debugging

    Placeholders (items without NodeId) are displayed with [Placeholder]
    markers to distinguish them from actual nodes. The formatter uses
    standard tree drawing characters for clear hierarchy visualization.

    Args:
        binder_repo: Port for binder persistence operations
        logger: Port for operational logging and audit trails

    Examples:
        >>> # With dependency injection
        >>> interactor = ShowStructure(
        ...     binder_repo=file_binder_repo,
        ...     logger=production_logger,
        ... )
        >>> # Display full structure
        >>> structure = interactor.execute()
        >>> print(structure)
        ├─ Part 1
        │  ├─ Chapter 1
        │  │  └─ Section 1.1
        │  └─ Chapter 2
        └─ Part 2
        >>>
        >>> # Display subtree from specific node
        >>> subtree = interactor.execute(node_id=part1_id)
        >>> print(subtree)
        Part 1
        ├─ Chapter 1
        │  └─ Section 1.1
        └─ Chapter 2

    """

    def __init__(
        self,
        binder_repo: 'BinderRepo',
        logger: 'Logger',
    ) -> None:
        """Initialize ShowStructure with injected dependencies.

        Args:
            binder_repo: Port for binder persistence operations
            logger: Port for operational logging and audit trails

        """
        self._binder_repo = binder_repo
        self._logger = logger

    def execute(self, node_id: NodeId | None = None) -> str:
        """Execute structure display workflow.

        Displays the binder hierarchy as a formatted tree structure.
        When node_id is provided, shows only the subtree starting from
        that node. When node_id is None, shows the complete binder structure.

        Args:
            node_id: Optional NodeId for subtree display (None = full structure)

        Returns:
            Formatted string representation of the tree structure using
            ASCII art characters for hierarchy visualization

        Raises:
            NodeNotFoundError: If node_id is specified but doesn't exist in binder
            FileSystemError: If binder cannot be loaded (propagated from ports)

        """
        if node_id is None:
            self._logger.info('Displaying full binder structure')
        else:
            self._logger.info('Displaying subtree structure for NodeId: %s', node_id)

        # Load binder structure
        binder = self._binder_repo.load()

        if node_id is None:
            # Display full structure
            return self._format_full_structure(binder)
        # Display subtree
        return self._format_subtree_structure(binder, node_id)

    def _format_full_structure(self, binder: Binder) -> str:
        """Format the complete binder structure.

        Args:
            binder: Binder instance to format

        Returns:
            Formatted string representation of full structure

        """
        if not binder.roots:
            self._logger.debug('Binder is empty')
            return 'Binder is empty - no nodes to display'

        total_items = self._count_all_items(binder.roots)
        placeholder_count = self._count_placeholders(binder.roots)

        self._logger.debug('Found %d total items in binder', total_items)
        if placeholder_count > 0:
            self._logger.debug('Found %d placeholders in structure', placeholder_count)

        # If there are multiple root items, they should have tree connectors
        if len(binder.roots) > 1:
            result = self._format_items_with_root_connectors(binder.roots)
        else:
            result = self._format_items(binder.roots, prefix='')

        self._logger.info('Structure display completed successfully')
        return result

    def _format_subtree_structure(self, binder: Binder, node_id: NodeId) -> str:
        """Format subtree structure starting from specified node.

        Args:
            binder: Binder instance to search
            node_id: NodeId of subtree root

        Returns:
            Formatted string representation of subtree

        Raises:
            NodeNotFoundError: If node_id doesn't exist in binder

        """
        # Find the target node in binder structure
        target_item = binder.find_by_id(node_id)
        if target_item is None:
            self._logger.error('Node not found for subtree display: %s', node_id)
            msg = 'Node not found for subtree display'
            raise NodeNotFoundError(msg, str(node_id))

        self._logger.debug('Found subtree root: %s', target_item.display_title)

        # Format the subtree starting from the target node
        result = self._format_single_item(
            target_item,
            prefix='',
            is_last=True,
            show_children=True,
            force_connector=False,
        )

        self._logger.info('Structure display completed successfully')
        return result

    def _format_items(self, items: list[BinderItem], prefix: str) -> str:
        """Format a list of BinderItems with tree structure.

        Args:
            items: List of BinderItems to format
            prefix: Current indentation prefix
            is_last_group: Whether this is the last group of siblings

        Returns:
            Formatted string representation

        """
        if not items:
            return ''

        lines = []
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            line = self._format_single_item(item, prefix, is_last=is_last, show_children=True, force_connector=False)
            lines.append(line)

        return '\n'.join(lines)

    def _format_items_with_root_connectors(self, items: list[BinderItem]) -> str:
        """Format root items with tree connectors.

        Args:
            items: List of root BinderItems to format

        Returns:
            Formatted string representation with root connectors

        """
        if not items:
            return ''

        lines = []
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            # Force connector even at root level
            line = self._format_single_item(item, prefix='', is_last=is_last, show_children=True, force_connector=True)
            lines.append(line)

        return '\n'.join(lines)

    def _format_single_item(
        self,
        item: BinderItem,
        prefix: str,
        *,
        is_last: bool,
        show_children: bool = True,
        force_connector: bool = False,
    ) -> str:
        """Format a single BinderItem with proper tree characters.

        Args:
            item: BinderItem to format
            prefix: Current indentation prefix
            is_last: Whether this is the last sibling
            show_children: Whether to recursively show children
            force_connector: Whether to force tree connector even at root level

        Returns:
            Formatted string representation of item and its children

        """
        # Choose tree connector
        connector = '' if not prefix and not force_connector else '└─ ' if is_last else '├─ '

        # Format display title with node ID in parentheses
        display_title = item.display_title
        display_title = f'{display_title} ({item.id})' if item.id is not None else f'{display_title} [Placeholder]'

        # Create the line for this item
        line = f'{prefix}{connector}{display_title}'

        if not show_children or not item.children:
            return line

        # Format children with appropriate prefix
        lines = [line]
        child_prefix = prefix + ('   ' if is_last else '│  ')

        for i, child in enumerate(item.children):
            child_is_last = i == len(item.children) - 1
            child_line = self._format_single_item(
                child,
                child_prefix,
                is_last=child_is_last,
                show_children=True,
                force_connector=False,
            )
            lines.append(child_line)

        return '\n'.join(lines)

    def _count_all_items(self, items: list[BinderItem]) -> int:
        """Count total number of items in tree structure.

        Args:
            items: Root list of BinderItems

        Returns:
            Total count of all items including nested children

        """
        count = len(items)
        for item in items:
            count += self._count_all_items(item.children)
        return count

    def _count_placeholders(self, items: list[BinderItem]) -> int:
        """Count placeholder items (items without NodeId) in tree structure.

        Args:
            items: Root list of BinderItems

        Returns:
            Count of placeholder items including nested children

        """
        count = sum(1 for item in items if item.id is None)
        for item in items:
            count += self._count_placeholders(item.children)
        return count


class MaterializeNode:  # pragma: no cover
    """Use case interactor for converting binder placeholders into actual nodes.

    Orchestrates the materialization of placeholder items by generating unique
    identifiers, creating node files, and updating the binder structure.
    Follows hexagonal architecture principles with pure business logic that
    delegates all I/O operations to injected port implementations.

    The materialization process:
    1. Locates placeholder by display title in binder structure
    2. Validates that the item is indeed a placeholder (has None id)
    3. Generates unique NodeId for the new node
    4. Creates node files with proper frontmatter and content
    5. Updates binder structure replacing placeholder with node reference
    6. Saves updated binder to persistent storage
    7. Logs all operations for audit trail

    Args:
        binder_repo: Port for binder persistence operations
        node_repo: Port for node file creation and management
        id_generator: Port for generating unique NodeId values
        logger: Port for operational logging and audit trails

    Examples:
        >>> # With dependency injection
        >>> interactor = MaterializeNode(
        ...     binder_repo=file_binder_repo,
        ...     node_repo=file_node_repo,
        ...     id_generator=uuid_generator,
        ...     logger=production_logger,
        ... )
        >>> node_id = interactor.execute(display_title='Chapter One', synopsis='The beginning')

    """

    def __init__(
        self,
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        id_generator: 'IdGenerator',
        logger: 'Logger',
    ) -> None:
        """Initialize MaterializeNode with injected dependencies.

        Args:
            binder_repo: Port for binder persistence operations
            node_repo: Port for node file creation and management
            id_generator: Port for generating unique NodeId values
            logger: Port for operational logging and audit trails

        """
        self._binder_repo = binder_repo
        self._node_repo = node_repo
        self._id_generator = id_generator
        self._logger = logger

    def execute(self, display_title: str, synopsis: str | None) -> NodeId:
        """Execute placeholder materialization workflow.

        Converts a binder placeholder with the specified display title into
        a concrete node with files and proper binder structure integration.

        Args:
            display_title: Display title of the placeholder to materialize
            synopsis: Optional synopsis/summary for the new node

        Returns:
            NodeId of the materialized node

        Raises:
            PlaceholderNotFoundError: If no placeholder with display_title exists
            AlreadyMaterializedError: If item with display_title already has NodeId
            BinderIntegrityError: If binder integrity is violated after materialization
            FileSystemError: If node files cannot be created (propagated from ports)

        """
        self._logger.info('Starting placeholder materialization for display_title=%s', display_title)

        # Discovery Phase - Find the placeholder in binder structure
        binder = self._binder_repo.load()
        placeholder = binder.find_placeholder_by_display_title(display_title)

        if placeholder is None:
            # Check if an item with this title already exists but is materialized
            for root_item in binder.roots:
                existing_item = self._find_item_by_title_recursive(root_item, display_title)
                if existing_item is not None and existing_item.id is not None:
                    self._logger.error('Item with display_title already materialized: %s', display_title)
                    msg = 'Item already materialized'
                    raise AlreadyMaterializedError(msg, display_title, str(existing_item.id))

            # No item found at all
            self._logger.error('Placeholder not found with display_title: %s', display_title)
            msg = 'Placeholder not found'
            raise PlaceholderNotFoundError(msg, display_title)

        # Validation Phase - Ensure it's actually a placeholder
        if placeholder.id is not None:  # pragma: no cover
            # This should never happen as find_placeholder_by_display_title only returns items with id=None
            self._logger.error('Item with display_title already materialized: %s', display_title)  # pragma: no cover
            msg = 'Item already materialized'
            raise AlreadyMaterializedError(
                msg,
                display_title,
                str(placeholder.id),
            )  # pragma: no cover

        # Generation Phase - Create unique identity
        node_id = self._id_generator.new()
        self._logger.debug('Generated new NodeId for materialization: %s', node_id)

        # Creation Phase - Set up node files with proper metadata
        self._node_repo.create(node_id, display_title, synopsis)
        self._logger.debug('Created node files for materialized NodeId: %s', node_id)

        # Materialization Phase - Update placeholder to reference actual node
        placeholder.node_id = node_id
        self._binder_repo.save(binder)
        self._logger.debug('Updated binder with materialized node: %s', node_id)

        # Completion
        self._logger.info('Placeholder materialization completed successfully for NodeId: %s', node_id)
        return node_id

    def _find_item_by_title_recursive(self, item: BinderItem, target_title: str) -> BinderItem | None:
        """Recursively search for any item (placeholder or materialized) by display title.

        Args:
            item: Current item to check
            target_title: Title to search for

        Returns:
            The BinderItem with matching display title, or None if not found

        """
        if item.display_title == target_title:
            return item

        for child in item.children:
            result = self._find_item_by_title_recursive(child, target_title)
            if result is not None:  # pragma: no branch
                return result

        return None


class AuditBinder:
    """Use case interactor for auditing binder consistency and integrity.

    Provides comprehensive validation of binder integrity by detecting four
    types of issues: PLACEHOLDER (no ID), MISSING (referenced but file doesn't
    exist), ORPHAN (file exists but not in binder), and MISMATCH (frontmatter
    ID ≠ filename). Follows hexagonal architecture principles with pure business
    logic that delegates all I/O operations to injected port implementations.

    The audit process:
    1. Loads binder structure from BinderRepo
    2. Scans project directory for existing node files via NodeRepo
    3. Cross-references binder items with file system state
    4. Validates frontmatter IDs match filenames for existing files
    5. Categorizes and reports all discovered issues by type
    6. Returns structured audit report with human-readable and JSON formats

    Issue Types and Detection Logic:
    - PLACEHOLDER: BinderItem.id is None (has display title but no NodeId)
    - MISSING: Binder references NodeId but corresponding file doesn't exist
    - ORPHAN: Node file exists but NodeId not found in binder structure
    - MISMATCH: File exists but frontmatter.id ≠ filename NodeId

    Args:
        binder_repo: Port for binder persistence operations
        node_repo: Port for node file scanning and validation
        logger: Port for operational logging and audit trails

    Examples:
        >>> # With dependency injection
        >>> interactor = AuditBinder(
        ...     binder_repo=file_binder_repo,
        ...     node_repo=file_node_repo,
        ...     logger=production_logger,
        ... )
        >>> report = interactor.execute()
        >>> if report.is_clean():
        ...     print('✓ No issues found')
        >>> else:
        ...     print(report.format_report())

    """

    def __init__(
        self,
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        logger: 'Logger',
    ) -> None:
        """Initialize AuditBinder with injected dependencies.

        Args:
            binder_repo: Port for binder persistence operations
            node_repo: Port for node file scanning and validation
            logger: Port for operational logging and audit trails

        """
        self._binder_repo = binder_repo
        self._node_repo = node_repo
        self._logger = logger

    def execute(self) -> AuditReport:
        """Execute binder audit workflow.

        Performs comprehensive audit of binder consistency by scanning the
        binder structure and cross-referencing with the file system state.
        Detects and categorizes all integrity issues.

        Returns:
            AuditReport containing all discovered issues organized by type

        Raises:
            BinderNotFoundError: If binder file doesn't exist
            FileSystemError: If files cannot be read (propagated from ports)

        """
        self._logger.info('Starting binder audit')

        # Load binder structure
        binder = self._binder_repo.load()
        self._logger.debug('Loaded binder structure with %d root items', len(binder.roots))

        # Initialize report
        report = AuditReport()

        # Scan for placeholders
        self._scan_placeholders(binder, report)

        # Get all node IDs referenced in binder
        binder_node_ids = binder.get_all_node_ids()
        self._logger.debug('Found %d node IDs in binder', len(binder_node_ids))

        # Get all existing node files from file system
        existing_files = self._get_existing_node_files()
        self._logger.debug('Found %d existing node files', len(existing_files))

        # Cross-reference binder with file system
        self._scan_missing_files(binder_node_ids, existing_files, report)
        self._scan_missing_notes_files(binder_node_ids, report)
        self._scan_orphaned_files(binder_node_ids, existing_files, report)
        self._scan_orphaned_invalid_files(binder_node_ids, report)
        self._scan_id_mismatches(existing_files, report)

        # Log summary
        total_issues = len(report.placeholders) + len(report.missing) + len(report.orphans) + len(report.mismatches)
        self._logger.info('Binder audit completed: %d issues found', total_issues)

        return report

    def _scan_placeholders(self, binder: Binder, report: AuditReport) -> None:
        """Scan binder structure for placeholder items.

        Args:
            binder: Binder instance to scan
            report: AuditReport to populate with findings

        """
        self._logger.debug('Scanning for placeholder items')

        def _scan_item_recursive(item: BinderItem, path: list[int]) -> None:
            """Recursively scan items and record placeholders."""
            if item.id is None:
                position = '[' + ']['.join(map(str, path)) + ']'
                placeholder_issue = PlaceholderIssue(
                    display_title=item.display_title,
                    position=position,
                )
                report.placeholders.append(placeholder_issue)
                self._logger.debug(
                    'Found placeholder: "%s" at position %s',
                    item.display_title,
                    position,
                )

            # Scan children
            for i, child in enumerate(item.children):
                child_path = [*path, i]
                _scan_item_recursive(child, child_path)

        # Scan all root items
        for i, root_item in enumerate(binder.roots):
            _scan_item_recursive(root_item, [i])

        self._logger.debug('Found %d placeholder items', len(report.placeholders))

    def _get_existing_node_files(self) -> set[NodeId]:
        """Get all existing node files from the file system.

        Returns:
            Set of NodeIds for files that exist on disk

        """
        return self._node_repo.get_existing_files()

    def _scan_missing_files(
        self,
        binder_node_ids: set[NodeId],
        existing_files: set[NodeId],
        report: AuditReport,
    ) -> None:
        """Scan for node IDs referenced in binder but missing from file system.

        Args:
            binder_node_ids: Set of NodeIds referenced in binder
            existing_files: Set of NodeIds that exist as files
            report: AuditReport to populate with findings

        """
        self._logger.debug('Scanning for missing files')

        missing_ids = binder_node_ids - existing_files
        for node_id in missing_ids:
            missing_issue = MissingIssue(
                node_id=node_id,
                expected_path=f'{node_id}.md',
            )
            report.missing.append(missing_issue)
            self._logger.debug('Found missing file: %s.md', node_id)

        self._logger.debug('Found %d missing files', len(report.missing))

    def _scan_missing_notes_files(
        self,
        binder_node_ids: set[NodeId],
        report: AuditReport,
    ) -> None:
        """Scan for node IDs that are missing their .notes.md files.

        Args:
            binder_node_ids: Set of NodeIds referenced in binder
            report: AuditReport to populate with findings

        """
        self._logger.debug('Scanning for missing notes files')

        for node_id in binder_node_ids:
            if not self._node_repo.file_exists(node_id, 'notes'):
                missing_issue = MissingIssue(
                    node_id=node_id,
                    expected_path=f'{node_id}.notes.md',
                )
                report.missing.append(missing_issue)
                self._logger.debug('Found missing notes file: %s.notes.md', node_id)

        notes_missing_count = sum(1 for m in report.missing if m.expected_path.endswith('.notes.md'))
        self._logger.debug('Found %d missing notes files', notes_missing_count)

    def _scan_orphaned_files(
        self,
        binder_node_ids: set[NodeId],
        existing_files: set[NodeId],
        report: AuditReport,
    ) -> None:
        """Scan for files that exist but aren't referenced in binder.

        Args:
            binder_node_ids: Set of NodeIds referenced in binder
            existing_files: Set of NodeIds that exist as files
            report: AuditReport to populate with findings

        """
        self._logger.debug('Scanning for orphaned files')

        orphaned_ids = existing_files - binder_node_ids
        for node_id in orphaned_ids:
            orphan_issue = OrphanIssue(
                node_id=node_id,
                file_path=f'{node_id}.md',
            )
            report.orphans.append(orphan_issue)
            self._logger.debug('Found orphaned file: %s.md', node_id)

        self._logger.debug('Found %d orphaned files', len(report.orphans))

    def _scan_orphaned_invalid_files(
        self,
        _binder_node_ids: set[NodeId],
        report: AuditReport,
    ) -> None:
        """Scan for files that look like node files but have invalid NodeIds.

        Args:
            _binder_node_ids: Set of NodeIds referenced in binder (currently unused)
            report: AuditReport to populate with findings

        """
        self._logger.debug('Scanning for orphaned files with invalid NodeIds')

        # Get all potential node files, including those with invalid NodeIds
        try:
            # Scan project directory for .md files that look like node files
            project_path = getattr(self._node_repo, 'project_path', None)
            if project_path is None:
                # For fake implementations, we can't scan the filesystem
                return

            from pathlib import Path

            project_path = Path(project_path)

            for md_file in project_path.glob('*.md'):
                # Skip system files
                if md_file.stem.startswith('_'):
                    continue

                # Skip .notes.md files
                if md_file.stem.endswith('.notes'):
                    continue

                # Skip freeform files (pattern: YYYYMMDDTHHMM_<uuid>.md)
                import re

                if re.match(r'^\d{8}T\d{4}_[0-9a-f-]+$', md_file.stem):
                    continue  # pragma: no cover

                # Try to create a NodeId from the filename
                try:
                    NodeId(md_file.stem)
                    # If successful, this is handled by regular orphan scanning
                    continue
                except NodeIdentityError:
                    # This file has an invalid NodeId but looks like a node file
                    pass

                # Check if this file might be a node file based on content
                try:
                    content = md_file.read_text()
                    if content.startswith('---') and '\nid:' in content:
                        # This looks like a node file with frontmatter
                        # Create a dummy NodeId for reporting purposes
                        dummy_node_id = NodeId('00000000-0000-7000-8000-000000000000')  # UUIDv7 format
                        orphan_issue = OrphanIssue(
                            node_id=dummy_node_id,
                            file_path=md_file.name,
                        )
                        report.orphans.append(orphan_issue)
                        self._logger.debug('Found orphaned file with invalid NodeId: %s', md_file.name)
                except (OSError, UnicodeDecodeError):  # pragma: no cover
                    # Couldn't read the file or doesn't look like a node file
                    self._logger.debug('Could not read file %s, skipping', md_file.name)  # pragma: no cover
                    continue  # pragma: no cover

        except (OSError, AttributeError) as exc:  # pragma: no cover
            self._logger.warning('Could not scan for orphaned invalid files: %s', exc)  # pragma: no cover

        invalid_orphan_count = sum(1 for o in report.orphans if o.file_path != f'{o.node_id}.md')
        self._logger.debug('Found %d orphaned files with invalid NodeIds', invalid_orphan_count)

    def _scan_id_mismatches(self, existing_files: set[NodeId], report: AuditReport) -> None:
        """Scan for files where frontmatter ID doesn't match filename.

        Args:
            existing_files: Set of NodeIds that exist as files
            report: AuditReport to populate with findings

        """
        self._logger.debug('Scanning for ID mismatches')

        for node_id in existing_files:
            try:
                frontmatter = self._node_repo.read_frontmatter(node_id)
                frontmatter_id_str = frontmatter.get('id')

                if frontmatter_id_str and frontmatter_id_str != str(node_id):
                    try:
                        actual_id = NodeId(frontmatter_id_str)
                        mismatch_issue = MismatchIssue(
                            file_path=f'{node_id}.md',
                            expected_id=node_id,
                            actual_id=actual_id,
                        )
                        report.mismatches.append(mismatch_issue)
                        self._logger.debug(
                            'Found ID mismatch in %s.md: expected %s, found %s',
                            node_id,
                            node_id,
                            actual_id,
                        )
                    except NodeIdentityError as e:
                        # Handle invalid frontmatter IDs as mismatches
                        self._logger.debug('Found invalid frontmatter ID %s: %s', frontmatter_id_str, e)
                        # Create a dummy NodeId for reporting purposes
                        dummy_actual_id = NodeId('00000000-0000-7000-8000-000000000001')  # UUIDv7 format
                        mismatch_issue = MismatchIssue(
                            file_path=f'{node_id}.md (frontmatter id: {frontmatter_id_str})',
                            expected_id=node_id,
                            actual_id=dummy_actual_id,
                        )
                        report.mismatches.append(mismatch_issue)
                        self._logger.debug(
                            'Found ID mismatch in %s.md: expected %s, found invalid %s',
                            node_id,
                            node_id,
                            frontmatter_id_str,
                        )
            except (OSError, KeyError, NodeNotFoundError) as e:
                # Log and skip files that can't be read
                self._logger.debug('Could not read file for node %s: %s', node_id, e)
                continue

        self._logger.debug('Found %d ID mismatches', len(report.mismatches))
