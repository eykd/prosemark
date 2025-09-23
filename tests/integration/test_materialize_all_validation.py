"""Integration test for command validation and mutual exclusion in materialize-all."""

from pathlib import Path
from typing import Never
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestMaterializeAllValidation:
    """Test command validation and argument mutual exclusion for materialize-all."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    def test_mutually_exclusive_dry_run_and_force(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test that --dry-run and --force are mutually exclusive."""
        # Execute with both flags
        result = runner.invoke(
            app, ['materialize-all', '--dry-run', '--force', '--path', str(binder_with_placeholders)]
        )

        # Should fail with validation error
        assert result.exit_code != 0
        assert any(
            phrase in result.output.lower()
            for phrase in ['mutually exclusive', 'cannot use both', 'conflict', 'incompatible']
        )

    def test_mutually_exclusive_verbose_and_quiet(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test that --verbose and --quiet are mutually exclusive."""
        # Execute with both flags
        result = runner.invoke(
            app, ['materialize-all', '--verbose', '--quiet', '--path', str(binder_with_placeholders)]
        )

        # Should fail with validation error
        assert result.exit_code != 0
        assert any(
            phrase in result.output.lower()
            for phrase in ['mutually exclusive', 'cannot use both', 'conflict', 'incompatible']
        )

    def test_invalid_path_argument(self, runner: CliRunner) -> None:
        """Test validation of invalid path arguments."""
        invalid_paths = [
            '/dev/null',  # Not a directory
            '/nonexistent/deeply/nested/path',  # Nonexistent path
            'relative/../path',  # Relative path with traversal
        ]

        for invalid_path in invalid_paths:
            result = runner.invoke(app, ['materialize-all', '--path', invalid_path])

            # Should fail with path validation error
            assert result.exit_code != 0
            assert any(
                phrase in result.output.lower()
                for phrase in ['invalid path', 'not found', 'not a directory', 'path does not exist']
            )

    def test_missing_required_path_argument(self, runner: CliRunner) -> None:
        """Test that path argument is required when not in project directory."""
        # Execute without --path argument from non-project directory
        with runner.isolated_filesystem():
            result = runner.invoke(app, ['materialize-all'])

            # Should fail with missing binder error when not in project directory
            assert result.exit_code != 0
            assert any(
                phrase in result.output.lower() for phrase in ['binder file not found', 'not found', 'no _binder.md']
            )

    def test_conflicting_batch_size_options(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test validation of conflicting batch size options."""
        # Test invalid batch size values
        invalid_batch_sizes = [0, -1, -10]

        for batch_size in invalid_batch_sizes:
            result = runner.invoke(
                app, ['materialize-all', '--batch-size', str(batch_size), '--path', str(binder_with_placeholders)]
            )

            # Should fail with validation error
            assert result.exit_code != 0
            assert any(
                phrase in result.output.lower()
                for phrase in ['invalid batch size', 'must be positive', 'greater than zero']
            )

    def test_invalid_timeout_values(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test validation of invalid timeout values."""
        invalid_timeouts = [-1, 0, 'invalid', '10s']  # Negative, zero, non-numeric, with unit

        for timeout in invalid_timeouts:
            result = runner.invoke(
                app, ['materialize-all', '--timeout', str(timeout), '--path', str(binder_with_placeholders)]
            )

            # Should fail with validation error
            assert result.exit_code != 0
            assert any(
                phrase in result.output.lower()
                for phrase in ['invalid timeout', 'must be greater than zero', 'not a valid integer', 'invalid value']
            )

    def test_unknown_flag_validation(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test handling of unknown flags."""
        unknown_flags = [
            '--unknown-flag',
            '--materialize-what',
            '--invalid-option',
        ]

        for flag in unknown_flags:
            result = runner.invoke(app, ['materialize-all', flag, '--path', str(binder_with_placeholders)])

            # Should fail with unknown option error
            assert result.exit_code != 0
            assert any(
                phrase in result.output.lower()
                for phrase in ['unknown option', 'unrecognized', 'invalid option', 'no such option']
            )

    def test_valid_flag_combinations(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test that valid flag combinations are accepted."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 8
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 1.5
            mock_result.message = 'Successfully materialized all 8 placeholders'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            valid_combinations = [
                ['--verbose', '--continue-on-error'],
                ['--force', '--continue-on-error'],
                ['--quiet', '--force'],
                ['--batch-size', '5', '--timeout', '60'],
            ]

            for flags in valid_combinations:
                result = runner.invoke(app, ['materialize-all', *flags, '--path', str(binder_with_placeholders)])

                # Should succeed with valid combinations
                assert result.exit_code == 0, f'Valid combination failed: {flags}'

    def test_dry_run_exclusive_validations(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test that --dry-run is exclusive with modification flags."""
        modification_flags = [
            ['--force'],
            ['--continue-on-error'],
            ['--force', '--continue-on-error'],
        ]

        for flags in modification_flags:
            result = runner.invoke(
                app, ['materialize-all', '--dry-run', *flags, '--path', str(binder_with_placeholders)]
            )

            # Should fail due to mutual exclusion
            assert result.exit_code != 0
            assert any(
                phrase in result.output.lower()
                for phrase in ['mutually exclusive', 'dry-run', 'cannot modify', 'incompatible']
            )

    def test_help_flag_precedence(self, runner: CliRunner) -> None:
        """Test that --help flag takes precedence and shows usage."""
        result = runner.invoke(app, ['materialize-all', '--help'])

        # Should succeed and show help
        assert result.exit_code == 0
        assert any(phrase in result.output.lower() for phrase in ['usage', 'help', 'options', 'materialize-all'])

    def test_version_flag_validation(self, runner: CliRunner) -> None:
        """Test version flag handling if available."""
        result = runner.invoke(app, ['--version'])

        # Should either show version or indicate it's not a valid command option
        # (Depending on whether version is implemented)
        if result.exit_code == 0:
            assert any(phrase in result.output.lower() for phrase in ['version', 'prosemark'])

    def test_command_argument_order_validation(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test that command arguments can be provided in different orders."""
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.type = 'batch'
            mock_result.total_placeholders = 8
            mock_result.successful_materializations = []
            mock_result.failed_materializations = []
            mock_result.execution_time = 1.2
            mock_result.message = 'Successfully materialized all 8 placeholders'

            mock_instance.execute.return_value = mock_result
            mock_use_case.return_value = mock_instance

            # Test different argument orders
            argument_orders = [
                ['materialize-all', '--path', str(binder_with_placeholders), '--verbose'],
                ['materialize-all', '--verbose', '--path', str(binder_with_placeholders)],
                ['materialize-all', '--path', str(binder_with_placeholders), '--batch-size', '10'],
            ]

            for args in argument_orders:
                result = runner.invoke(app, args)
                # All orders should work
                assert result.exit_code == 0, (
                    f'Argument order failed: {args}\nOutput: {result.output}\nException: {result.exception}'
                )

    def test_project_detection_validation(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validation when project detection fails."""
        # Create directory without binder
        non_project_dir = tmp_path / 'not_a_project'
        non_project_dir.mkdir()

        result = runner.invoke(app, ['materialize-all', '--path', str(non_project_dir)])

        # Should fail with project detection error
        assert result.exit_code != 0
        assert any(
            phrase in result.output.lower()
            for phrase in ['not a project', 'no binder', '_binder.md', 'invalid project']
        )

    def test_permission_validation_errors(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test validation of permission-related errors."""
        import os
        import stat

        if os.name != 'nt':  # Skip on Windows due to different permission model
            # Make binder file read-only
            binder_path = binder_with_placeholders / '_binder.md'
            current_mode = binder_path.stat().st_mode

            try:
                binder_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # Read-only

                result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_placeholders)])

                # Should handle permission error gracefully
                assert result.exit_code != 0
                assert any(
                    phrase in result.output.lower()
                    for phrase in ['permission', 'read-only', 'access denied', 'cannot write']
                )

            finally:
                # Restore permissions
                binder_path.chmod(current_mode)

    def test_concurrent_execution_validation(self, runner: CliRunner, binder_with_placeholders: Path) -> None:
        """Test validation for concurrent execution scenarios."""
        # This would test lock file validation if implemented
        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_instance = MagicMock()

            # Mock concurrent execution error
            def mock_execute_concurrent_error(**kwargs: object) -> Never:
                raise RuntimeError('Another materialize-all operation is already running')

            mock_instance.execute.side_effect = mock_execute_concurrent_error
            mock_use_case.return_value = mock_instance

            result = runner.invoke(app, ['materialize-all', '--path', str(binder_with_placeholders)])

            # Should handle concurrent execution error
            assert result.exit_code != 0
            assert any(
                phrase in result.output.lower() for phrase in ['already running', 'concurrent', 'lock', 'in progress']
            )
