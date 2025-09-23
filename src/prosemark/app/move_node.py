"""MoveNode use case for reorganizing nodes in the binder hierarchy."""

from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import BinderItem, NodeId
from prosemark.exceptions import NodeNotFoundError

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.logger import Logger


class MoveNode:
    """Move nodes within the binder hierarchy."""

    def __init__(
        self,
        *,
        binder_repo: 'BinderRepo',
        console: 'ConsolePort',
        logger: 'Logger',
    ) -> None:
        """Initialize the MoveNode use case.

        Args:
            binder_repo: Repository for binder operations.
            console: Console output port.
            logger: Logger port.

        """
        self.binder_repo = binder_repo
        self.console = console
        self.logger = logger

    def execute(
        self,
        *,
        node_id: NodeId,
        parent_id: NodeId | None = None,
        position: int | None = None,
        project_path: Path | None = None,
    ) -> None:
        """Move a node to a new position in the hierarchy.

        Args:
            node_id: ID of the node to move.
            parent_id: Optional new parent node ID (None for root level).
            position: Optional position within parent's children.
            project_path: Project directory path.

        Raises:
            NodeNotFoundError: If the node to move is not found.

        """
        project_path = project_path or Path.cwd()
        self.logger.info('Moving node: %s', node_id.value)

        # Load existing binder
        binder = self.binder_repo.load()

        # Find and remove the node from its current position
        item_to_move = self._remove_item(binder.roots, node_id)
        if not item_to_move:
            msg = f'Node {node_id.value} not found in binder'
            raise NodeNotFoundError(msg)

        # Add the node to its new position
        if parent_id:
            # Find new parent and add as child
            parent_item = self._find_item(binder.roots, parent_id)
            if not parent_item:
                # Restore item to original position and fail
                binder.roots.append(item_to_move)
                msg = f'Parent node {parent_id.value} not found'
                raise NodeNotFoundError(msg)

            # Check for circular reference
            if self._would_create_cycle(item_to_move, parent_id):  # pragma: no cover
                # Restore item to original position and fail  # pragma: no cover
                binder.roots.append(item_to_move)  # pragma: no cover
                self.console.print_error(
                    f'Cannot move {node_id.value}: would create circular reference',
                )  # pragma: no cover
                return  # pragma: no cover

            if position is not None and 0 <= position <= len(parent_item.children):
                parent_item.children.insert(position, item_to_move)
            else:
                parent_item.children.append(item_to_move)
        # Add as root item
        elif position is not None and 0 <= position <= len(binder.roots):
            binder.roots.insert(position, item_to_move)
        else:
            binder.roots.append(item_to_move)

        # Save updated binder
        self.binder_repo.save(binder)

        self.console.print_success(f'Moved node {node_id.value}')
        if parent_id:
            self.console.print_info(f'New parent: {parent_id.value}')
        else:
            self.console.print_info('Moved to root level')
        self.logger.info('Node moved: %s', node_id.value)

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
            if found:  # pragma: no cover
                return found  # pragma: no cover
        return None

    def _remove_item(self, items: list[BinderItem], node_id: NodeId) -> BinderItem | None:
        """Remove and return an item from the hierarchy.

        Args:
            items: List of binder items to search.
            node_id: Node ID to remove.

        Returns:
            The removed item if found, None otherwise.

        """
        for item in items:
            if item.node_id and item.node_id.value == node_id.value:
                items.remove(item)
                return item
            removed = self._remove_item(item.children, node_id)
            if removed:
                return removed
        return None

    def _would_create_cycle(self, item: BinderItem, parent_id: NodeId) -> bool:
        """Check if moving an item would create a cycle.

        Args:
            item: The item being moved.
            parent_id: The proposed new parent ID.

        Returns:
            True if this would create a cycle, False otherwise.

        """
        # Check if the parent is a descendant of the item being moved
        return self._find_item([item], parent_id) is not None
