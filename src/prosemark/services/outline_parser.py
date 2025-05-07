"""Binder Outline Parser service for converting between Markdown outlines and node trees.

This module provides functionality to parse Markdown-formatted outlines into
hierarchical node trees and generate Markdown outlines from existing node trees.
"""

import re

from prosemark.domain.nodes import Node


class OutlineParseError(Exception):
    """Raised when the outline cannot be parsed correctly."""


class OutlineLineFormatError(OutlineParseError):
    """Raised when a line in the outline does not match the expected format."""


class OutlineIndentationError(OutlineParseError):
    """Raised when the indentation structure of the outline is invalid."""


def parse_outline(outline_text: str) -> Node:
    """Parse a Markdown-formatted outline into a node tree.

    Args:
        outline_text: String containing the Markdown outline

    Returns:
        A root Node object containing the complete node tree

    Raises:
        OutlineParseError: If the outline format is invalid

    """
    if not outline_text.strip():
        return Node(node_id='root', title='Root')

    lines = outline_text.strip().split('\n')
    root_node = Node(node_id='root', title='Root')

    # Stack to keep track of parent nodes at each indentation level
    # The first element is the root node at level -1 (before any indentation)
    node_stack = [(root_node, -1)]

    for line in lines:
        try:
            # Extract indentation level, title, and node_id
            indent_level, title, node_id = _parse_line(line)
        except (OutlineLineFormatError, OutlineIndentationError):
            raise
        except Exception as e:
            msg = f'Failed to parse line: {line}. Error: {e!s}'
            raise OutlineParseError(msg) from e

        # Find the appropriate parent for this node based on indentation
        while node_stack and node_stack[-1][1] >= indent_level:
            node_stack.pop()

        if not node_stack:  # pragma: no cover
            raise OutlineIndentationError(line)

        # Check if the indentation level is valid (should be exactly 2 more than parent's level)
        parent_node, parent_level = node_stack[-1]
        if indent_level > parent_level + 2:
            raise OutlineIndentationError(line)

        # Create new node and add to parent
        new_node = Node(node_id=node_id, title=title)
        parent_node.add_child(new_node)

        # Add this node to the stack for potential children
        node_stack.append((new_node, indent_level))

    return root_node


def generate_outline(root_node: Node) -> str:
    """Generate a Markdown-formatted outline from a node tree.

    Args:
        root_node: The root Node object of the tree to convert

    Returns:
        A string containing the Markdown outline

    """
    # Skip the root node itself and start with its children
    lines: list[str] = []

    for child in root_node.children:
        _generate_node_line(child, lines, indent_level=0)

    return '\n'.join(lines)


def _parse_line(line: str) -> tuple[int, str, str]:
    """Parse a single line of the Markdown outline.

    Args:
        line: A single line from the Markdown outline

    Returns:
        A tuple of (indent_level, title, node_id)

    Raises:
        OutlineLineFormatError: If the line format is invalid

    """
    # Count leading spaces to determine indentation level
    indent_match = re.match(r'^(\s*)', line)
    if not indent_match:  # pragma: no cover
        raise OutlineLineFormatError('Could not determine indentation')

    indent_level = len(indent_match.group(1))

    # Extract title and node_id using regex
    pattern = r'^\s*- \[(.*?)\]\((.*?)\.md\)'
    match = re.match(pattern, line)

    if not match:
        raise OutlineLineFormatError("Line does not match expected format: '- [Title](ID.md)'")

    title = match.group(1)
    node_id = match.group(2)

    return indent_level, title, node_id


def _generate_node_line(node: Node, lines: list[str], indent_level: int) -> None:
    """Recursively generate Markdown lines for a node and its children.

    Args:
        node: The node to generate a line for
        lines: List to append the generated lines to
        indent_level: Current indentation level

    """
    # Create the line for this node
    indent = ' ' * indent_level
    line = f'{indent}- [{node.title}]({node.id}.md)'
    lines.append(line)

    # Process children with increased indentation
    for child in node.children:
        _generate_node_line(child, lines, indent_level + 2)
