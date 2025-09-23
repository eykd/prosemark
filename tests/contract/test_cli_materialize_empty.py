"""Contract test for CLI empty binder scenario."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from prosemark.cli.main import app as cli


class TestCLIMaterializeEmptyContract:
    """Test CLI contract for empty binder scenario."""

    def test_empty_binder_no_placeholders(self, tmp_path: Path) -> None:
        """Test --all flag with a binder that has no placeholders."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Empty Test Project

<!-- BEGIN_MANAGED_BLOCK -->
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        runner = CliRunner()
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case,
        ):
            mock_result = MagicMock()
            mock_result.total_placeholders = 0
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 0.01

            mock_use_case.return_value.execute.return_value = mock_result

            # Test JSON output
            result = runner.invoke(cli, ['materialize', '--all', '--json', '--path', str(tmp_path)])

            assert result.exit_code == 0

            output = json.loads(result.output)
            assert output['type'] == 'batch'
            assert output['total_placeholders'] == 0
            assert output['successful_materializations'] == 0
            assert output['failed_materializations'] == 0
            assert 'No placeholders' in output['message'] or output['total_placeholders'] == 0

    def test_empty_binder_human_readable(self, tmp_path: Path) -> None:
        """Test human-readable output for empty binder."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Empty Project

<!-- BEGIN_MANAGED_BLOCK -->
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        runner = CliRunner()
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case,
        ):
            mock_result = MagicMock()
            mock_result.total_placeholders = 0
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 0.01

            mock_use_case.return_value.execute.return_value = mock_result

            result = runner.invoke(cli, ['materialize', '--all', '--path', str(tmp_path)])

            assert result.exit_code == 0
            assert 'No placeholders found to materialize' in result.output

    def test_all_already_materialized(self, tmp_path: Path) -> None:
        """Test --all flag when all nodes are already materialized."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1](01923f0c-1234-7123-8abc-def012345678.md)
- [Chapter 2](01923f0c-1234-7123-8abc-def012345679.md)
- [Chapter 3](01923f0c-1234-7123-8abc-def012345680.md)
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        # Create the node files
        for i in range(8, 11):
            node_id = f'01923f0c-1234-7123-8abc-def01234567{i}'
            node_file = tmp_path / f'{node_id}.md'
            node_file.write_text(f'# Chapter {i - 7}\n\nContent.')
            notes_file = tmp_path / f'{node_id}.notes.md'
            notes_file.write_text('# Notes\n')

        runner = CliRunner()
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case,
        ):
            mock_result = MagicMock()
            mock_result.total_placeholders = 0
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 0.02

            mock_use_case.return_value.execute.return_value = mock_result

            result = runner.invoke(cli, ['materialize', '--all', '--path', str(tmp_path)])

            assert result.exit_code == 0
            assert 'No placeholders found' in result.output or 'already materialized' in result.output.lower()

    def test_binder_with_only_materialized_nodes_json(self, tmp_path: Path) -> None:
        """Test JSON response when binder has only materialized nodes."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Introduction](01923f0c-1234-7123-8abc-def012345678.md)
  - [Overview](01923f0c-1234-7123-8abc-def012345679.md)
  - [Goals](01923f0c-1234-7123-8abc-def012345680.md)
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        runner = CliRunner()
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case,
        ):
            mock_result = MagicMock()
            mock_result.total_placeholders = 0
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 0.015

            mock_use_case.return_value.execute.return_value = mock_result

            result = runner.invoke(cli, ['materialize', '--all', '--json', '--path', str(tmp_path)])

            assert result.exit_code == 0

            output = json.loads(result.output)
            assert output['type'] == 'batch'
            assert output['total_placeholders'] == 0
            assert output['successful_materializations'] == 0
            assert output['failed_materializations'] == 0
            assert output['execution_time'] >= 0

    def test_missing_binder_file(self, tmp_path: Path) -> None:
        """Test --all flag when _binder.md doesn't exist."""
        # Don't create a binder file

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['materialize', '--all', '--path', str(tmp_path)])

            assert result.exit_code == 1
            assert (
                'No _binder.md file found' in result.output
                or 'binder file not found' in result.output.lower()
                or 'No binder found' in result.output
            )
