from __future__ import annotations

import uuid
from typing import Any


class Node:
    """A node in a hierarchical document structure.

    Represents a single node in the document tree with content, metadata,
    and relationships to other nodes.
    """

    def __init__(
        self,
        id: str | None = None,
        title: str = '',
        notecard: str = '',
        content: str = '',
        notes: str = '',
        metadata: dict[str, Any] | None = None,
        parent: Node | None = None,
        children: list[Node] | None = None,
    ) -> None:
        """Initialize a new Node.

        Args:
            id: Unique identifier for the node. If None, a UUID will be generated.
            title: Short descriptive title for the node.
            notecard: Brief summary of the node's content.
            content: Main content of the node.
            notes: Additional notes about the node.
            metadata: Key-value pairs for additional information.
            parent: Reference to the parent node.
            children: List of child nodes.

        """
        self.id = id if id is not None else str(uuid.uuid4())
        self.title = title
        self.notecard = notecard
        self.content = content
        self.notes = notes
        self.metadata = metadata or {}
        self.parent = parent
        self.children: list[Node] = []

        # Add children if provided
        if children:
            for child in children:
                self.add_child(child)

    def add_child(self, child: Node, position: int | None = None) -> None:
        """Add a child node to this node.

        Args:
            child: The node to add as a child.
            position: Optional position to insert the child. If None, appends to the end.

        """
        # Set the parent of the child node
        child.parent = self

        # Add the child to the children list
        if position is None:
            self.children.append(child)
        else:
            self.children.insert(position, child)

    def remove_child(self, child: Node | str) -> Node | None:
        """Remove a child node from this node.

        Args:
            child: The node or node ID to remove. If a string is provided,
                it will be treated as a node ID.

        Returns:
            The removed node or None if not found.

        """
        # Find the child node
        child_node = None
        if isinstance(child, str):
            child_node = self.get_child_by_id(child)
        else:
            child_node = child

        # Remove the child if found in children list
        if child_node in self.children:
            self.children.remove(child_node)
            child_node.parent = None
            return child_node

        return None

    def get_child_by_id(self, id: str) -> Node | None:
        """Get a child node by its ID.

        Args:
            id: The ID of the child node to find.

        Returns:
            The child node or None if not found.

        """
        for child in self.children:
            if child.id == id:
                return child
        return None

    def get_descendants(self) -> list[Node]:
        """Get all descendant nodes recursively.

        Returns:
            List of all descendant nodes.

        """
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_ancestors(self) -> list[Node]:
        """Get all ancestor nodes recursively.

        Returns:
            List of all ancestor nodes.

        """
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def move_child(self, child: Node | str, position: int) -> bool:
        """Move a child node to a new position in the children list.

        Args:
            child: The node or node ID to move.
            position: The new position for the child. Must be within valid range
                of the children list.

        Returns:
            True if successful, False otherwise.

        """
        # Find the child node
        child_node = None
        if isinstance(child, str):
            child_node = self.get_child_by_id(child)
        else:
            child_node = child

        # Move the child if found and position is valid
        if child_node in self.children and 0 <= position < len(self.children):
            self.children.remove(child_node)
            self.children.insert(position, child_node)
            return True

        return False
