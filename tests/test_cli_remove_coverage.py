"""Coverage tests for CLI remove command uncovered lines."""

from unittest.mock import patch

from click.testing import CliRunner

from prosemark.cli.remove import remove_command
from prosemark.exceptions import FileSystemError, NodeNotFoundError


class TestCLIRemoveCoverage:
    """Test uncovered lines in CLI remove command."""

    def test_remove_command_node_not_found_error(self) -> None:
        """Test remove command handles NodeNotFoundError (lines 60-61)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and RemoveNode use case to raise NodeNotFoundError
            with patch('prosemark.cli.remove.NodeId') as mock_node_id:
                mock_node_id.return_value = mock_node_id

                with patch('prosemark.cli.remove.RemoveNode') as mock_remove_class:
                    mock_remove_instance = mock_remove_class.return_value
                    mock_remove_instance.execute.side_effect = NodeNotFoundError('Node not found')

                    result = runner.invoke(remove_command, ['test-id'])

                    assert result.exit_code == 1
                    assert 'Error: Node not found' in result.output

    def test_remove_command_file_system_error(self) -> None:
        """Test remove command handles FileSystemError (lines 63-64)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and RemoveNode use case to raise FileSystemError
            with patch('prosemark.cli.remove.NodeId') as mock_node_id:
                mock_node_id.return_value = mock_node_id

                # Mock the binder_repo.load() call
                with patch('prosemark.cli.remove.BinderRepoFs') as mock_binder_repo_class:
                    mock_binder_repo = mock_binder_repo_class.return_value
                    mock_binder = mock_binder_repo.load.return_value
                    mock_item = mock_binder.find_by_id.return_value
                    mock_item.display_title = 'Test Node'

                    with patch('prosemark.cli.remove.RemoveNode') as mock_remove_class:
                        mock_remove_instance = mock_remove_class.return_value
                        mock_remove_instance.execute.side_effect = FileSystemError('Permission denied')

                        result = runner.invoke(remove_command, ['test-id'])

                        assert result.exit_code == 3
                        assert 'Error: File deletion failed' in result.output
