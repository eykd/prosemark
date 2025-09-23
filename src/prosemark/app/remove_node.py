"""RemoveNode use case for removing nodes from the binder."""

from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import BinderItem, NodeId
from prosemark.exceptions import FileSystemError, NodeNotFoundError

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.logger import Logger
    from prosemark.ports.node_repo import NodeRepo


class RemoveNode:
    """Remove nodes from the binder hierarchy."""

    def __init__(
        self,
        *,
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        console: 'ConsolePort',
        logger: 'Logger',
    ) -> None:
        """Initialize the RemoveNode use case.

        Args:
            binder_repo: Repository for binder operations.
            node_repo: Repository for node operations.
            console: Console output port.
            logger: Logger port.

        """
        self.binder_repo = binder_repo
        self.node_repo = node_repo
        self.console = console
        self.logger = logger

    def execute(
        self,
        *,
        node_id: NodeId,
        keep_children: bool = False,
        delete_files: bool = False,
        project_path: Path | None = None,
    ) -> None:
        """Remove a node from the binder.

        Args:
            node_id: ID of the node to remove.
            keep_children: If True, promote children to parent level.
                          If False, remove entire subtree.
            delete_files: If True, delete the node's .md and .notes.md files.
            project_path: Project directory path.

        Raises:
            NodeNotFoundError: If the node to remove is not found.

        """
        project_path = project_path or Path.cwd()
        self.logger.info('Removing node: %s', node_id.value)

        # Load existing binder
        binder = self.binder_repo.load()

        # Find the node's parent and position
        parent_items, position = self._find_parent_and_position(binder.roots, node_id)
        if parent_items is None:
            msg = f'Node {node_id.value} not found in binder'
            raise NodeNotFoundError(msg)

        # Get the item to remove
        item_to_remove = parent_items[position]

        # Handle children based on keep_children flag
        if keep_children:
            # Promote children to parent level
            for i, child in enumerate(item_to_remove.children):
                parent_items.insert(position + 1 + i, child)

        # Remove the item
        parent_items.pop(position)

        # Save updated binder
        self.binder_repo.save(binder)

        # Delete files if requested
        if delete_files:
            try:
                self.node_repo.delete(node_id, delete_files=True)
                self.console.print_info(f'Deleted files: {node_id.value}.md, {node_id.value}.notes.md')
            except FileSystemError as e:
                self.console.print_warning(f'Could not delete files: {e}')

        self.console.print_success(f'Removed node {node_id.value} from binder')
        if keep_children:
            self.console.print_info('Children promoted to parent level')
        elif item_to_remove.children:
            self.console.print_info(f'Removed {len(item_to_remove.children)} child nodes')
        self.logger.info('Node removed: %s', node_id.value)

    def _find_parent_and_position(
        self,
        items: list[BinderItem],
        node_id: NodeId,
        parent: list[BinderItem] | None = None,
    ) -> tuple[list[BinderItem] | None, int]:
        """Find the parent list and position of a node.

        Args:
            items: List of binder items to search.
            node_id: Node ID to find.
            parent: Parent list (used for recursion).

        Returns:
            Tuple of (parent_list, position) if found, (None, -1) otherwise.

        """
        if parent is None:
            parent = items

        for i, item in enumerate(items):
            if item.node_id and item.node_id.value == node_id.value:
                return parent, i
            found_parent, found_pos = self._find_parent_and_position(item.children, node_id, item.children)
            if found_parent is not None:
                return found_parent, found_pos
        return None, -1
