"""Tests to cover missing lines in CLI main command."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from prosemark.cli.main import app, main


class TestMainMissingCoverage:
    """Test missing coverage lines in main command."""

    def test_structure_command_with_children_json_format(self) -> None:
        """Test structure command with children in JSON format (line 255)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize a project first
            from click.testing import CliRunner as ClickRunner

            from prosemark.cli.init import init_command

            click_runner = ClickRunner()
            init_result = click_runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Create a mock binder with children
            mock_child = Mock()
            mock_child.display_title = 'Child Item'
            mock_child.id = 'child-123'
            mock_child.children = []

            mock_item = Mock()
            mock_item.display_title = 'Parent Item'
            mock_item.id = 'parent-123'
            mock_item.children = [mock_child]

            mock_binder = Mock()
            mock_binder.roots = [mock_item]

            with patch('prosemark.cli.main.BinderRepoFs') as mock_binder_repo:
                mock_binder_instance = Mock()
                mock_binder_instance.load.return_value = mock_binder
                mock_binder_repo.return_value = mock_binder_instance

                result = runner.invoke(app, ['structure', '--format', 'json'])

                assert result.exit_code == 0
                # Parse the JSON output to verify children are included
                output_data = json.loads(result.stdout)
                assert 'roots' in output_data
                assert len(output_data['roots']) == 1
                parent = output_data['roots'][0]
                assert 'children' in parent
                assert len(parent['children']) == 1
                assert parent['children'][0]['display_title'] == 'Child Item'

    def test_structure_command_with_item_without_id(self) -> None:
        """Test structure command with item that has no ID (line 251->253)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize a project first
            from click.testing import CliRunner as ClickRunner

            from prosemark.cli.init import init_command

            click_runner = ClickRunner()
            init_result = click_runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Create a mock item with no ID - set both id and node_id to None to trigger the branch
            mock_item = Mock()
            mock_item.display_title = 'Item Without ID'
            mock_item.children = []
            mock_item.id = None  # This will make the node_id expression evaluate to None
            mock_item.node_id = None

            mock_binder = Mock()
            mock_binder.roots = [mock_item]

            with patch('prosemark.cli.main.BinderRepoFs') as mock_binder_repo:
                mock_binder_instance = Mock()
                mock_binder_instance.load.return_value = mock_binder
                mock_binder_repo.return_value = mock_binder_instance

                result = runner.invoke(app, ['structure', '--format', 'json'])

                assert result.exit_code == 0
                # Parse the JSON output to verify no node_id is included
                output_data = json.loads(result.stdout)
                assert 'roots' in output_data
                assert len(output_data['roots']) == 1
                item = output_data['roots'][0]
                assert 'node_id' not in item  # Should not have node_id since it was None

    def test_remove_command_with_confirmation(self) -> None:
        """Test remove command when user confirms deletion (line 406->411)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Initialize a project first
            from click.testing import CliRunner as ClickRunner

            from prosemark.cli.init import init_command

            click_runner = ClickRunner()
            init_result = click_runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the confirmation to return True
            with (
                patch('prosemark.cli.main.typer.confirm', return_value=True),
                patch('prosemark.cli.main.RemoveNode') as mock_remove,
            ):
                mock_remove_instance = Mock()
                mock_remove.return_value = mock_remove_instance

                # Run remove command with delete-files but without force (so it asks for confirmation)
                # Use a valid UUID7 format
                result = runner.invoke(app, ['remove', '0192f0c1-2345-7123-8abc-def012345678', '--delete-files'])

                # The command should proceed past the confirmation (line 406->411)
                # and execute the use case
                assert result.exit_code == 0
                assert mock_remove_instance.execute.called

    def test_audit_command_filesystem_error_handling(self) -> None:
        """Test audit command handles FileSystemError (lines 500-501)."""
        runner = CliRunner()

        with runner.isolated_filesystem(), patch('prosemark.cli.main.AuditBinder') as mock_audit:
            from prosemark.exceptions import FileSystemError

            mock_audit_instance = Mock()
            mock_audit_instance.execute.side_effect = FileSystemError('Test filesystem error')
            mock_audit.return_value = mock_audit_instance

            result = runner.invoke(app, ['audit'])

            assert result.exit_code == 2
            assert 'Error: Test filesystem error' in result.stdout

    def test_main_function_called_directly(self) -> None:
        """Test main() function when script is run directly (line 510)."""
        # Test that the main function exists and is callable
        assert callable(main)

        # Mock typer.run to test the main function
        with patch('prosemark.cli.main.app') as mock_app:
            main()
            mock_app.assert_called_once()

    def test_if_main_block_execution(self) -> None:
        """Test the if __name__ == '__main__' block execution."""
        # This is a bit tricky to test directly, but we can verify the pattern exists
        # and that main() would be called in that context

        # Read the main.py file to verify the pattern exists
        main_file = Path(__file__).parent.parent / 'src' / 'prosemark' / 'cli' / 'main.py'
        content = main_file.read_text()

        assert "if __name__ == '__main__':" in content
        assert 'main()' in content

        # Test that main function works
        with patch('prosemark.cli.main.app') as mock_app:
            main()
            mock_app.assert_called_once()
