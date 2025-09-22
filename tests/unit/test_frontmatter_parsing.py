"""Unit tests for YAML frontmatter parsing."""

from datetime import datetime
from pathlib import Path

import pytest

from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.domain.entities import Node
from prosemark.domain.models import NodeId
from prosemark.exceptions import FileSystemError, FrontmatterFormatError


class TestFrontmatterParsing:
    """Test YAML frontmatter parsing functionality."""

    @pytest.fixture
    def codec(self) -> FrontmatterCodec:
        """Create a frontmatter codec instance."""
        return FrontmatterCodec()

    def test_parse_valid_frontmatter(self, codec: FrontmatterCodec) -> None:
        """Test parsing valid YAML frontmatter."""
        content = """---
id: 01234567-89ab-7def-8123-456789abcdef
title: "Test Chapter"
synopsis: |
  This is a multi-line synopsis
  that spans several lines
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:45:00Z
---

# Test Chapter

This is the content below the frontmatter.
"""

        metadata, body = codec.parse(content)

        assert metadata['id'] == '01234567-89ab-7def-8123-456789abcdef'
        assert metadata['title'] == 'Test Chapter'
        assert 'multi-line synopsis' in metadata['synopsis']
        assert metadata['created'] == '2025-09-20T15:30:00Z'
        assert metadata['updated'] == '2025-09-20T15:45:00Z'
        assert body == '# Test Chapter\n\nThis is the content below the frontmatter.\n'

    def test_parse_minimal_frontmatter(self, codec: FrontmatterCodec) -> None:
        """Test parsing minimal required frontmatter."""
        content = """---
id: 01234567-89ab-7def-8123-456789abcdef
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

Content only."""

        metadata, body = codec.parse(content)

        assert metadata['id'] == '01234567-89ab-7def-8123-456789abcdef'
        assert metadata['created'] == '2025-09-20T15:30:00Z'
        assert metadata['updated'] == '2025-09-20T15:30:00Z'
        assert body == 'Content only.'

    def test_parse_frontmatter_with_null_values(self, codec: FrontmatterCodec) -> None:
        """Test parsing frontmatter with null values."""
        content = """---
id: 01234567-89ab-7def-8123-456789abcdef
title: null
synopsis: null
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

Content."""

        metadata, _body = codec.parse(content)

        assert metadata['id'] == '01234567-89ab-7def-8123-456789abcdef'
        assert metadata['title'] is None
        assert metadata['synopsis'] is None

    def test_serialize_node_to_frontmatter(self, codec: FrontmatterCodec) -> None:
        """Test serializing a Node object to frontmatter."""
        from pathlib import Path

        node = Node(
            node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
            title='Test Node',
            synopsis='A test node for serialization',
            created=datetime.fromisoformat('2025-09-20T15:30:00+00:00'),
            updated=datetime.fromisoformat('2025-09-20T15:45:00+00:00'),
            draft_path=Path('01234567.md'),
            notes_path=Path('01234567.notes.md'),
        )

        body_content = '# Test Node\n\nNode content here.'
        frontmatter = {
            'id': str(node.id),
            'title': node.title,
            'synopsis': node.synopsis,
            'created': node.created.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'updated': node.updated.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        result = codec.generate(frontmatter, body_content)

        # Verify the structure
        assert result.startswith('---\n')
        assert 'id: 01234567-89ab-7def-8123-456789abcdef' in result
        assert 'title: Test Node' in result or 'title: "Test Node"' in result
        assert 'synopsis: A test node for serialization' in result
        # Accept both quoted and unquoted timestamp formats
        assert 'created: 2025-09-20T15:30:00Z' in result or "created: '2025-09-20T15:30:00Z'" in result
        assert 'updated: 2025-09-20T15:45:00Z' in result or "updated: '2025-09-20T15:45:00Z'" in result
        assert result.endswith('\n# Test Node\n\nNode content here.')

    def test_serialize_node_with_multiline_synopsis(self, codec: FrontmatterCodec) -> None:
        """Test serializing a node with multiline synopsis."""
        node = Node(
            node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
            title='Multiline Test',
            synopsis='Line 1\nLine 2\nLine 3',
            created=datetime.fromisoformat('2025-09-20T15:30:00+00:00'),
            updated=datetime.fromisoformat('2025-09-20T15:30:00+00:00'),
            draft_path=Path('01234567.md'),
            notes_path=Path('01234567.notes.md'),
        )

        frontmatter = {
            'id': str(node.id),
            'title': node.title,
            'synopsis': node.synopsis,
            'created': node.created.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'updated': node.updated.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        result = codec.generate(frontmatter, 'Content.')

        # Should use YAML literal block scalar for multiline or quoted strings
        assert (
            'synopsis: |\n' in result
            or 'synopsis: >\n' in result
            or ('synopsis:' in result and 'Line 1' in result and 'Line 2' in result and 'Line 3' in result)
        )
        assert 'Line 1' in result
        assert 'Line 2' in result
        assert 'Line 3' in result

    def test_serialize_node_with_null_fields(self, codec: FrontmatterCodec) -> None:
        """Test serializing a node with null optional fields."""
        from pathlib import Path

        node = Node(
            node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
            title=None,
            synopsis=None,
            created=datetime.fromisoformat('2025-09-20T15:30:00+00:00'),
            updated=datetime.fromisoformat('2025-09-20T15:30:00+00:00'),
            draft_path=Path('01234567-89ab-7def-8123-456789abcdef.md'),
            notes_path=Path('01234567-89ab-7def-8123-456789abcdef.notes.md'),
        )

        frontmatter = {
            'id': str(node.id),
            'title': node.title,
            'synopsis': node.synopsis,
            'created': node.created.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'updated': node.updated.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        result = codec.generate(frontmatter, 'Content.')

        assert 'title: null' in result or 'title:' in result
        assert 'synopsis: null' in result or 'synopsis:' in result

    def test_roundtrip_consistency(self, codec: FrontmatterCodec) -> None:
        """Test that parsing and serializing maintains consistency."""
        original_node = Node(
            node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
            title='Roundtrip Test',
            synopsis='A test of roundtrip consistency\nwith multiple lines',
            created=datetime.fromisoformat('2025-09-20T15:30:00+00:00'),
            updated=datetime.fromisoformat('2025-09-20T15:45:00+00:00'),
            draft_path=Path('01234567.md'),
            notes_path=Path('01234567.notes.md'),
        )

        body_content = '# Original Content\n\nWith some text.'

        # Serialize then parse
        frontmatter = {
            'id': str(original_node.id),
            'title': original_node.title,
            'synopsis': original_node.synopsis,
            'created': original_node.created.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'updated': original_node.updated.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        serialized = codec.generate(frontmatter, body_content)
        metadata, parsed_body = codec.parse(serialized)

        # Verify metadata roundtrip
        assert metadata['id'] == original_node.id.value
        assert metadata['title'] == original_node.title
        assert metadata['synopsis'] == original_node.synopsis
        assert metadata['created'] == '2025-09-20T15:30:00Z'
        assert metadata['updated'] == '2025-09-20T15:45:00Z'

        # Verify body roundtrip
        assert parsed_body == body_content

    def test_parse_invalid_yaml_frontmatter(self, codec: FrontmatterCodec) -> None:
        """Test handling of invalid YAML in frontmatter."""
        invalid_contents = [
            """---
id: 01234567-89ab-7def-8123-456789abcdef
title: "Unterminated quote
created: 2025-09-20T15:30:00Z
---
Content.""",
            """---
id: [invalid: yaml: structure
created: 2025-09-20T15:30:00Z
---
Content.""",
            """---
- this
- is
- a
- list
- not
- a
- mapping
---
Content.""",
        ]

        for content in invalid_contents:
            with pytest.raises((FileSystemError, Exception)):
                codec.parse(content)

    def test_parse_missing_frontmatter_delimiters(self, codec: FrontmatterCodec) -> None:
        """Test handling content without proper frontmatter delimiters."""
        # Content with no frontmatter should be valid
        valid_content = 'No frontmatter at all'
        frontmatter, remaining = codec.parse(valid_content)
        assert frontmatter == {}
        assert remaining == valid_content

        # Content with malformed frontmatter delimiters should raise exceptions
        invalid_contents = [
            """---
id: test
No closing delimiter""",
            """id: test
---
Missing opening delimiter""",
            """
---
---
Empty frontmatter with content below.""",
        ]

        for content in invalid_contents:
            with pytest.raises((FrontmatterFormatError, FileSystemError, Exception)):
                codec.parse(content)

    def test_parse_frontmatter_with_special_characters(self, codec: FrontmatterCodec) -> None:
        """Test parsing frontmatter containing special characters."""
        content = """---
id: 01234567-89ab-7def-8123-456789abcdef
title: 'Title with "quotes" and ''apostrophes'''
synopsis: |
  Synopsis with special chars: @#$%^&*()
  And unicode: café naïve résumé 中文 🚀
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

Content with special chars."""

        metadata, _body = codec.parse(content)

        assert 'quotes' in metadata['title']
        assert 'apostrophes' in metadata['title']
        assert '@#$%^&*()' in metadata['synopsis']
        assert 'café naïve résumé 中文 🚀' in metadata['synopsis']

    def test_preserve_unknown_frontmatter_fields(self, codec: FrontmatterCodec) -> None:
        """Test that unknown frontmatter fields are preserved."""
        content = """---
id: 01234567-89ab-7def-8123-456789abcdef
title: "Test"
custom_field: "custom value"
tags:
  - fiction
  - draft
word_count: 1500
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

Content."""

        metadata, _body = codec.parse(content)

        # Known fields should be parsed
        assert metadata['id'] == '01234567-89ab-7def-8123-456789abcdef'
        assert metadata['title'] == 'Test'

        # Unknown fields should be preserved
        assert metadata['custom_field'] == 'custom value'
        assert metadata['tags'] == ['fiction', 'draft']
        assert metadata['word_count'] == 1500

    def test_datetime_format_consistency(self, codec: FrontmatterCodec) -> None:
        """Test that datetime formatting is consistent."""
        # Test various datetime formats
        datetime_formats = [
            '2025-09-20T15:30:00Z',
            '2025-09-20T15:30:00.000Z',
            '2025-09-20T15:30:00+00:00',
        ]

        for dt_format in datetime_formats:
            content = f"""---
id: 01234567-89ab-7def-8123-456789abcdef
created: {dt_format}
updated: {dt_format}
---
Content."""

            metadata, _ = codec.parse(content)

            # Should parse successfully
            assert 'created' in metadata
            assert 'updated' in metadata

    def test_empty_body_handling(self, codec: FrontmatterCodec) -> None:
        """Test handling of files with only frontmatter."""
        content = """---
id: 01234567-89ab-7def-8123-456789abcdef
title: "Empty Body Test"
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---"""

        metadata, body = codec.parse(content)

        assert metadata['id'] == '01234567-89ab-7def-8123-456789abcdef'
        assert body == ''

    def test_whitespace_preservation_in_body(self, codec: FrontmatterCodec) -> None:
        """Test that whitespace in body content is preserved."""
        content = """---
id: 01234567-89ab-7def-8123-456789abcdef
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Title

Paragraph 1

    Indented content

Paragraph 2
    With mixed indentation

Final line"""

        _metadata, body = codec.parse(content)

        # Whitespace should be preserved exactly
        assert '    Indented content' in body
        assert '    With mixed indentation' in body
        assert body.endswith('Final line')

    def test_large_content_handling(self, codec: FrontmatterCodec) -> None:
        """Test handling of large content files."""
        # Create large body content
        large_body = '# Large Content\n\n' + ('This is a test line.\n' * 1000)

        content = f"""---
id: 01234567-89ab-7def-8123-456789abcdef
title: "Large Content Test"
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

{large_body}"""

        metadata, body = codec.parse(content)

        assert metadata['title'] == 'Large Content Test'
        assert len(body) > 10000  # Should handle large content
        assert body.count('This is a test line.') == 1000
