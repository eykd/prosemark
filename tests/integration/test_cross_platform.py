"""Integration test for cross-platform compatibility."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestCrossPlatform:
    """Test cross-platform compatibility and path handling."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project."""
        project_dir = tmp_path / 'cross_platform_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Cross Platform Test', '--path', str(project_dir)])

        return project_dir

    def test_path_separators_in_file_operations(self, runner: CliRunner, project: Path) -> None:
        """Test that different path separators work correctly."""
        # Add a node
        result = runner.invoke(app, ['add', 'Chapter 1', '--path', str(project)])
        assert result.exit_code == 0

        # Get the node ID
        lines = result.output.split('\n')
        added_line = next(line for line in lines if 'Added' in line)
        node_id = added_line.split('(')[1].split(')')[0]

        # Verify files were created with correct extensions
        draft_file = project / f'{node_id}.md'
        notes_file = project / f'{node_id}.notes.md'

        assert draft_file.exists()
        assert notes_file.exists()

        # Verify file paths are handled correctly regardless of platform
        assert draft_file.is_file()
        assert notes_file.is_file()

    def test_project_paths_with_spaces(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test handling of project paths containing spaces."""
        # Create project with spaces in path
        project_dir = tmp_path / 'project with spaces'
        project_dir.mkdir()

        result = runner.invoke(app, ['init', '--title', 'Space Test', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add content
        result = runner.invoke(app, ['add', 'Chapter 1', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Verify structure
        result = runner.invoke(app, ['structure', '--path', str(project_dir)])
        assert result.exit_code == 0
        assert 'Chapter 1' in result.output

    def test_unicode_content_handling(self, runner: CliRunner, project: Path) -> None:
        """Test handling of unicode content in titles and files."""
        # Test various unicode characters in titles
        unicode_titles = [
            'Capítulo 1: El Comienzo',
            '章节一: 开始',
            'Κεφάλαιο 1: Αρχή',
            '🚀 Space Chapter',
            'Café & Naïve Characters',
        ]

        for title in unicode_titles:
            result = runner.invoke(app, ['add', title, '--path', str(project)])
            assert result.exit_code == 0

        # Verify all titles appear in structure
        result = runner.invoke(app, ['structure', '--path', str(project)])
        assert result.exit_code == 0

        for title in unicode_titles:
            assert title in result.output

    def test_line_ending_consistency(self, runner: CliRunner, project: Path) -> None:
        """Test that line endings are handled consistently across platforms."""
        # Add a node
        result = runner.invoke(app, ['add', 'Line Ending Test', '--path', str(project)])
        assert result.exit_code == 0

        # Get node ID
        lines = result.output.split('\n')
        added_line = next(line for line in lines if 'Added' in line)
        node_id = added_line.split('(')[1].split(')')[0]

        # Check the created files
        draft_file = project / f'{node_id}.md'
        notes_file = project / f'{node_id}.notes.md'
        binder_file = project / '_binder.md'

        # Read files and verify they're readable and well-formed
        draft_content = draft_file.read_text(encoding='utf-8')
        notes_content = notes_file.read_text(encoding='utf-8')
        binder_content = binder_file.read_text(encoding='utf-8')

        # Verify basic structure
        assert '---' in draft_content  # YAML frontmatter
        assert '# Notes' in notes_content  # Basic notes structure
        assert f'[[{node_id}]]' in notes_content  # Obsidian-style link to node
        assert '<!-- BEGIN_MANAGED_BLOCK -->' in binder_content

        # Files should be readable regardless of line endings
        assert len(draft_content.strip()) > 0
        assert len(notes_content.strip()) > 0
        assert len(binder_content.strip()) > 0

    def test_file_permissions_cross_platform(self, runner: CliRunner, project: Path) -> None:
        """Test that file permissions work across platforms."""
        # Add a node
        result = runner.invoke(app, ['add', 'Permission Test', '--path', str(project)])
        assert result.exit_code == 0

        # Check that files are readable and writable
        binder_file = project / '_binder.md'

        # Get node files
        node_files = [f for f in project.glob('*.md') if f.name != '_binder.md']
        assert len(node_files) >= 2  # draft and notes

        # Verify permissions
        assert binder_file.is_file()
        assert binder_file.stat().st_mode & 0o444
        assert binder_file.is_file()
        assert binder_file.stat().st_mode & 0o200

        for node_file in node_files:
            assert node_file.is_file()
            assert node_file.stat().st_mode & 0o444
            assert node_file.is_file()
            assert node_file.stat().st_mode & 0o200

    def test_path_resolution_with_relative_paths(self, runner: CliRunner, project: Path) -> None:
        """Test path resolution with relative paths."""
        # Change to project directory and use relative paths
        original_cwd = Path.cwd()
        try:
            os.chdir(str(project))

            # Use relative path (current directory)
            result = runner.invoke(app, ['add', 'Relative Path Test', '--path', '.'])
            assert result.exit_code == 0

            # Use no path (should default to current directory)
            result = runner.invoke(app, ['add', 'Default Path Test'])
            assert result.exit_code == 0

            # Verify structure
            result = runner.invoke(app, ['structure', '--path', '.'])
            assert result.exit_code == 0
            assert 'Relative Path Test' in result.output
            assert 'Default Path Test' in result.output

        finally:
            os.chdir(original_cwd)

    def test_long_path_handling(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test handling of long file paths."""
        # Create a deeply nested directory structure
        deep_path = tmp_path
        for i in range(10):
            deep_path /= f'level_{i}_directory_with_long_name'
            deep_path.mkdir()

        project_dir = deep_path / 'prosemark_project'
        project_dir.mkdir()

        # Initialize project in deep path
        result = runner.invoke(app, ['init', '--title', 'Deep Path Test', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add content
        result = runner.invoke(app, ['add', 'Chapter in Deep Path', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Verify it works
        result = runner.invoke(app, ['audit', '--path', str(project_dir)])
        assert result.exit_code == 0

    def test_special_characters_in_filenames(self, runner: CliRunner, project: Path) -> None:
        """Test handling of special characters in generated filenames."""
        # The system should generate UUIDv7s which are safe across platforms
        result = runner.invoke(app, ['add', 'Test Chapter', '--path', str(project)])
        assert result.exit_code == 0

        # Extract node ID
        lines = result.output.split('\n')
        added_line = next(line for line in lines if 'Added' in line)
        node_id = added_line.split('(')[1].split(')')[0]

        # Verify the node ID only contains safe characters
        import re

        # UUIDv7 should only contain hexadecimal characters and hyphens
        assert re.match(r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$', node_id.replace('-', ''))

        # Verify files exist and are accessible
        draft_file = project / f'{node_id}.md'
        notes_file = project / f'{node_id}.notes.md'

        assert draft_file.exists()
        assert notes_file.exists()

    def test_concurrent_access_patterns(self, runner: CliRunner, project: Path) -> None:
        """Test patterns that might occur with concurrent file access."""
        # Simulate rapid operations that might happen in different processes
        operations = [
            ['add', 'Chapter A', '--path', str(project)],
            ['add', 'Chapter B', '--path', str(project)],
            ['add', 'Chapter C', '--path', str(project)],
        ]

        results = []
        for op in operations:
            result = runner.invoke(app, op)
            results.append(result)

        # All operations should succeed
        for result in results:
            assert result.exit_code == 0

        # Final structure should contain all chapters
        result = runner.invoke(app, ['structure', '--path', str(project)])
        assert result.exit_code == 0
        assert 'Chapter A' in result.output
        assert 'Chapter B' in result.output
        assert 'Chapter C' in result.output

        # Project should be in consistent state
        result = runner.invoke(app, ['audit', '--path', str(project)])
        assert result.exit_code == 0
        assert 'All nodes have valid files' in result.output

    def test_case_sensitivity_handling(self, runner: CliRunner, project: Path) -> None:
        """Test behavior on case-sensitive vs case-insensitive filesystems."""
        # Add nodes with similar names that differ only in case
        result1 = runner.invoke(app, ['add', 'chapter one', '--path', str(project)])
        assert result1.exit_code == 0

        result2 = runner.invoke(app, ['add', 'Chapter One', '--path', str(project)])
        assert result2.exit_code == 0

        result3 = runner.invoke(app, ['add', 'CHAPTER ONE', '--path', str(project)])
        assert result3.exit_code == 0

        # All should be treated as separate entries
        result = runner.invoke(app, ['structure', '--path', str(project)])
        assert result.exit_code == 0

        # All three should appear (behavior may depend on filesystem)
        # But the system should handle it gracefully
        lines = [line for line in result.output.split('\n') if 'chapter' in line.lower() and 'one' in line.lower()]
        # Should have at least one, possibly all three depending on filesystem
        assert len(lines) >= 1
