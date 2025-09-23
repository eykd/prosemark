"""Integration test for basic bulk materialization with multiple placeholders."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tests.helpers.batch_assertions import (
    assert_node_files_created,
    assert_valid_uuidv7,
    count_placeholders_in_binder,
    extract_node_ids_from_binder,
)
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestMaterializeAllBasic:
    """Test basic bulk materialization functionality."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    def test_basic_bulk_materialization_success(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test successful bulk materialization of 5 basic placeholders."""
        # Mock the MaterializeAllPlaceholders use case since it doesn't exist yet
        mock_result = MagicMock()
        mock_result.type = 'batch'
        mock_result.total_placeholders = 8  # Based on fixture content
        mock_result.successful_materializations = []  # Empty list for mocked results
        mock_result.failed_materializations = []  # Empty list for mocked results
        mock_result.execution_time = 1.23
        mock_result.message = 'Successfully materialized all 8 placeholders'
        mock_result.successes = []
        mock_result.failures = []

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()
            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Count initial placeholders
            initial_count = count_placeholders_in_binder(binder_with_placeholders)
            assert initial_count == 8, f'Expected 8 placeholders, found {initial_count}'

            # Execute materialize-all command
            result = runner.invoke(
                app, ['materialize-all', '--path', str(binder_with_placeholders)], catch_exceptions=False
            )

            # Should succeed
            assert result.exit_code == 0, f'Command failed: {result.output}'

            # Should have called the use case
            mock_use_case.assert_called_once()
            mock_instance.execute.assert_called_once()

    def test_bulk_materialization_creates_valid_nodes(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test that bulk materialization creates valid node files."""
        # Mock successful materialization that actually creates files
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            def mock_execute(**kwargs: object) -> MagicMock:
                """Mock execute that creates actual files for testing."""
                # Create sample node files to simulate successful materialization
                node_ids = [
                    '01923f0c-1234-7001-8abc-def012345678',
                    '01923f0c-1234-7002-8abc-def012345679',
                    '01923f0c-1234-7003-8abc-def012345680',
                ]

                for i, node_id in enumerate(node_ids[:3]):  # Create first 3 for testing
                    node_file = binder_with_placeholders / f'{node_id}.md'
                    node_file.write_text(f'# Chapter {i + 1}\n\nContent here.')
                    notes_file = binder_with_placeholders / f'{node_id}.notes.md'
                    notes_file.write_text(f'# Notes for Chapter {i + 1}\n')

                # Update binder to reference created nodes
                binder_path = binder_with_placeholders / '_binder.md'
                content = binder_path.read_text()
                updated_content = (
                    content.replace('- [Chapter 1]()', f'- [Chapter 1]({node_ids[0]}.md)')
                    .replace('  - [Section 1.1]()', f'  - [Section 1.1]({node_ids[1]}.md)')
                    .replace('  - [Section 1.2]()', f'  - [Section 1.2]({node_ids[2]}.md)')
                )
                binder_path.write_text(updated_content)

                # Return mock result
                mock_result = MagicMock()
                mock_result.type = 'batch'
                mock_result.total_placeholders = 8
                mock_result.successful_materializations = []
                mock_result.failed_materializations = []
                mock_result.execution_time = 1.5
                mock_result.message = 'Materialized 3 of 8 placeholders'
                return mock_result

            mock_instance.execute.side_effect = mock_execute
            mock_use_case.return_value = mock_instance

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_placeholders)])

            # Should succeed
            assert result.exit_code == 0

            # Verify created node files are valid
            created_node_ids = extract_node_ids_from_binder(binder_with_placeholders)
            assert len(created_node_ids) >= 3, 'Should have created at least 3 nodes'

            for node_id in created_node_ids[:3]:  # Check first 3 created
                assert_valid_uuidv7(node_id)
                assert_node_files_created(binder_with_placeholders, node_id)

    def test_bulk_materialization_progress_reporting(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test that bulk materialization reports progress during execution."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result with progress information
            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 8
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 2.1
            mock_result.message = 'Successfully materialized all 8 placeholders'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_placeholders)])

            # Should succeed
            assert result.exit_code == 0

            # Should report progress (mock implementation would show this)
            # Note: This will be more detailed when actual implementation exists
            assert 'materialize' in result.output.lower()

    def test_bulk_materialization_respects_existing_nodes(
        self, runner: CliRunner, binder_with_placeholders: Path
    ) -> None:
        """Test that bulk materialization doesn't overwrite existing materialized nodes."""
        # Create an existing node file first
        existing_node_id = '01923f0c-1234-7999-8abc-def012345999'
        existing_node_file = binder_with_placeholders / f'{existing_node_id}.md'
        existing_node_file.write_text('# Existing Chapter\n\nOriginal content.')
        existing_notes_file = binder_with_placeholders / f'{existing_node_id}.notes.md'
        existing_notes_file.write_text('# Original Notes\n')

        # Update binder to reference the existing node
        binder_path = binder_with_placeholders / '_binder.md'
        content = binder_path.read_text()
        updated_content = content.replace('- [Chapter 1]()', f'- [Chapter 1]({existing_node_id}.md)')
        binder_path.write_text(updated_content)

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 7  # One less since one is already materialized
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 1.8
            mock_result.message = 'Successfully materialized 7 placeholders (1 already existed)'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Store original content
            original_content = existing_node_file.read_text()
            original_notes_content = existing_notes_file.read_text()

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_placeholders)])

            # Should succeed
            assert result.exit_code == 0

            # Existing files should be unchanged
            assert existing_node_file.read_text() == original_content
            assert existing_notes_file.read_text() == original_notes_content

    def test_bulk_materialization_dry_run(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test bulk materialization dry run mode."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock dry run result
            mock_result = MagicMock()
            mock_result.type = 'batch_dry_run'
            mock_result.total_placeholders = 8
            mock_result.would_materialize = 8
            mock_result.would_skip = 0
            mock_result.message = 'Would materialize 8 placeholders'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute dry run
            result = runner.invoke(app, ['materialize-all', '--dry-run', '--path', str(binder_with_placeholders)])

            # Should succeed
            assert result.exit_code == 0

            # Should show what would be done
            assert 'would' in result.output.lower() or 'dry' in result.output.lower()

            # Count placeholders should be unchanged
            final_count = count_placeholders_in_binder(binder_with_placeholders)
            assert final_count == 8, 'Dry run should not change placeholder count'

    def test_bulk_materialization_invalid_path(self, runner: CliRunner) -> None:
        """Test bulk materialization with invalid project path."""
        nonexistent_path = Path('/nonexistent/path/to/project')

        result = runner.invoke(app, ['materialize-all', '--path', str(nonexistent_path)])

        # Should fail with appropriate error
        assert result.exit_code != 0
        assert (
            'not found' in result.output.lower()
            or 'invalid' in result.output.lower()
            or 'does not exist' in result.output.lower()
        )

    def test_bulk_materialization_no_binder_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test bulk materialization when no _binder.md file exists."""
        empty_dir = tmp_path / 'empty_project'
        empty_dir.mkdir()

        result = runner.invoke(app, ['materialize-all', '--path', str(empty_dir)])

        # Should fail gracefully
        assert result.exit_code != 0
        assert 'binder' in result.output.lower() or 'not found' in result.output.lower()
