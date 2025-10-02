"""Integration test for compiling all root nodes without providing node_id."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestCompileAllRoots:
    """Test compiling all materialized root nodes when no node_id is provided."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path / 'test_project'

    def test_compile_all_roots_with_three_roots(self, runner: CliRunner, project_dir: Path) -> None:
        """Compile all roots when no node_id provided."""
        # Setup: Initialize project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add 3 root nodes
        result = runner.invoke(app, ['add', 'Chapter 1', '--path', str(project_dir)])
        assert result.exit_code == 0

        result = runner.invoke(app, ['add', 'Chapter 2', '--path', str(project_dir)])
        assert result.exit_code == 0

        result = runner.invoke(app, ['add', 'Chapter 3', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Write content to each node
        # Find the node files and write content
        nodes = list(project_dir.glob('*.md'))
        nodes = [n for n in nodes if n.name != '_binder.md' and '.notes.md' not in n.name]
        assert len(nodes) == 3

        # Sort by creation order (we need to identify them properly)
        # Read structure to get node IDs in order
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0

        import json

        structure_data = json.loads(result.output)
        roots = structure_data['roots']
        assert len(roots) == 3

        # Write content to each node file
        for idx, root_item in enumerate(roots, 1):
            node_id = root_item['node_id']
            node_file = project_dir / f'{node_id}.md'
            assert node_file.exists()

            # Append content to the file
            content = node_file.read_text()
            content += f'\n\nChapter {idx} content'
            node_file.write_text(content)

        # Execute: Compile without node_id
        result = runner.invoke(app, ['compile', '--path', str(project_dir)])

        # Verify: All roots compiled, double newline separators
        assert result.exit_code == 0
        assert 'Chapter 1 content' in result.output
        assert 'Chapter 2 content' in result.output
        assert 'Chapter 3 content' in result.output

        # Verify ordering: Chapter 1 before Chapter 2 before Chapter 3
        pos1 = result.output.find('Chapter 1')
        pos2 = result.output.find('Chapter 2')
        pos3 = result.output.find('Chapter 3')
        assert pos1 < pos2 < pos3

    def test_compile_all_roots_ordering_preserved(self, runner: CliRunner, project_dir: Path) -> None:
        """Compilation order matches binder order."""
        # Setup: Initialize project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add nodes in specific order
        result = runner.invoke(app, ['add', 'Alpha', '--path', str(project_dir)])
        assert result.exit_code == 0

        result = runner.invoke(app, ['add', 'Beta', '--path', str(project_dir)])
        assert result.exit_code == 0

        result = runner.invoke(app, ['add', 'Gamma', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Get node files and write unique content
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0

        import json

        structure_data = json.loads(result.output)
        roots = structure_data['roots']

        for root_item in roots:
            node_id = root_item['node_id']
            title = root_item['display_title']
            node_file = project_dir / f'{node_id}.md'

            content = node_file.read_text()
            content += f'\n\nContent for {title}'
            node_file.write_text(content)

        # Execute compile
        result = runner.invoke(app, ['compile', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Verify ordering matches binder order
        alpha_pos = result.output.find('Content for Alpha')
        beta_pos = result.output.find('Content for Beta')
        gamma_pos = result.output.find('Content for Gamma')

        assert alpha_pos < beta_pos < gamma_pos
