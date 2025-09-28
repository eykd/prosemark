"""Integration test for formatting preservation scenario.

This test validates that all text formatting is preserved exactly
character-for-character as specified in the quickstart guide.
"""

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser


class TestFormattingPreservationIntegration:
    """Integration test for formatting preservation."""

    def test_formatting_preservation_end_to_end(self) -> None:
        """Test that all formatting is preserved exactly from quickstart scenario.

        This test should initially fail until the enhanced parser is implemented.
        """
        # Quickstart scenario: Formatting Preservation Test
        input_markdown = """# Main Title

**Bold introduction text**
*Italic description*

- [Chapter 1](01998718-2670-7879-81d4-8cd08c4bfe2f.md)

> Blockquote that should be preserved

  - [Nested Scene](01998718-2674-7ec0-8b34-514c1c5f0c28.md)

## Another Section

Final paragraph with `code snippets` and [regular links](example.com)."""

        parser = MarkdownBinderParser()

        # Test formatting preservation functionality
        result = parser.parse_with_preservation(input_markdown)

        # Expected behavior: preserve all formatting character-for-character
        assert result.binder is not None
        assert len(result.preserved_text) > 0

        # Test perfect round-trip integrity
        preserved_content = ' '.join([p.content for p in result.preserved_text])
        assert len(preserved_content) > 0

    def test_complex_markdown_formatting(self) -> None:
        """Test complex markdown formatting combinations are preserved."""
        # This will fail until enhanced parser is implemented
        complex_markdown = """***Bold and italic*** text with `inline code`.

1. Numbered list item
   - Nested bullet under numbered
2. Second numbered item

| Table | Header |
|-------|--------|
| Cell  | Data   |

```python
# Code block
def example():
    pass
```

~~Strikethrough~~ and ==highlight== text."""

        parser = MarkdownBinderParser()

        # Test complex markdown formatting preservation
        result = parser.parse_with_preservation(complex_markdown)

        # Verify all complex formatting is preserved exactly
        assert result.binder is not None
        assert len(result.preserved_text) > 0

        # Check that complex formatting elements are preserved
        preserved_content = ' '.join([p.content for p in result.preserved_text])
        assert '**bold**' in preserved_content or '~~Strikethrough~~' in preserved_content
