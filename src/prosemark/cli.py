"""The main Prosemark command line interface.

This module provides the command-line interface for the Prosemark application,
allowing users to manage projects and nodes through the terminal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:  # pragma: no cover
    from click.core import Context as ClickContext


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
@click.argument('name')
@click.option('--description', '-d', help='Description of the project')
@click.pass_context
def init(ctx: ClickContext, name: str, description: str | None = None) -> None:
    """Create a new project.

    NAME is the name of the new project to create.
    """
    from prosemark.domain.nodes import Node
    from prosemark.domain.projects import Project

    repository = ctx.obj['repository']

    # Create a new project with a root node
    root_node = Node(node_id='root', title='Root')
    project = Project(name=name, description=description or '', root_node=root_node)

    # Save the project, which will create the _binder.md file
    repository.save_project(project)

    click.echo(f"Project '{name}' initialized successfully in {ctx.obj['data_dir']}")


@main.command()
@click.pass_context
def info(ctx: ClickContext) -> None:
    """Display information about the current project."""


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


@main.command()
@click.argument('node_id')
@click.pass_context
def remove(ctx: ClickContext, node_id: str) -> None:
    """Remove a node from the project.

    NODE_ID is the ID of the node to remove.
    """


@main.command()
@click.argument('node_id')
@click.argument('new_parent_id')
@click.option('--position', '-p', type=int, help='Position to insert the node')
@click.pass_context
def move(ctx: ClickContext, node_id: str, new_parent_id: str, position: int | None = None) -> None:
    """Move a node to a new parent.

    NODE_ID is the ID of the node to move.
    NEW_PARENT_ID is the ID of the new parent node.
    """


@main.command()
@click.argument('node_id')
@click.pass_context
def show(ctx: ClickContext, node_id: str) -> None:
    """Display node content.

    NODE_ID is the ID of the node to display.
    """


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
    node_id: str,
    title: str | None = None,
    notecard: str | None = None,
    content: str | None = None,
    notes: str | None = None,
    editor: bool = True,  # noqa: FBT001, FBT002
) -> None:
    """Edit node content with the default text editor.

    NODE_ID is the ID of the node to edit.
    """


@main.command()
@click.option('--node-id', '-n', help='ID of the node to start from (defaults to root)')
@click.pass_context
def structure(ctx: ClickContext, node_id: str | None = None) -> None:
    """Display the project structure."""


if __name__ == '__main__':  # pragma: no cover
    main()
