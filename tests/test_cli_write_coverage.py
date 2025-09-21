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
            patch('prosemark.cli.write.WriteFreeform') as mock_write_class,
        ):
            # Mock the WriteFreeform use case to raise FileSystemError
            mock_write_instance = mock_write_class.return_value
            mock_write_instance.execute.side_effect = FileSystemError('Permission denied')

            result = runner.invoke(write_command, ['Test Title'])

            assert result.exit_code == 1
            assert 'Error: File creation failed' in result.output

    def test_write_command_editor_launch_error(self) -> None:
        """Test write command handles EditorLaunchError (lines 48-50)."""
        runner = CliRunner()

        with (
            runner.isolated_filesystem(),
            patch('prosemark.cli.write.WriteFreeform') as mock_write_class,
        ):
            # Mock the WriteFreeform use case to raise EditorLaunchError
            mock_write_instance = mock_write_class.return_value
            mock_write_instance.execute.side_effect = EditorLaunchError('Editor not found')

            result = runner.invoke(write_command, ['Test Title'])

            assert result.exit_code == 2
            assert 'Error: Editor launch failed' in result.output
