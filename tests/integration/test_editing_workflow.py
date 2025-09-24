"""Integration test for node content editing workflow."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.cli.main import app


class TestEditingWorkflow:
    """Test the complete editing workflow for node content."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> dict[str, Any]:
        """Create a project with some content."""
        project_dir = tmp_path / 'test_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        result = runner.invoke(app, ['add', 'Test Chapter', '--path', str(project_dir)])

        # Extract node ID from output
        lines = result.output.split('\n')
        added_line = next(line for line in lines if 'Added' in line)
        node_id = added_line.split('(')[1].split(')')[0]

        return {'dir': project_dir, 'node_id': node_id}

    def test_edit_draft_content(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test editing draft content of a node."""
        # Mock the editor launch to simulate editing
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            # Simulate editor modifying the file
            def side_effect(*args: object, **kwargs: object) -> MagicMock:
                # Get the file path from the command
                assert isinstance(args[0], (list, tuple)), 'Expected command as list/tuple'
                file_path = Path(args[0][1])
                # Write some content to simulate editing
                file_path.write_text(
                    """---
id: {id}
title: "Test Chapter"
synopsis: |
  A test chapter for integration testing
created: 2025-09-20T12:00:00Z
updated: 2025-09-20T12:00:00Z
---

# Test Chapter

This is the edited content of the test chapter.
""".format(id=project['node_id'])
                )
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect

            result = runner.invoke(app, ['edit', project['node_id'], '--part', 'draft', '--path', str(project['dir'])])
            assert result.exit_code == 0

            # Verify the content was edited
            draft_file = project['dir'] / f'{project["node_id"]}.md'
            content = draft_file.read_text()
            assert 'This is the edited content' in content

    def test_edit_notes_content(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test editing notes content of a node."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            def side_effect(*args: object, **kwargs: object) -> MagicMock:
                file_path = Path(args[0][1])  # type: ignore[index]
                file_path.write_text(
                    """---
id: {id}
title: "Test Chapter"
created: 2025-09-20T12:00:00Z
updated: 2025-09-20T12:00:00Z
---

# Notes for Test Chapter

- Character development ideas
- Plot points to remember
- Research notes
""".format(id=project['node_id'])
                )
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect

            result = runner.invoke(app, ['edit', project['node_id'], '--part', 'notes', '--path', str(project['dir'])])
            assert result.exit_code == 0

            # Verify the notes were edited
            notes_file = project['dir'] / f'{project["node_id"]}.notes.md'
            content = notes_file.read_text()
            assert 'Character development ideas' in content

    def test_edit_synopsis(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test editing the synopsis in frontmatter."""
        with patch('prosemark.adapters.editor_launcher_system.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            def side_effect(*args: object, **kwargs: object) -> MagicMock:
                file_path = Path(args[0][1])  # type: ignore[index]
                # Update the synopsis in frontmatter
                content = file_path.read_text()
                content = content.replace(
                    'synopsis: null',
                    'synopsis: |\n  This chapter introduces the main character\n  and sets up the central conflict',
                )
                file_path.write_text(content)
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect

            result = runner.invoke(
                app, ['edit', project['node_id'], '--part', 'synopsis', '--path', str(project['dir'])]
            )
            assert result.exit_code == 0

            # Verify the synopsis was updated
            draft_file = project['dir'] / f'{project["node_id"]}.md'
            content = draft_file.read_text()
            assert 'introduces the main character' in content

    def test_write_freeform_content(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test creating freeform writing files."""
        # Mock the open method directly on the EditorLauncherSystem class
        with patch.object(EditorLauncherSystem, 'open'):
            result = runner.invoke(app, ['write', '--title', 'Quick Ideas', '--path', str(project['dir'])])
            assert result.exit_code == 0
            assert 'Created freeform file' in result.output

            # Verify a freeform file was created
            freeform_files = list(project['dir'].glob('2025*.md'))
            assert len(freeform_files) >= 1

            # Verify the file has correct structure
            content = freeform_files[0].read_text()
            assert '---' in content  # YAML frontmatter
            assert 'title: "Quick Ideas"' in content
            assert '# Freewrite Session' in content

            # Note: The freewriting command now uses a TUI instead of launching an external editor
            # so we don't expect the editor mock to be called

    def test_edit_nonexistent_node_fails(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that editing a non-existent node fails gracefully."""
        # Use a properly formatted UUID that doesn't exist
        nonexistent_id = '01999999-9999-7999-8999-999999999999'
        result = runner.invoke(app, ['edit', nonexistent_id, '--part', 'draft', '--path', str(project['dir'])])
        assert result.exit_code != 0
        assert 'not found' in result.output.lower() or 'error' in result.output.lower()
