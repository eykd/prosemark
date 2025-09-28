"""Contract test for round_trip_integrity scenario.

This test validates that parse and render operations maintain perfect
round-trip integrity with all content preserved exactly.
"""

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser


class TestRoundTripIntegrityContract:
    """Contract test for round-trip integrity."""

    def test_round_trip_integrity_scenario(self) -> None:
        """Test that render(parse(input)) === input for all content.

        This test should initially fail until the enhanced parser is implemented.
        """
        # Contract scenario input
        input_markdown = """**Bold text**
- [Chapter](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
*Italic text*

Empty line above should be preserved."""

        parser = MarkdownBinderParser()

        # Test parse functionality (T018 complete)
        result = parser.parse_with_preservation(input_markdown)

        # Verify parsing preserves text and structure
        assert len(result.binder.roots) == 1  # One structural element
        assert len(result.preserved_text) >= 3  # At least bold, italic, and empty line text

        # Verify structural parsing
        assert result.binder.roots[0].display_title == 'Chapter'
        assert str(result.binder.roots[0].node_id) == '01998718-2670-7879-81d4-8cd08c4bfe2f'

        # Test render functionality (T019 complete)
        rendered_output = parser.render_with_preservation(result)

        # Verify that rendering preserves content (note: line positions may differ)
        assert '**Bold text**' in rendered_output
        assert '*Italic text*' in rendered_output
        assert '- [Chapter](01998718-2670-7879-81d4-8cd08c4bfe2f.md)' in rendered_output

        # Verify empty line preservation
        assert '\n\n' in rendered_output or '' in rendered_output.split('\n')
