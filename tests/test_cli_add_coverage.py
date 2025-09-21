"""Coverage tests for CLI add command uncovered lines."""

from unittest.mock import patch

from click.testing import CliRunner

from prosemark.cli.add import add_command
from prosemark.exceptions import FileSystemError, NodeNotFoundError


class TestCLIAddCoverage:
    """Test uncovered lines in CLI add command."""

    def test_add_command_invalid_parent_id_format(self) -> None:
        """Test add command with invalid parent ID format (lines 77-78)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId constructor to raise ValueError to trigger lines 77-78
            with patch('prosemark.cli.add.NodeId') as mock_node_id:
                mock_node_id.side_effect = ValueError('Invalid UUID format')

                result = runner.invoke(add_command, ['New Chapter', '--parent', 'some-parent'])

                # Should exit with code 1 and show parent not found error
                assert result.exit_code == 1
                assert 'Error: Parent node not found' in result.output

    def test_add_command_node_not_found_error(self) -> None:
        """Test add command handles NodeNotFoundError (lines 92-93)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the AddNode use case to raise NodeNotFoundError
            with patch('prosemark.cli.add.AddNode') as mock_add_class:
                mock_add_instance = mock_add_class.return_value
                mock_add_instance.execute.side_effect = NodeNotFoundError('Parent node not found')

                result = runner.invoke(add_command, ['New Chapter'])

                assert result.exit_code == 1
                assert 'Error: Parent node not found' in result.output

    def test_add_command_value_error(self) -> None:
        """Test add command handles ValueError (lines 95-96)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the AddNode use case to raise ValueError
            with patch('prosemark.cli.add.AddNode') as mock_add_class:
                mock_add_instance = mock_add_class.return_value
                mock_add_instance.execute.side_effect = ValueError('Invalid position index')

                result = runner.invoke(add_command, ['New Chapter'])

                assert result.exit_code == 2
                assert 'Error: Invalid position index' in result.output

    def test_add_command_file_system_error(self) -> None:
        """Test add command handles FileSystemError (lines 98-99)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the AddNode use case to raise FileSystemError
            with patch('prosemark.cli.add.AddNode') as mock_add_class:
                mock_add_instance = mock_add_class.return_value
                mock_add_instance.execute.side_effect = FileSystemError('Permission denied')

                result = runner.invoke(add_command, ['New Chapter'])

                assert result.exit_code == 3
                assert 'Error: File creation failed - Permission denied' in result.output

    def test_add_command_invalid_position_negative(self) -> None:
        """Test add command with negative position index (lines 68-69)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Try to add with negative position
            result = runner.invoke(add_command, ['New Chapter', '--position', '-1'])

            # Should exit with code 2 and show invalid position error
            assert result.exit_code == 2
            assert 'Error: Invalid position index' in result.output

    def test_add_command_auto_init_without_binder(self) -> None:
        """Test add command auto-initializes project when no binder exists (lines 32-47)."""
        runner = CliRunner()

        with (
            runner.isolated_filesystem(),
            patch('prosemark.cli.add.InitProject') as mock_init_class,
            patch('prosemark.cli.add.AddNode') as mock_add_class,
        ):
            # Don't initialize - let add command auto-initialize

            # Mock the InitProject use case to verify auto-init is called
            mock_init_instance = mock_init_class.return_value

            # Mock the AddNode use case to return a node ID
            mock_add_instance = mock_add_class.return_value
            test_node_id = 'test-node-id-123'
            mock_add_instance.execute.return_value = test_node_id

            result = runner.invoke(add_command, ['New Chapter'])

            # Should succeed and auto-initialize
            assert result.exit_code == 0

            # Verify InitProject was called (auto-init happened)
            mock_init_class.assert_called_once()
            mock_init_instance.execute.assert_called_once()

    def test_add_command_success_output(self) -> None:
        """Test add command success output (lines 87-89)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the AddNode use case to return a known node ID
            with patch('prosemark.cli.add.AddNode') as mock_add_class:
                mock_add_instance = mock_add_class.return_value
                test_node_id = 'test-node-id-123'
                mock_add_instance.execute.return_value = test_node_id

                result = runner.invoke(add_command, ['New Chapter'])

                # Should succeed and show success output
                assert result.exit_code == 0
                assert 'Added "New Chapter" (test-node-id-123)' in result.output
                assert 'Created files: test-node-id-123.md, test-node-id-123.notes.md' in result.output
                assert 'Updated binder structure' in result.output
