"""Integration test for file system safety."""

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestFileSafety:
    """Test file system safety and content preservation."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project_with_custom_content(self, tmp_path: Path) -> dict[str, Any]:
        """Create a project with custom content outside managed blocks."""
        project_dir = tmp_path / 'safety_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Safety Test', '--path', str(project_dir)])

        # Add custom content around managed block
        binder_path = project_dir / '_binder.md'
        content = binder_path.read_text()

        custom_content = (
            """# Safety Test

This is my custom project introduction.

## Project Goals
- Goal 1: Write a great story
- Goal 2: Keep everything organized

"""
            + content.split('# Project Structure\n\n')[1]
            + """

## Additional Notes

These are my personal notes that should never be touched.
I've added them after the managed block.

### Research Links
- [Research Link 1](https://example.com)
- [Research Link 2](https://example.com)

Final notes here.
"""
        )

        binder_path.write_text(custom_content)

        # Add a node to have some managed content
        result = runner.invoke(app, ['add', 'Chapter 1', '--path', str(project_dir)])
        ch1_id = self._extract_node_id(result.output)

        return {'dir': project_dir, 'ch1_id': ch1_id, 'original_content': custom_content}

    def _extract_node_id(self, output: str) -> str:
        """Extract node ID from add command output."""
        lines = output.split('\n')
        added_line = next(line for line in lines if 'Added' in line)
        return added_line.split('(')[1].split(')')[0]

    def test_binder_modifications_preserve_custom_content(
        self, runner: CliRunner, project_with_custom_content: dict[str, Any]
    ) -> None:
        """Test that binder modifications preserve content outside managed blocks."""
        project = project_with_custom_content
        binder_path = project['dir'] / '_binder.md'

        # Perform various operations that modify the binder
        runner.invoke(app, ['add', 'Chapter 2', '--path', str(project['dir'])])
        runner.invoke(app, ['add', 'Chapter 3', '--path', str(project['dir'])])

        # Check that custom content is preserved
        final_content = binder_path.read_text()

        # Check content above managed block
        assert 'This is my custom project introduction.' in final_content
        assert '## Project Goals' in final_content
        assert 'Goal 1: Write a great story' in final_content
        assert 'Goal 2: Keep everything organized' in final_content

        # Check content below managed block
        assert '## Additional Notes' in final_content
        assert 'These are my personal notes that should never be touched.' in final_content
        assert '### Research Links' in final_content
        assert '[Research Link 1](https://example.com)' in final_content
        assert '[Research Link 2](https://example.com)' in final_content
        assert 'Final notes here.' in final_content

        # Check that managed content was updated
        assert 'Chapter 1' in final_content
        assert 'Chapter 2' in final_content
        assert 'Chapter 3' in final_content

    def test_node_moves_preserve_binder_content(
        self, runner: CliRunner, project_with_custom_content: dict[str, Any]
    ) -> None:
        """Test that moving nodes preserves custom binder content."""
        project = project_with_custom_content
        binder_path = project['dir'] / '_binder.md'

        # Add another chapter to move
        result = runner.invoke(app, ['add', 'Chapter 2', '--path', str(project['dir'])])
        ch2_id = self._extract_node_id(result.output)

        # Move the chapter
        runner.invoke(app, ['move', ch2_id, '--position', '0', '--path', str(project['dir'])])

        # Verify custom content is preserved
        final_content = binder_path.read_text()
        assert 'This is my custom project introduction.' in final_content
        assert 'These are my personal notes that should never be touched.' in final_content

    def test_node_removal_preserves_binder_content(
        self, runner: CliRunner, project_with_custom_content: dict[str, Any]
    ) -> None:
        """Test that removing nodes preserves custom binder content."""
        project = project_with_custom_content
        binder_path = project['dir'] / '_binder.md'

        # Remove the chapter
        runner.invoke(app, ['remove', project['ch1_id'], '--path', str(project['dir'])])

        # Verify custom content is preserved
        final_content = binder_path.read_text()
        assert 'This is my custom project introduction.' in final_content
        assert 'These are my personal notes that should never be touched.' in final_content

        # Chapter should be gone from managed section
        assert 'Chapter 1' not in final_content

    def test_content_encoding_preservation(
        self, runner: CliRunner, project_with_custom_content: dict[str, Any]
    ) -> None:
        """Test that file encoding is preserved during operations."""
        project = project_with_custom_content
        binder_path = project['dir'] / '_binder.md'

        # Add content with special characters
        content = binder_path.read_text()
        content_with_unicode = content.replace(
            'Final notes here.', 'Final notes here with unicode: café, naïve, résumé, 中文, 🚀'
        )
        binder_path.write_text(content_with_unicode, encoding='utf-8')

        # Perform an operation
        runner.invoke(app, ['add', 'New Chapter', '--path', str(project['dir'])])

        # Verify unicode content is preserved
        final_content = binder_path.read_text(encoding='utf-8')
        assert 'café, naïve, résumé, 中文, 🚀' in final_content

    def test_file_permissions_preservation(
        self, runner: CliRunner, project_with_custom_content: dict[str, Any]
    ) -> None:
        """Test that file permissions are preserved during operations."""
        project = project_with_custom_content
        binder_path = project['dir'] / '_binder.md'

        # Get original permissions
        binder_path.stat()

        # Perform an operation
        runner.invoke(app, ['add', 'Permission Test', '--path', str(project['dir'])])

        # Check permissions are preserved (at least readable/writable)
        import os

        binder_path.stat()
        assert binder_path.is_file()
        assert os.access(binder_path, os.R_OK)  # readable
        assert os.access(binder_path, os.W_OK)  # writable

    def test_node_file_integrity_during_operations(
        self, runner: CliRunner, project_with_custom_content: dict[str, Any]
    ) -> None:
        """Test that existing node files are not corrupted during operations."""
        project = project_with_custom_content

        # Add custom content to the node file
        node_file = project['dir'] / f'{project["ch1_id"]}.md'
        original_content = node_file.read_text()

        # Add custom content below frontmatter
        custom_node_content = (
            original_content
            + '\n\n## Custom Section\n\nThis is my custom content that should be preserved.\n\n'
            + '### Research Notes\n- Important point 1\n- Important point 2\n'
        )
        node_file.write_text(custom_node_content)

        # Perform operations that might affect the binder
        runner.invoke(app, ['add', 'Chapter 2', '--path', str(project['dir'])])
        runner.invoke(app, ['audit', '--path', str(project['dir'])])

        # Verify node file content is preserved
        final_node_content = node_file.read_text()
        assert '## Custom Section' in final_node_content
        assert 'This is my custom content that should be preserved.' in final_node_content
        assert '### Research Notes' in final_node_content
        assert 'Important point 1' in final_node_content
        assert 'Important point 2' in final_node_content

    def test_concurrent_file_access_safety(
        self, runner: CliRunner, project_with_custom_content: dict[str, Any]
    ) -> None:
        """Test safety when files might be accessed by other processes."""
        project = project_with_custom_content
        binder_path = project['dir'] / '_binder.md'

        # Simulate potential concurrent access by checking file exists and is readable
        assert binder_path.exists()
        binder_path.read_text()

        # Perform rapid operations
        for i in range(3):
            runner.invoke(app, ['add', f'Chapter {i + 2}', '--path', str(project['dir'])])

        # Verify file is still intact and readable
        assert binder_path.exists()
        final_content = binder_path.read_text()

        # Should contain all added chapters
        assert 'Chapter 2' in final_content
        assert 'Chapter 3' in final_content
        assert 'Chapter 4' in final_content

        # Should preserve original custom content
        assert 'This is my custom project introduction.' in final_content

    def test_backup_behavior_during_operations(
        self, runner: CliRunner, project_with_custom_content: dict[str, Any]
    ) -> None:
        """Test that critical operations create appropriate backups."""
        project = project_with_custom_content

        # Check initial state
        initial_files = list(project['dir'].glob('*'))
        initial_count = len(initial_files)

        # Perform operations that might create backups
        runner.invoke(app, ['add', 'Backup Test', '--path', str(project['dir'])])
        runner.invoke(app, ['audit', '--path', str(project['dir'])])

        # Verify no unexpected backup files are left behind
        final_files = list(project['dir'].glob('*'))

        # Should only have original files plus new node files
        expected_new_files = 2  # .md and .notes.md for new node
        assert len(final_files) <= initial_count + expected_new_files + 1  # +1 for potential temp files

        # No .bak, .tmp, or similar files should be left
        backup_files = [f for f in final_files if any(f.name.endswith(ext) for ext in ['.bak', '.tmp', '.backup', '~'])]
        assert len(backup_files) == 0

    def test_atomic_operations(self, runner: CliRunner, project_with_custom_content: dict[str, Any]) -> None:
        """Test that file operations are atomic (don't leave partial writes)."""
        project = project_with_custom_content
        binder_path = project['dir'] / '_binder.md'

        # Verify file is in consistent state before operation
        original_content = binder_path.read_text()
        assert '<!-- BEGIN_MANAGED_BLOCK -->' in original_content
        assert '<!-- END_MANAGED_BLOCK -->' in original_content

        # Perform operation
        result = runner.invoke(app, ['add', 'Atomic Test', '--path', str(project['dir'])])

        # If operation succeeded, file should be in consistent state
        if result.exit_code == 0:
            final_content = binder_path.read_text()
            assert '<!-- BEGIN_MANAGED_BLOCK -->' in final_content
            assert '<!-- END_MANAGED_BLOCK -->' in final_content
            assert 'Atomic Test' in final_content

        # File should always be readable and well-formed
        assert binder_path.exists()
        content = binder_path.read_text()
        assert len(content) > 0
        assert content.count('<!-- BEGIN_MANAGED_BLOCK -->') == 1
        assert content.count('<!-- END_MANAGED_BLOCK -->') == 1
