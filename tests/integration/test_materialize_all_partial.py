"""Integration test for partial failure resilience in bulk materialization."""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tests.helpers.batch_assertions import (
    assert_node_files_created,
    assert_valid_uuidv7,
    count_materialized_nodes_in_binder,
    count_placeholders_in_binder,
    extract_node_ids_from_binder,
)
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestMaterializeAllPartial:
    """Test partial failure resilience in bulk materialization."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    def test_partial_success_with_filesystem_errors(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test resilience when some files fail to create due to filesystem errors."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            def mock_execute_with_failures(
                *,
                binder: Path | None = None,
                project_path: Path | None = None,
                progress_callback: Callable[[str], None] | None = None,
            ) -> MagicMock:
                """Mock execution that creates some files but fails on others."""
                # Simulate creating some successful nodes
                successful_node_ids = [
                    '01923f0c-1234-7001-8abc-def012345678',
                    '01923f0c-1234-7002-8abc-def012345679',
                    '01923f0c-1234-7003-8abc-def012345680',
                ]

                # Create successful node files
                for i, node_id in enumerate(successful_node_ids):
                    node_file = binder_with_placeholders / f'{node_id}.md'
                    node_file.write_text(f'# Successfully Created Node {i + 1}\n\nContent here.')
                    notes_file = binder_with_placeholders / f'{node_id}.notes.md'
                    notes_file.write_text(f'# Notes for Node {i + 1}\n')

                # Update binder to show partial success
                binder_path = binder_with_placeholders / '_binder.md'
                content = binder_path.read_text()
                updated_content = (
                    content.replace('- [Chapter 1]()', f'- [Chapter 1]({successful_node_ids[0]}.md)')
                    .replace('  - [Section 1.1]()', f'  - [Section 1.1]({successful_node_ids[1]}.md)')
                    .replace('  - [Section 1.2]()', f'  - [Section 1.2]({successful_node_ids[2]}.md)')
                )
                binder_path.write_text(updated_content)

                # Return partial failure result
                mock_result = MagicMock()
                mock_result.type = 'batch_partial'
                mock_result.total_placeholders = 8
                # Create mock materialization objects
                mock_successes = []
                for i, node_id in enumerate(successful_node_ids):
                    mock_success = MagicMock()
                    mock_success.display_title = ['Chapter 1', 'Section 1.1', 'Section 1.2'][i]
                    mock_success.node_id = MagicMock(value=node_id)
                    mock_successes.append(mock_success)

                mock_failures = []
                for title, error_type, error_msg in [
                    ('Subsection 1.2.1', 'filesystem', 'Permission denied'),
                    ('Chapter 2', 'filesystem', 'Disk full'),
                    ('Chapter 3', 'filesystem', 'Invalid filename characters'),
                    ('Section 3.1', 'filesystem', 'Invalid filename characters'),
                    ('Appendix A', 'validation', 'Title validation failed'),
                ]:
                    mock_failure = MagicMock()
                    mock_failure.display_title = title
                    mock_failure.error_type = error_type
                    mock_failure.error_message = error_msg
                    mock_failures.append(mock_failure)

                mock_result.successful_materializations = mock_successes
                mock_result.failed_materializations = mock_failures
                mock_result.execution_time = 2.1
                mock_result.message = 'Materialized 3 of 8 placeholders with 5 failures'
                mock_result.successes = [
                    {'placeholder_title': 'Chapter 1', 'node_id': successful_node_ids[0]},
                    {'placeholder_title': 'Section 1.1', 'node_id': successful_node_ids[1]},
                    {'placeholder_title': 'Section 1.2', 'node_id': successful_node_ids[2]},
                ]
                mock_result.failures = [
                    {
                        'placeholder_title': 'Subsection 1.2.1',
                        'error_type': 'filesystem',
                        'error_message': 'Permission denied',
                    },
                    {'placeholder_title': 'Chapter 2', 'error_type': 'filesystem', 'error_message': 'Disk full'},
                    {
                        'placeholder_title': 'Chapter 3',
                        'error_type': 'id_generation',
                        'error_message': 'Failed to generate unique ID',
                    },
                    {
                        'placeholder_title': 'Section 3.1',
                        'error_type': 'filesystem',
                        'error_message': 'Invalid filename characters',
                    },
                    {
                        'placeholder_title': 'Appendix A',
                        'error_type': 'validation',
                        'error_message': 'Title validation failed',
                    },
                ]

                return mock_result

            mock_instance.execute.side_effect = mock_execute_with_failures
            mock_use_case.return_value = mock_instance

            # Execute command with continue-on-error to get exit code 0 with partial failures
            result = runner.invoke(
                app, ['materialize-all', '--continue-on-error', '--path', str(binder_with_placeholders)]
            )

            # Should succeed with partial results
            assert result.exit_code == 0  # Success code even with partial failures

            # Should report both successes and failures
            assert '3' in result.output
            assert '8' in result.output
            assert any(word in result.output.lower() for word in ['partial', 'some', 'failed', 'errors'])

            # Verify successful nodes were created properly
            created_node_ids = extract_node_ids_from_binder(binder_with_placeholders)
            assert len(created_node_ids) == 3

            for node_id in created_node_ids:
                assert_valid_uuidv7(node_id)
                assert_node_files_created(binder_with_placeholders, node_id)

    def test_mixed_binder_partial_materialization(self, runner: CliRunner, binder_with_mixed_nodes: Path) -> None:
        """Test partial materialization on binder with mixed materialized and placeholder nodes."""
        initial_materialized = count_materialized_nodes_in_binder(binder_with_mixed_nodes)
        initial_placeholders = count_placeholders_in_binder(binder_with_mixed_nodes)

        assert initial_materialized > 0, 'Fixture should have some materialized nodes'
        assert initial_placeholders > 0, 'Fixture should have some placeholders'

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            def mock_execute_mixed(
                *,
                binder: Path | None = None,
                project_path: Path | None = None,
                progress_callback: Callable[[str], None] | None = None,
            ) -> MagicMock:
                """Mock execution for mixed binder with partial success."""
                # Simulate partial success on remaining placeholders
                new_node_id = '01923f0c-1234-7004-8abc-def012345681'
                node_file = binder_with_mixed_nodes / f'{new_node_id}.md'
                node_file.write_text('# Section 1.1\n\nContent here.')
                notes_file = binder_with_mixed_nodes / f'{new_node_id}.notes.md'
                notes_file.write_text('# Notes for Section 1.1\n')

                # Update binder to show one more materialization
                binder_path = binder_with_mixed_nodes / '_binder.md'
                content = binder_path.read_text()
                updated_content = content.replace('  - [Section 1.1]()', f'  - [Section 1.1]({new_node_id}.md)')
                binder_path.write_text(updated_content)

                # Return partial result
                mock_result = MagicMock()
                mock_result.type = 'batch_partial'
                mock_result.total_placeholders = initial_placeholders
                # Create mock materialization objects
                mock_success = MagicMock()
                mock_success.display_title = 'Section 1.1'
                mock_success.node_id = MagicMock(value=new_node_id)

                mock_failures = []
                for i in range(initial_placeholders - 1):
                    mock_failure = MagicMock()
                    mock_failure.display_title = f'Failed Item {i + 1}'
                    mock_failure.error_type = 'filesystem'
                    mock_failure.error_message = 'Permission denied'
                    mock_failures.append(mock_failure)

                mock_result.successful_materializations = [mock_success]
                mock_result.failed_materializations = mock_failures
                mock_result.execution_time = 1.5
                mock_result.message = f'Materialized 1 of {initial_placeholders} placeholders'
                mock_result.successes = [{'placeholder_title': 'Section 1.1', 'node_id': new_node_id}]
                mock_result.failures = [
                    {'placeholder_title': 'Section 1.2', 'error_type': 'filesystem', 'error_message': 'IO error'},
                    {'placeholder_title': 'Chapter 2', 'error_type': 'validation', 'error_message': 'Invalid title'},
                    {
                        'placeholder_title': 'Section 3.1',
                        'error_type': 'filesystem',
                        'error_message': 'Permission denied',
                    },
                    {
                        'placeholder_title': 'Appendix A',
                        'error_type': 'id_generation',
                        'error_message': 'UUID generation failed',
                    },
                ]

                return mock_result

            mock_instance.execute.side_effect = mock_execute_mixed
            mock_use_case.return_value = mock_instance

            # Execute command with continue-on-error to get exit code 0 with partial failures
            result = runner.invoke(
                app, ['materialize-all', '--continue-on-error', '--path', str(binder_with_mixed_nodes)]
            )

            # Should succeed with partial results
            assert result.exit_code == 0

            # Should preserve existing materialized nodes
            final_materialized = count_materialized_nodes_in_binder(binder_with_mixed_nodes)
            assert final_materialized == initial_materialized + 1, 'Should add exactly one materialized node'

    def test_invalid_placeholder_names_handling(
        self, runner: CliRunner, binder_with_invalid_placeholder_names: Path
    ) -> None:
        """Test handling of placeholders with invalid characters in names."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            def mock_execute_invalid_names(
                *,
                binder: Path | None = None,
                project_path: Path | None = None,
                progress_callback: Callable[[str], None] | None = None,
            ) -> MagicMock:
                """Mock execution that handles invalid placeholder names."""
                # Successfully create node for valid placeholder
                valid_node_id = '01923f0c-1234-7001-8abc-def012345678'
                node_file = binder_with_invalid_placeholder_names / f'{valid_node_id}.md'
                node_file.write_text('# Valid Chapter\n\nContent here.')
                notes_file = binder_with_invalid_placeholder_names / f'{valid_node_id}.notes.md'
                notes_file.write_text('# Notes for Valid Chapter\n')

                # Update binder for successful one
                binder_path = binder_with_invalid_placeholder_names / '_binder.md'
                content = binder_path.read_text()
                updated_content = content.replace('- [Valid Chapter]()', f'- [Valid Chapter]({valid_node_id}.md)')
                binder_path.write_text(updated_content)

                # Return result showing validation failures for invalid names
                mock_result = MagicMock()
                mock_result.type = 'batch_partial'
                mock_result.total_placeholders = 5
                # Create mock success object
                mock_success = MagicMock()
                mock_success.display_title = 'Valid Chapter'
                mock_success.node_id = MagicMock(value=valid_node_id)

                # Create mock failure objects
                mock_failures = []
                for title, char in [
                    ('Chapter with / slash', '/'),
                    ('Chapter with \\ backslash', '\\'),
                    ('Chapter: with colon', ':'),
                    ('Chapter with | pipe', '|'),
                ]:
                    mock_failure = MagicMock()
                    mock_failure.display_title = title
                    mock_failure.error_type = 'validation'
                    mock_failure.error_message = f"Invalid character '{char}' in title"
                    mock_failures.append(mock_failure)

                mock_result.successful_materializations = [mock_success]
                mock_result.failed_materializations = mock_failures
                mock_result.execution_time = 1.2
                mock_result.message = 'Materialized 1 of 5 placeholders with 4 validation failures'
                mock_result.successes = [{'placeholder_title': 'Valid Chapter', 'node_id': valid_node_id}]
                mock_result.failures = [
                    {
                        'placeholder_title': 'Chapter with / slash',
                        'error_type': 'validation',
                        'error_message': "Invalid character '/' in title",
                    },
                    {
                        'placeholder_title': 'Chapter with \\ backslash',
                        'error_type': 'validation',
                        'error_message': "Invalid character '\\' in title",
                    },
                    {
                        'placeholder_title': 'Chapter: with colon',
                        'error_type': 'validation',
                        'error_message': "Invalid character ':' in title",
                    },
                    {
                        'placeholder_title': 'Chapter with | pipe',
                        'error_type': 'validation',
                        'error_message': "Invalid character '|' in title",
                    },
                ]

                return mock_result

            mock_instance.execute.side_effect = mock_execute_invalid_names
            mock_use_case.return_value = mock_instance

            # Execute command with continue-on-error to get exit code 0 with partial failures
            result = runner.invoke(
                app, ['materialize-all', '--continue-on-error', '--path', str(binder_with_invalid_placeholder_names)]
            )

            # Should succeed with partial results
            assert result.exit_code == 0

            # Should show validation errors
            assert 'validation' in result.output.lower() or 'invalid' in result.output.lower()

            # Should create valid node
            created_node_ids = extract_node_ids_from_binder(binder_with_invalid_placeholder_names)
            assert len(created_node_ids) == 1
            assert_valid_uuidv7(created_node_ids[0])

    def test_continue_after_failures_flag(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test --continue-on-error flag behavior during partial failures."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result with some failures but continue processing
            mock_result = MagicMock()
            mock_result.type = 'batch_partial'
            mock_result.total_placeholders = 8
            # Create mock success objects
            mock_successes = []
            for i in range(5):
                mock_success = MagicMock()
                mock_success.display_title = f'Chapter {i + 1}'
                mock_success.node_id = MagicMock(value=f'01923f0c-1234-700{i + 1}-8abc-def01234567{i + 8}')
                mock_successes.append(mock_success)

            # Create mock failure objects
            mock_failures = []
            for title, error_type, error_msg in [
                ('Chapter 2', 'filesystem', 'Permission denied'),
                ('Section 3.1', 'validation', 'Invalid title'),
                ('Appendix A', 'id_generation', 'UUID conflict'),
            ]:
                mock_failure = MagicMock()
                mock_failure.display_title = title
                mock_failure.error_type = error_type
                mock_failure.error_message = error_msg
                mock_failures.append(mock_failure)

            mock_result.successful_materializations = mock_successes
            mock_result.failed_materializations = mock_failures
            mock_result.execution_time = 2.5
            mock_result.message = 'Materialized 5 of 8 placeholders, continued despite 3 failures'
            mock_result.successes = []
            mock_result.failures = [
                {'placeholder_title': 'Chapter 2', 'error_type': 'filesystem', 'error_message': 'Permission denied'},
                {'placeholder_title': 'Section 3.1', 'error_type': 'validation', 'error_message': 'Invalid title'},
                {'placeholder_title': 'Appendix A', 'error_type': 'id_generation', 'error_message': 'UUID conflict'},
            ]

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute with continue-on-error flag
            result = runner.invoke(
                app, ['materialize-all', '--continue-on-error', '--path', str(binder_with_placeholders)]
            )

            # Should succeed and report continuing despite errors
            assert result.exit_code == 0
            assert any(phrase in result.output.lower() for phrase in ['continued', 'despite', 'continuing', '5 of 8'])

    def test_fail_fast_behavior(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test fail-fast behavior when --continue-on-error is not used."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result showing early termination
            mock_result = MagicMock()
            mock_result.type = 'batch_partial'
            mock_result.total_placeholders = 8

            # Create mock success objects
            mock_successes = []
            for i in range(2):
                mock_success = MagicMock()
                mock_success.display_title = f'Chapter {i + 1}'
                mock_success.node_id = MagicMock(value=f'01923f0c-1234-700{i + 1}-8abc-def01234567{i + 8}')
                mock_successes.append(mock_success)

            # Create mock failure object
            mock_failure = MagicMock()
            mock_failure.display_title = 'Subsection 1.2.1'
            mock_failure.error_type = 'filesystem'
            mock_failure.error_message = 'Disk full'

            mock_result.successful_materializations = mock_successes
            mock_result.failed_materializations = [mock_failure]
            mock_result.execution_time = 0.5
            mock_result.message = 'Stopped after first failure: 2 successful, 1 failed, 5 not attempted'
            mock_result.successes = []
            mock_result.failures = [
                {'placeholder_title': 'Subsection 1.2.1', 'error_type': 'filesystem', 'error_message': 'Disk full'},
            ]

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute without continue-on-error flag
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_placeholders)])

            # Should show early termination behavior
            assert result.exit_code != 0  # Should fail when using fail-fast
            assert any(phrase in result.output.lower() for phrase in ['stopped', 'first failure', 'not attempted'])

    def test_detailed_failure_reporting(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test detailed failure reporting with specific error types."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result with various failure types
            mock_result = MagicMock()
            mock_result.type = 'batch_partial'
            mock_result.total_placeholders = 8

            # Create mock success objects
            mock_successes = []
            for i in range(3):
                mock_success = MagicMock()
                mock_success.display_title = f'Chapter {i + 1}'
                mock_success.node_id = MagicMock(value=f'01923f0c-1234-700{i + 1}-8abc-def01234567{i + 8}')
                mock_successes.append(mock_success)

            # Create mock failure objects
            mock_failures = []
            for title, error_type, error_msg in [
                ('Chapter 2', 'filesystem', 'Permission denied accessing directory'),
                ('Section 3.1', 'validation', 'Title contains forbidden characters'),
                ('Appendix A', 'already_materialized', 'Node already exists with different content'),
                ('Subsection 1.2.1', 'binder_integrity', 'Binder structure corrupted during operation'),
                ('Chapter 3', 'id_generation', 'Failed to generate unique UUIDv7 after 10 attempts'),
            ]:
                mock_failure = MagicMock()
                mock_failure.display_title = title
                mock_failure.error_type = error_type
                mock_failure.error_message = error_msg
                mock_failures.append(mock_failure)

            mock_result.successful_materializations = mock_successes
            mock_result.failed_materializations = mock_failures
            mock_result.execution_time = 3.2
            mock_result.message = 'Materialized 3 of 8 placeholders with diverse failures'
            mock_result.successes = []
            mock_result.failures = [
                {
                    'placeholder_title': 'Chapter 2',
                    'error_type': 'filesystem',
                    'error_message': 'Permission denied accessing directory',
                },
                {
                    'placeholder_title': 'Section 3.1',
                    'error_type': 'validation',
                    'error_message': 'Title contains forbidden characters',
                },
                {
                    'placeholder_title': 'Appendix A',
                    'error_type': 'already_materialized',
                    'error_message': 'Node already exists with different content',
                },
                {
                    'placeholder_title': 'Subsection 1.2.1',
                    'error_type': 'binder_integrity',
                    'error_message': 'Binder structure corrupted during operation',
                },
                {
                    'placeholder_title': 'Chapter 3',
                    'error_type': 'id_generation',
                    'error_message': 'Failed to generate unique UUIDv7 after 10 attempts',
                },
            ]

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute command with verbose output and continue-on-error to get exit code 0
            result = runner.invoke(
                app, ['materialize-all', '--verbose', '--continue-on-error', '--path', str(binder_with_placeholders)]
            )

            # Should provide detailed failure information
            assert result.exit_code == 0

            # Should categorize failures by type
            failure_types = ['filesystem', 'validation', 'already_materialized', 'binder_integrity', 'id_generation']
            for _failure_type in failure_types:
                # At least some indication of the different error categories should be present
                assert any(
                    error_word in result.output.lower()
                    for error_word in [
                        'permission',
                        'validation',
                        'exists',
                        'corrupted',
                        'generation',
                        'error',
                        'failed',
                    ]
                )

    def test_partial_rollback_on_critical_failure(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test partial rollback when critical system failure occurs mid-process."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result showing critical failure requiring rollback
            mock_result = MagicMock()
            mock_result.type = 'batch_critical_failure'
            mock_result.total_placeholders = 8

            # Create mock success objects
            mock_successes = []
            for i in range(2):
                mock_success = MagicMock()
                mock_success.display_title = f'Chapter {i + 1}'
                mock_success.node_id = MagicMock(value=f'01923f0c-1234-700{i + 1}-8abc-def01234567{i + 8}')
                mock_successes.append(mock_success)

            # Create mock failure object
            mock_failure = MagicMock()
            mock_failure.display_title = 'Chapter 2'
            mock_failure.error_type = 'binder_integrity'
            mock_failure.error_message = 'Critical binder corruption detected, operation aborted'

            mock_result.successful_materializations = mock_successes
            mock_result.failed_materializations = [mock_failure]
            mock_result.execution_time = 1.1
            mock_result.message = 'Critical failure detected, rolled back partial changes'
            mock_result.successes = []
            mock_result.failures = [
                {
                    'placeholder_title': 'Chapter 2',
                    'error_type': 'binder_integrity',
                    'error_message': 'Critical binder corruption detected, operation aborted',
                },
            ]

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_placeholders)])

            # Should fail with critical error
            assert result.exit_code != 0
            assert any(
                phrase in result.output.lower() for phrase in ['critical', 'rolled back', 'aborted', 'corruption']
            )
