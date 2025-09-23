"""Contract test for CLI partial failure handling."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from prosemark.cli.main import app as cli


class TestCLIMaterializePartialContract:
    """Test CLI contract for partial failure handling."""

    def test_partial_failure_response_format(self, tmp_path: Path) -> None:
        """Test response format when some materializations fail."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Valid Chapter 1]()
- [Valid Chapter 2]()
- [Invalid/Chapter]()
- [Another:Invalid]()
- [Valid Chapter 3]()
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        runner = CliRunner()
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case,
        ):
            # Mock partial failure result
            mock_result = MagicMock()
            mock_result.total_placeholders = 5

            # Create successful materializations
            successful = []
            for i, title in enumerate(['Valid Chapter 1', 'Valid Chapter 2', 'Valid Chapter 3'], 1):
                mock_success = MagicMock()
                mock_success.display_title = title
                mock_success.node_id = MagicMock(value=f'01923f0c-1234-7123-8abc-def01234567{i}')
                mock_success.position = f'[{i - 1}]'
                successful.append(mock_success)

            # Create failed materializations
            failures = []
            for title, error_type, error_msg in [
                ('Invalid/Chapter', 'filesystem', 'Invalid characters in filename'),
                ('Another:Invalid', 'filesystem', 'Invalid characters in filename'),
            ]:
                mock_failure = MagicMock()
                mock_failure.display_title = title
                mock_failure.error_type = error_type
                mock_failure.error_message = error_msg
                mock_failure.position = '[2]'
                failures.append(mock_failure)

            mock_result.successful_materializations = successful
            mock_result.failed_materializations = failures
            mock_result.execution_time = 3.456

            mock_use_case.return_value.execute.return_value = mock_result

            # Run with JSON output
            result = runner.invoke(cli, ['materialize', '--all', '--json', '--path', str(tmp_path)])

            # Partial failure should exit with code 1
            assert result.exit_code == 1

            # Validate JSON structure
            output = json.loads(result.output)
            assert output['type'] == 'batch_partial'
            assert output['total_placeholders'] == 5
            assert output['successful_materializations'] == 3
            assert output['failed_materializations'] == 2
            assert output['execution_time'] == 3.456
            assert 'Materialized 3 of 5 placeholders (2 failures)' in output['message']

            # Check successes
            assert 'successes' in output
            assert len(output['successes']) == 3
            for success in output['successes']:
                assert 'placeholder_title' in success
                assert 'node_id' in success

            # Check failures
            assert 'failures' in output
            assert len(output['failures']) == 2
            for failure in output['failures']:
                assert 'placeholder_title' in failure
                assert 'error_type' in failure
                assert failure['error_type'] == 'filesystem'
                assert 'error_message' in failure

    def test_partial_failure_human_readable_output(self, tmp_path: Path) -> None:
        """Test human-readable output for partial failures."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Good Chapter]()
- [Bad/Chapter]()
- [Another Good]()
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        runner = CliRunner()
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case,
        ):
            mock_result = MagicMock()
            mock_result.total_placeholders = 3

            # Mock successes
            successful = []
            for title in ['Good Chapter', 'Another Good']:
                mock_success = MagicMock()
                mock_success.display_title = title
                mock_success.node_id = MagicMock(value='01923f0c-1234-7123-8abc-def012345678')
                successful.append(mock_success)

            # Mock failure
            mock_failure = MagicMock()
            mock_failure.display_title = 'Bad/Chapter'
            mock_failure.error_type = 'filesystem'
            mock_failure.error_message = 'Invalid characters in filename'

            mock_result.successful_materializations = successful
            mock_result.failed_materializations = [mock_failure]
            mock_result.execution_time = 1.0

            mock_use_case.return_value.execute.return_value = mock_result

            result = runner.invoke(cli, ['materialize', '--all', '--path', str(tmp_path)])

            assert result.exit_code == 1

            # Check for expected messages in output
            assert "✓ Materialized 'Good Chapter'" in result.output
            assert "✓ Materialized 'Another Good'" in result.output
            assert "✗ Failed to materialize 'Bad/Chapter'" in result.output
            assert 'Invalid characters in filename' in result.output
            assert 'Materialized 2 of 3 placeholders (1 failure)' in result.output

    def test_all_failures_response(self, tmp_path: Path) -> None:
        """Test response when all materializations fail."""
        binder_path = tmp_path / '_binder.md'
        binder_content = """# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Bad/Title1]()
- [Bad:Title2]()
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

            failures = []
            for title in ['Bad/Title1', 'Bad:Title2']:
                mock_failure = MagicMock()
                mock_failure.display_title = title
                mock_failure.error_type = 'filesystem'
                mock_failure.error_message = 'Invalid characters'
                failures.append(mock_failure)

            mock_result.failed_materializations = failures
            mock_result.execution_time = 0.5

            mock_use_case.return_value.execute.return_value = mock_result

            result = runner.invoke(cli, ['materialize', '--all', '--json', '--path', str(tmp_path)])

            # All failures should still exit with code 1
            assert result.exit_code == 1

            output = json.loads(result.output)
            assert output['type'] == 'batch_partial'
            assert output['total_placeholders'] == 2
            assert output['successful_materializations'] == 0
            assert output['failed_materializations'] == 2
            assert len(output['failures']) == 2
            assert len(output['successes']) == 0
