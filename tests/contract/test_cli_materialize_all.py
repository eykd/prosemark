"""Contract test for CLI materialize --all flag validation."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from prosemark.cli.main import app as cli


class TestCLIMaterializeAllContract:
    """Test CLI contract for --all flag validation."""

    def test_materialize_all_flag_success(self, tmp_path: Path) -> None:
        """Test successful materialization with --all flag."""
        # Setup binder with placeholders
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1]()
- [Chapter 2]()
- [Chapter 3]()
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        runner = CliRunner()
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case,
        ):
            # Mock successful batch result
            mock_result = MagicMock()
            mock_result.total_placeholders = 3
            mock_result.successful_materializations = [
                MagicMock(
                    display_title='Chapter 1',
                    node_id=MagicMock(value='01923f0c-1234-7123-8abc-def012345678'),
                ),
                MagicMock(
                    display_title='Chapter 2',
                    node_id=MagicMock(value='01923f0c-1234-7123-8abc-def012345679'),
                ),
                MagicMock(
                    display_title='Chapter 3',
                    node_id=MagicMock(value='01923f0c-1234-7123-8abc-def012345680'),
                ),
            ]
            mock_result.failed_materializations = []
            mock_result.execution_time = 1.234

            mock_use_case.return_value.execute.return_value = mock_result

            result = runner.invoke(cli, ['materialize', '--all', '--path', str(tmp_path)])

            # Check exit code
            assert result.exit_code == 0

            # Parse JSON output if available, otherwise check text output
            try:
                output = json.loads(result.output)
                assert output['type'] == 'batch'
                assert output['total_placeholders'] == 3
                assert output['successful_materializations'] == 3
                assert output['failed_materializations'] == 0
                assert output['execution_time'] == 1.234
            except json.JSONDecodeError:
                # Check human-readable output
                assert 'Successfully materialized all 3 placeholders' in result.output

    def test_materialize_all_no_placeholders(self, tmp_path: Path) -> None:
        """Test --all flag when only materialized nodes exist (no true placeholders)."""
        # Setup binder with only materialized nodes (no placeholders)
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1](01923f0c-1234-7123-8abc-def012345678.md)
- [Chapter 2](01923f0c-1234-7123-8abc-def012345679.md)
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['materialize', '--all', '--path', str(tmp_path)])

            # Should process materialized items to ensure complete file sets
            assert result.exit_code == 0
            assert 'Found 2 placeholders to materialize' in result.output
            assert 'Successfully materialized all 2 placeholders' in result.output

    def test_materialize_mutual_exclusion_error(self, tmp_path: Path) -> None:
        """Test that title and --all are mutually exclusive."""
        binder_path = tmp_path / '_binder.md'
        binder_path.write_text('# Test\n<!-- BEGIN_MANAGED_BLOCK -->\n<!-- END_MANAGED_BLOCK -->')

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['materialize', 'Some Title', '--all', '--path', str(tmp_path)])

            # Should fail with validation error
            assert result.exit_code == 1
            assert "Cannot specify both 'title' and '--all' options" in result.output

    def test_materialize_missing_required_option(self, tmp_path: Path) -> None:
        """Test that either title or --all is required."""
        binder_path = tmp_path / '_binder.md'
        binder_path.write_text('# Test\n<!-- BEGIN_MANAGED_BLOCK -->\n<!-- END_MANAGED_BLOCK -->')

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['materialize', '--path', str(tmp_path)])

            # Should fail with validation error
            assert result.exit_code == 1
            assert "Must specify either placeholder 'title' or '--all' flag" in result.output

    def test_materialize_all_no_binder(self, tmp_path: Path) -> None:
        """Test --all flag when no binder file exists."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['materialize', '--all', '--path', str(tmp_path)])

            # Should fail with not found error
            assert result.exit_code == 1
            assert 'No _binder.md file found' in result.output or 'binder file not found' in result.output.lower()
