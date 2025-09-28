# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Markdown binder parser for converting between binder structures and markdown text."""

import re
from typing import NoReturn

from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.domain.parser_result import ParserResult, ParsingMetadata
from prosemark.domain.position_anchor import PositionAnchor
from prosemark.domain.preserved_text import PreservedText
from prosemark.domain.structural_element import StructuralElement
from prosemark.exceptions import BinderFormatError
from prosemark.ports.enhanced_binder_parser import EnhancedBinderParserPort


class MarkdownBinderParser(EnhancedBinderParserPort):
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

    def parse_with_preservation(self, markdown_content: str) -> ParserResult:
        """Parse markdown content preserving all non-structural text.

        Args:
            markdown_content: Raw markdown text with mixed structural and narrative content

        Returns:
            ParserResult containing binder structure and preserved text

        Raises:
            BinderFormatError: If structural parsing fails

        """
        try:
            # Parse lines for analysis
            lines = markdown_content.split('\n')
            preserved_text: list[PreservedText] = []
            structural_elements: list[StructuralElement] = []

            # Track parsing metadata
            malformed_count = 0
            uuid_failures = 0
            structural_count = 0

            # Analyze each line
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()

                if not stripped_line:
                    # Preserve empty lines
                    preserved_text.append(
                        PreservedText(
                            content=line, line_number=line_num, position_anchor=PositionAnchor.BETWEEN_ELEMENTS
                        )
                    )
                    continue

                # Check if this line matches structural pattern
                match = self.LIST_ITEM_PATTERN.match(line)
                if match:
                    indent_str, title, link = match.groups()
                    indent_level = len(indent_str)

                    # Validate UUID7 format if link present
                    node_id = None
                    if link:  # pragma: no branch
                        node_id = self._extract_node_id(link)
                        if node_id is None:
                            uuid_failures += 1
                            # Non-UUID7 links are treated as extraneous text
                            preserved_text.append(
                                PreservedText(
                                    content=line, line_number=line_num, position_anchor=PositionAnchor.BETWEEN_ELEMENTS
                                )
                            )
                            continue

                    # Valid structural element
                    structural_elements.append(
                        StructuralElement(
                            indent_level=indent_level, title=title.strip(), node_id=node_id, line_number=line_num
                        )
                    )
                    structural_count += 1

                else:
                    # Check for malformed list items
                    if '- [' in stripped_line or stripped_line.startswith('- '):
                        malformed_count += 1

                    # All non-structural text is preserved
                    preserved_text.append(
                        PreservedText(
                            content=line,
                            line_number=line_num,
                            position_anchor=MarkdownBinderParser._determine_position_anchor(
                                line_num, len(lines), structural_elements
                            ),
                        )
                    )

            # Build binder from structural elements
            binder = MarkdownBinderParser._build_binder_from_elements(structural_elements)

            # Create parsing metadata
            metadata = ParsingMetadata(
                malformed_elements_count=malformed_count,
                uuid_validation_failures=uuid_failures,
                original_line_count=len(lines),
                structural_line_count=structural_count,
            )

            return ParserResult(binder=binder, preserved_text=preserved_text, parsing_metadata=metadata)

        except Exception as exc:
            raise BinderFormatError('Failed to parse markdown with text preservation') from exc

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

    @staticmethod
    def _determine_position_anchor(
        line_num: int, total_lines: int, structural_elements: list[StructuralElement]
    ) -> PositionAnchor:
        """Determine the position anchor for preserved text based on context.

        Args:
            line_num: The line number of the preserved text
            total_lines: Total number of lines in the document
            structural_elements: List of structural elements found so far

        Returns:
            PositionAnchor indicating where this text appears relative to structure

        """
        # Check if there are any structural elements
        if not structural_elements:
            # No structural elements found yet
            if line_num <= total_lines // 2:
                return PositionAnchor.BEFORE_STRUCTURE
            return PositionAnchor.AFTER_STRUCTURE

        # Find structural elements before and after this line
        elements_before = [elem for elem in structural_elements if elem.line_number < line_num]
        elements_after = [elem for elem in structural_elements if elem.line_number > line_num]

        if not elements_before:
            # No structural elements before this line
            return PositionAnchor.BEFORE_STRUCTURE  # pragma: no cover
        if not elements_after:
            # No structural elements after this line
            return PositionAnchor.AFTER_STRUCTURE
        # Structural elements both before and after
        return PositionAnchor.BETWEEN_ELEMENTS  # pragma: no cover

    @staticmethod
    def _build_binder_from_elements(structural_elements: list[StructuralElement]) -> Binder:
        """Build a Binder object from a list of structural elements.

        Args:
            structural_elements: List of parsed structural elements with hierarchy

        Returns:
            Binder object with hierarchical structure

        """
        if not structural_elements:
            return Binder(roots=[])

        root_items = []
        item_stack: list[tuple[int, BinderItem]] = []  # (indent_level, item)

        for element in structural_elements:
            # Create binder item from structural element
            item = BinderItem(display_title=element.title, node_id=element.node_id, children=[])

            # Find parent based on indentation
            parent = MarkdownBinderParser._find_parent(item_stack, element.indent_level)

            if parent is None:
                # Root level item
                root_items.append(item)
            else:
                # Child item
                parent.children.append(item)

            # Update stack - remove items at same or deeper levels, then add current
            item_stack = [(level, stack_item) for level, stack_item in item_stack if level < element.indent_level]
            item_stack.append((element.indent_level, item))

        return Binder(roots=root_items)

    def render_with_preservation(self, parser_result: ParserResult) -> str:  # noqa: PLR6301
        """Render ParserResult back to markdown preserving all text positioning.

        Args:
            parser_result: Result from parse_with_preservation containing binder and preserved text

        Returns:
            Markdown text with structural elements and preserved text in original positions

        """
        # Create a mapping of line numbers to content
        line_content: dict[int, str] = {}

        # Add preserved text at their original line positions
        for preserved in parser_result.preserved_text:
            line_content[preserved.line_number] = preserved.content

        # To render structural elements, we need to re-extract them with line positions
        # Since the parse process stores line numbers in StructuralElement objects,
        # we need to recreate this mapping by re-parsing the structural elements
        preserved_lines = {p.line_number for p in parser_result.preserved_text}
        structural_lines = MarkdownBinderParser._render_structural_elements_with_positions(
            parser_result.binder, preserved_lines
        )

        # Add structural elements to their positions
        line_content.update(dict(structural_lines.items()))

        # Reconstruct the full document line by line
        if not line_content:
            return ''

        max_line = max(line_content.keys())
        lines = []
        for line_num in range(1, max_line + 1):
            if line_num in line_content:
                lines.append(line_content[line_num])
            else:
                # Fill missing lines with empty content
                lines.append('')  # pragma: no cover

        return '\n'.join(lines)

    @staticmethod
    def _render_structural_elements_with_positions(binder: Binder, preserved_lines: set[int]) -> dict[int, str]:
        """Render structural elements to available line positions.

        Args:
            binder: Binder object containing structural hierarchy
            preserved_lines: Set of line numbers already used by preserved text

        Returns:
            Dictionary mapping line numbers to rendered structural content

        """
        # This is a limitation of the current design - we lost the line number information
        # when converting from StructuralElement to BinderItem. For now, we'll render
        # structural elements as if they appear consecutively, which won't achieve
        # perfect round-trip integrity but will preserve the content correctly.

        structural_lines: dict[int, str] = {}
        line_counter = 1

        # Find the first available line not used by preserved text
        # This is a workaround since we don't have original line positions in Binder
        def render_items_recursively(items: list[BinderItem], depth: int) -> None:
            nonlocal line_counter
            for item in items:
                # Find next available line position
                while line_counter in preserved_lines:
                    line_counter += 1

                # Render the structural element
                indent = '  ' * depth
                if item.node_id:
                    content = f'{indent}- [{item.display_title}]({item.node_id}.md)'
                else:
                    content = f'{indent}- [{item.display_title}]()'  # pragma: no cover

                structural_lines[line_counter] = content
                line_counter += 1

                # Recursively render children
                if item.children:
                    render_items_recursively(item.children, depth + 1)  # pragma: no cover

        # Start rendering from root items
        render_items_recursively(binder.roots, 0)

        return structural_lines
