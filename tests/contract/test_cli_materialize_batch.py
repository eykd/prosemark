"""Contract test for CLI batch materialization success response."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from prosemark.cli.main import app as cli


class TestCLIMaterializeBatchContract:
    """Test CLI contract for batch success response."""

    def test_batch_success_response_format(self, tmp_path: Path) -> None:
        """Test that successful batch materialization returns correct format."""
        # Setup binder
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1]()
- [Chapter 2]()
- [Section 2.1]()
- [Chapter 3]()
- [Appendix]()
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
            mock_result.total_placeholders = 5
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 2.5

            # Create mock successful materializations
            for i, title in enumerate(['Chapter 1', 'Chapter 2', 'Section 2.1', 'Chapter 3', 'Appendix'], 1):
                mock_materialization = MagicMock()
                mock_materialization.display_title = title
                mock_materialization.node_id = MagicMock(value=f'01923f0c-1234-7123-8abc-def01234567{i}')
                mock_materialization.file_paths = [
                    f'01923f0c-1234-7123-8abc-def01234567{i}.md',
                    f'01923f0c-1234-7123-8abc-def01234567{i}.notes.md',
                ]
                mock_materialization.position = f'[{i - 1}]'
                mock_result.successful_materializations.append(mock_materialization)

            mock_use_case.return_value.execute.return_value = mock_result

            # Run with JSON output
            result = runner.invoke(cli, ['materialize', '--all', '--json', '--path', str(tmp_path)])

            assert result.exit_code == 0

            # Validate JSON structure
            output = json.loads(result.output)
            assert output['type'] == 'batch'
            assert output['total_placeholders'] == 5
            assert output['successful_materializations'] == 5
            assert output['failed_materializations'] == 0
            assert output['execution_time'] == 2.5
            assert 'message' in output
            assert 'Successfully materialized all 5 placeholders' in output['message']

            # Check details if provided
            if 'details' in output:
                assert len(output['details']) == 5
                for detail in output['details']:
                    assert 'placeholder_title' in detail
                    assert 'node_id' in detail
                    # Validate UUID format
                    assert len(detail['node_id']) == 36

    def test_batch_success_human_readable_output(self, tmp_path: Path) -> None:
        """Test human-readable output for batch success."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1]()
- [Chapter 2]()
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        runner = CliRunner()
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case,
        ):
            mock_result = MagicMock()
            mock_result.total_placeholders = 2
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 0.5

            for i, title in enumerate(['Chapter 1', 'Chapter 2'], 1):
                mock_mat = MagicMock()
                mock_mat.display_title = title
                mock_mat.node_id = MagicMock(value=f'01923f0c-1234-7123-8abc-def01234567{i}')
                mock_result.successful_materializations.append(mock_mat)

            mock_use_case.return_value.execute.return_value = mock_result

            result = runner.invoke(cli, ['materialize', '--all', '--path', str(tmp_path)])

            assert result.exit_code == 0

            # Check for expected messages in output
            assert 'Found 2 placeholders to materialize' in result.output
            assert "✓ Materialized 'Chapter 1'" in result.output
            assert "✓ Materialized 'Chapter 2'" in result.output
            assert 'Successfully materialized all 2 placeholders' in result.output

    def test_empty_batch_response(self, tmp_path: Path) -> None:
        """Test response when batch finds zero placeholders."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

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
            mock_result.execution_time = 0.1

            mock_use_case.return_value.execute.return_value = mock_result

            result = runner.invoke(cli, ['materialize', '--all', '--json', '--path', str(tmp_path)])

            assert result.exit_code == 0

            output = json.loads(result.output)
            assert output['type'] == 'batch'
            assert output['total_placeholders'] == 0
            assert output['successful_materializations'] == 0
            assert output['failed_materializations'] == 0
