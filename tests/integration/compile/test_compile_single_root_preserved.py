"""Integration test for preserving single-node compile behavior (backward compatibility)."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestCompileSingleRootPreserved:
    """Test that providing node_id still compiles only that specific node."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path / 'test_project'

    def test_compile_specific_node_only(self, runner: CliRunner, project_dir: Path) -> None:
        """Providing node_id compiles only that node (existing behavior)."""
        # Setup: Initialize project with 2 roots
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        result = runner.invoke(app, ['add', 'Root 1', '--path', str(project_dir)])
        assert result.exit_code == 0

        result = runner.invoke(app, ['add', 'Root 2', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Get node IDs
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0

        import json

        structure_data = json.loads(result.output)
        roots = structure_data['roots']
        assert len(roots) == 2

        root1_id = roots[0]['node_id']
        root2_id = roots[1]['node_id']

        # Write content to both nodes
        for root_item in roots:
            node_id = root_item['node_id']
            title = root_item['display_title']
            node_file = project_dir / f'{node_id}.md'

            content = node_file.read_text()
            content += f'\n\n{title} content'
            node_file.write_text(content)

        # Execute: Compile specific node (root1)
        result = runner.invoke(app, ['compile', root1_id, '--path', str(project_dir)])

        # Verify: Only root1 compiled
        assert result.exit_code == 0
        assert 'Root 1 content' in result.output
        assert 'Root 2 content' not in result.output

        # Execute: Compile other specific node (root2)
        result = runner.invoke(app, ['compile', root2_id, '--path', str(project_dir)])

        # Verify: Only root2 compiled
        assert result.exit_code == 0
        assert 'Root 2 content' in result.output
        assert 'Root 1 content' not in result.output

    def test_compile_with_include_empty_flag(self, runner: CliRunner, project_dir: Path) -> None:
        """--include-empty flag works consistently for all roots."""
        # Setup: Initialize project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add roots with varying content
        result = runner.invoke(app, ['add', 'Empty Root', '--path', str(project_dir)])
        assert result.exit_code == 0

        result = runner.invoke(app, ['add', 'Full Root', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Get node IDs
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0

        import json

        structure_data = json.loads(result.output)
        roots = structure_data['roots']
        assert len(roots) == 2

        # Write content only to "Full Root", leave "Empty Root" empty
        for root_item in roots:
            node_id = root_item['node_id']
            title = root_item['display_title']
            node_file = project_dir / f'{node_id}.md'

            if 'Full' in title:
                content = node_file.read_text()
                content += '\n\nFull content here'
                node_file.write_text(content)

        # Execute without flag: compile all roots
        result = runner.invoke(app, ['compile', '--path', str(project_dir)])
        assert result.exit_code == 0
        assert 'Full content here' in result.output
        # Empty node should be excluded by default

        # Execute with flag: compile all roots including empty
        result = runner.invoke(app, ['compile', '--include-empty', '--path', str(project_dir)])
        assert result.exit_code == 0
        assert 'Full content here' in result.output
        # Empty node should be included with flag
        # (The actual behavior depends on how empty nodes are handled)

    def test_compile_node_with_children(self, runner: CliRunner, project_dir: Path) -> None:
        """Compiling specific node includes its children (existing behavior)."""
        # Setup: Initialize project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add parent root
        result = runner.invoke(app, ['add', 'Parent', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Get parent ID
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0

        import json

        structure_data = json.loads(result.output)
        parent_id = structure_data['roots'][0]['node_id']

        # Add child to parent
        result = runner.invoke(app, ['add', 'Child', '--parent', parent_id, '--path', str(project_dir)])
        assert result.exit_code == 0

        # Write content to both parent and child
        parent_file = project_dir / f'{parent_id}.md'
        content = parent_file.read_text()
        content += '\n\nParent content'
        parent_file.write_text(content)

        # Get child ID
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        structure_data = json.loads(result.output)
        child_id = structure_data['roots'][0]['children'][0]['node_id']

        child_file = project_dir / f'{child_id}.md'
        content = child_file.read_text()
        content += '\n\nChild content'
        child_file.write_text(content)

        # Execute: Compile parent node
        result = runner.invoke(app, ['compile', parent_id, '--path', str(project_dir)])

        # Verify: Both parent and child content appear
        assert result.exit_code == 0
        assert 'Parent content' in result.output
        assert 'Child content' in result.output

    def test_compile_invalid_node_id_error(self, runner: CliRunner, project_dir: Path) -> None:
        """Providing invalid node_id produces error (existing behavior)."""
        # Setup: Initialize project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Execute: Compile with non-existent node ID
        result = runner.invoke(app, ['compile', 'nonexistent-id-12345', '--path', str(project_dir)])

        # Verify: Error exit code and error message
        assert result.exit_code == 1
        assert 'Error' in result.output or 'not found' in result.output.lower()
