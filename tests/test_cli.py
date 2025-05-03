from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from prosemark import cli
from prosemark.adapters.markdown import MarkdownFileAdapter
from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


def test_it_should_run_main_successfully() -> None:
    """Test that the main function runs without errors."""
    with patch('prosemark.cli.cli') as mock_cli:
        cli.main()
        mock_cli.assert_called_once_with(obj={})


def test_cli_version(runner: CliRunner) -> None:
    """Test that the CLI displays version information."""
    result = runner.invoke(cli.cli, ['--version'])
    assert result.exit_code == 0
    assert 'version' in result.output.lower()


def test_cli_help(runner: CliRunner) -> None:
    """Test that the CLI displays help information."""
    result = runner.invoke(cli.cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'Options:' in result.output
    assert 'Commands:' in result.output


def test_init_command(runner: CliRunner) -> None:
    """Test the init command creates a new project."""
    with runner.isolated_filesystem(), patch.object(MarkdownFileAdapter, 'create_project') as mock_create:
        mock_create.return_value = Project(name='test-project')

        result = runner.invoke(cli.cli, ['--data-dir', '.', 'init', 'test-project'])

        assert result.exit_code == 0
        assert 'created successfully' in result.output
        mock_create.assert_called_once_with('test-project', '')


def test_init_command_with_description(runner: CliRunner) -> None:
    """Test the init command with a description."""
    with runner.isolated_filesystem(), patch.object(MarkdownFileAdapter, 'create_project') as mock_create:
        mock_create.return_value = Project(name='test-project', description='Test description')

        result = runner.invoke(
            cli.cli, ['--data-dir', '.', 'init', 'test-project', '--description', 'Test description']
        )

        assert result.exit_code == 0
        assert 'created successfully' in result.output
        mock_create.assert_called_once_with('test-project', 'Test description')


def test_init_command_error(runner: CliRunner) -> None:
    """Test the init command handles errors."""
    with runner.isolated_filesystem(), patch.object(MarkdownFileAdapter, 'create_project') as mock_create:
        mock_create.side_effect = ValueError('Project already exists')

        result = runner.invoke(cli.cli, ['--data-dir', '.', 'init', 'test-project'])

        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Project already exists' in result.output


def test_list_command_with_projects(runner: CliRunner) -> None:
    """Test the list command shows available projects."""
    with runner.isolated_filesystem(), patch.object(MarkdownFileAdapter, 'list_projects') as mock_list:
        mock_list.return_value = [
            {'id': 'project1', 'name': 'Project 1'},
            {'id': 'project2', 'name': 'Project 2'},
        ]

        result = runner.invoke(cli.cli, ['--data-dir', '.', 'list-projects'])

        assert result.exit_code == 0
        assert 'Available projects:' in result.output
        assert 'Project 1' in result.output
        assert 'Project 2' in result.output


def test_list_command_no_projects(runner: CliRunner) -> None:
    """Test the list command when no projects exist."""
    with runner.isolated_filesystem(), patch.object(MarkdownFileAdapter, 'list_projects') as mock_list:
        mock_list.return_value = []

        result = runner.invoke(cli.cli, ['--data-dir', '.', 'list-projects'])

        assert result.exit_code == 0
        assert 'No projects found' in result.output


def test_add_command(runner: CliRunner) -> None:
    """Test the add command creates a new node."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Create a mock node
            node = Node(node_id='test-node-id', title='Test Node')
            with patch.object(Project, 'create_node', return_value=node):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'add', 'test-project', 'root-id', 'Test Node']
                )

                assert result.exit_code == 0
                assert 'added successfully' in result.output
                assert 'test-node-id' in result.output
                mock_save.assert_called_once_with(project)


def test_add_command_parent_not_found(runner: CliRunner) -> None:
    """Test the add command when parent node is not found."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Mock create_node to return None (parent not found)
            with patch.object(Project, 'create_node', return_value=None):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'add', 'test-project', 'non-existent-id', 'Test Node']
                )

                assert result.exit_code == 1
                assert 'Error: Parent node' in result.output
                assert 'not found' in result.output
                mock_save.assert_not_called()


def test_remove_command(runner: CliRunner) -> None:
    """Test the remove command removes a node."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Create a mock node to be removed
            node = Node(node_id='test-node-id', title='Test Node')
            with patch.object(Project, 'remove_node', return_value=node):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'remove', 'test-project', 'test-node-id']
                )

                assert result.exit_code == 0
                assert 'removed successfully' in result.output
                mock_save.assert_called_once_with(project)


def test_remove_command_node_not_found(runner: CliRunner) -> None:
    """Test the remove command when node is not found."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Mock remove_node to return None (node not found or is root)
            with patch.object(Project, 'remove_node', return_value=None):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'remove', 'test-project', 'non-existent-id']
                )

                assert result.exit_code == 1
                assert 'Error: Node with ID' in result.output
                assert 'not found or is the root node' in result.output
                mock_save.assert_not_called()


def test_move_command(runner: CliRunner) -> None:
    """Test the move command moves a node."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Mock move_node to return True (success)
            with patch.object(Project, 'move_node', return_value=True):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'move', 'test-project', 'node-id', 'new-parent-id']
                )

                assert result.exit_code == 0
                assert 'moved successfully' in result.output
                mock_save.assert_called_once_with(project)


def test_move_command_failure(runner: CliRunner) -> None:
    """Test the move command when move operation fails."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Mock move_node to return False (failure)
            with patch.object(Project, 'move_node', return_value=False):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'move', 'test-project', 'node-id', 'new-parent-id']
                )

                assert result.exit_code == 1
                assert 'Error: Failed to move node' in result.output
                mock_save.assert_not_called()


def test_show_command(runner: CliRunner) -> None:
    """Test the show command displays node content."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Create a mock node with content
            node = Node(
                node_id='test-node-id',
                title='Test Node',
                notecard='Test notecard',
                content='Test content',
                notes='Test notes'
            )
            child = Node(node_id='child-id', title='Child Node')
            node.add_child(child)

            with patch.object(Project, 'get_node_by_id', return_value=node):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'show', 'test-project', 'test-node-id']
                )

                assert result.exit_code == 0
                assert 'Title: Test Node' in result.output
                assert 'Notecard:' in result.output
                assert 'Test notecard' in result.output
                assert 'Content:' in result.output
                assert 'Test content' in result.output
                assert 'Notes:' in result.output
                assert 'Test notes' in result.output
                assert 'Children:' in result.output
                assert 'Child Node' in result.output


def test_show_command_node_not_found(runner: CliRunner) -> None:
    """Test the show command when node is not found."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Mock get_node_by_id to return None (node not found)
            with patch.object(Project, 'get_node_by_id', return_value=None):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'show', 'test-project', 'non-existent-id']
                )

                assert result.exit_code == 1
                assert 'Error: Node with ID' in result.output
                assert 'not found' in result.output


def test_structure_command(runner: CliRunner) -> None:
    """Test the structure command displays project structure."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load:

            # Create a mock project with a structure
            project = Project(name='test-project')
            root = project.root_node
            node1 = Node(node_id='node1', title='Node 1')
            node2 = Node(node_id='node2', title='Node 2')
            child1 = Node(node_id='child1', title='Child 1')

            root.add_child(node1)
            root.add_child(node2)
            node1.add_child(child1)

            mock_load.return_value = project

            result = runner.invoke(
                cli.cli,
                ['--data-dir', '.', 'structure', 'test-project']
            )

            assert result.exit_code == 0
            assert 'Structure for project' in result.output
            assert 'Node 1' in result.output
            assert 'Node 2' in result.output
            assert 'Child 1' in result.output


def test_edit_command_with_options(runner: CliRunner) -> None:
    """Test the edit command with direct options."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Create a mock node to edit
            node = Node(node_id='test-node-id', title='Old Title')

            with patch.object(Project, 'get_node_by_id', return_value=node):
                result = runner.invoke(
                    cli.cli,
                    [
                        '--data-dir', '.', 'edit', 'test-project', 'test-node-id',
                        '--title', 'New Title',
                        '--notecard', 'New notecard',
                        '--content', 'New content',
                        '--notes', 'New notes',
                        '--no-editor'  # Don't open editor
                    ]
                )

                assert result.exit_code == 0
                assert 'updated successfully' in result.output
                assert node.title == 'New Title'
                assert node.notecard == 'New notecard'
                assert node.content == 'New content'
                assert node.notes == 'New notes'
                mock_save.assert_called_once_with(project)


def test_edit_command_with_editor(runner: CliRunner) -> None:
    """Test the edit command with the editor functionality."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Create a mock node to edit
            node = Node(
                node_id='test-node-id',
                title='Old Title',
                notecard='Old notecard',
                content='Old content',
                notes='Old notes'
            )

            # Mock the editor to return edited content
            edited_text = """# Title: Edited Title

# Notecard (brief summary):
Edited notecard

# Content (main text):
Edited content

# Notes (additional information):
Edited notes

# Instructions:
# Edit the content above. Lines starting with # are comments and will be ignored.
"""

            with patch.object(Project, 'get_node_by_id', return_value=node), \
                 patch.object(click, 'edit', return_value=edited_text):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'edit', 'test-project', 'test-node-id']
                )

                assert result.exit_code == 0
                assert 'updated successfully' in result.output
                assert node.title == 'Edited Title'
                assert node.notecard == 'Edited notecard'
                assert node.content == 'Edited content'
                assert node.notes == 'Edited notes'
                mock_save.assert_called_once_with(project)


def test_edit_command_node_not_found(runner: CliRunner) -> None:
    """Test the edit command when node is not found."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Mock get_node_by_id to return None (node not found)
            with patch.object(Project, 'get_node_by_id', return_value=None):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'edit', 'test-project', 'non-existent-id']
                )

                assert result.exit_code == 1
                assert 'Error: Node with ID' in result.output
                assert 'not found' in result.output


def test_structure_command_with_node_id(runner: CliRunner) -> None:
    """Test the structure command with a specific node ID."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load:

            # Create a mock project with a structure
            project = Project(name='test-project')
            root = project.root_node
            node1 = Node(node_id='node1', title='Node 1')
            node2 = Node(node_id='node2', title='Node 2')
            child1 = Node(node_id='child1', title='Child 1')

            root.add_child(node1)
            root.add_child(node2)
            node1.add_child(child1)

            mock_load.return_value = project

            result = runner.invoke(
                cli.cli,
                ['--data-dir', '.', 'structure', 'test-project', '--node-id', 'node1']
            )

            assert result.exit_code == 0
            assert 'Structure for project' in result.output
            assert 'Node 1' in result.output
            assert 'Child 1' in result.output
            # Node 2 should not be in the output as we're starting from node1
            assert 'Node 2' not in result.output


def test_structure_command_node_not_found(runner: CliRunner) -> None:
    """Test the structure command when the specified node is not found."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Mock get_node_by_id to return None (node not found)
            with patch.object(Project, 'get_node_by_id', return_value=None):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'structure', 'test-project', '--node-id', 'non-existent-id']
                )

                assert result.exit_code == 1
                assert 'Error: Node with ID' in result.output
                assert 'not found' in result.output


def test_edit_command_with_editor_no_changes(runner: CliRunner) -> None:
    """Test the edit command with the editor returning None (no changes)."""
    with runner.isolated_filesystem():
        with patch.object(MarkdownFileAdapter, 'load') as mock_load, \
             patch.object(MarkdownFileAdapter, 'save') as mock_save:

            # Create a mock project
            project = Project(name='test-project')
            mock_load.return_value = project

            # Create a mock node to edit
            node = Node(
                node_id='test-node-id',
                title='Old Title',
                notecard='Old notecard',
                content='Old content',
                notes='Old notes'
            )

            # Mock the editor to return None (user closed without saving)
            with patch.object(Project, 'get_node_by_id', return_value=node), \
                 patch.object(click, 'edit', return_value=None):
                result = runner.invoke(
                    cli.cli,
                    ['--data-dir', '.', 'edit', 'test-project', 'test-node-id']
                )

                assert result.exit_code == 0
                assert 'updated successfully' in result.output
                # Values should remain unchanged
                assert node.title == 'Old Title'
                assert node.notecard == 'Old notecard'
                assert node.content == 'Old content'
                assert node.notes == 'Old notes'
                mock_save.assert_called_once_with(project)
