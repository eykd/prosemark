# Node Class Specification

## Overview
The `Node` class is a core domain entity in the Prosemark system that represents a single node in a hierarchical document structure. Each node contains content, metadata, and relationships to other nodes.

## Requirements

### Attributes
- `id`: A unique identifier for the node (UUID string)
- `title`: A short descriptive title for the node (string)
- `notecard`: A brief summary or description of the node's content (string)
- `content`: The main content of the node (string)
- `notes`: Additional notes or comments about the node (string)
- `metadata`: Arbitrary key-value pairs for storing additional information (dict)
- `parent`: Reference to the parent node (Node or None)
- `children`: Ordered list of child nodes (list of Node objects)

### Methods
- `__init__`: Initialize a new Node with required attributes
- `add_child`: Add a child node to this node
- `remove_child`: Remove a child node from this node
- `get_child_by_id`: Retrieve a child node by its ID
- `get_descendants`: Get all descendant nodes (recursive)
- `get_ancestors`: Get all ancestor nodes (recursive)
- `move_child`: Change the position of a child node in the children list

## Behavior
- A node without a parent is considered a root node
- When a node is added as a child to another node, its parent reference should be updated
- When a node is removed as a child, its parent reference should be set to None
- Node IDs should be generated automatically if not provided
- Nodes should maintain the order of their children

## Interface

```python
class Node:
    def __init__(
        self,
        id: str | None = None,
        title: str = "",
        notecard: str = "",
        content: str = "",
        notes: str = "",
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
        pass

    def add_child(self, child: Node, position: int | None = None) -> None:
        """Add a child node to this node.

        Args:
            child: The node to add as a child.
            position: Optional position to insert the child. If None, appends to the end.
        """
        pass

    def remove_child(self, child: Node | str) -> Node | None:
        """Remove a child node from this node.

        Args:
            child: The node or node ID to remove.

        Returns:
            The removed node or None if not found.
        """
        pass

    def get_child_by_id(self, id: str) -> Node | None:
        """Get a child node by its ID.

        Args:
            id: The ID of the child node to find.

        Returns:
            The child node or None if not found.
        """
        pass

    def get_descendants(self) -> list[Node]:
        """Get all descendant nodes recursively.

        Returns:
            List of all descendant nodes.
        """
        pass

    def get_ancestors(self) -> list[Node]:
        """Get all ancestor nodes recursively.

        Returns:
            List of all ancestor nodes.
        """
        pass

    def move_child(self, child: Node | str, position: int) -> bool:
        """Move a child node to a new position in the children list.

        Args:
            child: The node or node ID to move.
            position: The new position for the child.

        Returns:
            True if successful, False otherwise.
        """
        pass
```

## Testing Requirements
- Test node creation with various attribute combinations
- Test parent-child relationship management
- Test child node ordering and positioning
- Test node retrieval by ID
- Test ancestor and descendant retrieval
- Test metadata handling
- Test edge cases (e.g., circular references, duplicate IDs)
