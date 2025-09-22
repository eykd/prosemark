"""Unit tests for markdown parsing functionality."""

import pytest

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import BinderIntegrityError


class TestMarkdownParsing:
    """Test markdown binder parsing functionality."""

    @pytest.fixture
    def parser(self) -> MarkdownBinderParser:
        """Create a markdown binder parser instance."""
        return MarkdownBinderParser()

    def test_parse_simple_flat_structure(self, parser: MarkdownBinderParser) -> None:
        """Test parsing a simple flat binder structure."""
        markdown_content = """- [Chapter 1](0192f0c1-1111-7000-8000-000000000001.md)
- [Chapter 2](0192f0c1-2222-7000-8000-000000000002.md)
- [Chapter 3](0192f0c1-3333-7000-8000-000000000003.md)"""

        binder = parser.parse_to_binder(markdown_content)
        items = binder.roots

        assert len(items) == 3
        assert items[0].display_title == 'Chapter 1'
        assert items[0].node_id is not None
        assert items[0].node_id.value == '0192f0c1-1111-7000-8000-000000000001'
        assert len(items[0].children) == 0

        assert items[1].display_title == 'Chapter 2'
        assert items[1].node_id is not None
        assert items[1].node_id.value == '0192f0c1-2222-7000-8000-000000000002'

        assert items[2].display_title == 'Chapter 3'
        assert items[2].node_id is not None
        assert items[2].node_id.value == '0192f0c1-3333-7000-8000-000000000003'

    def test_parse_nested_structure(self, parser: MarkdownBinderParser) -> None:
        """Test parsing a nested hierarchical structure."""
        markdown_content = """- [Part 1](0192f0c1-1111-7000-8000-000000000001.md)
  - [Chapter 1.1](0192f0c1-2222-7000-8000-000000000002.md)
  - [Chapter 1.2](0192f0c1-3333-7000-8000-000000000003.md)
    - [Section 1.2.1](0192f0c1-4444-7000-8000-000000000004.md)
    - [Section 1.2.2](0192f0c1-5555-7000-8000-000000000005.md)
- [Part 2](0192f0c1-6666-7000-8000-000000000006.md)
  - [Chapter 2.1](0192f0c1-7777-7000-8000-000000000007.md)"""

        binder = parser.parse_to_binder(markdown_content)
        items = binder.roots

        assert len(items) == 2

        # Part 1
        part1 = items[0]
        assert part1.display_title == 'Part 1'
        assert part1.node_id is not None
        assert part1.node_id.value == '0192f0c1-1111-7000-8000-000000000001'
        assert len(part1.children) == 2

        # Chapter 1.1
        ch11 = part1.children[0]
        assert ch11.display_title == 'Chapter 1.1'
        assert ch11.node_id is not None
        assert ch11.node_id.value == '0192f0c1-2222-7000-8000-000000000002'
        assert len(ch11.children) == 0

        # Chapter 1.2
        ch12 = part1.children[1]
        assert ch12.display_title == 'Chapter 1.2'
        assert ch12.node_id is not None
        assert ch12.node_id.value == '0192f0c1-3333-7000-8000-000000000003'
        assert len(ch12.children) == 2

        # Section 1.2.1
        sec121 = ch12.children[0]
        assert sec121.display_title == 'Section 1.2.1'
        assert sec121.node_id is not None
        assert sec121.node_id.value == '0192f0c1-4444-7000-8000-000000000004'

        # Section 1.2.2
        sec122 = ch12.children[1]
        assert sec122.display_title == 'Section 1.2.2'
        assert sec122.node_id is not None
        assert sec122.node_id.value == '0192f0c1-5555-7000-8000-000000000005'

        # Part 2
        part2 = items[1]
        assert part2.display_title == 'Part 2'
        assert part2.node_id is not None
        assert part2.node_id.value == '0192f0c1-6666-7000-8000-000000000006'
        assert len(part2.children) == 1

        ch21 = part2.children[0]
        assert ch21.display_title == 'Chapter 2.1'
        assert ch21.node_id is not None
        assert ch21.node_id.value == '0192f0c1-7777-7000-8000-000000000007'

    def test_parse_placeholders(self, parser: MarkdownBinderParser) -> None:
        """Test parsing placeholders (items without links)."""
        markdown_content = """- [Written Chapter](0192f0c1-1111-7000-8000-000000000001.md)
- [Future Chapter]()
- [Another Future Chapter]
- [Part with Mixed]()
  - [Written Section](0192f0c1-2222-7000-8000-000000000002.md)
  - [Placeholder Section]()"""

        binder = parser.parse_to_binder(markdown_content)
        items = binder.roots

        assert len(items) == 4

        # Written chapter
        assert items[0].display_title == 'Written Chapter'
        assert items[0].node_id is not None
        assert items[0].node_id.value == '0192f0c1-1111-7000-8000-000000000001'

        # Placeholder chapters
        assert items[1].display_title == 'Future Chapter'
        assert items[1].node_id is None

        assert items[2].display_title == 'Another Future Chapter'
        assert items[2].node_id is None

        # Mixed part
        part = items[3]
        assert part.display_title == 'Part with Mixed'
        assert part.node_id is None
        assert len(part.children) == 2

        written_section = part.children[0]
        assert written_section.display_title == 'Written Section'
        assert written_section.node_id is not None
        assert written_section.node_id.value == '0192f0c1-2222-7000-8000-000000000002'

        placeholder_section = part.children[1]
        assert placeholder_section.display_title == 'Placeholder Section'
        assert placeholder_section.node_id is None

    def test_serialize_simple_structure(self, parser: MarkdownBinderParser) -> None:
        """Test serializing a simple binder structure to markdown."""
        items = [
            BinderItem(display_title='Chapter 1', node_id=NodeId('0192f0c1-1111-7000-8000-000000000001'), children=[]),
            BinderItem(display_title='Chapter 2', node_id=NodeId('0192f0c1-2222-7000-8000-000000000002'), children=[]),
            BinderItem(display_title='Future Chapter', node_id=None, children=[]),
        ]
        binder = Binder(roots=items)

        result = parser.render_from_binder(binder)

        expected_lines = [
            '- [Chapter 1](0192f0c1-1111-7000-8000-000000000001.md)',
            '- [Chapter 2](0192f0c1-2222-7000-8000-000000000002.md)',
            '- [Future Chapter]()',
        ]

        for expected_line in expected_lines:
            assert expected_line in result

    def test_serialize_nested_structure(self, parser: MarkdownBinderParser) -> None:
        """Test serializing a nested structure to markdown."""
        items = [
            BinderItem(
                display_title='Part 1',
                node_id=NodeId('0192f0c1-1111-7000-8000-000000000001'),
                children=[
                    BinderItem(
                        display_title='Chapter 1.1', node_id=NodeId('0192f0c1-2222-7000-8000-000000000002'), children=[]
                    ),
                    BinderItem(
                        display_title='Chapter 1.2',
                        node_id=None,
                        children=[
                            BinderItem(
                                display_title='Section 1.2.1',
                                node_id=NodeId('0192f0c1-3333-7000-8000-000000000003'),
                                children=[],
                            )
                        ],
                    ),
                ],
            )
        ]
        binder = Binder(roots=items)

        result = parser.render_from_binder(binder)

        # Check structure preservation
        lines = result.split('\n')
        lines = [line for line in lines if line.strip()]  # Remove empty lines

        assert '- [Part 1](0192f0c1-1111-7000-8000-000000000001.md)' in lines
        assert '  - [Chapter 1.1](0192f0c1-2222-7000-8000-000000000002.md)' in lines
        assert '  - [Chapter 1.2]()' in lines
        assert '    - [Section 1.2.1](0192f0c1-3333-7000-8000-000000000003.md)' in lines

    def test_roundtrip_consistency(self, parser: MarkdownBinderParser) -> None:
        """Test that parsing and serializing maintains consistency."""
        original_markdown = """- [Part 1](0192f0c1-1111-7000-8000-000000000001.md)
  - [Chapter 1.1](0192f0c1-2222-7000-8000-000000000002.md)
  - [Chapter 1.2]()
    - [Section 1.2.1](0192f0c1-3333-7000-8000-000000000003.md)
- [Part 2](0192f0c1-4444-7000-8000-000000000004.md)
- [Future Part]()"""

        # Parse then serialize
        binder = parser.parse_to_binder(original_markdown)
        items = binder.roots
        serialized = parser.render_from_binder(binder)

        # Parse again to verify structure
        binder2 = parser.parse_to_binder(serialized)
        items2 = binder2.roots

        # Compare structures
        assert len(items) == len(items2) == 3

        # Part 1
        assert items[0].display_title == items2[0].display_title == 'Part 1'
        assert items[0].node_id is not None
        assert items2[0].node_id is not None
        assert items[0].node_id.value == items2[0].node_id.value == '0192f0c1-1111-7000-8000-000000000001'
        assert len(items[0].children) == len(items2[0].children) == 2

        # Chapter 1.1
        ch11_orig = items[0].children[0]
        ch11_new = items2[0].children[0]
        assert ch11_orig.display_title == ch11_new.display_title == 'Chapter 1.1'
        assert ch11_orig.node_id is not None
        assert ch11_new.node_id is not None
        assert ch11_orig.node_id.value == ch11_new.node_id.value == '0192f0c1-2222-7000-8000-000000000002'

        # Chapter 1.2 (placeholder with child)
        ch12_orig = items[0].children[1]
        ch12_new = items2[0].children[1]
        assert ch12_orig.display_title == ch12_new.display_title == 'Chapter 1.2'
        assert ch12_orig.node_id is None
        assert ch12_new.node_id is None
        assert len(ch12_orig.children) == len(ch12_new.children) == 1

    def test_parse_malformed_markdown(self, parser: MarkdownBinderParser) -> None:
        """Test handling of malformed markdown structures."""
        malformed_examples = [
            'Not a list item',
            '* Wrong list marker [Chapter](01234567.md)',
            '- [Missing closing bracket(01234567.md)',
            '- [No link at all',
            '- Chapter without brackets',
            '  - Indented but no parent',
        ]

        for malformed in malformed_examples:
            with pytest.raises((BinderIntegrityError, Exception)):
                parser.parse_to_binder(malformed)

    def test_parse_complex_titles(self, parser: MarkdownBinderParser) -> None:
        """Test parsing titles with special characters."""
        markdown_content = """- [Chapter 1: "The Beginning"](0192f0c1-1111-7000-8000-000000000001.md)
- [Chapter 2: Café & Naïve](0192f0c1-2222-7000-8000-000000000002.md)
- [Chapter 3: [Brackets] and (Parens)](0192f0c1-3333-7000-8000-000000000003.md)
- [Chapter 4: 中文 Title](0192f0c1-4444-7000-8000-000000000004.md)
- [Chapter 5: Emoji 🚀 Title](0192f0c1-5555-7000-8000-000000000005.md)"""

        binder = parser.parse_to_binder(markdown_content)
        items = binder.roots

        assert len(items) == 5
        assert items[0].display_title == 'Chapter 1: "The Beginning"'
        assert items[1].display_title == 'Chapter 2: Café & Naïve'
        assert items[2].display_title == 'Chapter 3: [Brackets] and (Parens)'
        assert items[3].display_title == 'Chapter 4: 中文 Title'
        assert items[4].display_title == 'Chapter 5: Emoji 🚀 Title'

    def test_parse_various_link_formats(self, parser: MarkdownBinderParser) -> None:
        """Test parsing various markdown link formats."""
        markdown_content = """- [Standard Link](0192f0c1-2345-7123-8abc-def012345678.md)
- [Full UUID](0192f0c2-3456-7234-8abc-def012345679.md)
- [Another ID](0192f0c3-4567-7345-8abc-def01234567a.md)
- [With Path](subfolder/0192f0c4-5678-7456-8abc-def01234567b.md)
- [Empty Link]()
- [Just Title]"""

        binder = parser.parse_to_binder(markdown_content)
        items = binder.roots

        assert len(items) == 6

        # Standard UUIDv7
        assert items[0].node_id is not None
        assert items[0].node_id.value == '0192f0c1-2345-7123-8abc-def012345678'

        # Full UUID
        assert items[1].node_id is not None
        assert items[1].node_id.value == '0192f0c2-3456-7234-8abc-def012345679'

        # Another UUIDv7
        assert items[2].node_id is not None
        assert items[2].node_id.value == '0192f0c3-4567-7345-8abc-def01234567a'

        # With path (should extract just the ID)
        assert items[3].node_id is not None
        assert items[3].node_id.value == '0192f0c4-5678-7456-8abc-def01234567b'

        # Empty link (placeholder)
        assert items[4].node_id is None

        # No link (placeholder)
        assert items[5].node_id is None

    def test_parse_inconsistent_indentation(self, parser: MarkdownBinderParser) -> None:
        """Test handling of inconsistent indentation."""
        # Mixed tabs and spaces, irregular indentation
        markdown_content = """- [Part 1](01234567.md)
  - [Chapter 1.1](89abcdef.md)
    - [Section 1.1.1](deadbeef.md)
      - [Subsection](cafebabe.md)
  - [Chapter 1.2](feedface.md)"""

        binder = parser.parse_to_binder(markdown_content)
        items = binder.roots

        # Should parse hierarchical structure correctly
        assert len(items) == 1
        part1 = items[0]
        assert part1.display_title == 'Part 1'
        assert len(part1.children) == 2

        ch11 = part1.children[0]
        assert ch11.display_title == 'Chapter 1.1'
        assert len(ch11.children) == 1

        sec111 = ch11.children[0]
        assert sec111.display_title == 'Section 1.1.1'
        assert len(sec111.children) == 1

        subsec = sec111.children[0]
        assert subsec.display_title == 'Subsection'

    def test_serialize_preserves_order(self, parser: MarkdownBinderParser) -> None:
        """Test that serialization preserves item order."""
        items = [
            BinderItem('Zebra', NodeId('0192f0c1-2345-7123-8abc-def012345678'), []),
            BinderItem('Alpha', NodeId('0192f0c2-3456-7234-8abc-def012345679'), []),
            BinderItem('Beta', None, []),
            BinderItem('Charlie', NodeId('0192f0c3-4567-7345-8abc-def01234567a'), []),
        ]
        binder = Binder(roots=items)

        result = parser.render_from_binder(binder)
        lines = [line for line in result.split('\n') if line.strip()]

        # Order should be preserved (not alphabetical)
        assert 'Zebra' in lines[0]
        assert 'Alpha' in lines[1]
        assert 'Beta' in lines[2]
        assert 'Charlie' in lines[3]

    def test_empty_structure_handling(self, parser: MarkdownBinderParser) -> None:
        """Test handling of empty structures."""
        # Empty markdown
        binder = parser.parse_to_binder('')
        items = binder.roots
        assert len(items) == 0

        # Whitespace only
        binder = parser.parse_to_binder('   \n\n   ')
        items = binder.roots
        assert len(items) == 0

        # Serialize empty structure
        empty_binder = Binder(roots=[])
        result = parser.render_from_binder(empty_binder)
        assert result.strip() == ''

    def test_maximum_nesting_depth(self, parser: MarkdownBinderParser) -> None:
        """Test handling of deep nesting."""
        # Create deeply nested structure
        markdown_content = """- [Level 1](0192f0c1-2345-7123-8abc-def012345678.md)
  - [Level 2](0192f0c1-2345-7456-8abc-def012345679.md)
    - [Level 3](0192f0c1-2345-7789-8abc-def01234567a.md)
      - [Level 4](0192f0c1-2345-7abc-8abc-def01234567b.md)
        - [Level 5](0192f0c1-2345-7def-8abc-def01234567c.md)
          - [Level 6](0192f0c1-2345-7fed-8abc-def01234567d.md)"""

        binder = parser.parse_to_binder(markdown_content)
        items = binder.roots

        # Should handle deep nesting
        current = items[0]
        level = 1
        while current.children:
            assert current.display_title == f'Level {level}'
            current = current.children[0]
            level += 1

        # Check the final level title and count
        assert current.display_title == f'Level {level}'
        assert level == 6  # Reached the 6th and final level
