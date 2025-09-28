"""Contract test for handle_malformed_syntax scenario.

This test validates that malformed structural elements are treated as
extraneous text while valid elements are processed normally.
"""

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser


class TestHandleMalformedSyntaxContract:
    """Contract test for malformed syntax handling."""

    def test_handle_malformed_syntax_scenario(self) -> None:
        """Test that malformed structural elements are preserved as extraneous text.

        This test should initially fail until the enhanced parser is implemented.
        """
        # Contract scenario input
        input_markdown = """- [Broken link(missing-closing-bracket.md)
- [Valid link](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
- Malformed list item without brackets"""

        # Expected results from contract
        expected_preserved_count = 2  # Malformed elements treated as text
        expected_structural_count = 1  # Only valid list item

        parser = MarkdownBinderParser()

        # Test the enhanced parser implementation
        result = parser.parse_with_preservation(input_markdown)

        # Verify malformed syntax handling
        assert len(result.preserved_text) == expected_preserved_count
        assert len(result.binder.roots) == expected_structural_count

        # Verify malformed elements are preserved
        preserved_contents = [pt.content for pt in result.preserved_text]
        assert '- [Broken link(missing-closing-bracket.md)' in preserved_contents
        assert '- Malformed list item without brackets' in preserved_contents

        # Verify valid link is parsed structurally
        assert result.binder.roots[0].display_title == 'Valid link'
        assert str(result.binder.roots[0].node_id) == '01998718-2670-7879-81d4-8cd08c4bfe2f'
