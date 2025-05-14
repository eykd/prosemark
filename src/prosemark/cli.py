"""The main Prosemark command line interface.

This module provides the command-line interface for the Prosemark application,
allowing users to manage projects and nodes through the terminal.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from prosemark.adapters.cli import CliService
from prosemark.repositories.project import ProjectRepository

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator

    from click.core import Context as ClickContext

    from prosemark.domain.nodes import NodeID


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
@click.option(
    '--pager/--no-pager',
    default=True,
    help='Use a pager to display long output',
)
@click.pass_context
def main(ctx: ClickContext, data_dir: str, verbose: bool, pager: bool) -> None:  # noqa: FBT001
    """Prosemark - A tool for structured document creation and management.

    Prosemark helps you organize your writing projects with a hierarchical
    structure of nodes, each containing content, notes, and metadata.
    """
    from prosemark.storages.filesystem import FilesystemMdNodeStorage

    ctx.ensure_object(dict)
    ctx.obj['data_dir'] = data_dir
    ctx.obj['verbose'] = verbose
    ctx.obj['pager'] = pager
    # Create storage and repository instances
    storage = FilesystemMdNodeStorage(Path(data_dir))
    repository = ProjectRepository(storage)
    ctx.obj['repository'] = repository
    ctx.obj['cli_service'] = CliService(repository)


@main.command()
@click.argument('title')
@click.option('--description', '-d', help='Description of the project')
@click.pass_context
def init(ctx: ClickContext, title: str, description: str | None = None) -> None:
    """Create a new project.

    TITLE is the title of the new project to create.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.init_project(title, description)
    click.echo(f"{result} in {ctx.obj['data_dir']}")


@main.command()
@click.pass_context
def info(ctx: ClickContext) -> None:
    """Display information about the current project."""
    cli_service = ctx.obj['cli_service']
    _echo_lines(cli_service.get_project_info(), ctx)


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
    cli_service = ctx.obj['cli_service']
    result = cli_service.add_node(
        parent_id=parent_id,
        title=title,
        notecard=notecard,
        content=content,
        notes=notes,
        position=position,
    )
    click.echo(result)


@main.command()
@click.argument('node_id')
@click.pass_context
def remove(ctx: ClickContext, node_id: NodeID) -> None:
    """Remove a node from the project.

    NODE_ID is the ID of the node to remove.
    """
    cli_service = ctx.obj['cli_service']
    result = cli_service.remove_node(node_id)
    click.echo(result)


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
    cli_service = ctx.obj['cli_service']
    result = cli_service.move_node(node_id, new_parent_id, position)
    click.echo(result)


@main.command()
@click.argument('node_id')
@click.pass_context
def show(ctx: ClickContext, node_id: NodeID) -> None:
    """Display node content.

    NODE_ID is the ID of the node to display.
    """
    cli_service = ctx.obj['cli_service']
    success, lines = cli_service.show_node(node_id)
    
    if not success:
        click.echo(lines[0])
        return
        
    click.echo_via_pager('\n'.join(lines))


@main.command()
@click.argument('node_id')
@click.option('--editor/--no-editor', default=True, help='Open in editor')
@click.pass_context
def edit(
    ctx: ClickContext,
    node_id: NodeID,
    editor: bool = True,  # noqa: FBT001, FBT002
) -> None:
    """Edit node content with the default text editor.

    NODE_ID is the ID of the node to edit.
    """
    cli_service = ctx.obj['cli_service']
    
    # Prepare the node content for editing
    success, content = cli_service.prepare_node_for_editor(node_id)
    if not success:
        click.echo(content)
        return

    if editor:  # noqa: SIM108  # pragma: no cover
        # Open the editor with the formatted content
        edited_content = click.edit(content, extension='.md')
    else:
        edited_content = content

    # Update the node with edited content
    success, message = cli_service.edit_node(node_id, edited_content)
    click.echo(message)


@main.command()
@click.option('--node-id', '-n', help='ID of the node to start from (defaults to root)')
@click.pass_context
def structure(ctx: ClickContext, node_id: NodeID | None = None) -> None:
    """Display the project structure."""
    cli_service = ctx.obj['cli_service']
    success, lines = cli_service.get_project_structure(node_id)
    
    if not success:
        for line in lines:
            click.echo(line)
        return
        
    _echo_lines(lines, ctx)


def _echo_lines(lines: Generator[str, None, None], ctx: ClickContext) -> None:
    if ctx.obj['pager']:
        click.echo_via_pager(lines)
    else:  # pragma: no cover
        for line in lines:
            click.echo(line, nl=False)


if __name__ == '__main__':  # pragma: no cover
    main()
