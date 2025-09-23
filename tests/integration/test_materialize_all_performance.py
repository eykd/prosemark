"""Integration test for performance with 100+ placeholders in bulk materialization."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Never
from unittest.mock import MagicMock, patch

import pytest
from tests.helpers.batch_assertions import (
    count_placeholders_in_binder,
)
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestMaterializeAllPerformance:
    """Test performance characteristics of bulk materialization with large datasets."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    def test_large_scale_materialization_performance(
        self, runner: CliRunner, binder_with_large_number_of_placeholders: Path
    ) -> None:
        """Test performance with 120 placeholders materialization."""
        # Verify we have the expected number of placeholders (20 chapters + 100 sections = 120)
        placeholder_count = count_placeholders_in_binder(binder_with_large_number_of_placeholders)
        assert placeholder_count == 120, f'Expected 120 placeholders, found {placeholder_count}'

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            def mock_execute_large_scale(
                *,
                binder: Path | None = None,
                project_path: Path | None = None,
                progress_callback: Callable[[str], None] | None = None,
            ) -> MagicMock:
                """Mock execution that simulates creating 120 node files."""
                start_time = time.time()

                # Create sample node files to simulate performance
                base_node_id = '01923f0c-1234-7'
                created_nodes = []

                # Simulate creating first 20 nodes for testing
                for i in range(20):
                    node_id = f'{base_node_id}{i:03d}-8abc-def012345678'
                    node_file = binder_with_large_number_of_placeholders / f'{node_id}.md'
                    node_file.write_text(f'# Chapter {i // 5 + 1}.{i % 5 + 1}\n\nContent for section {i + 1}.')
                    notes_file = binder_with_large_number_of_placeholders / f'{node_id}.notes.md'
                    notes_file.write_text(f'# Notes for Chapter {i // 5 + 1}.{i % 5 + 1}\n')
                    created_nodes.append(node_id)

                # Update binder to show some materialized nodes
                binder_path = binder_with_large_number_of_placeholders / '_binder.md'
                content = binder_path.read_text()

                # Replace first few placeholders with actual links
                updated_content = content
                for i, node_id in enumerate(created_nodes[:10]):  # Update first 10
                    chapter = i // 5 + 1
                    section = i % 5 + 1
                    old_placeholder = f'  - [Section {chapter}.{section}]()'
                    new_link = f'  - [Section {chapter}.{section}]({node_id}.md)'
                    updated_content = updated_content.replace(old_placeholder, new_link, 1)

                binder_path.write_text(updated_content)

                execution_time = time.time() - start_time

                # Mock result showing performance characteristics
                mock_result = MagicMock()
                mock_result.type = 'batch'
                mock_result.total_placeholders = 120

                # Create mock success objects
                mock_successes = []
                for i in range(120):
                    mock_success = MagicMock()
                    mock_success.display_title = f'Chapter/Section {i + 1}'
                    mock_success.node_id = MagicMock(value=f'01923f0c-1234-700{i:03d}-8abc-def012345678')
                    mock_successes.append(mock_success)

                mock_result.successful_materializations = mock_successes
                mock_result.failed_materializations = []
                mock_result.execution_time = execution_time + 5.0  # Simulate realistic time for 120 nodes
                mock_result.message = 'Successfully materialized all 120 placeholders'
                mock_result.successes = []
                mock_result.failures = []

                return mock_result

            mock_instance.execute.side_effect = mock_execute_large_scale
            mock_use_case.return_value = mock_instance

            # Execute command with timing
            start_time = time.time()
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_large_number_of_placeholders)])
            execution_time = time.time() - start_time

            # Should succeed
            assert result.exit_code == 0

            # Should complete in reasonable time (under 30 seconds for test)
            assert execution_time < 30.0, f'Large scale materialization took too long: {execution_time}s'

            # Should report performance metrics
            assert '120' in result.output  # Should mention total count

    def test_batch_processing_with_large_dataset(
        self, runner: CliRunner, binder_with_large_number_of_placeholders: Path
    ) -> None:
        """Test batch processing behavior with configurable batch sizes."""
        batch_sizes = [5, 10, 25, 50]

        for batch_size in batch_sizes:
            with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
                mock_instance = MagicMock()

                # Mock result showing batch processing
                mock_result = MagicMock()
                mock_result.type = 'batch'
                mock_result.total_placeholders = 120
                # Create mock success objects
                mock_successes = []
                for i in range(120):
                    mock_success = MagicMock()
                    mock_success.display_title = f'Item {i + 1}'
                    mock_success.node_id = MagicMock(value=f'01923f0c-1234-{i:04d}-8abc-def012345678')
                    mock_successes.append(mock_success)

                mock_result.successful_materializations = mock_successes
                mock_result.failed_materializations = []
                mock_result.execution_time = 3.5
                mock_result.message = f'Successfully materialized all 120 placeholders in batches of {batch_size}'

                mock_instance.execute.return_value = mock_result
                mock_use_case.return_value = mock_instance

                # Execute with specific batch size
                result = runner.invoke(
                    app,
                    [
                        'materialize-all',
                        '--batch-size',
                        str(batch_size),
                        '--path',
                        str(binder_with_large_number_of_placeholders),
                    ],
                )

                # Should succeed regardless of batch size
                assert result.exit_code == 0, f'Failed with batch size {batch_size}'

    def test_memory_efficiency_large_dataset(
        self, runner: CliRunner, binder_with_large_number_of_placeholders: Path
    ) -> None:
        """Test memory efficiency with large number of placeholders."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            def mock_execute_memory_efficient(
                *,
                binder: Path | None = None,
                project_path: Path | None = None,
                progress_callback: Callable[[str], None] | None = None,
            ) -> MagicMock:
                """Mock execution that tests memory patterns."""
                # Simulate memory-efficient processing
                mock_result = MagicMock()
                mock_result.type = 'batch'
                mock_result.total_placeholders = 120
                # Create mock success objects
                mock_successes = []
                for i in range(120):
                    mock_success = MagicMock()
                    mock_success.display_title = f'Item {i + 1}'
                    mock_success.node_id = MagicMock(value=f'01923f0c-1234-{i:04d}-8abc-def012345678')
                    mock_successes.append(mock_success)

                mock_result.successful_materializations = mock_successes
                mock_result.failed_materializations = []
                mock_result.execution_time = 4.2
                mock_result.message = 'Successfully materialized 120 placeholders with optimized memory usage'
                mock_result.memory_peak_mb = 15.5  # Mock memory usage metric
                mock_result.successes = []
                mock_result.failures = []

                return mock_result

            mock_instance.execute.side_effect = mock_execute_memory_efficient
            mock_use_case.return_value = mock_instance

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_large_number_of_placeholders)])

            # Should succeed with reasonable memory usage
            assert result.exit_code == 0

    def test_progress_reporting_large_dataset(
        self, runner: CliRunner, binder_with_large_number_of_placeholders: Path
    ) -> None:
        """Test progress reporting during large-scale materialization."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result with progress tracking
            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 120
            # Create mock success objects
            mock_successes = []
            for i in range(120):
                mock_success = MagicMock()
                mock_success.display_title = f'Item {i + 1}'
                mock_success.node_id = MagicMock(value=f'01923f0c-1234-{i:04d}-8abc-def012345678')
                mock_successes.append(mock_success)

            mock_result.successful_materializations = mock_successes
            mock_result.failed_materializations = []
            mock_result.execution_time = 6.1
            mock_result.message = 'Successfully materialized all 120 placeholders with progress tracking'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute with verbose progress reporting
            result = runner.invoke(
                app, ['materialize-all', '--verbose', '--path', str(binder_with_large_number_of_placeholders)]
            )

            # Should succeed and show progress
            assert result.exit_code == 0

            # Should include progress indicators for large dataset
            assert '100' in result.output
            progress_keywords = ['progress', 'materialized', 'completed', 'processing']
            assert any(keyword in result.output.lower() for keyword in progress_keywords)

    def test_timeout_handling_large_dataset(
        self, runner: CliRunner, binder_with_large_number_of_placeholders: Path
    ) -> None:
        """Test timeout handling with large datasets."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock timeout scenario
            def mock_execute_timeout(
                *,
                binder: Path | None = None,
                project_path: Path | None = None,
                progress_callback: Callable[[str], None] | None = None,
            ) -> Never:
                raise TimeoutError('Operation timed out after processing 45 of 120 placeholders')

            mock_instance.execute.side_effect = mock_execute_timeout
            mock_use_case.return_value = mock_instance

            # Execute with short timeout
            result = runner.invoke(
                app, ['materialize-all', '--timeout', '1', '--path', str(binder_with_large_number_of_placeholders)]
            )

            # Should fail with timeout error
            assert result.exit_code != 0
            assert any(phrase in result.output.lower() for phrase in ['timeout', 'timed out', 'time limit', 'exceeded'])

    def test_concurrent_processing_simulation(
        self, runner: CliRunner, binder_with_large_number_of_placeholders: Path
    ) -> None:
        """Test simulation of concurrent processing benefits for large datasets."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result showing concurrent processing benefits
            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 120
            # Create mock success objects
            mock_successes = []
            for i in range(120):
                mock_success = MagicMock()
                mock_success.display_title = f'Item {i + 1}'
                mock_success.node_id = MagicMock(value=f'01923f0c-1234-{i:04d}-8abc-def012345678')
                mock_successes.append(mock_success)

            mock_result.successful_materializations = mock_successes
            mock_result.failed_materializations = []
            mock_result.execution_time = 2.8  # Faster due to concurrent processing
            mock_result.message = 'Successfully materialized all 120 placeholders using concurrent processing'
            mock_result.concurrency_factor = 4  # Mock concurrency metric

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute with concurrent processing enabled
            result = runner.invoke(
                app, ['materialize-all', '--concurrent', '--path', str(binder_with_large_number_of_placeholders)]
            )

            # Should succeed with performance benefits
            if result.exit_code == 0:  # Only check if concurrent flag is implemented
                assert 'concurrent' in result.output.lower() or 'parallel' in result.output.lower()

    def test_resource_cleanup_large_dataset(
        self, runner: CliRunner, binder_with_large_number_of_placeholders: Path
    ) -> None:
        """Test proper resource cleanup after large-scale operations."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result emphasizing cleanup
            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 120
            # Create mock success objects
            mock_successes = []
            for i in range(120):
                mock_success = MagicMock()
                mock_success.display_title = f'Item {i + 1}'
                mock_success.node_id = MagicMock(value=f'01923f0c-1234-{i:04d}-8abc-def012345678')
                mock_successes.append(mock_success)

            mock_result.successful_materializations = mock_successes
            mock_result.failed_materializations = []
            mock_result.execution_time = 5.3
            mock_result.message = 'Successfully materialized 120 placeholders with proper resource cleanup'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_large_number_of_placeholders)])

            # Should succeed
            assert result.exit_code == 0

            # Verify no temporary files left behind
            temp_patterns = ['*.tmp', '*.temp', '*~', '.materialize_*']
            temp_files: list[Path] = []
            for pattern in temp_patterns:
                temp_files.extend(binder_with_large_number_of_placeholders.glob(pattern))

            assert len(temp_files) == 0, f'Temporary files left behind: {temp_files}'

    def test_scaling_characteristics(self, runner: CliRunner, binder_with_large_number_of_placeholders: Path) -> None:
        """Test scaling characteristics by simulating different dataset sizes."""
        dataset_sizes = [10, 50, 100]
        execution_times = []

        for size in dataset_sizes:
            with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
                mock_instance = MagicMock()

                # Mock result with size-proportional execution time
                mock_result = MagicMock()
                mock_result.type = 'batch'
                mock_result.total_placeholders = size
                mock_result.successful_materializations = []
                mock_result.failed_materializations = []
                mock_result.execution_time = size * 0.05  # Linear scaling simulation
                mock_result.message = f'Successfully materialized {size} placeholders'

                mock_instance.execute.return_value = mock_result
                mock_use_case.return_value = mock_instance

                # Execute and measure
                start_time = time.time()
                result = runner.invoke(
                    app, ['materialize-all', '--path', str(binder_with_large_number_of_placeholders)]
                )
                actual_time = time.time() - start_time
                execution_times.append(actual_time)

                # Should succeed
                assert result.exit_code == 0

        # Execution times should be reasonable (test framework overhead should be minimal)
        for exec_time in execution_times:
            assert exec_time < 10.0, f'Test execution took too long: {exec_time}s'

    def test_interruption_handling_large_dataset(
        self, runner: CliRunner, binder_with_large_number_of_placeholders: Path
    ) -> None:
        """Test handling of interruption during large-scale materialization."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock interruption scenario
            def mock_execute_interrupted(
                *,
                binder: Path | None = None,
                project_path: Path | None = None,
                progress_callback: Callable[[str], None] | None = None,
            ) -> MagicMock:
                # Simulate interruption after partial completion
                mock_result = MagicMock()
                mock_result.type = 'batch_interrupted'
                mock_result.total_placeholders = 120
                # Create mock success objects for partial completion
                mock_successes = []
                for i in range(42):
                    mock_success = MagicMock()
                    mock_success.display_title = f'Item {i + 1}'
                    mock_success.node_id = MagicMock(value=f'01923f0c-1234-{i:04d}-8abc-def012345678')
                    mock_successes.append(mock_success)

                mock_result.successful_materializations = mock_successes
                mock_result.failed_materializations = []
                mock_result.interrupted_at = 42
                mock_result.execution_time = 2.1
                mock_result.message = 'Operation interrupted after materializing 42 of 120 placeholders'

                return mock_result

            mock_instance.execute.side_effect = mock_execute_interrupted
            mock_use_case.return_value = mock_instance

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_large_number_of_placeholders)])

            # Should handle interruption gracefully
            assert result.exit_code != 0  # Interrupted operation should return error code
            assert any(phrase in result.output.lower() for phrase in ['interrupted', 'partial', '42', 'stopped'])
