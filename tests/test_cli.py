from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from prosemark.cli import main


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


def test_cli_main(runner: CliRunner) -> None:
    """Test that the CLI runs without error."""
    result = runner.invoke(main)
    assert result.exit_code == 0


def test_cli_init(runner: CliRunner) -> None:
    """Test the init command."""
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init', 'Test Project', '--description', 'A test project'])
        assert result.exit_code == 0
        assert "Project 'Test Project' initialized successfully" in result.output
        assert Path('_binder.md').exists()


def test_cli_info(runner: CliRunner) -> None:
    """Test the info command."""
    with runner.isolated_filesystem():
        # First create a project
        runner.invoke(main, ['init', 'Test Project', '--description', 'A test project'])

        # Then get info about it
        result = runner.invoke(main, ['info'])
        assert result.exit_code == 0
        assert 'Project: Test Project' in result.output
        assert 'Description: A test project' in result.output
        assert 'Nodes: 1' in result.output


def test_cli_add(runner: CliRunner) -> None:
    """Test the add command."""
    with runner.isolated_filesystem():
        # First create a project
        runner.invoke(main, ['init', 'Test Project'])

        # Then add a node
        result = runner.invoke(
            main, ['add', '_binder', 'New Node', '--notecard', 'A brief summary', '--content', 'Some content']
        )
        assert result.exit_code == 0
        assert 'Node added successfully' in result.output


def test_cli_remove(runner: CliRunner) -> None:
    """Test the remove command."""
    with runner.isolated_filesystem():
        # First create a project with a node
        runner.invoke(main, ['init', 'Test Project'])
        runner.invoke(main, ['add', '_binder', 'Node to remove'])

        # Get the node ID from the structure
        structure_result = runner.invoke(main, ['structure'])
        node_id = structure_result.output.split('\n')[1].split()[0]

        # Then remove the node
        result = runner.invoke(main, ['remove', node_id])
        assert result.exit_code == 0
        assert 'Node removed successfully' in result.output


def test_cli_move(runner: CliRunner) -> None:
    """Test the move command."""
    with runner.isolated_filesystem():
        # First create a project with nodes
        runner.invoke(main, ['init', 'Test Project'])
        runner.invoke(main, ['add', '_binder', 'Parent Node'])
        runner.invoke(main, ['add', '_binder', 'Node to move'])

        # Get node IDs from the structure
        structure_result = runner.invoke(main, ['structure'])
        lines = structure_result.output.split('\n')
        parent_id = lines[1].split()[0]
        node_id = lines[2].split()[0]

        # Then move the node
        result = runner.invoke(main, ['move', node_id, parent_id])
        assert result.exit_code == 0
        assert 'Node moved successfully' in result.output


def test_cli_show(runner: CliRunner) -> None:
    """Test the show command."""
    with runner.isolated_filesystem():
        # First create a project with a node
        runner.invoke(main, ['init', 'Test Project'])
        runner.invoke(main, ['add', '_binder', 'Node to show', '--content', 'This is the content'])

        # Get the node ID from the structure
        structure_result = runner.invoke(main, ['structure'])
        node_id = structure_result.output.split('\n')[1].split()[0]

        # Then show the node
        result = runner.invoke(main, ['show', node_id])
        assert result.exit_code == 0
        assert 'Title: Node to show' in result.output
        assert 'Content:' in result.output
        assert 'This is the content' in result.output


def test_cli_edit(runner: CliRunner) -> None:
    """Test the edit command."""
    with runner.isolated_filesystem():
        # First create a project with a node
        runner.invoke(main, ['init', 'Test Project'])
        runner.invoke(main, ['add', '_binder', 'Node to edit'])

        # Get the node ID from the structure
        structure_result = runner.invoke(main, ['structure'])
        node_id = structure_result.output.split('\n')[1].split()[0]

        # Then edit the node without opening an editor
        result = runner.invoke(main, ['edit', node_id, '--title', 'Updated Title', '--no-editor'])
        assert result.exit_code == 0
        assert 'Node updated successfully' in result.output


def test_cli_structure(runner: CliRunner) -> None:
    """Test the structure command."""
    with runner.isolated_filesystem():
        # First create a project with nodes
        runner.invoke(main, ['init', 'Test Project'])
        runner.invoke(main, ['add', '_binder', 'Child Node 1'])
        runner.invoke(main, ['add', '_binder', 'Child Node 2'])

        # Then display the structure
        result = runner.invoke(main, ['structure'])
        assert result.exit_code == 0
        assert '_binder - _binder' in result.output
        assert 'Child Node 1' in result.output
        assert 'Child Node 2' in result.output
