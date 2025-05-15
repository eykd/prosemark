from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from prosemark.cli import main
from prosemark.domain.nodes import Node

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

    from click.testing import CliRunner

    from prosemark.domain.nodes import NodeID
    from prosemark.repositories.project import ProjectRepository


def test_cli_main(runner: CliRunner) -> None:
    """Test that the CLI runs without error."""
    result = runner.invoke(main)
    assert result.exit_code == 0


def test_cli_init(runner: CliRunner, runner_path: Path) -> None:
    """Test the init command."""
    result = runner.invoke(main, ['init', 'Test Project', '--description', 'A test project'])
    assert result.exit_code == 0
    assert result.output == textwrap.dedent(
        """\
        Project 'Test Project' initialized successfully.
        """
    )
    assert (runner_path / '_binder.md').exists()


def test_cli_info(runner: CliRunner) -> None:
    """Test the info command."""
    # First create a project
    runner.invoke(main, ['init', 'Test Project', '--description', 'A test project'])

    # Then get info about it
    result = runner.invoke(main, ['info'])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        """\
        Project: Test Project
        Description: A test project
        Nodes: 1

        Metadata:

        """
    )
    assert result.output == expected


def test_cli_add(runner: CliRunner, node_ids: list[NodeID]) -> None:
    """Test the add command."""
    # First create a project
    runner.invoke(main, ['init', 'Test Project'])

    # Then add a node
    result = runner.invoke(
        main, ['add', '_binder', 'New Node', '--notecard', 'A brief summary', '--content', 'Some content']
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        f"""\
        Node added successfully with ID: {node_ids[1]}
        """
    )
    assert result.output == expected


def test_cli_remove(runner: CliRunner) -> None:
    """Test the remove command."""
    # First create a project with a node
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node to remove'])

    # Get the node ID from the structure
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]

    # Then remove the node
    result = runner.invoke(main, ['remove', node_id])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        """\
        Node 'Node to remove' removed successfully
        """
    )
    assert result.output == expected


def test_cli_move(runner: CliRunner) -> None:
    """Test the move command."""
    # First create a project with nodes
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Parent Node'])
    runner.invoke(main, ['add', '_binder', 'Node to move'])

    # Get node IDs from the structure
    structure_result = runner.invoke(main, ['structure'])
    lines = structure_result.output.split('\n')
    parent_id = lines[1].split()[1]
    node_id = lines[2].split()[1]

    # Then move the node
    result = runner.invoke(main, ['move', node_id, parent_id])
    assert result.exit_code == 0
    assert result.output == 'Node moved successfully\n'


def test_cli_show(runner: CliRunner, node_ids: list[NodeID]) -> None:
    """Test the show command."""
    # First create a project with a node
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node to show', '--content', 'This is the content'])

    # Get the node ID from the structure
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]

    # Then show the node
    result = runner.invoke(main, ['show', node_id])
    assert result.exit_code == 0
    assert result.output == textwrap.dedent(
        f"""\
        Title: Node to show

        Notecard:
        [[{node_ids[1]} notecard.md]]

        Content:
        This is the content

        Notes:
        [[{node_ids[1]} notes.md]]

        """
    )


def test_cli_edit(runner: CliRunner) -> None:
    """Test the edit command."""
    # First create a project with a node
    runner.invoke(main, ['init', 'Test Project'])
    runner.invoke(main, ['add', '_binder', 'Node to edit'])

    # Get the node ID from the structure
    structure_result = runner.invoke(main, ['structure'])
    node_id = structure_result.output.split('\n')[1].split()[1]

    # Then edit the node without opening an editor
    result = runner.invoke(main, ['edit', node_id, '--no-editor'])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        """\
        Node updated successfully
        """
    )
    assert result.output == expected


def test_cli_structure(
    runner: CliRunner, node_ids: list[NodeID], fs_project_repository: ProjectRepository, runner_path: Path
) -> None:
    """Test the structure command."""
    runner.invoke(main, ['init', 'New Project'])
    project = fs_project_repository.load_project()

    # Add some nodes
    child1 = project.create_node(project.root_node.id, title='Child 1')
    assert isinstance(child1, Node)
    project.create_node(project.root_node.id, title='Child 2')
    project.create_node(child1.id, title='Grandchild')
    fs_project_repository.save_project(project)

    assert (runner_path / '_binder.md').read_text() == textwrap.dedent(
        """\
        ---
        id: _binder
        title: New Project
        ---
        // Notecard: [[_binder notecard.md]]
        // Notes: [[_binder notes.md]]

        # New Project

        [[_binder notecard.md]]

        - [Child 1](202501020304050601.md)
          - [Grandchild](202501020304050603.md)
        - [Child 2](202501020304050602.md)
        """
    )

    # Then display the structure
    result = runner.invoke(main, ['structure'])
    assert result.exit_code == 0
    expected = textwrap.dedent(
        f"""\
        _binder - New Project
        - {node_ids[1]} Child 1
          - {node_ids[3]} Grandchild
        - {node_ids[2]} Child 2

        """
    )
    assert result.output == expected
