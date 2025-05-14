"""Tests for the NodeParser class."""

from __future__ import annotations

import textwrap

from prosemark.parsers.nodes import NodeParser


class TestNodeParser:
    """Tests for the NodeParser class."""

    def test_parse_empty_content(self) -> None:
        """Test parsing empty content."""
        result = NodeParser.parse('', 'node123')
        assert result == {
            'id': 'node123',
            'title': '',
            'notecard': '',
            'content': '',
            'notes': '',
            'metadata': {},
        }

    def test_parse_content_without_header(self) -> None:
        """Test parsing content without a YAML header."""
        content = 'This is just plain content\nwithout any header.'
        result = NodeParser.parse(content, 'test_id')
        assert result['id'] == 'test_id'
        assert result['title'] == ''
        assert result['content'] == content
        assert result['metadata'] == {}

    def test_parse_with_yaml_header(self) -> None:
        """Test parsing content with a YAML header."""
        content = """---
id: node123
title: Test Node
custom_field: custom value
---
This is the content."""
        result = NodeParser.parse(content)
        assert result['id'] == 'node123'
        assert result['title'] == 'Test Node'
        assert result['content'] == 'This is the content.'
        assert result['metadata'] == {'custom_field': 'custom value'}

    def test_parse_with_directives(self) -> None:
        """Test parsing content with directives."""
        content = """---
id: node123
title: Test Node
---
// Notecard: [[node123 notecard.md]]
// Notes: [[node123 notes.md]]
// Custom: Some custom directive

This is the content."""
        result = NodeParser.parse(content)
        assert result['id'] == 'node123'
        assert result['title'] == 'Test Node'
        assert result['notecard'] == '[[node123 notecard.md]]'
        assert result['notes'] == '[[node123 notes.md]]'
        assert result['metadata'] == {'Custom': 'Some custom directive'}
        assert result['content'] == 'This is the content.'

    def test_parse_with_invalid_yaml(self) -> None:
        """Test parsing content with invalid YAML header."""
        content = """---
This is not valid YAML
---
Content after invalid header."""
        result = NodeParser.parse(content, 'fallback_id')
        # Should treat everything as content when YAML is invalid
        assert result['id'] == 'fallback_id'
        assert result['content'] == content

    def test_serialize_minimal(self) -> None:
        """Test serializing with minimal data."""
        node_data = {
            'id': 'node123',
            'title': 'Test Node',
        }
        result = NodeParser.serialize(node_data)
        assert '---' in result
        assert 'id: node123' in result
        assert 'title: Test Node' in result
        assert '// Notecard: [[node123 notecard.md]]' in result
        assert '// Notes: [[node123 notes.md]]' in result

    def test_serialize_complete(self) -> None:
        """Test serializing with complete data."""
        node_data = {
            'id': 'node123',
            'title': 'Test Node',
            'notecard': '[[node123 notecard.md]]',
            'notes': '[[node123 notes.md]]',
            'content': 'This is the content.',
            'metadata': {'custom_field': 'custom value'},
        }
        result = NodeParser.serialize(node_data)
        expected = textwrap.dedent(
            """\
            ---
            id: node123
            title: Test Node
            custom_field: custom value
            ---
            // Notecard: [[node123 notecard.md]]
            // Notes: [[node123 notes.md]]

            This is the content."""
        )
        assert result == expected

    def test_round_trip(self) -> None:
        """Test round-trip parsing and serializing."""
        original_content = """---
id: node123
title: Test Node
custom_field: custom value
---
// Notecard: [[node123 notecard.md]]
// Notes: [[node123 notes.md]]

# Test Node

This is the content."""

        # Parse the content
        parsed = NodeParser.parse(original_content)

        # Serialize it back
        serialized = NodeParser.serialize(parsed)

        # Parse again to compare
        reparsed = NodeParser.parse(serialized)

        # Check that the important fields match
        assert reparsed['id'] == parsed['id']
        assert reparsed['title'] == parsed['title']
        assert reparsed['notecard'] == parsed['notecard']
        assert reparsed['notes'] == parsed['notes']
        assert reparsed['content'] == parsed['content']
        assert reparsed['metadata'] == parsed['metadata']

    def test_process_directives(self) -> None:
        """Test processing directives separately."""
        content = """// Directive1: Value1
// Directive2: Value2

Content starts here."""

        content_lines, directives = NodeParser.process_directives(content)
        assert directives == {'Directive1': 'Value1', 'Directive2': 'Value2'}
        assert content_lines == ['Content starts here.']

    def test_process_directives_mixed(self) -> None:
        """Test processing mixed content with directives."""
        content = """// Directive1: Value1
Some text
// Directive2: Value2
More text"""

        content_lines, directives = NodeParser.process_directives(content)
        # Only the first directive should be processed
        assert directives == {'Directive1': 'Value1'}
        assert content_lines == ['Some text', '// Directive2: Value2', 'More text']

    def test_prepare_for_editor_minimal(self) -> None:
        """Test preparing minimal node data for editor."""
        from prosemark.domain.nodes import Node

        node = Node(
            id='node123',
            title='Test Node',
        )
        result = NodeParser.prepare_for_editor(node)
        expected = textwrap.dedent(
            """\
            id: node123
            title: Test Node

            // Notecard

            // Notes

            // Content"""
        )
        assert result == expected

    def test_prepare_for_editor_complete(self) -> None:
        """Test preparing complete node data for editor."""
        from prosemark.domain.nodes import Node

        node = Node(
            id='node123',
            title='Test Node',
            notecard='This is a notecard',
            notes='These are notes',
            content='This is the content',
            metadata={'custom_field': 'custom value'},
        )
        result = NodeParser.prepare_for_editor(node)
        expected = textwrap.dedent(
            """\
            id: node123
            title: Test Node
            custom_field: custom value

            // Notecard
            This is a notecard

            // Notes
            These are notes

            // Content
            This is the content"""
        )
        assert result == expected

    def test_parse_from_editor_minimal(self) -> None:
        """Test parsing minimal editor content."""
        content = """id: node123
title: Test Node

// Notecard

// Notes

// Content"""
        result = NodeParser.parse_from_editor('node123', content)
        assert result.id == 'node123'
        assert result.title == 'Test Node'
        assert result.notecard == ''
        assert result.notes == ''
        assert result.content == ''
        assert result.metadata == {}

    def test_parse_from_editor_complete(self) -> None:
        """Test parsing complete editor content."""
        content = """id: node123
title: Test Node
custom_field: custom value

// Notecard
This is a notecard

// Notes
These are notes

// Content
This is the content"""
        result = NodeParser.parse_from_editor('node123', content)
        assert result.id == 'node123'
        assert result.title == 'Test Node'
        assert result.notecard == 'This is a notecard'
        assert result.notes == 'These are notes'
        assert result.content == 'This is the content'
        assert result.metadata == {'custom_field': 'custom value'}

    def test_parse_from_editor_empty(self) -> None:
        """Test parsing empty editor content."""
        result = NodeParser.parse_from_editor('node123', '')
        assert result.id == 'node123'
        assert result.title == ''
        assert result.notecard == ''
        assert result.notes == ''
        assert result.content == ''
        assert result.metadata == {}

    def test_parse_from_editor_malformed(self) -> None:
        """Test parsing malformed editor content."""
        content = """id: node123
title: Test Node
// Notecard
This is a notecard
// Notes
These are notes
// Content
This is the content"""
        result = NodeParser.parse_from_editor('node123', content)
        assert result.id == 'node123'
        assert result.title == 'Test Node'
        assert result.notecard == 'This is a notecard'
        assert result.notes == 'These are notes'
        assert result.content == 'This is the content'
        assert result.metadata == {}

    def test_serialize_always_uses_wikilinks(self) -> None:
        """Test that notecards and notes are always serialized with wikilinks."""
        # Test with empty notecard and notes
        node_data = {
            'id': 'node123',
            'title': 'Test Node',
        }
        result = NodeParser.serialize(node_data)
        assert '// Notecard: [[node123 notecard.md]]' in result
        assert '// Notes: [[node123 notes.md]]' in result

        # Test with non-empty notecard and notes
        node_data = {
            'id': 'node123',
            'title': 'Test Node',
            'notecard': 'Some notecard content',
            'notes': 'Some notes content',
        }
        result = NodeParser.serialize(node_data)
        assert '// Notecard: [[node123 notecard.md]]' in result
        assert '// Notes: [[node123 notes.md]]' in result

        # Test with wikilink format notecard and notes
        node_data = {
            'id': 'node123',
            'title': 'Test Node',
            'notecard': '[[node123 notecard.md]]',
            'notes': '[[node123 notes.md]]',
        }
        result = NodeParser.serialize(node_data)
        assert '// Notecard: [[node123 notecard.md]]' in result
        assert '// Notes: [[node123 notes.md]]' in result
