"""Integration test for complete project lifecycle."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestProjectLifecycle:
    """Test complete project lifecycle from creation to audit."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path / 'test_project'

    def test_complete_project_lifecycle(self, runner: CliRunner, project_dir: Path) -> None:
        """Test creating, managing, and auditing a project."""
        project_dir.mkdir()

        # 1. Initialize project
        result = runner.invoke(app, ['init', '--title', 'My Novel', '--path', str(project_dir)])
        assert result.exit_code == 0
        assert 'initialized successfully' in result.output
        assert (project_dir / '_binder.md').exists()

        # 2. Add root-level chapters
        result = runner.invoke(app, ['add', 'Chapter 1: Beginning', '--path', str(project_dir)])
        assert result.exit_code == 0
        assert 'Added' in result.output

        result = runner.invoke(app, ['add', 'Chapter 2: Middle', '--path', str(project_dir)])
        assert result.exit_code == 0

        # 3. View structure
        result = runner.invoke(app, ['structure', '--path', str(project_dir)])
        assert result.exit_code == 0
        assert 'Chapter 1: Beginning' in result.output
        assert 'Chapter 2: Middle' in result.output

        # 4. Add nested sections
        # Get the node ID from the JSON structure output instead
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0

        import json

        structure_data = json.loads(result.output)
        # Find Chapter 1 in the roots
        chapter1_item = next(
            item for item in structure_data['roots'] if 'Chapter 1: Beginning' in item['display_title']
        )
        node_id = chapter1_item['node_id']

        result = runner.invoke(app, ['add', 'Section 1.1', '--parent', node_id, '--path', str(project_dir)])
        assert result.exit_code == 0

        # 5. Add placeholder
        result = runner.invoke(app, ['add', 'Chapter 3: End', '--path', str(project_dir)])
        assert result.exit_code == 0

        # 6. Materialize placeholder (actually Chapter 3 is already created, let's add a real placeholder)
        # First, let's manually create a placeholder by editing the binder
        binder_path = project_dir / '_binder.md'
        content = binder_path.read_text()
        # Add a placeholder in the managed section
        content = content.replace('<!-- END_MANAGED_BLOCK -->', '- [Future Chapter]()\n<!-- END_MANAGED_BLOCK -->')
        binder_path.write_text(content)

        # Now materialize it
        result = runner.invoke(app, ['materialize', 'Future Chapter', '--path', str(project_dir)])
        assert result.exit_code == 0
        assert 'Materialized' in result.output

        # 7. Move a node
        # Get Chapter 2 ID from JSON structure
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0
        structure_data = json.loads(result.output)
        chapter2_item = next(item for item in structure_data['roots'] if 'Chapter 2: Middle' in item['display_title'])
        chapter2_id = chapter2_item['node_id']

        result = runner.invoke(app, ['move', chapter2_id, '--position', '0', '--path', str(project_dir)])
        assert result.exit_code == 0

        # 8. Remove a node
        result = runner.invoke(app, ['remove', chapter2_id, '--path', str(project_dir)])
        assert result.exit_code == 0

        # 9. Audit project (should find orphaned files from removed node)
        result = runner.invoke(app, ['audit', '--path', str(project_dir)])
        assert result.exit_code == 1  # Exit code 1 because of orphaned files
        assert 'orphan' in result.output.lower()

        # 10. Final structure verification
        result = runner.invoke(app, ['structure', '--path', str(project_dir)])
        assert result.exit_code == 0
        # Chapter 2 should be gone
        assert 'Chapter 2: Middle' not in result.output
        # Others should remain
        assert 'Chapter 1: Beginning' in result.output
        assert 'Section 1.1' in result.output
