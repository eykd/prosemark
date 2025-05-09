"""Outline parser for Commonmark-style unordered lists.

This module provides functionality to parse documents containing Commonmark-style
unordered lists into an abstract syntax tree (AST), while preserving all other content.
The AST can be manipulated and transformed back into text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto


class NodeType(Enum):
    """Types of nodes in the outline AST."""

    DOCUMENT = auto()
    LIST = auto()
    LIST_ITEM = auto()
    TEXT = auto()


@dataclass
class Node:
    """A node in the outline AST.

    Represents a single node in the document tree with content and
    relationships to other nodes.
    """

    type: NodeType
    content: str = ''
    children: list[Node] = field(default_factory=list)
    parent: Node | None = None

    def add_child(self, child: Node, position: int | None = None) -> None:
        """Add a child node to this node.

        Args:
            child: The child node to add.
            position: Optional position to insert the child at. If None, appends to the end.

        """
        if child.parent is not None:
            child.parent.remove_child(child)

        child.parent = self

        if position is None:
            self.children.append(child)
        else:
            self.children.insert(min(position, len(self.children)), child)

    def remove_child(self, child: Node) -> Node | None:
        """Remove a child node from this node.

        Args:
            child: The child node to remove.

        Returns:
            The removed node if found, None otherwise.

        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            return child
        return None

    def add_sibling_before(self, sibling: Node) -> bool:
        """Add a sibling node before this node.

        Args:
            sibling: The sibling node to add.

        Returns:
            True if successful, False if this node has no parent.

        """
        if self.parent is None:
            return False

        if sibling.parent is not None:
            sibling.parent.remove_child(sibling)

        position = self.parent.children.index(self)
        self.parent.add_child(sibling, position)
        return True

    def add_sibling_after(self, sibling: Node) -> bool:
        """Add a sibling node after this node.

        Args:
            sibling: The sibling node to add.

        Returns:
            True if successful, False if this node has no parent.

        """
        if self.parent is None:
            return False

        if sibling.parent is not None:
            sibling.parent.remove_child(sibling)

        position = self.parent.children.index(self) + 1
        self.parent.add_child(sibling, position)
        return True

    def remove_sibling(self, sibling: Node) -> Node | None:
        """Remove a sibling node.

        Args:
            sibling: The sibling node to remove.

        Returns:
            The removed node if found, None otherwise.

        """
        if self.parent is None:
            return None
        return self.parent.remove_child(sibling)

    def add_parent(self, new_parent: Node) -> bool:
        """Insert a new parent between this node and its current parent.

        Args:
            new_parent: The new parent node.

        Returns:
            True if successful, False if this node has no parent.

        """
        if self.parent is None:
            return False

        old_parent = self.parent
        old_parent.remove_child(self)
        old_parent.add_child(new_parent)
        new_parent.add_child(self)
        return True


class OutlineParseError(Exception):
    """Base exception for outline parsing errors."""


class OutlineParser:
    """Parser for Commonmark-style unordered lists.

    This class provides methods to parse documents with unordered lists into an AST
    and transform the AST back into text.
    """

    # Regex for detecting list items (- * +)
    LIST_ITEM_PATTERN = re.compile(r'^(\s*)([*+-])(\s+)(.*)$')

    @classmethod
    def parse(cls, text: str) -> Node:  # noqa: C901
        """Parse a document containing Commonmark-style unordered lists into an AST.

        Args:
            text: The document text to parse.

        Returns:
            The root node of the AST.

        """
        root = Node(type=NodeType.DOCUMENT)
        lines = text.splitlines(True)  # Keep line endings  # noqa: FBT003

        # Handle empty document
        if not lines:
            return root

        current_list: Node | None = None
        current_items: list[tuple[int, Node]] = []  # (indent_level, node)

        line_index = 0
        while line_index < len(lines):
            line = lines[line_index]
            match = cls.LIST_ITEM_PATTERN.match(line)

            if match:
                # This is a list item
                indent, _marker, _space, _content = match.groups()
                indent_level = len(indent)

                # Create list node if we're not in a list yet
                if current_list is None:
                    current_list = Node(type=NodeType.LIST)
                    root.add_child(current_list)

                # Create the list item node - preserve the full line including indentation
                item_content = line.rstrip('\n')
                item_node = Node(type=NodeType.LIST_ITEM, content=item_content)

                # Find the parent based on indentation
                while current_items and current_items[-1][0] >= indent_level:
                    current_items.pop()

                if not current_items:
                    # Top-level list item
                    current_list.add_child(item_node)
                else:
                    # Nested list item
                    _parent_indent, parent_node = current_items[-1]

                    # Check if we need a new list container for this item
                    if parent_node.type == NodeType.LIST_ITEM:
                        # Create a new list under the parent item
                        list_node = Node(type=NodeType.LIST)
                        parent_node.add_child(list_node)
                        list_node.add_child(item_node)
                    else:
                        # Add to existing list
                        parent_node.add_child(item_node)

                current_items.append((indent_level, item_node))
                line_index += 1
            else:
                # This is regular text
                if current_list is not None:
                    # We're exiting a list section
                    current_list = None
                    current_items = []

                # Collect consecutive non-list lines
                text_content = ''
                while line_index < len(lines):
                    line = lines[line_index]
                    if cls.LIST_ITEM_PATTERN.match(line):
                        break
                    text_content += line
                    line_index += 1

                if text_content:  # pragma: no branch
                    text_node = Node(type=NodeType.TEXT, content=text_content)
                    root.add_child(text_node)

        return root

    @classmethod
    def to_text(cls, node: Node) -> str:
        """Convert an AST back to text.

        Args:
            node: The root node of the AST.

        Returns:
            The text representation of the AST.

        """
        if node.type == NodeType.DOCUMENT:
            return ''.join(cls.to_text(child) for child in node.children)

        if node.type == NodeType.TEXT:
            return node.content

        if node.type == NodeType.LIST:
            return ''.join(cls.to_text(child) for child in node.children)

        if node.type == NodeType.LIST_ITEM:
            result = node.content

            # Add newline if not already present
            if not result.endswith('\n'):  # pragma: no branch
                result += '\n'

            # Process children (which could be nested lists)
            if node.children:
                child_text = ''.join(cls.to_text(child) for child in node.children)
                result += child_text

            return result

        return ''  # pragma: no cover
