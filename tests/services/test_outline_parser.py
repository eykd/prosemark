"""Tests for the outline parser service."""

import pytest

from prosemark.domain.nodes import Node
from prosemark.services.outline_parser import OutlineParseError, generate_outline, parse_outline


class TestOutlineParser:
    """Tests for the outline parser service."""

    def test_parse_empty_outline(self):
        """Test parsing an empty outline."""
        result = parse_outline('')
        assert result.title == 'Root'
        assert result.id == 'root'
        assert len(result.children) == 0

    def test_parse_simple_outline(self):
        """Test parsing a simple outline with one level."""
        outline = '- [Book 1](20250506032834876147.md)'
        result = parse_outline(outline)

        assert len(result.children) == 1
        book = result.children[0]
        assert book.title == 'Book 1'
        assert book.id == '20250506032834876147'
        assert len(book.children) == 0

    def test_parse_nested_outline(self):
        """Test parsing a nested outline with multiple levels."""
        outline = """- [Book 1](20250506032834876147.md)
  - [Chapter 1](20250506032925694067.md)
    - [Scene 1](20250506T065810.md)
    - [Scene 2](20250506T065932.md)
  - [Chapter 2](20250506032931240962.md)
- [Book 2](20250506T065942.md)
  - [Chapter 1](20250506T070132.md)"""

        result = parse_outline(outline)

        assert len(result.children) == 2
        book1 = result.children[0]
        book2 = result.children[1]

        assert book1.title == 'Book 1'
        assert book1.id == '20250506032834876147'
        assert len(book1.children) == 2

        chapter1 = book1.children[0]
        assert chapter1.title == 'Chapter 1'
        assert chapter1.id == '20250506032925694067'
        assert len(chapter1.children) == 2

        scene1 = chapter1.children[0]
        assert scene1.title == 'Scene 1'
        assert scene1.id == '20250506T065810'

        chapter2 = book1.children[1]
        assert chapter2.title == 'Chapter 2'

        assert book2.title == 'Book 2'
        assert len(book2.children) == 1

    def test_invalid_outline_format(self):
        """Test that invalid outline formats raise appropriate errors."""
        invalid_outline = '- Book 1 without proper format'
        with pytest.raises(OutlineParseError):
            parse_outline(invalid_outline)

    def test_generate_outline_empty(self):
        """Test generating an outline from an empty root node."""
        root = Node(node_id='root', title='Root')
        result = generate_outline(root)
        assert result == ''

    def test_generate_simple_outline(self):
        """Test generating a simple outline with one level."""
        root = Node(node_id='root', title='Root')
        book = Node(node_id='20250506032834876147', title='Book 1')
        root.add_child(book)

        result = generate_outline(root)
        assert result == '- [Book 1](20250506032834876147.md)'

    def test_generate_nested_outline(self):
        """Test generating a nested outline with multiple levels."""
        # Create node structure
        root = Node(node_id='root', title='Root')

        book1 = Node(node_id='20250506032834876147', title='Book 1')
        chapter1 = Node(node_id='20250506032925694067', title='Chapter 1')
        scene1 = Node(node_id='20250506T065810', title='Scene 1')
        scene2 = Node(node_id='20250506T065932', title='Scene 2')
        chapter2 = Node(node_id='20250506032931240962', title='Chapter 2')

        book2 = Node(node_id='20250506T065942', title='Book 2')
        book2_chapter1 = Node(node_id='20250506T070132', title='Chapter 1')

        # Build hierarchy
        root.add_child(book1)
        book1.add_child(chapter1)
        chapter1.add_child(scene1)
        chapter1.add_child(scene2)
        book1.add_child(chapter2)

        root.add_child(book2)
        book2.add_child(book2_chapter1)

        # Generate outline
        result = generate_outline(root)
        expected = """- [Book 1](20250506032834876147.md)
  - [Chapter 1](20250506032925694067.md)
    - [Scene 1](20250506T065810.md)
    - [Scene 2](20250506T065932.md)
  - [Chapter 2](20250506032931240962.md)
- [Book 2](20250506T065942.md)
  - [Chapter 1](20250506T070132.md)"""

        assert result == expected

    def test_round_trip(self):
        """Test that parsing and then generating returns the original outline."""
        original = """- [Book 1](20250506032834876147.md)
  - [Chapter 1](20250506032925694067.md)
    - [Scene 1](20250506T065810.md)
    - [Scene 2](20250506T065932.md)
  - [Chapter 2](20250506032931240962.md)
- [Book 2](20250506T065942.md)
  - [Chapter 1](20250506T070132.md)"""

        parsed = parse_outline(original)
        generated = generate_outline(parsed)

        assert generated == original
