"""Contract test for validate_uuid7_links scenario.

This test validates that only valid UUID7 links are treated as structural
elements, with non-UUID7 links preserved as extraneous text.
"""

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser


class TestValidateUuid7LinksContract:
    """Contract test for UUID7 link validation."""

    def test_validate_uuid7_links_scenario(self) -> None:
        """Test that only valid UUID7 links are treated as structural elements.

        This test should initially fail until the enhanced parser is implemented.
        """
        # Contract scenario input
        input_markdown = """- [UUID7 link](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
- [Non-UUID link](some-other-file.md)
- [Invalid UUID](12345-invalid-uuid.md)"""

        # Expected results from contract
        expected_structural_count = 1  # Only UUID7 link is structural
        expected_preserved_count = 2  # Non-UUID7 links treated as extraneous

        parser = MarkdownBinderParser()

        # Test the enhanced parser implementation
        result = parser.parse_with_preservation(input_markdown)

        # Verify UUID7 validation
        assert len(result.binder.roots) == expected_structural_count
        assert len(result.preserved_text) == expected_preserved_count

        # Verify only UUID7 link is structural
        assert result.binder.roots[0].display_title == 'UUID7 link'
        assert str(result.binder.roots[0].node_id) == '01998718-2670-7879-81d4-8cd08c4bfe2f'

        # Verify non-UUID7 links are preserved as text
        preserved_contents = [pt.content for pt in result.preserved_text]
        assert '- [Non-UUID link](some-other-file.md)' in preserved_contents
        assert '- [Invalid UUID](12345-invalid-uuid.md)' in preserved_contents
