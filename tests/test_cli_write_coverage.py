"""Coverage tests for CLI write command uncovered lines."""

from unittest.mock import patch

from click.testing import CliRunner

from prosemark.cli.write import write_command
from prosemark.exceptions import EditorLaunchError, FileSystemError


class TestCLIWriteCoverage:
    """Test uncovered lines in CLI write command."""

    def test_write_command_file_system_error(self) -> None:
        """Test write command handles FileSystemError (lines 45-47)."""
        runner = CliRunner()

        with (
            runner.isolated_filesystem(),
            patch('prosemark.freewriting.container.run_freewriting_session') as mock_run_session,
        ):
            # Mock the freewriting session to raise FileSystemError
            mock_run_session.side_effect = FileSystemError('Permission denied')

            result = runner.invoke(write_command, ['Test Title'])

            assert result.exit_code == 1
            assert 'Error: File creation failed' in result.output

    def test_write_command_editor_launch_error(self) -> None:
        """Test write command handles EditorLaunchError (lines 48-50)."""
        runner = CliRunner()

        with (
            runner.isolated_filesystem(),
            patch('prosemark.freewriting.container.run_freewriting_session') as mock_run_session,
        ):
            # Mock the freewriting session to raise EditorLaunchError
            mock_run_session.side_effect = EditorLaunchError('Editor not found')

            result = runner.invoke(write_command, ['Test Title'])

            assert result.exit_code == 2
            assert 'Error: Editor launch failed' in result.output
