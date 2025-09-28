"""Integration tests for structure command with node_id parameter.

These tests verify the end-to-end functionality of subtree display
with real binder files and complete CLI execution.
"""

import json
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app

runner = CliRunner()


class TestStructureIntegration:
    """Integration tests for structure command subtree functionality."""

    @pytest.fixture
    def test_project_dir(self) -> Generator[Path, None, None]:
        """Create a temporary project directory with binder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create a test binder file with known structure (matching prosemark format)
            binder_content = """# Project Structure

<!-- BEGIN_MANAGED_BLOCK -->
- [Book I: Return of the Exile](01996e70-e27d-7ada-908e-ef3b5ddb5223.md)
  - [I: Return of the Exile](01996e71-899f-7739-bf7d-bfb673837fcf.md)
    - [1. The Director](01997898-1dca-74d7-a727-b9a7023d0866.md)
      - [⇒ Academic—introducing Kolteo](01997898-1dcf-7bb2-806d-3c29d1ee5ed1.md)
      - [⇒ Kolteo—preparing to meet Julin](01997898-1dd1-719f-ad9f-ead37718612d.md)
    - [2. Confrontation in the Spaceport](01997898-1dda-740a-ae05-fef5b4f7d85b.md)
  - [II. Julin on the Run](01997898-1df4-7475-bb0f-9fbe31323555.md)
- [Book II: The Academy](01996e70-e27d-7ada-908e-ef3b5ddb5224.md)
  - [Chapter 1](01996e71-899f-7739-bf7d-bfb673837fd0.md)
<!-- END_MANAGED_BLOCK -->
"""
            binder_file = project_path / '_binder.md'
            binder_file.write_text(binder_content)

            yield project_path

    def test_full_tree_display_backward_compatibility(self, test_project_dir: Path) -> None:
        """Test that structure command without node_id shows full tree.

        Given: A project with binder containing multiple books and chapters
        When: structure command is run without node_id
        Then: Should display the entire tree structure
        """
        # Act
        result = runner.invoke(app, ['structure', '--path', str(test_project_dir)])

        # Assert
        assert result.exit_code == 0
        assert 'Project Structure:' in result.output
        # Should show both books
        assert 'Book I: Return of the Exile' in result.output
        assert 'Book II: The Academy' in result.output
        # Should show nested structure
        assert '1. The Director' in result.output
        assert 'Academic—introducing Kolteo' in result.output

    def test_subtree_display_with_valid_node_id(self, test_project_dir: Path) -> None:
        """Test subtree display with valid node_id.

        Given: A project with known node structure
        When: structure command is run with a chapter node_id
        Then: Should display only that chapter and its children
        """
        # Use the Director chapter node_id
        chapter_id = '01997898-1dca-74d7-a727-b9a7023d0866'

        # Act
        result = runner.invoke(app, ['structure', '--path', str(test_project_dir), chapter_id])

        # Assert
        assert result.exit_code == 0
        assert 'Project Structure:' in result.output
        # Should show the chapter
        assert '1. The Director' in result.output
        # Should show its children
        assert 'Academic—introducing Kolteo' in result.output
        assert 'Kolteo—preparing to meet Julin' in result.output
        # Should NOT show other chapters or books
        assert 'Book II' not in result.output
        assert 'Confrontation in the Spaceport' not in result.output

    def test_json_format_with_node_id(self, test_project_dir: Path) -> None:
        """Test JSON format output with node_id.

        Given: A project with known node structure
        When: structure command is run with node_id and --format json
        Then: Should output subtree in valid JSON format
        """
        # Use Book I node_id
        book_id = '01996e70-e27d-7ada-908e-ef3b5ddb5223'

        # Act
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(test_project_dir), book_id])

        # Assert
        assert result.exit_code == 0

        # Parse and validate JSON
        try:
            data = json.loads(result.output)
        except json.JSONDecodeError:
            pytest.fail(f'Output is not valid JSON: {result.output}')

        # Verify structure
        assert 'roots' in data or 'root' in data
        if 'roots' in data:
            assert len(data['roots']) > 0
            root = data['roots'][0]
        else:
            root = data['root']

        # Should contain the book
        assert 'Return of the Exile' in root.get('display_title', '')
        # Should have the correct node_id
        assert book_id in root.get('node_id', '')

    def test_error_handling_invalid_node_id(self, test_project_dir: Path) -> None:
        """Test error handling for invalid node_id format.

        Given: A project with valid binder
        When: structure command is run with invalid UUID format
        Then: Should show clear error message
        """
        # Act with invalid UUID format
        result = runner.invoke(app, ['structure', '--path', str(test_project_dir), 'not-a-uuid'])

        # Assert
        assert result.exit_code == 1
        assert 'Invalid' in result.output
        assert 'format' in result.output

    def test_error_handling_nonexistent_node_id(self, test_project_dir: Path) -> None:
        """Test error handling for non-existent node_id.

        Given: A project with valid binder
        When: structure command is run with valid UUID that doesn't exist
        Then: Should show node not found error
        """
        # Act with non-existent UUID
        nonexistent_uuid = '01996e70-aaaa-7ada-908e-ef3b5ddb5999'
        result = runner.invoke(app, ['structure', '--path', str(test_project_dir), nonexistent_uuid])

        # Assert
        assert result.exit_code == 1
        assert 'not found' in result.output.lower()
        assert nonexistent_uuid in result.output

    def test_empty_tree_handling(self) -> None:
        """Test handling of empty binder with and without node_id.

        Given: A project with empty binder
        When: structure command is run
        Then: Should show appropriate empty message
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create empty binder
            binder_file = project_path / '_binder.md'
            binder_file.write_text('# Project Structure\n\n<!-- BEGIN_MANAGED_BLOCK -->\n<!-- END_MANAGED_BLOCK -->\n')

            # Test without node_id
            result = runner.invoke(app, ['structure', '--path', str(project_path)])
            assert result.exit_code == 0
            assert 'Project Structure:' in result.output

            # Test with node_id (should still fail gracefully)
            result = runner.invoke(
                app, ['structure', '--path', str(project_path), '01996e70-aaaa-7ada-908e-ef3b5ddb5999']
            )
            assert result.exit_code == 1
            assert 'not found' in result.output.lower()

    def test_leaf_node_subtree_display(self, test_project_dir: Path) -> None:
        """Test subtree display for a leaf node with no children.

        Given: A project with known leaf nodes
        When: structure command is run with a leaf node_id
        Then: Should display only that single node
        """
        # Use a scene node_id (leaf)
        leaf_id = '01997898-1dcf-7bb2-806d-3c29d1ee5ed1'

        # Act
        result = runner.invoke(app, ['structure', '--path', str(test_project_dir), leaf_id])

        # Assert
        assert result.exit_code == 0
        assert 'Academic—introducing Kolteo' in result.output
        # Should not show siblings or parents
        assert 'preparing to meet Julin' not in result.output
        assert 'The Director' not in result.output
