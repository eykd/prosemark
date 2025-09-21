"""Coverage tests for CLI move command uncovered lines."""

from unittest.mock import patch

from click.testing import CliRunner

from prosemark.cli.move import move_command
from prosemark.exceptions import BinderIntegrityError, NodeNotFoundError


class TestCLIMoveCoverage:
    """Test uncovered lines in CLI move command."""

    def test_move_command_node_not_found_error(self) -> None:
        """Test move command handles NodeNotFoundError (lines 53-54)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and MoveNode use case to raise NodeNotFoundError
            with patch('prosemark.cli.move.NodeId') as mock_node_id:
                mock_node_id.return_value = mock_node_id

                with patch('prosemark.cli.move.MoveNode') as mock_move_class:
                    mock_move_instance = mock_move_class.return_value
                    mock_move_instance.execute.side_effect = NodeNotFoundError('Node not found')

                    result = runner.invoke(move_command, ['test-id'])

                    assert result.exit_code == 1
                    assert 'Error: Node not found' in result.output

    def test_move_command_binder_integrity_error(self) -> None:
        """Test move command handles BinderIntegrityError (lines 56-57)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and MoveNode use case to raise BinderIntegrityError
            with patch('prosemark.cli.move.NodeId') as mock_node_id:
                mock_node_id.return_value = mock_node_id

                with patch('prosemark.cli.move.MoveNode') as mock_move_class:
                    mock_move_instance = mock_move_class.return_value
                    mock_move_instance.execute.side_effect = BinderIntegrityError('Circular reference')

                    result = runner.invoke(move_command, ['test-id'])

                    assert result.exit_code == 3
                    assert 'Error: Would create circular reference' in result.output

    def test_move_command_value_error(self) -> None:
        """Test move command handles ValueError (lines 56-57)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId constructor to raise ValueError for invalid parent
            with patch('prosemark.cli.move.NodeId') as mock_node_id:
                # First call succeeds for node_id, second call raises ValueError for parent
                mock_node_id.side_effect = [mock_node_id, ValueError('Invalid UUID')]

                result = runner.invoke(move_command, ['test-id', '--parent', 'invalid-parent'])

                assert result.exit_code == 2
                assert 'Error: Invalid parent or position' in result.output
