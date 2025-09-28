"""Integration test for end-to-end workflow scenario.

This test validates the complete workflow from the quickstart guide
including project creation, binder operations, and text preservation.
"""

import tempfile
from pathlib import Path

from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser


class TestEndToEndWorkflowIntegration:
    """Integration test for complete end-to-end workflow."""

    def test_end_to_end_workflow_simulation(self) -> None:
        """Test complete workflow simulation from quickstart guide.

        This test should initially fail until the enhanced parser is implemented.
        """
        # Quickstart scenario: End-to-End Workflow Test
        outline_content = """**The Lost Fleet Chronicles**
An epic space opera exploring themes of loyalty, sacrifice, and redemption.

- [Book I: Return of the Exile](book1-uuid.md)

  Director Kolteo's story begins here.

  - [Part I: The Return](part1-uuid.md)
    **Everyday world, everyday conflict**
    The protagonist's normal life before the inciting incident.

    - [Chapter 1: The Director](01998718-2670-7879-81d4-8cd08c4bfe2f.md)

The story continues with more books and complexity..."""

        parser = MarkdownBinderParser()

        # Test the enhanced parsing functionality
        result = parser.parse_with_preservation(outline_content)

        # Verify narrative structure preservation
        assert result.binder is not None
        assert len(result.preserved_text) > 0

        # Test structural hierarchy parsing
        assert len(result.binder.roots) > 0

        # Confirm round-trip integrity
        assert result.parsing_metadata.original_line_count > 0

    def test_file_system_workflow(self) -> None:
        """Test workflow with actual file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            outline_file = temp_path / 'outline.md'

            # Create test binder file
            test_content = """**Project Overview**
This is a test project.

- [Chapter 1](01998718-2670-7879-81d4-8cd08c4bfe2f.md)

Final notes."""

            outline_file.write_text(test_content)

            # Test reading and parsing
            content = outline_file.read_text()
            parser = MarkdownBinderParser()

            # Current behavior test (will be enhanced later)
            binder = parser.parse_to_binder(content)
            rendered = parser.render_from_binder(binder)

            # Verify current structural parsing works
            assert len(binder.roots) == 1
            assert binder.roots[0].display_title == 'Chapter 1'

            # Write back to file (current behavior)
            outline_file.write_text(rendered)
            updated_content = outline_file.read_text()

            # Current behavior: only structural elements preserved
            assert '- [Chapter 1]' in updated_content
            # Note: Narrative text is currently lost in existing implementation

    def test_performance_with_large_binder(self) -> None:
        """Test performance with large binder structure."""
        # Create large binder content for performance testing
        large_content_parts = ['**Large Binder Test**\n\n']

        for i in range(50):  # Reduced from 100 for faster testing
            large_content_parts.extend((
                f'Narrative section {i}\n',
                f'- [Chapter {i}](0199871{i:04d}-2670-7879-81d4-8cd08c4bfe2f.md)\n',
                f'  Description for chapter {i}\n\n',
            ))

        large_content = ''.join(large_content_parts)

        parser = MarkdownBinderParser()

        # Test current parser performance
        import time

        start_time = time.time()
        binder = parser.parse_to_binder(large_content)
        parse_time = time.time() - start_time

        # Performance should be reasonable (under 1 second for 50 chapters)
        assert parse_time < 1.0

        # Verify structure was parsed correctly
        assert len(binder.roots) == 50

        # This test will be enhanced once enhanced parser is implemented
        # to test performance with text preservation
