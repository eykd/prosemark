"""AddNode use case for adding content nodes to the binder."""

from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import BinderItem, NodeId

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.clock import Clock
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.id_generator import IdGenerator
    from prosemark.ports.logger import Logger
    from prosemark.ports.node_repo import NodeRepo


class AddNode:
    """Add a new content node to the binder hierarchy."""

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
        """Initialize the AddNode use case.

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
        parent_id: NodeId | None = None,
        position: int | None = None,
        project_path: Path | None = None,
    ) -> NodeId:
        """Add a new node to the binder.

        Args:
            title: Title for the new node.
            parent_id: Optional parent node ID for nested placement.
            position: Optional position within parent's children.
            project_path: Project directory path.

        Returns:
            The ID of the newly created node.

        """
        project_path = project_path or Path.cwd()
        self.logger.info('Adding node: %s', title)

        # Load existing binder
        binder = self.binder_repo.load()

        # Generate new node ID
        node_id = self.id_generator.new()

        # Create the node files
        self.node_repo.create(node_id, title, None)

        # Create binder item
        new_item = BinderItem(display_title=title, node_id=node_id, children=[])

        # Add to binder hierarchy
        if parent_id:
            # Find parent and add as child
            parent_item = self._find_item(binder.roots, parent_id)
            if not parent_item:
                self.console.print_error(f'Parent node {parent_id.value} not found')
                return node_id

            if position is not None and 0 <= position <= len(parent_item.children):
                parent_item.children.insert(position, new_item)
            else:
                parent_item.children.append(new_item)
        # Add as root item
        elif position is not None and 0 <= position <= len(binder.roots):
            binder.roots.insert(position, new_item)
        else:
            binder.roots.append(new_item)

        # Save updated binder
        self.binder_repo.save(binder)

        self.console.print_success(f'Added "{title}" ({node_id.value})')
        self.logger.info('Node added: %s', node_id.value)

        return node_id

    def _find_item(self, items: list[BinderItem], node_id: NodeId) -> BinderItem | None:
        """Find an item by node ID in the hierarchy.

        Args:
            items: List of binder items to search.
            node_id: Node ID to find.

        Returns:
            The binder item if found, None otherwise.

        """
        for item in items:
            if item.node_id and item.node_id.value == node_id.value:
                return item
            found = self._find_item(item.children, node_id)
            if found:
                return found
        return None
