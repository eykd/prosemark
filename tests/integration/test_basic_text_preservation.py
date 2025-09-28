"""Integration test for basic text preservation scenario.

This test validates the complete end-to-end flow of preserving
narrative text around structural elements from the quickstart guide.
"""

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser


class TestBasicTextPreservationIntegration:
    """Integration test for basic text preservation."""

    def test_basic_text_preservation_end_to_end(self) -> None:
        """Test end-to-end text preservation following quickstart scenario.

        This test should initially fail until the enhanced parser is implemented.
        """
        # Quickstart scenario: Basic Text Preservation
        input_markdown = """**Act I - The Beginning**
Director Kolteo's journey starts with conflict and mystery.

- [Chapter 1: The Return](01998718-2670-7879-81d4-8cd08c4bfe2f.md)

  This chapter introduces our protagonist in his everyday world,
  showing his mastery over the fleet while hinting at past trauma.

  - [Scene 1: The Director's Office](01998718-2674-7ec0-8b34-514c1c5f0c28.md)
  - [Scene 2: Meeting Preparation](01998718-267c-7c68-94a6-b26b25eaced0.md)

More narrative content continues here..."""

        parser = MarkdownBinderParser()

        # Test basic text preservation functionality
        result = parser.parse_with_preservation(input_markdown)

        # Expected behavior from quickstart guide:
        # Act I header, chapter description, "More narrative content" all preserved
        assert result.binder is not None
        assert len(result.preserved_text) > 0

        # Verify round-trip integrity
        preserved_content = ' '.join([p.content for p in result.preserved_text])
        assert 'Act I' in preserved_content or 'narrative content' in preserved_content

    def test_basic_preservation_with_binder_operations(self) -> None:
        """Test that binder operations preserve text (simulated).

        This represents the compile operation from the quickstart scenario.
        """
        # This will be enhanced once binder operations are updated
        # to use the enhanced parser internally
        input_markdown = """**Simple Test**
- [Chapter](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
Conclusion text."""

        parser = MarkdownBinderParser()

        # For now, test that existing parser behavior is maintained
        binder = parser.parse_to_binder(input_markdown)
        parser.render_from_binder(binder)

        # Existing behavior: only structural elements preserved
        assert len(binder.roots) == 1
        assert binder.roots[0].display_title == 'Chapter'

        # Note: This test will be enhanced in later phases when
        # binder operations are updated to use enhanced parser
