"""The main Prosemark command line interface.

This module provides the command-line interface for the Prosemark application,
allowing users to manage projects and nodes through the terminal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from prosemark.domain.factories import NodeFactory, ProjectFactory

if TYPE_CHECKING:  # pragma: no cover
    from click.core import Context as ClickContext

    from prosemark.domain.nodes import Node, NodeID


@click.group()
@click.version_option()
@click.option(
    '--data-dir',
    default='.',
    help='Directory where project data is stored',
    type=click.Path(),
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    default=False,
    help='Enable verbose output (print tracebacks on errors)',
)
@click.pass_context
def main(ctx: ClickContext, data_dir: str, verbose: bool) -> None:  # noqa: FBT001
    """Prosemark - A tool for structured document creation and management.

    Prosemark helps you organize your writing projects with a hierarchical
    structure of nodes, each containing content, notes, and metadata.
    """
    from pathlib import Path

    from prosemark.repositories.project import ProjectRepository
    from prosemark.storages.filesystem import FilesystemMdNodeStorage

    ctx.ensure_object(dict)
    ctx.obj['data_dir'] = data_dir
    ctx.obj['verbose'] = verbose

    # Create storage and repository instances
    storage = FilesystemMdNodeStorage(Path(data_dir))
    repository = ProjectRepository(storage)
    ctx.obj['repository'] = repository


@main.command()
@click.argument('title')
@click.option('--description', '-d', help='Description of the project')
@click.pass_context
def init(ctx: ClickContext, title: str, description: str | None = None) -> None:
    """Create a new project.

    TITLE is the title of the new project to create.
    """
    repository = ctx.obj['repository']

    # Create a new project with a root node
    project = ProjectFactory.build(root_node=NodeFactory.build(id='_binder', title=title, notecard=description or ''))

    # Save the project, which will create the _binder.md file
    repository.save_project(project)

    click.echo(f"Project '{title}' initialized successfully in {ctx.obj['data_dir']}")


@main.command()
@click.pass_context
def info(ctx: ClickContext) -> None:
    """Display information about the current project."""
    repository = ctx.obj['repository']
    project = repository.load_project()
    click.echo(f'Project: {project.title}')
    click.echo(f'Description: {project.notecard}')
    click.echo(f'Nodes: {project.get_node_count()}')

    click.echo('\nMetadata:')
    for key, value in project.root_node.metadata.items():
        click.echo(f'  {key}: {value}')


@main.command()
@click.argument('parent_id')
@click.argument('title')
@click.option('--notecard', '-n', help='Brief summary of the node')
@click.option('--content', '-c', help='Main content of the node')
@click.option('--notes', help='Additional notes about the node')
@click.option('--position', '-p', type=int, help='Position to insert the node')
@click.pass_context
def add(
    ctx: ClickContext,
    parent_id: str,
    title: str,
    notecard: str = '',
    content: str = '',
    notes: str = '',
    position: int | None = None,
) -> None:
    """Add a new node to the project.

    PARENT_ID is the ID of the parent node.
    TITLE is the title of the new node.
    """
    repository = ctx.obj['repository']
    project = repository.load_project()

    node = project.create_node(
        parent_id=parent_id,
        title=title,
        notecard=notecard,
        content=content,
        notes=notes,
        position=position,
    )
    repository.save_project(project)
    repository.save_node(node)

    click.echo(f'Node added successfully with ID: {node.id}')


@main.command()
@click.argument('node_id')
@click.pass_context
def remove(ctx: ClickContext, node_id: NodeID) -> None:
    """Remove a node from the project.

    NODE_ID is the ID of the node to remove.
    """
    repository = ctx.obj['repository']
    project = repository.load_project()

    node = project.remove_node(node_id)
    if node:
        repository.save_project(project)
        click.echo(f"Node '{node.title}' removed successfully")
    else:  # pragma: no cover
        click.echo(f"Node with ID '{node_id}' not found")


@main.command()
@click.argument('node_id')
@click.argument('new_parent_id')
@click.option('--position', '-p', type=int, help='Position to insert the node')
@click.pass_context
def move(ctx: ClickContext, node_id: NodeID, new_parent_id: NodeID, position: int | None = None) -> None:
    """Move a node to a new parent.

    NODE_ID is the ID of the node to move.
    NEW_PARENT_ID is the ID of the new parent node.
    """
    repository = ctx.obj['repository']
    project = repository.load_project()

    success = project.move_node(node_id, new_parent_id, position)
    if success:
        repository.save_project(project)
        click.echo('Node moved successfully')
    else:  # pragma: no cover
        click.echo(f"Failed to move node '{node_id}' to parent '{new_parent_id}'")


@main.command()
@click.argument('node_id')
@click.pass_context
def show(ctx: ClickContext, node_id: NodeID) -> None:
    """Display node content.

    NODE_ID is the ID of the node to display.
    """
    repository = ctx.obj['repository']
    project = repository.load_project()

    node = project.get_node_by_id(node_id)
    if not node:  # pragma: no cover
        click.echo(f"Node with ID '{node_id}' not found")
        return

    repository.load_node_content(node)

    click.echo(f'Title: {node.title}')
    if node.notecard:  # pragma: no branch
        click.echo(f'\nNotecard: {node.notecard}')

    if node.content:  # pragma: no branch
        click.echo('\nContent:')
        click.echo(node.content)

    if node.notes:  # pragma: no branch
        click.echo('\nNotes:')
        click.echo(node.notes)


@main.command()
@click.argument('node_id')
@click.option('--title', '-t', help='New title for the node')
@click.option('--notecard', '-n', help='New notecard for the node')
@click.option('--content', '-c', help='New content for the node')
@click.option('--notes', help='New notes for the node')
@click.option('--editor/--no-editor', default=True, help='Open in editor')
@click.pass_context
def edit(
    ctx: ClickContext,
    node_id: NodeID,
    title: str | None = None,
    notecard: str | None = None,
    content: str | None = None,
    notes: str | None = None,
    editor: bool = True,  # noqa: FBT001, FBT002
) -> None:
    """Edit node content with the default text editor.

    NODE_ID is the ID of the node to edit.
    """
    repository = ctx.obj['repository']
    project = repository.load_project()

    node = project.get_node_by_id(node_id)
    if not node:  # pragma: no cover
        click.echo(f"Node with ID '{node_id}' not found")
        return

    repository.load_node_content(node)

    # Update node properties if provided
    if title is not None:  # pragma: no branch
        node.title = title
    if notecard is not None:  # pragma: no cover
        node.notecard = notecard
    if content is not None:  # pragma: no cover
        node.content = content
    if notes is not None:  # pragma: no cover
        node.notes = notes

    # TODO: Implement editor functionality
    if editor:  # pragma: no cover
        click.echo('Editor functionality not implemented yet, using provided values')

    repository.save_node(node)
    click.echo('Node updated successfully')


@main.command()
@click.option('--node-id', '-n', help='ID of the node to start from (defaults to root)')
@click.pass_context
def structure(ctx: ClickContext, node_id: NodeID | None = None) -> None:
    """Display the project structure."""
    repository = ctx.obj['repository']
    project = repository.load_project()

    if node_id:  # pragma: no cover
        start_node = project.get_node_by_id(node_id)
        if not start_node:
            click.echo(f"Node with ID '{node_id}' not found")
            return
    else:
        start_node = project.root_node

    def print_node(node: Node, level: int = 0) -> None:
        if level == 0:
            click.echo(f'{node.id} - {node.title}')
        else:
            click.echo(f'- {node.id} {node.title}')
        for child in node.children:
            print_node(child, level + 1)

    print_node(start_node)


if __name__ == '__main__':  # pragma: no cover
    main()
