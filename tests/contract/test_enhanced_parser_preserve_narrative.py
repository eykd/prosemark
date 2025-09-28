"""Contract test for preserve_narrative_text scenario.

This test validates that the enhanced parser preserves narrative text
while correctly parsing structural elements.
"""

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser


class TestPreserveNarrativeTextContract:
    """Contract test for narrative text preservation."""

    def test_preserve_narrative_text_scenario(self) -> None:
        """Test that narrative text is preserved alongside structural elements.

        This test should initially fail until the enhanced parser is implemented.
        """
        # Contract scenario input
        input_markdown = """**Act I**
Director Kolteo's story begins here.
- [Chapter 1](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
  Some descriptive text about the chapter.
  - [Scene 1](01998718-2674-7ec0-8b34-514c1c5f0c28.md)"""

        # Expected results from contract
        expected_preserved_count = 3  # "**Act I**", "Director Kolteo's story...", "Some descriptive text"

        parser = MarkdownBinderParser()

        # Test the enhanced parser implementation
        result = parser.parse_with_preservation(input_markdown)

        # Verify preserved text count and content
        assert len(result.preserved_text) == expected_preserved_count
        assert len(result.binder.roots) == 1  # One root chapter
        assert len(result.binder.roots[0].children) == 1  # One scene

        # Verify specific preserved text content
        preserved_contents = [pt.content for pt in result.preserved_text]
        assert preserved_contents[0] == '**Act I**'
        assert preserved_contents[1] == "Director Kolteo's story begins here."
        assert 'Some descriptive text about the chapter.' in preserved_contents[2]
