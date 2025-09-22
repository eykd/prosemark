"""Integration test for project audit and integrity checking."""

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestAuditIntegrity:
    """Test project audit functionality and integrity checking."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> dict[str, Any]:
        """Create a project with various content."""
        project_dir = tmp_path / 'audit_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Audit Test', '--path', str(project_dir)])

        # Add some nodes
        result = runner.invoke(app, ['add', 'Chapter 1', '--path', str(project_dir)])
        ch1_id = self._extract_node_id(result.output)

        result = runner.invoke(app, ['add', 'Chapter 2', '--path', str(project_dir)])
        ch2_id = self._extract_node_id(result.output)

        return {'dir': project_dir, 'ch1_id': ch1_id, 'ch2_id': ch2_id}

    def _extract_node_id(self, output: str) -> str:
        """Extract node ID from add command output."""
        lines = output.split('\n')
        added_line = next(line for line in lines if 'Added' in line)
        return added_line.split('(')[1].split(')')[0]

    def test_audit_healthy_project(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test auditing a healthy project with no issues."""
        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 0
        assert 'integrity check completed' in result.output
        assert 'All nodes have valid files' in result.output
        assert 'All references are consistent' in result.output
        assert 'No orphaned files found' in result.output

    def test_audit_detects_missing_files(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that audit detects missing node files."""
        # Delete a draft file to create missing file issue
        draft_file = project['dir'] / f'{project["ch1_id"]}.md'
        draft_file.unlink()

        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 1  # Exit code 1 when issues are found
        assert 'missing' in result.output.lower()
        assert 'files not found' in result.output.lower()
        assert project['ch1_id'] in result.output

    def test_audit_detects_missing_notes_files(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that audit detects missing notes files."""
        # Delete a notes file
        notes_file = project['dir'] / f'{project["ch2_id"]}.notes.md'
        notes_file.unlink()

        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 1  # Exit code 1 when issues are found
        assert 'missing' in result.output.lower()
        assert 'files not found' in result.output.lower()
        assert project['ch2_id'] in result.output

    def test_audit_detects_orphaned_files(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that audit detects orphaned node files."""
        # Create an orphaned file that's not in the binder
        orphan_file = project['dir'] / 'orphaned123.md'
        orphan_file.write_text("""---
id: orphaned123
title: "Orphaned Chapter"
created: 2025-09-20T12:00:00Z
updated: 2025-09-20T12:00:00Z
---

# Orphaned Chapter

This chapter is not referenced in the binder.
""")

        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 1  # Exit code 1 when issues are found
        assert 'orphan' in result.output.lower()
        assert 'orphaned123.md' in result.output

    def test_audit_detects_id_mismatches(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that audit detects ID mismatches between filename and content."""
        # Modify the ID in a file's frontmatter
        draft_file = project['dir'] / f'{project["ch1_id"]}.md'
        content = draft_file.read_text()

        # Change the ID in frontmatter to something different
        new_content = content.replace(f'id: {project["ch1_id"]}', 'id: mismatched123')
        draft_file.write_text(new_content)

        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 1  # Exit code 1 when issues are found
        assert 'mismatch' in result.output.lower()
        assert project['ch1_id'] in result.output
        assert 'mismatched123' in result.output

    def test_audit_detects_placeholders(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that audit correctly identifies placeholders."""
        # Add placeholders to the binder
        binder_path = project['dir'] / '_binder.md'
        content = binder_path.read_text()

        new_binder = content.replace(
            '<!-- END_MANAGED_BLOCK -->',
            """- [Future Chapter]()
- [Another Placeholder]()
  - [Nested Placeholder]()
<!-- END_MANAGED_BLOCK -->""",
        )
        binder_path.write_text(new_binder)

        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 0
        assert 'placeholder' in result.output.lower()
        assert 'Future Chapter' in result.output
        assert 'Another Placeholder' in result.output
        assert 'Nested Placeholder' in result.output

    def test_audit_multiple_issue_types(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test audit when multiple types of issues exist."""
        # Create missing file issue
        draft_file = project['dir'] / f'{project["ch1_id"]}.md'
        draft_file.unlink()

        # Create orphaned file
        orphan_file = project['dir'] / 'orphan456.md'
        orphan_file.write_text("""---
id: orphan456
title: "Orphan"
created: 2025-09-20T12:00:00Z
updated: 2025-09-20T12:00:00Z
---

Orphaned content.
""")

        # Add placeholder
        binder_path = project['dir'] / '_binder.md'
        content = binder_path.read_text()
        new_binder = content.replace(
            '<!-- END_MANAGED_BLOCK -->', '- [Placeholder Chapter]()\n<!-- END_MANAGED_BLOCK -->'
        )
        binder_path.write_text(new_binder)

        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 1  # Exit code 1 when real issues (missing/orphaned files) are found

        # Should detect all issue types
        assert 'placeholder' in result.output.lower()
        assert 'missing' in result.output.lower()
        assert 'orphan' in result.output.lower()
        assert 'Placeholder Chapter' in result.output
        assert project['ch1_id'] in result.output
        assert 'orphan456.md' in result.output

    def test_audit_empty_project(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test auditing an empty project."""
        project_dir = tmp_path / 'empty_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Empty Project', '--path', str(project_dir)])

        result = runner.invoke(app, ['audit', '--path', str(project_dir)])
        assert result.exit_code == 0
        assert 'integrity check completed' in result.output
        # Should show clean audit for empty project
        assert 'All nodes have valid files' in result.output

    def test_audit_preserves_binder_content(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that audit doesn't modify the binder file."""
        binder_path = project['dir'] / '_binder.md'
        original_content = binder_path.read_text()
        # Store original mtime for comparison
        # Run audit
        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 0

        # Verify binder wasn't modified
        assert binder_path.read_text() == original_content
        # Note: mtime might change due to filesystem resolution, so we don't check it

    def test_audit_ignores_non_node_files(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that audit ignores non-node markdown files."""
        # Create various non-node files
        (project['dir'] / 'README.md').write_text('# Project README')
        (project['dir'] / 'notes.md').write_text('# General Notes')
        (project['dir'] / 'todo.txt').write_text('Things to do')
        (project['dir'] / 'script.py').write_text("print('hello')")

        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 0

        # These files should not be flagged as orphans
        assert 'README.md' not in result.output
        assert 'notes.md' not in result.output
        assert 'todo.txt' not in result.output
        assert 'script.py' not in result.output

    def test_audit_position_information(self, runner: CliRunner, project: dict[str, Any]) -> None:
        """Test that audit provides position information for issues."""
        # Add nested structure with placeholders
        binder_path = project['dir'] / '_binder.md'
        content = binder_path.read_text()

        new_binder = content.replace(
            '<!-- END_MANAGED_BLOCK -->',
            """- [Part 1]()
  - [Chapter 1.1]()
  - [Chapter 1.2]()
- [Part 2]()
  - [Chapter 2.1]()
<!-- END_MANAGED_BLOCK -->""",
        )
        binder_path.write_text(new_binder)

        result = runner.invoke(app, ['audit', '--path', str(project['dir'])])
        assert result.exit_code == 0

        # Should include position information for placeholders
        assert 'placeholder' in result.output.lower()
        # Should show hierarchical positions
        lines = result.output.split('\n')
        placeholder_lines = [
            line
            for line in lines
            if any(title in line for title in ['Part 1', 'Chapter 1.1', 'Chapter 1.2', 'Part 2', 'Chapter 2.1'])
        ]
        assert len(placeholder_lines) >= 5  # All our placeholders should be listed
