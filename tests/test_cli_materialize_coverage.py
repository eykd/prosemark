"""Coverage tests for CLI materialize command uncovered lines."""

from unittest.mock import patch

from click.testing import CliRunner

from prosemark.cli.materialize import materialize_command
from prosemark.exceptions import FileSystemError


class TestCLIMaterializeCoverage:
    """Test uncovered lines in CLI materialize command."""

    def test_materialize_command_graceful_already_materialized_handling(self) -> None:
        """Test materialize command gracefully handles already-materialized nodes."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command
            from prosemark.domain.models import NodeId

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the MaterializeNode use case to return a MaterializeResult (simulating newly materialized)
            with patch('prosemark.cli.materialize.MaterializeNode') as mock_materialize_class:
                from prosemark.app.materialize_node import MaterializeResult

                mock_materialize_instance = mock_materialize_class.return_value
                test_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
                mock_materialize_instance.execute.return_value = MaterializeResult(
                    test_node_id, was_already_materialized=False
                )

                result = runner.invoke(materialize_command, ['Test Chapter'])

                assert result.exit_code == 0
                assert f'Materialized "Test Chapter" ({test_node_id.value})' in result.output

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

    def test_materialize_command_already_materialized_no_output(self) -> None:
        """Test materialize command produces no output when node was already materialized (line 49)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command
            from prosemark.domain.models import NodeId

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the MaterializeNode use case to return MaterializeResult with was_already_materialized=True
            with patch('prosemark.cli.materialize.MaterializeNode') as mock_materialize_class:
                from prosemark.app.materialize_node import MaterializeResult

                mock_materialize_instance = mock_materialize_class.return_value
                test_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
                mock_materialize_instance.execute.return_value = MaterializeResult(
                    test_node_id, was_already_materialized=True
                )

                result = runner.invoke(materialize_command, ['Test Chapter'])

                assert result.exit_code == 0
                # Should have no success output when already materialized
                assert 'Materialized "Test Chapter"' not in result.output
                assert 'Created files:' not in result.output
                assert 'Updated binder structure' not in result.output
