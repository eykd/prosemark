"""MaterializeNode use case for converting placeholders to actual nodes."""

from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import BinderItem, NodeId
from prosemark.exceptions import PlaceholderNotFoundError

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.clock import Clock
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.id_generator import IdGenerator
    from prosemark.ports.logger import Logger
    from prosemark.ports.node_repo import NodeRepo


class MaterializeNode:
    """Convert placeholder items in the binder to actual content nodes."""

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
    ) -> NodeId:
        """Materialize a placeholder into a real node.

        Args:
            title: Title of the placeholder to materialize.
            project_path: Project directory path.

        Returns:
            The ID of the newly created node.

        Raises:
            PlaceholderNotFoundError: If no placeholder with the given title is found.

        """
        project_path = project_path or Path.cwd()
        self.logger.info('Materializing placeholder: %s', title)

        # Load existing binder
        binder = self.binder_repo.load()

        # Find the placeholder item
        placeholder = self._find_placeholder(binder.roots, title)
        if not placeholder:
            msg = f"Placeholder '{title}' not found"
            raise PlaceholderNotFoundError(msg)

        # Check if already materialized
        if placeholder.node_id:  # pragma: no cover
            self.console.print_warning(f"'{title}' is already materialized")  # pragma: no cover
            return placeholder.node_id  # pragma: no cover

        # Generate new node ID
        node_id = self.id_generator.new()

        # Create the node files
        self.node_repo.create(node_id, title, None)

        # Update the placeholder with the node ID
        placeholder.node_id = node_id

        # Save updated binder
        self.binder_repo.save(binder)

        self.console.print_success(f'Materialized "{title}" ({node_id.value})')
        self.console.print_info(f'Created files: {node_id.value}.md, {node_id.value}.notes.md')
        self.logger.info('Placeholder materialized: %s -> %s', title, node_id.value)

        return node_id

    def _find_placeholder(self, items: list[BinderItem], title: str) -> BinderItem | None:
        """Find a placeholder item by title in the hierarchy.

        Args:
            items: List of binder items to search.
            title: Title to search for.

        Returns:
            The placeholder item if found, None otherwise.

        """
        for item in items:
            if item.display_title == title and not item.node_id:
                return item
            found = self._find_placeholder(item.children, title)
            if found:
                return found
        return None
