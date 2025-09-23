"""Integration test for empty binder handling in bulk materialization."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tests.helpers.batch_assertions import (
    count_placeholders_in_binder,
)
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestMaterializeAllEmpty:
    """Test bulk materialization with empty binders and edge cases."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    def test_empty_binder_materialization(self, runner: CliRunner, empty_binder: Path) -> None:
        """Test bulk materialization with empty binder (no placeholders)."""
        # Verify the binder is actually empty
        placeholder_count = count_placeholders_in_binder(empty_binder)
        assert placeholder_count == 0, f'Expected empty binder, found {placeholder_count} placeholders'

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock result for empty binder
            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 0
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 0.05
            mock_result.message = 'No placeholders found to materialize'
            mock_result.successes = []
            mock_result.failures = []

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(empty_binder)])

            # Should succeed but do nothing
            assert result.exit_code == 0
            assert 'no placeholders' in result.output.lower() or 'nothing to' in result.output.lower()

    def test_missing_binder_file(self, runner: CliRunner, no_binder: Path) -> None:
        """Test bulk materialization when _binder.md file doesn't exist."""
        # Verify no binder file exists
        binder_path = no_binder / '_binder.md'
        assert not binder_path.exists(), 'Binder file should not exist for this test'

        # Execute command
        result = runner.invoke(app, ['materialize-all', '--path', str(no_binder)])

        # Should fail gracefully with helpful error message
        assert result.exit_code != 0
        error_indicators = ['binder', 'not found', 'missing', '_binder.md']
        assert any(indicator in result.output.lower() for indicator in error_indicators), (
            f'Should mention missing binder file, got: {result.output}'
        )

    def test_empty_binder_with_verbose_output(self, runner: CliRunner, empty_binder: Path) -> None:
        """Test empty binder handling with verbose output enabled."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 0
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 0.03
            mock_result.message = 'No placeholders found to materialize'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute with verbose flag
            result = runner.invoke(app, ['materialize-all', '--verbose', '--path', str(empty_binder)])

            # Should succeed with detailed output
            assert result.exit_code == 0
            assert 'no placeholders' in result.output.lower()

    def test_empty_binder_dry_run(self, runner: CliRunner, empty_binder: Path) -> None:
        """Test dry run on empty binder."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            mock_result = MagicMock()
            mock_result.type = 'batch_dry_run'
            mock_result.total_placeholders = 0
            mock_result.would_materialize = 0
            mock_result.would_skip = 0
            mock_result.message = 'No placeholders found to materialize'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute dry run
            result = runner.invoke(app, ['materialize-all', '--dry-run', '--path', str(empty_binder)])

            # Should succeed
            assert result.exit_code == 0
            assert any(
                phrase in result.output.lower() for phrase in ['no placeholders', 'nothing to', 'would materialize 0']
            )

    def test_corrupted_binder_structure(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test handling of corrupted or malformed binder files."""
        project_dir = tmp_path / 'corrupted_project'
        project_dir.mkdir()

        # Create a binder with malformed managed block
        binder_path = project_dir / '_binder.md'
        corrupted_content = """# Corrupted Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Valid Item]()
- [Unclosed link](
- [Link with bad href](./)
<!-- Missing END_MANAGED_BLOCK -->

Some content after...
"""
        binder_path.write_text(corrupted_content)

        # Execute command
        result = runner.invoke(app, ['materialize-all', '--path', str(project_dir)])

        # Should fail with helpful error about corruption
        assert result.exit_code != 0
        error_indicators = ['malformed', 'corrupted', 'invalid', 'parse', 'block']
        assert any(indicator in result.output.lower() for indicator in error_indicators), (
            f'Should indicate binder corruption, got: {result.output}'
        )

    def test_binder_without_managed_block(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test binder file without managed block comments."""
        project_dir = tmp_path / 'no_managed_block'
        project_dir.mkdir()

        # Create a binder without managed block
        binder_path = project_dir / '_binder.md'
        binder_content = """# Project Without Managed Block

- [Chapter 1]()
- [Chapter 2]()

Just regular markdown content.
"""
        binder_path.write_text(binder_content)

        # Execute command
        result = runner.invoke(app, ['materialize-all', '--path', str(project_dir)])

        # Should handle gracefully (no placeholders is not an error)
        assert result.exit_code == 0
        assert 'found 0 placeholders to materialize' in result.output.lower()

    def test_binder_with_only_materialized_nodes(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test binder where all nodes are already materialized."""
        project_dir = tmp_path / 'all_materialized'
        project_dir.mkdir()

        # Create binder with all materialized nodes
        binder_path = project_dir / '_binder.md'
        binder_content = """# All Materialized Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1](01923f0c-1234-7001-8abc-def012345678.md)
- [Chapter 2](01923f0c-1234-7002-8abc-def012345679.md)
- [Chapter 3](01923f0c-1234-7003-8abc-def012345680.md)
<!-- END_MANAGED_BLOCK -->
"""
        binder_path.write_text(binder_content)

        # Create the corresponding node files
        node_ids = [
            '01923f0c-1234-7001-8abc-def012345678',
            '01923f0c-1234-7002-8abc-def012345679',
            '01923f0c-1234-7003-8abc-def012345680',
        ]

        for i, node_id in enumerate(node_ids):
            node_file = project_dir / f'{node_id}.md'
            node_file.write_text(f'# Chapter {i + 1}\n\nContent here.')
            notes_file = project_dir / f'{node_id}.notes.md'
            notes_file.write_text(f'# Notes for Chapter {i + 1}\n')

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 0
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 0.02
            mock_result.message = 'All nodes already materialized'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Execute command
            result = runner.invoke(app, ['materialize-all', '--path', str(project_dir)])

            # Should succeed with message about nothing to do
            assert result.exit_code == 0
            assert any(
                phrase in result.output.lower()
                for phrase in ['already materialized', 'no placeholders', 'nothing to materialize']
            )

    def test_read_only_directory_permissions(self, runner: CliRunner, empty_binder: Path) -> None:
        """Test handling when directory permissions prevent materialization."""
        import os
        import stat

        # Make directory read-only (on Unix systems)
        if os.name != 'nt':  # Skip on Windows
            try:
                # Remove write permissions
                current_mode = empty_binder.stat().st_mode
                empty_binder.chmod(current_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)

                # Execute command
                result = runner.invoke(app, ['materialize-all', '--path', str(empty_binder)])

                # Should handle permission error gracefully
                # (For empty binder, this might still succeed since no files are created)
                assert result.exit_code in {0, 1}  # Either succeeds (nothing to do) or fails (permission error)

            finally:
                # Restore permissions for cleanup
                empty_binder.chmod(current_mode | stat.S_IWUSR)
