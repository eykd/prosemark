"""Tests for the YAML frontmatter codec."""

from typing import Any

import pytest

from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.exceptions import FrontmatterFormatError


class TestFrontmatterCodec:
    """Test the FrontmatterCodec adapter."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.codec = FrontmatterCodec()

    def test_parse_content_without_frontmatter(self) -> None:
        """Test parsing content without frontmatter."""
        content = '# Hello World\n\nThis is content without frontmatter.'

        frontmatter, remaining = self.codec.parse(content)

        assert frontmatter == {}
        assert remaining == content

    def test_parse_content_with_valid_frontmatter(self) -> None:
        """Test parsing content with valid frontmatter."""
        content = """---
title: Test Document
author: Test Author
draft: true
---
# Hello World

This is the content."""

        frontmatter, remaining = self.codec.parse(content)

        assert frontmatter == {'title': 'Test Document', 'author': 'Test Author', 'draft': True}
        assert remaining == '# Hello World\n\nThis is the content.'

    def test_parse_content_with_empty_frontmatter(self) -> None:
        """Test parsing content with empty frontmatter block."""
        content = """---
---
# Hello World

This is the content."""

        frontmatter, remaining = self.codec.parse(content)

        # Empty frontmatter blocks don't match the regex pattern, so whole content is returned
        assert frontmatter == {}
        assert remaining == content

    def test_parse_content_with_null_frontmatter(self) -> None:
        """Test parsing content with null YAML frontmatter."""
        content = """---
null
---
# Hello World

This is the content."""

        frontmatter, remaining = self.codec.parse(content)

        assert frontmatter == {}
        assert remaining == '# Hello World\n\nThis is the content.'

    def test_parse_content_with_non_dict_frontmatter_raises_error(self) -> None:
        """Test parsing content with non-dictionary frontmatter raises error."""
        content = """---
- item1
- item2
---
# Hello World"""

        with pytest.raises(FrontmatterFormatError, match='Frontmatter must be a YAML mapping/dictionary'):
            self.codec.parse(content)

    def test_parse_content_with_invalid_yaml_raises_error(self) -> None:
        """Test parsing content with invalid YAML raises error."""
        content = """---
title: [invalid yaml
author: missing bracket
---
# Hello World"""

        with pytest.raises(FrontmatterFormatError, match='Invalid YAML in frontmatter block'):
            self.codec.parse(content)

    def test_parse_content_with_windows_line_endings(self) -> None:
        """Test parsing content with Windows CRLF line endings."""
        content = '---\r\ntitle: Test\r\n---\r\n# Content'

        frontmatter, remaining = self.codec.parse(content)

        assert frontmatter == {'title': 'Test'}
        assert remaining == '# Content'

    def test_generate_with_empty_frontmatter(self) -> None:
        """Test generating content with empty frontmatter."""
        frontmatter: dict[str, Any] = {}
        content = '# Hello World\n\nThis is content.'

        result = self.codec.generate(frontmatter, content)

        assert result == content

    def test_generate_with_valid_frontmatter(self) -> None:
        """Test generating content with valid frontmatter."""
        frontmatter = {'title': 'Test Document', 'author': 'Test Author', 'draft': True}
        content = '# Hello World\n\nThis is content.'

        result = self.codec.generate(frontmatter, content)

        expected = """---
author: Test Author
draft: true
title: Test Document
---
# Hello World

This is content."""
        assert result == expected

    def test_generate_with_none_frontmatter(self) -> None:
        """Test generating content with None as frontmatter."""
        frontmatter = None
        content = '# Hello World'

        # This tests the truthiness check: if not frontmatter
        result = self.codec.generate(frontmatter, content)  # type: ignore[arg-type]

        assert result == content

    def test_generate_with_unicode_content(self) -> None:
        """Test generating content with Unicode characters."""
        frontmatter = {'title': 'Tëst Dócümënt', 'emoji': '🎉'}
        content = '# Hello 世界'

        result = self.codec.generate(frontmatter, content)

        assert '🎉' in result
        assert 'Tëst Dócümënt' in result
        assert '世界' in result

    def test_generate_with_unserializable_frontmatter_raises_error(self) -> None:
        """Test generating content with unserializable frontmatter raises error."""

        # Create an object that can't be serialized to YAML
        class UnserializableObject:
            def __reduce__(self) -> str:
                raise TypeError('Cannot serialize this object')

        frontmatter = {'bad_object': UnserializableObject()}
        content = '# Test'

        with pytest.raises(FrontmatterFormatError, match='Failed to serialize frontmatter to YAML'):
            self.codec.generate(frontmatter, content)

    def test_update_frontmatter_on_content_without_existing_frontmatter(self) -> None:
        """Test updating frontmatter on content without existing frontmatter."""
        content = '# Hello World\n\nThis is content.'
        updates = {'title': 'New Title', 'draft': False}

        result = self.codec.update_frontmatter(content, updates)

        expected = """---
draft: false
title: New Title
---
# Hello World

This is content."""
        assert result == expected

    def test_update_frontmatter_on_content_with_existing_frontmatter(self) -> None:
        """Test updating frontmatter on content with existing frontmatter."""
        content = """---
title: Old Title
author: Test Author
---
# Hello World

This is content."""

        updates = {'title': 'New Title', 'draft': True}

        result = self.codec.update_frontmatter(content, updates)

        expected = """---
author: Test Author
draft: true
title: New Title
---
# Hello World

This is content."""
        assert result == expected

    def test_update_frontmatter_with_empty_updates(self) -> None:
        """Test updating frontmatter with empty updates dictionary."""
        content = """---
title: Existing Title
---
# Content"""

        updates: dict[str, Any] = {}

        result = self.codec.update_frontmatter(content, updates)

        # Should preserve existing frontmatter
        assert 'title: Existing Title' in result
        assert '# Content' in result

    def test_update_frontmatter_removes_fields_with_none_values(self) -> None:
        """Test that update_frontmatter properly handles None values."""
        content = """---
title: Existing Title
author: Existing Author
---
# Content"""

        # Update with None value should overwrite the existing value
        updates = {'author': None, 'new_field': 'new_value'}

        result = self.codec.update_frontmatter(content, updates)

        assert 'new_field: new_value' in result
        assert 'author: null' in result or 'author:' in result

    def test_frontmatter_pattern_regex(self) -> None:
        """Test the frontmatter pattern regex directly."""
        # Test the regex pattern matches frontmatter correctly
        pattern = FrontmatterCodec.FRONTMATTER_PATTERN

        # Valid frontmatter
        content1 = '---\ntitle: test\n---\ncontent'
        match1 = pattern.match(content1)
        assert match1 is not None
        assert match1.group(1) == 'title: test'
        assert match1.group(2) == 'content'

        # No frontmatter
        content2 = 'just content'
        match2 = pattern.match(content2)
        assert match2 is None

        # Frontmatter not at start
        content3 = 'some text\n---\ntitle: test\n---\ncontent'
        match3 = pattern.match(content3)
        assert match3 is None

    def test_parse_and_generate_roundtrip(self) -> None:
        """Test that parse and generate operations are reversible."""
        original_content = """---
title: Test Document
tags:
  - test
  - markdown
count: 42
---
# Hello World

This is some content with **bold** text."""

        # Parse the original content
        frontmatter, content = self.codec.parse(original_content)

        # Generate content from parsed data
        regenerated = self.codec.generate(frontmatter, content)

        # Parse the regenerated content
        parsed_frontmatter, parsed_content = self.codec.parse(regenerated)

        # Should match original parsed data
        assert parsed_frontmatter == frontmatter
        assert parsed_content == content

    def test_check_misplaced_frontmatter_with_valid_divider(self) -> None:
        """Test _check_misplaced_frontmatter when content has valid divider."""
        # Content with --- in middle but no frontmatter-like content before it
        # This should hit line 134 (break) without raising errors
        content = 'Some content\n---\nMore content'

        # This should not raise an error and should complete normally
        # Test through the public parse method
        frontmatter, remaining = self.codec.parse(content)
        assert frontmatter == {}
        assert remaining == content

    def test_check_misplaced_frontmatter_with_no_dividers(self) -> None:
        """Test _check_misplaced_frontmatter when no dividers found."""
        # Content with no --- lines, should hit the for loop exit (126->exit)
        content = 'Some content without any dividers\nJust plain text'

        # This should not raise an error and should complete normally
        # Test through the public parse method
        frontmatter, remaining = self.codec.parse(content)
        assert frontmatter == {}
        assert remaining == content

    def test_check_misplaced_frontmatter_with_embedded_dashes(self) -> None:
        """Test _check_misplaced_frontmatter when --- appears as part of content but not as separator."""
        # Content with --- embedded in text but no standalone --- lines
        # This should hit the for loop exit (126->exit) since no line.strip() == '---'
        content = 'Some content with embedded --- dashes\nAnother line with ---more dashes'

        # This should not raise an error and should complete normally
        # Test through the public parse method
        frontmatter, remaining = self.codec.parse(content)
        assert frontmatter == {}
        assert remaining == content
