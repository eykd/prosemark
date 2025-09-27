"""MaterializeNode use case for converting placeholders to actual nodes."""

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from prosemark.domain.models import BinderItem, NodeId
from prosemark.exceptions import PlaceholderNotFoundError

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.clock import Clock
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.id_generator import IdGenerator
    from prosemark.ports.logger import Logger
    from prosemark.ports.node_repo import NodeRepo


class MaterializeResult(NamedTuple):
    """Result of a materialization operation."""

    node_id: NodeId
    was_already_materialized: bool


class MaterializeNode:
    """Convert placeholder items in the binder to actual content nodes.

    Also creates missing notes files for already-materialized nodes.
    """

    def __init__(
        self,
        *,
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        id_generator: 'IdGenerator',
        clock: 'Clock',
        console: 'ConsolePort',
        logger: 'Logger',
    ) -> None:
        """Initialize the MaterializeNode use case.

        Args:
            binder_repo: Repository for binder operations.
            node_repo: Repository for node operations.
            id_generator: Generator for unique node IDs.
            clock: Clock for timestamps.
            console: Console output port.
            logger: Logger port.

        """
        self.binder_repo = binder_repo
        self.node_repo = node_repo
        self.id_generator = id_generator
        self.clock = clock
        self.console = console
        self.logger = logger

    def execute(
        self,
        *,
        title: str,
        project_path: Path | None = None,
    ) -> MaterializeResult:
        """Materialize a placeholder into a real node.

        If the placeholder is already materialized but is missing a notes file,
        this method will create the missing notes file with an obsidian-style link.

        Args:
            title: Title of the placeholder to materialize.
            project_path: Project directory path.

        Returns:
            MaterializeResult containing the node ID and whether it was already materialized.

        Raises:
            PlaceholderNotFoundError: If no placeholder with the given title is found.

        """
        project_path = project_path or Path.cwd()
        self.logger.info('Materializing placeholder: %s', title)

        # Load existing binder
        binder = self.binder_repo.load()

        # Find the item by title (placeholder or materialized)
        item = self._find_item_by_title(binder.roots, title)
        if not item:
            msg = f"Item '{title}' not found"
            raise PlaceholderNotFoundError(msg)

        # Check if already materialized
        if item.node_id:
            # Node is already materialized, but check if notes file is missing
            existing_node_id = item.node_id
            if not self.node_repo.file_exists(existing_node_id, 'notes'):
                self.logger.info('Creating missing notes file for: %s', existing_node_id.value)
                self.node_repo.create_notes_file(existing_node_id)
                self.console.print_success(f'Created missing notes file for "{title}" ({existing_node_id.value})')
                self.console.print_info(f'Created file: {existing_node_id.value}.notes.md')
            else:
                self.console.print_warning(f"'{title}' is already materialized")
            return MaterializeResult(existing_node_id, was_already_materialized=True)

        # Generate new node ID
        node_id = self.id_generator.new()

        # Create the node files
        self.node_repo.create(node_id, title, None)

        # Update the item with the node ID
        item.node_id = node_id

        # Save updated binder
        self.binder_repo.save(binder)

        self.console.print_success(f'Materialized "{title}" ({node_id.value})')
        self.console.print_info(f'Created files: {node_id.value}.md, {node_id.value}.notes.md')
        self.logger.info('Placeholder materialized: %s -> %s', title, node_id.value)

        return MaterializeResult(node_id, was_already_materialized=False)

    def _find_item_by_title(self, items: list[BinderItem], title: str) -> BinderItem | None:
        """Find an item by title in the hierarchy (placeholder or materialized).

        Args:
            items: List of binder items to search.
            title: Title to search for.

        Returns:
            The item if found, None otherwise.

        """
        for item in items:
            if item.display_title == title:
                return item
            found = self._find_item_by_title(item.children, title)
            if found:
                return found
        return None
