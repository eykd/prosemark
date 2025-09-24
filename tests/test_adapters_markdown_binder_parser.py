"""Tests for MarkdownBinderParser adapter."""

from unittest.mock import patch

import pytest

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser
from prosemark.domain.models import BinderItem
from prosemark.exceptions import BinderFormatError


class TestMarkdownBinderParser:
    """Test MarkdownBinderParser adapter methods."""

    @pytest.fixture
    def parser(self) -> MarkdownBinderParser:
        """Create a MarkdownBinderParser instance."""
        return MarkdownBinderParser()

    def test_parse_to_binder_handles_exception(self, parser: MarkdownBinderParser) -> None:
        """Test parse_to_binder raises BinderFormatError when exception occurs during parsing."""
        # Arrange - patch to cause an exception during parsing
        malformed_content = '- [Item](link.md)'

        with (
            patch.object(parser, '_extract_node_id', side_effect=Exception('Simulated parsing error')),
            pytest.raises(BinderFormatError, match='Failed to parse markdown binder content'),
        ):
            # Act & Assert
            parser.parse_to_binder(malformed_content)

    def test_extract_node_id_handles_empty_link(self, parser: MarkdownBinderParser) -> None:
        """Test _extract_node_id returns None for empty link."""
        # Act & Assert - empty string
        assert parser._extract_node_id('') is None

        # Act & Assert - whitespace only
        assert parser._extract_node_id('   ') is None

    def test_find_parent_returns_none_when_no_parent_found(self, parser: MarkdownBinderParser) -> None:
        """Test _find_parent returns None when no suitable parent is found."""
        # Arrange - empty stack means no parents available
        item_stack: list[tuple[int, BinderItem]] = []

        # Act
        result = parser._find_parent(item_stack, 0)

        # Assert
        assert result is None

    def test_find_parent_returns_none_when_no_shallower_level_in_stack(self, parser: MarkdownBinderParser) -> None:
        """Test _find_parent returns None when stack has items but none at shallower level."""
        # Arrange - stack with items all at same or deeper level than target
        item1 = BinderItem(display_title='Item 1', node_id=None)
        item2 = BinderItem(display_title='Item 2', node_id=None)
        item_stack = [
            (2, item1),  # Level 2
            (3, item2),  # Level 3
        ]

        # Act - looking for parent at level 1 (shallower than any in stack)
        result = parser._find_parent(item_stack, 1)

        # Assert
        assert result is None

    def test_render_item_handles_placeholder_without_node_id(self, parser: MarkdownBinderParser) -> None:
        """Test _render_item correctly renders placeholder items without NodeId."""
        # Arrange
        placeholder_item = BinderItem(display_title='Placeholder Item', node_id=None)
        lines: list[str] = []

        # Act
        parser._render_item(placeholder_item, 0, lines)

        # Assert
        assert len(lines) == 1
        assert lines[0] == '- [Placeholder Item]()'

    def test_check_bracket_patterns_unclosed_bracket_error(self, parser: MarkdownBinderParser) -> None:
        """Test _check_bracket_patterns raises error for unclosed bracket."""
        # Line with equal bracket counts but unclosed pattern (line 97)
        # Has equal [ and ] counts, but ends with text instead of ], and no parentheses
        markdown_content = '- [Text] more text'

        # Should raise malformed error for unclosed bracket when parsed
        with pytest.raises(BinderFormatError, match='unclosed bracket'):
            parser.parse_to_binder(markdown_content)

    def test_extract_node_id_invalid_uuid_format(self, parser: MarkdownBinderParser) -> None:
        """Test _extract_node_id handles content with no UUID pattern match."""
        # Content with link that doesn't match the NODE_ID_PATTERN regex
        markdown_content = '- [text](invalid-uuid-format)'

        # Should successfully parse but the binder item won't have a valid node_id
        binder = parser.parse_to_binder(markdown_content)
        assert len(binder.roots) == 1
        assert binder.roots[0].display_title == 'text'
        assert binder.roots[0].node_id is None
