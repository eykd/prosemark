"""Project module for the prosemark document structure.

This module defines the Project class which represents a complete document project.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from prosemark.domain.nodes import Node


@dataclass
class Project:
    """A project in the prosemark system.

    Represents a complete document project with a hierarchical structure of nodes.
    """

    root_node: Node

    @property
    def title(self) -> str:
        """Get the title of the project."""
        return self.root_node.title

    @property
    def card(self) -> str:
        """Get the binder notecard of the project."""
        return self.root_node.card

    def get_node_by_id(self, node_id: str) -> Node | None:
        """Retrieve a node from anywhere in the project tree by its ID.

        Args:
            node_id: The ID of the node to find.

        Returns:
            The node if found, None otherwise.

        """
        # Check if it's the root node
        if self.root_node.id == node_id:
            return self.root_node

        # Search in all descendants
        for node in self.root_node.get_descendants():
            if node.id == node_id:
                return node

        return None

    def create_node(
        self,
        parent_id: str,
        title: str = '',
        card: str = '',
        text: str = '',
        notes: str = '',
        metadata: dict[str, Any] | None = None,
        position: int | None = None,
    ) -> Node | None:
        """Create a new node and add it to the specified parent node.

        Args:
            parent_id: The ID of the parent node.
            title: Short descriptive title for the node.
            card: Brief summary of the node's content.
            text: Main content of the node.
            notes: Additional notes about the node.
            metadata: Key-value pairs for additional information.
            position: Optional position to insert the node. If None, appends to the end.

        Returns:
            The newly created node or None if the parent node couldn't be found.

        """
        parent = self.get_node_by_id(parent_id)
        if parent is None:
            return None

        new_node = Node(
            title=title,
            card=card,
            text=text,
            notes=notes,
            metadata=metadata if metadata is not None else {},
        )

        parent.add_child(new_node, position)
        return new_node

    def move_node(
        self,
        node_id: str,
        new_parent_id: str,
        position: int | None = None,
    ) -> bool:
        """Move a node from its current parent to a new parent.

        Args:
            node_id: The ID of the node to move.
            new_parent_id: The ID of the new parent node.
            position: Optional position to insert the node. If None, appends to the end.

        Returns:
            True if successful, False otherwise.

        """
        node = self.get_node_by_id(node_id)
        new_parent = self.get_node_by_id(new_parent_id)

        # Check if nodes exist and new_parent is not a descendant of node
        if (
            node is None
            or new_parent is None
            or node is self.root_node
            or node in new_parent.get_ancestors()
            or new_parent in node.get_descendants()  # pragma: no cover
        ):
            return False

        # Remove from current parent
        if node.parent:  # pragma: no branch
            node.parent.remove_child(node)

        # Add to new parent
        new_parent.add_child(node, position)
        return True

    def remove_node(self, node_id: str) -> Node | None:
        """Remove a node from the project tree.

        Args:
            node_id: The ID of the node to remove.

        Returns:
            The removed node or None if the node couldn't be found or is the root node.

        """
        node = self.get_node_by_id(node_id)

        # Cannot remove root node or non-existent node
        if node is None or node is self.root_node:
            return None

        # Get children before removing from parent
        children = node.children.copy()

        # Remove from parent
        if node.parent:  # pragma: no branch
            removed = node.parent.remove_child(node)

            # Set parent to None for all children
            for child in children:
                child.parent = None

            return removed

        return None  # pragma: no cover

    def get_node_count(self) -> int:
        """Get the total number of nodes in the project.

        Returns:
            The total number of nodes, including the root node.

        """
        # Count the root node plus all descendants
        return 1 + len(self.root_node.get_descendants())

    def get_structure(self) -> list[dict[str, Any]]:
        """Get a structured representation of the project hierarchy.

        Returns:
            A list of dictionaries representing the project structure.

        """
        return self._build_structure(self.root_node)

    def _build_structure(self, node: Node) -> list[dict[str, Any]]:
        """Recursively build a structured representation of the node hierarchy.

        Args:
            node: The node to build the structure from.

        Returns:
            A list of dictionaries representing the node structure.

        """
        result = []
        node_info: dict[str, Any] = {
            'id': node.id,
            'title': node.title,
            'children': [],  # This is a list that will be modified
        }

        if node.children:  # pragma: no cover
            for child in node.children:
                # Append each child's structure to the children list
                for child_structure in self._build_structure(child):
                    node_info['children'].append(child_structure)

        result.append(node_info)
        return result
