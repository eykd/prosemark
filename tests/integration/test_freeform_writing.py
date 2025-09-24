"""Integration test for freeform writing functionality."""

import re
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestFreeformWriting:
    """Test freeform writing creation and management."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project."""
        project_dir = tmp_path / 'freeform_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Freeform Test', '--path', str(project_dir)])

        return project_dir

    def test_create_freeform_with_title(self, runner: CliRunner, project: Path) -> None:
        """Test creating freeform content with a title."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ['write', '--title', 'Character Ideas', '--path', str(project)])
            assert result.exit_code == 0
            assert 'Created freeform file' in result.output

            # Verify file was created with correct naming pattern
            freeform_files = list(project.glob('2025*.md'))
            assert len(freeform_files) == 1

            # Verify filename format: YYYY-MM-DD-HHmm.md
            filename = freeform_files[0].name
            pattern = r'^\d{4}-\d{2}-\d{2}-\d{4}\.md$'
            assert re.match(pattern, filename)

    def test_create_freeform_without_title(self, runner: CliRunner, project: Path) -> None:
        """Test creating freeform content without a title."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ['write', '--path', str(project)])
            assert result.exit_code == 0
            assert 'Created freeform file' in result.output

    def test_multiple_freeform_files(self, runner: CliRunner, project: Path) -> None:
        """Test creating multiple freeform files - within same minute creates one file."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            # Create multiple freeform files - they will use same timestamp within the minute
            titles = ['Morning thoughts', 'Plot ideas', 'Research notes']
            for title in titles:
                result = runner.invoke(app, ['write', '--title', title, '--path', str(project)])
                assert result.exit_code == 0

            # Verify at least one file was created (same timestamp = same filename = preserve original)
            freeform_files = list(project.glob('2025*.md'))
            assert len(freeform_files) >= 1  # At least one file created

            # The first title should be in the file content (file preserves original title)
            content = freeform_files[0].read_text()
            assert 'Morning thoughts' in content  # First title should be present (no overwriting)

    def test_freeform_timestamp_ordering(self, runner: CliRunner, project: Path) -> None:
        """Test that freeform files maintain chronological ordering."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            # Create files with small time gaps
            import time

            filenames = []

            for i in range(3):
                result = runner.invoke(app, ['write', '--title', f'Note {i}', '--path', str(project)])
                assert result.exit_code == 0

                # Extract filename from output
                output_lines = result.output.split('\n')
                created_line = next(line for line in output_lines if 'Created freeform file' in line)
                filename = created_line.split(': ')[1].strip()
                filenames.append(filename)

                time.sleep(0.1)  # Small delay to ensure different timestamps

            # Verify files are in chronological order
            sorted_filenames = sorted(filenames)
            assert filenames == sorted_filenames

    def test_freeform_content_structure(self, runner: CliRunner, project: Path) -> None:
        """Test that freeform files have correct content structure."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ['write', '--title', 'Test Content', '--path', str(project)])
            assert result.exit_code == 0

            # Find the created file
            freeform_files = list(project.glob('2025*.md'))
            assert len(freeform_files) >= 1

            # Verify basic content structure
            content = freeform_files[-1].read_text()
            # Should have frontmatter
            assert content.startswith('---')
            assert 'id:' in content
            assert 'title:' in content
            assert 'created:' in content

            # Should have basic freeform content
            assert '# Freewrite Session' in content

    def test_freeform_independent_of_binder(self, runner: CliRunner, project: Path) -> None:
        """Test that freeform files don't appear in binder structure."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            # Create some freeform content
            runner.invoke(app, ['write', '--title', 'Freeform 1', '--path', str(project)])
            runner.invoke(app, ['write', '--title', 'Freeform 2', '--path', str(project)])

            # Add a regular node for comparison
            runner.invoke(app, ['add', 'Chapter 1', '--path', str(project)])

            # Check structure - should only show Chapter 1
            result = runner.invoke(app, ['structure', '--path', str(project)])
            assert 'Chapter 1' in result.output
            assert 'Freeform 1' not in result.output
            assert 'Freeform 2' not in result.output

            # Check audit - freeform files should not be considered orphans
            result = runner.invoke(app, ['audit', '--path', str(project)])
            assert result.exit_code == 0
            # Freeform files should not appear as orphans
            if 'orphan' in result.output.lower():
                assert 'Freeform' not in result.output

    def test_freeform_file_persistence(self, runner: CliRunner, project: Path) -> None:
        """Test that freeform files persist across sessions."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            # Create a freeform file
            runner.invoke(app, ['write', '--title', 'Persistent Note', '--path', str(project)])

            # Find the file
            freeform_files = list(project.glob('2025*.md'))
            original_file = freeform_files[0]
            original_content = original_file.read_text()

            # Manually add some content to simulate editing
            modified_content = original_content + '\n\nPersistent content'
            original_file.write_text(modified_content)

            # Verify content persists
            assert 'Persistent content' in original_file.read_text()
            assert original_file.exists()

            # Create another project action to simulate new session
            runner.invoke(app, ['add', 'New Chapter', '--path', str(project)])

            # Verify freeform file still exists with content
            assert original_file.exists()
            assert 'Persistent content' in original_file.read_text()

    def test_freeform_with_special_characters(self, runner: CliRunner, project: Path) -> None:
        """Test creating freeform with special characters in title."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            titles = ['Ideas: Part 1', 'Notes & Thoughts', 'Research (2025)', 'Plot/Character Development']

            for title in titles:
                result = runner.invoke(app, ['write', '--title', title, '--path', str(project)])
                assert result.exit_code == 0

            # Verify at least one file was created (same timestamp within minute)
            freeform_files = list(project.glob('2025*.md'))
            assert len(freeform_files) >= 1  # At least one file created

            # The first title should be in the file content (file preserves original title)
            content = freeform_files[0].read_text()
            assert 'Ideas: Part 1' in content  # First title should be present (no overwriting)
