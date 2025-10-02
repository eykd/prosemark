"""Integration test for placeholder filtering during compilation."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestCompileWithPlaceholders:
    """Test that placeholders are filtered out during multi-root compilation."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path / 'test_project'

    def test_compile_filters_placeholder_roots(self, runner: CliRunner, project_dir: Path) -> None:
        """Only materialized roots compiled, placeholders skipped."""
        # Setup: Initialize project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add 2 materialized nodes
        result = runner.invoke(app, ['add', 'Actual 1', '--path', str(project_dir)])
        assert result.exit_code == 0

        result = runner.invoke(app, ['add', 'Actual 2', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Manually add placeholders to binder
        binder_path = project_dir / '_binder.md'
        content = binder_path.read_text()

        # Insert placeholders before END_MANAGED_BLOCK
        content = content.replace(
            '<!-- END_MANAGED_BLOCK -->',
            '- [Placeholder 1]()\n- [Placeholder 2]()\n<!-- END_MANAGED_BLOCK -->',
        )
        binder_path.write_text(content)

        # Write content to materialized nodes
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0

        import json

        structure_data = json.loads(result.output)
        roots = structure_data['roots']

        # Write content only to materialized nodes (those with node_id)
        for root_item in roots:
            if root_item.get('node_id'):  # Skip placeholders (node_id is None or missing)
                node_id = root_item['node_id']
                title = root_item['display_title']
                node_file = project_dir / f'{node_id}.md'

                content = node_file.read_text()
                content += f'\n\n{title} content'
                node_file.write_text(content)

        # Execute: Compile without node_id
        result = runner.invoke(app, ['compile', '--path', str(project_dir)])

        # Verify: Only actual nodes compiled, placeholders skipped
        assert result.exit_code == 0
        assert 'Actual 1 content' in result.output
        assert 'Actual 2 content' in result.output
        assert 'Placeholder' not in result.output

    def test_compile_mixed_placeholders_and_nodes_ordering(self, runner: CliRunner, project_dir: Path) -> None:
        """Placeholders don't affect ordering of materialized nodes."""
        # Setup: Initialize project
        project_dir.mkdir()
        result = runner.invoke(app, ['init', '--title', 'Test Project', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add nodes in specific pattern: node, placeholder, node
        result = runner.invoke(app, ['add', 'First', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Add placeholder manually
        binder_path = project_dir / '_binder.md'
        content = binder_path.read_text()
        content = content.replace(
            '<!-- END_MANAGED_BLOCK -->',
            '- [Middle Placeholder]()\n<!-- END_MANAGED_BLOCK -->',
        )
        binder_path.write_text(content)

        result = runner.invoke(app, ['add', 'Last', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Write content to materialized nodes
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_dir)])
        assert result.exit_code == 0

        import json

        structure_data = json.loads(result.output)
        roots = structure_data['roots']

        for root_item in roots:
            if root_item.get('node_id'):  # Skip placeholders
                node_id = root_item['node_id']
                title = root_item['display_title']
                node_file = project_dir / f'{node_id}.md'

                content = node_file.read_text()
                content += f'\n\nContent: {title}'
                node_file.write_text(content)

        # Execute compile
        result = runner.invoke(app, ['compile', '--path', str(project_dir)])
        assert result.exit_code == 0

        # Verify: Only materialized nodes appear, in binder order
        assert 'Content: First' in result.output
        assert 'Content: Last' in result.output
        assert 'Middle Placeholder' not in result.output

        # Verify ordering: First before Last
        first_pos = result.output.find('Content: First')
        last_pos = result.output.find('Content: Last')
        assert first_pos < last_pos
