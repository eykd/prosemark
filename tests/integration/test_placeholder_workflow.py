"""Integration test for placeholder materialization workflow."""

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestPlaceholderWorkflow:
    """Test placeholder creation and materialization workflow."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project_with_placeholders(self, tmp_path: Path) -> dict[str, Any]:
        """Create a project with some placeholders."""
        project_dir = tmp_path / 'placeholder_project'
        project_dir.mkdir()

        runner = CliRunner()
        runner.invoke(app, ['init', '--title', 'Placeholder Test', '--path', str(project_dir)])

        # Add real nodes
        result = runner.invoke(app, ['add', 'Chapter 1', '--path', str(project_dir)])
        ch1_id = self._extract_node_id(result.output)

        # Manually add placeholders to the binder
        binder_path = project_dir / '_binder.md'
        content = binder_path.read_text()

        # Insert placeholders in the managed section
        new_binder = content.replace(
            '<!-- END_MANAGED_BLOCK -->',
            """- [Chapter 2: The Middle]()
  - [Section 2.1]()
  - [Section 2.2]()
- [Chapter 3: The End]()
  - [Important Scene]()
- [Epilogue]()
<!-- END_MANAGED_BLOCK -->""",
        )
        binder_path.write_text(new_binder)

        return {'dir': project_dir, 'ch1_id': ch1_id}

    def _extract_node_id(self, output: str) -> str:
        """Extract node ID from add command output."""
        lines = output.split('\n')
        added_line = next(line for line in lines if 'Added' in line)
        return added_line.split('(')[1].split(')')[0]

    def test_identify_placeholders_in_audit(self, runner: CliRunner, project_with_placeholders: dict[str, Any]) -> None:
        """Test that audit correctly identifies placeholders."""
        result = runner.invoke(app, ['audit', '--path', str(project_with_placeholders['dir'])])
        assert result.exit_code == 0

        # Should report placeholders
        assert 'placeholder' in result.output.lower()
        assert 'Chapter 2: The Middle' in result.output
        assert 'Section 2.1' in result.output
        assert 'Section 2.2' in result.output
        assert 'Chapter 3: The End' in result.output
        assert 'Important Scene' in result.output
        assert 'Epilogue' in result.output

    def test_materialize_top_level_placeholder(
        self, runner: CliRunner, project_with_placeholders: dict[str, Any]
    ) -> None:
        """Test materializing a top-level placeholder."""
        result = runner.invoke(app, ['materialize', 'Epilogue', '--path', str(project_with_placeholders['dir'])])
        assert result.exit_code == 0
        assert 'Materialized' in result.output

        # Verify files were created
        project_dir = project_with_placeholders['dir']
        epilogue_files = list(project_dir.glob('*.md'))
        # Filter to find the epilogue file (not _binder.md or notes files)
        epilogue_draft = [
            f
            for f in epilogue_files
            if f.name != '_binder.md' and not f.name.endswith('.notes.md') and 'Epilogue' in f.read_text()
        ]
        assert len(epilogue_draft) >= 1

        # Verify it's no longer a placeholder in audit
        result = runner.invoke(app, ['audit', '--path', str(project_with_placeholders['dir'])])
        # Epilogue should not be in placeholders anymore
        lines = result.output.split('\n')
        placeholder_section = False
        for line in lines:
            if 'placeholder' in line.lower():
                placeholder_section = True
            elif placeholder_section and 'Epilogue' in line:
                pytest.fail('Epilogue still appears as placeholder after materialization')

    def test_materialize_nested_placeholder(self, runner: CliRunner, project_with_placeholders: dict[str, Any]) -> None:
        """Test materializing a nested placeholder."""
        result = runner.invoke(app, ['materialize', 'Section 2.1', '--path', str(project_with_placeholders['dir'])])
        assert result.exit_code == 0
        assert 'Materialized' in result.output

        # Verify the parent (Chapter 2) is still a placeholder
        result = runner.invoke(app, ['audit', '--path', str(project_with_placeholders['dir'])])
        assert 'Chapter 2: The Middle' in result.output  # Still a placeholder
        # But Section 2.1 should not be a placeholder anymore

    def test_materialize_parent_with_materialized_children(
        self, runner: CliRunner, project_with_placeholders: dict[str, Any]
    ) -> None:
        """Test materializing a parent that has already-materialized children."""
        # First materialize a child
        runner.invoke(app, ['materialize', 'Important Scene', '--path', str(project_with_placeholders['dir'])])

        # Now materialize the parent
        result = runner.invoke(
            app, ['materialize', 'Chapter 3: The End', '--path', str(project_with_placeholders['dir'])]
        )
        assert result.exit_code == 0

        # Verify both are materialized
        result = runner.invoke(app, ['audit', '--path', str(project_with_placeholders['dir'])])

        # Neither should appear as placeholders
        assert '⚠ PLACEHOLDER: "Chapter 3: The End"' not in result.output
        assert '⚠ PLACEHOLDER: "Important Scene"' not in result.output

    def test_materialize_nonexistent_placeholder(
        self, runner: CliRunner, project_with_placeholders: dict[str, Any]
    ) -> None:
        """Test that materializing a non-existent placeholder fails."""
        result = runner.invoke(
            app, ['materialize', 'Nonexistent Chapter', '--path', str(project_with_placeholders['dir'])]
        )
        assert result.exit_code != 0
        assert 'not found' in result.output.lower()

    def test_materialize_already_materialized(
        self, runner: CliRunner, project_with_placeholders: dict[str, Any]
    ) -> None:
        """Test that materializing an already-materialized node is handled gracefully."""
        # Chapter 1 is already materialized
        result = runner.invoke(app, ['materialize', 'Chapter 1', '--path', str(project_with_placeholders['dir'])])
        # Should succeed silently (warning goes through console, not CLI output)
        assert result.exit_code == 0
        assert result.output.strip() == ''  # CLI should be silent for already-materialized items

    def test_structure_shows_placeholders(self, runner: CliRunner, project_with_placeholders: dict[str, Any]) -> None:
        """Test that structure command shows placeholders distinctly."""
        result = runner.invoke(app, ['structure', '--path', str(project_with_placeholders['dir'])])
        assert result.exit_code == 0

        # All items should be visible
        assert 'Chapter 1' in result.output  # Real node
        assert 'Chapter 2: The Middle' in result.output  # Placeholder
        assert 'Section 2.1' in result.output
        assert 'Section 2.2' in result.output
        assert 'Chapter 3: The End' in result.output
        assert 'Important Scene' in result.output
        assert 'Epilogue' in result.output

    def test_remove_placeholder(self, runner: CliRunner, project_with_placeholders: dict[str, Any]) -> None:
        """Test that placeholders can be removed from the binder."""
        # First get the structure to verify placeholder exists
        result = runner.invoke(app, ['structure', '--path', str(project_with_placeholders['dir'])])
        assert 'Epilogue' in result.output

        # Removing a placeholder requires manual binder editing or special handling
        # Since placeholders don't have IDs, this might not work with current remove command
        # This test documents the expected behavior

        # For now, verify we can't remove by title (since remove expects an ID)
        result = runner.invoke(app, ['remove', 'Epilogue', '--path', str(project_with_placeholders['dir'])])
        # Should fail because "Epilogue" is not a valid node ID
        assert result.exit_code != 0
