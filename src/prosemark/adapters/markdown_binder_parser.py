# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Markdown binder parser for converting between binder structures and markdown text."""

import re
from typing import NoReturn

from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import BinderFormatError


class MarkdownBinderParser:
    """Parser for converting between Binder objects and markdown list format.

    This adapter handles bidirectional conversion between:
    - Binder domain objects with tree structure
    - Markdown unordered list representation with links

    Supported markdown format:
    ```
    - [Title](file.md)
      - [Nested Item](nested.md)
    - [Another Root](another.md)
    ```

    The parser maintains:
    - Hierarchical structure through indentation
    - NodeId extraction from filenames (assumes {id}.md pattern)
    - Placeholder support for items without links
    - Proper tree parent-child relationships
    """

    # Pattern to match markdown list items with optional links
    # Updated to handle brackets in titles and empty links
    LIST_ITEM_PATTERN = re.compile(r'^(\s*)- \[(.*?)\](?:\(([^)]*)\))?(?:\s*)$', re.MULTILINE)

    # Pattern to extract NodeId from markdown links (assuming {id}.md format, possibly with path)
    NODE_ID_PATTERN = re.compile(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:\.md)?$')

    def parse_to_binder(self, markdown_content: str) -> Binder:
        """Parse markdown content into a Binder object.

        Args:
            markdown_content: Markdown text with unordered list structure

        Returns:
            Binder object with parsed hierarchy

        Raises:
            BinderFormatError: If markdown format is invalid or malformed

        """
        try:
            # Validate markdown format
            MarkdownBinderParser._validate_markdown_format(markdown_content)

            # Find all list items with their indentation
            matches = self.LIST_ITEM_PATTERN.findall(markdown_content)
            if not matches:
                MarkdownBinderParser._handle_no_matches(markdown_content)
                return Binder(roots=[])

            # Build tree structure
            return self._build_binder_tree(matches)

        except BinderFormatError:
            raise
        except Exception as exc:  # noqa: BLE001
            MarkdownBinderParser._raise_parse_error(exc)

    def render_from_binder(self, binder: Binder) -> str:
        """Render Binder object as markdown list content.

        Args:
            binder: Binder object to render

        Returns:
            Markdown text with unordered list structure

        """
        lines: list[str] = []
        for root in binder.roots:
            self._render_item(root, 0, lines)
        return '\n'.join(lines)

    @staticmethod
    def _validate_markdown_format(markdown_content: str) -> None:
        """Validate markdown format and raise errors for malformed patterns."""
        lines = markdown_content.strip().split('\n')
        for line in lines:
            stripped_line = line.strip()
            if stripped_line:  # Skip empty lines
                MarkdownBinderParser._check_bracket_patterns(stripped_line)

    @staticmethod
    def _check_bracket_patterns(line: str) -> None:
        """Check for malformed bracket patterns in a line."""
        if '- [' in line and line.count('[') != line.count(']'):
            MarkdownBinderParser._raise_malformed_error('unmatched brackets')
        if '- [' in line and '[' in line and not line.endswith(']') and ')' not in line:
            MarkdownBinderParser._raise_malformed_error('unclosed bracket')

    @staticmethod
    def _handle_no_matches(markdown_content: str) -> None:
        """Handle case where no list items were matched."""
        lines = markdown_content.strip().split('\n')
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and ('- ' in stripped_line or '* ' in stripped_line or stripped_line.startswith('  - ')):
                MarkdownBinderParser._raise_malformed_error('invalid list item format')
        # If there's any non-empty content but no valid list items, it might be malformed
        if any(line.strip() for line in lines):
            MarkdownBinderParser._raise_malformed_error('content found but no valid list items')

    def _build_binder_tree(self, matches: list[tuple[str, str, str]]) -> Binder:
        """Build the binder tree structure from matched list items.

        Returns:
            Constructed Binder with hierarchical structure

        """
        root_items = []
        item_stack: list[tuple[int, BinderItem]] = []  # (indent_level, item)

        for indent_str, title, link in matches:
            indent_level = len(indent_str)

            # Extract NodeId from link if present
            node_id = self._extract_node_id(link) if link else None

            # Create binder item
            item = BinderItem(display_title=title.strip(), node_id=node_id, children=[])

            # Find parent based on indentation
            parent = MarkdownBinderParser._find_parent(item_stack, indent_level)

            if parent is None:
                # Root level item
                root_items.append(item)
            else:
                # Child item
                parent.children.append(item)

            # Update stack - remove items at same or deeper levels, then add current
            item_stack = [(level, stack_item) for level, stack_item in item_stack if level < indent_level]
            item_stack.append((indent_level, item))

        return Binder(roots=root_items)

    @staticmethod
    def _raise_malformed_error(issue: str) -> NoReturn:
        """Raise a BinderFormatError with malformed markdown message.

        Raises:
            BinderFormatError: Always raised with issue-specific message

        """
        msg = f'Malformed markdown: {issue}'
        raise BinderFormatError(msg)

    @staticmethod
    def _raise_parse_error(exc: Exception) -> NoReturn:
        """Raise a BinderFormatError for parse failures.

        Raises:
            BinderFormatError: Always raised with exception context

        """
        msg = 'Failed to parse markdown binder content'
        raise BinderFormatError(msg) from exc

    def _render_item(self, item: BinderItem, depth: int, lines: list[str]) -> None:
        """Render a single binder item and its children to lines."""
        indent = '  ' * depth
        if item.node_id:
            # Item with link
            lines.append(f'{indent}- [{item.display_title}]({item.node_id}.md)')
        else:
            # Placeholder item
            lines.append(f'{indent}- [{item.display_title}]()')

        # Render children
        for child in item.children:
            self._render_item(child, depth + 1, lines)

    def _extract_node_id(self, link: str) -> NodeId | None:
        """Extract NodeId from markdown link if valid UUID format.

        Returns:
            NodeId if link contains valid UUID, None otherwise

        """
        if not link:
            return None

        match = self.NODE_ID_PATTERN.search(link)
        if match:
            try:
                return NodeId(match.group(1))
            except ValueError:  # pragma: no cover
                # Invalid UUID format
                return None
        return None

    @staticmethod
    def _find_parent(item_stack: list[tuple[int, BinderItem]], indent_level: int) -> BinderItem | None:
        """Find the appropriate parent item based on indentation level.

        Returns:
            Parent BinderItem or None if no appropriate parent found

        """
        # Find the item with the largest indent level that's less than current
        parent = None
        for level, item in reversed(item_stack):
            if level < indent_level:
                parent = item
                break
        return parent
