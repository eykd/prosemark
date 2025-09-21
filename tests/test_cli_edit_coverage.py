"""Coverage tests for CLI edit command uncovered lines."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from prosemark.cli.edit import edit_command
from prosemark.exceptions import EditorLaunchError, FileSystemError, NodeNotFoundError


class TestCLIEditCoverage:
    """Test uncovered lines in CLI edit command."""

    def test_edit_command_success_draft(self) -> None:
        """Test edit command success with draft part (lines 22-43)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and EditPart use case to succeed
            with patch('prosemark.cli.edit.NodeId') as mock_node_id:
                mock_node_id.return_value = Mock()

                with patch('prosemark.cli.edit.EditPart') as mock_edit_class:
                    mock_edit_instance = mock_edit_class.return_value

                    result = runner.invoke(edit_command, ['test-node-id', '--part', 'draft'])

                    # Should succeed and show success message for draft
                    assert result.exit_code == 0
                    assert 'Opened test-node-id.md in editor' in result.output

                    # Verify EditPart was called
                    mock_edit_class.assert_called_once()
                    mock_edit_instance.execute.assert_called_once()

    def test_edit_command_success_notes(self) -> None:
        """Test edit command success with notes part (lines 44-45)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and EditPart use case to succeed
            with patch('prosemark.cli.edit.NodeId') as mock_node_id:
                mock_node_id.return_value = Mock()

                with patch('prosemark.cli.edit.EditPart'):
                    result = runner.invoke(edit_command, ['test-node-id', '--part', 'notes'])

                    # Should succeed and show success message for notes
                    assert result.exit_code == 0
                    assert 'Opened test-node-id.notes.md in editor' in result.output

    def test_edit_command_success_other_part(self) -> None:
        """Test edit command success with other part (lines 46-47)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and EditPart use case to succeed
            with patch('prosemark.cli.edit.NodeId') as mock_node_id:
                mock_node_id.return_value = Mock()

                with patch('prosemark.cli.edit.EditPart'):
                    result = runner.invoke(edit_command, ['test-node-id', '--part', 'synopsis'])

                    # Should succeed and show success message for other part
                    assert result.exit_code == 0
                    assert 'Opened synopsis for test-node-id in editor' in result.output

    def test_edit_command_node_not_found_error(self) -> None:
        """Test edit command handles NodeNotFoundError (lines 49-51)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and EditPart use case to raise NodeNotFoundError
            with patch('prosemark.cli.edit.NodeId') as mock_node_id:
                mock_node_id.return_value = Mock()

                with patch('prosemark.cli.edit.EditPart') as mock_edit_class:
                    mock_edit_instance = mock_edit_class.return_value
                    mock_edit_instance.execute.side_effect = NodeNotFoundError('Node not found')

                    result = runner.invoke(edit_command, ['nonexistent-id', '--part', 'draft'])

                    assert result.exit_code == 1
                    assert 'Error: Node not found' in result.output

    def test_edit_command_editor_launch_error(self) -> None:
        """Test edit command handles EditorLaunchError (lines 52-54)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and EditPart use case to raise EditorLaunchError
            with patch('prosemark.cli.edit.NodeId') as mock_node_id:
                mock_node_id.return_value = Mock()

                with patch('prosemark.cli.edit.EditPart') as mock_edit_class:
                    mock_edit_instance = mock_edit_class.return_value
                    mock_edit_instance.execute.side_effect = EditorLaunchError('Editor not available')

                    result = runner.invoke(edit_command, ['test-node-id', '--part', 'draft'])

                    assert result.exit_code == 2
                    assert 'Error: Editor not available' in result.output

    def test_edit_command_file_system_error(self) -> None:
        """Test edit command handles FileSystemError (lines 55-57)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and EditPart use case to raise FileSystemError
            with patch('prosemark.cli.edit.NodeId') as mock_node_id:
                mock_node_id.return_value = Mock()

                with patch('prosemark.cli.edit.EditPart') as mock_edit_class:
                    mock_edit_instance = mock_edit_class.return_value
                    mock_edit_instance.execute.side_effect = FileSystemError('Permission denied')

                    result = runner.invoke(edit_command, ['test-node-id', '--part', 'draft'])

                    assert result.exit_code == 3
                    assert 'Error: File permission denied' in result.output

    def test_edit_command_value_error(self) -> None:
        """Test edit command handles ValueError (lines 58-60)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock NodeId and EditPart use case to raise ValueError
            with patch('prosemark.cli.edit.NodeId') as mock_node_id:
                mock_node_id.return_value = Mock()

                with patch('prosemark.cli.edit.EditPart') as mock_edit_class:
                    mock_edit_instance = mock_edit_class.return_value
                    mock_edit_instance.execute.side_effect = ValueError('Invalid part specified')

                    result = runner.invoke(edit_command, ['test-node-id', '--part', 'invalid'])

                    assert result.exit_code == 1
                    assert 'Error: Invalid part specified' in result.output
