"""Coverage tests for CLI structure command uncovered lines."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from prosemark.cli.structure import structure_command
from prosemark.exceptions import FileSystemError


class TestCLIStructureCoverage:
    """Test uncovered lines in CLI structure command."""

    def test_structure_command_json_format_with_children(self) -> None:
        """Test structure command with JSON format and children (lines 56, 63-64)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the ShowStructure use case and binder structure
            with patch('prosemark.cli.structure.ShowStructure') as mock_show_class:
                mock_show_instance = mock_show_class.return_value
                mock_show_instance.execute.return_value = 'Mocked tree'

                # Mock the binder repo to return a structure with children
                with patch('prosemark.cli.structure.BinderRepoFs') as mock_binder_repo_class:
                    mock_binder_repo = mock_binder_repo_class.return_value
                    mock_binder = mock_binder_repo.load.return_value

                    # Create mock items with children to trigger line 56
                    mock_child = Mock()
                    mock_child.display_title = 'Child Chapter'
                    mock_child.id = None
                    mock_child.node_id = 'child-id'
                    mock_child.children = []

                    mock_parent = Mock()
                    mock_parent.display_title = 'Parent Chapter'
                    mock_parent.id = 'parent-id'
                    mock_parent.children = [mock_child]

                    mock_binder.roots = [mock_parent]

                    result = runner.invoke(structure_command, ['--format', 'json'])

                    assert result.exit_code == 0
                    assert '"display_title": "Parent Chapter"' in result.output
                    assert '"node_id": "parent-id"' in result.output
                    assert '"children"' in result.output

    def test_structure_command_file_system_error(self) -> None:
        """Test structure command handles FileSystemError (lines 63-64)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock the ShowStructure use case to raise FileSystemError
            with patch('prosemark.cli.structure.ShowStructure') as mock_show_class:
                mock_show_instance = mock_show_class.return_value
                mock_show_instance.execute.side_effect = FileSystemError('Permission denied')

                result = runner.invoke(structure_command, [])

                assert result.exit_code == 1
                assert 'Error: Permission denied' in result.output
