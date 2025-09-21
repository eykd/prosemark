"""Coverage tests for CLI materialize command uncovered lines."""

from unittest.mock import patch

from click.testing import CliRunner

from prosemark.cli.materialize import materialize_command
from prosemark.exceptions import AlreadyMaterializedError, FileSystemError


class TestCLIMaterializeCoverage:
    """Test uncovered lines in CLI materialize command."""

    def test_materialize_command_already_materialized_error(self) -> None:
        """Test materialize command handles AlreadyMaterializedError (lines 52-53)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the MaterializeNode use case to raise AlreadyMaterializedError
            with patch('prosemark.cli.materialize.MaterializeNode') as mock_materialize_class:
                mock_materialize_instance = mock_materialize_class.return_value
                mock_materialize_instance.execute.side_effect = AlreadyMaterializedError('Already materialized')

                result = runner.invoke(materialize_command, ['Test Chapter'])

                assert result.exit_code == 1
                assert "Error: 'Test Chapter' is already materialized" in result.output

    def test_materialize_command_file_system_error(self) -> None:
        """Test materialize command handles FileSystemError (lines 55-56)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the MaterializeNode use case to raise FileSystemError
            with patch('prosemark.cli.materialize.MaterializeNode') as mock_materialize_class:
                mock_materialize_instance = mock_materialize_class.return_value
                mock_materialize_instance.execute.side_effect = FileSystemError('Permission denied')

                result = runner.invoke(materialize_command, ['Test Chapter'])

                assert result.exit_code == 2
                assert 'Error: File creation failed' in result.output
