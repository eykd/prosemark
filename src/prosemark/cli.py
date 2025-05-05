"""The main Prosemark command line interface.

This module provides the command-line interface for the Prosemark application,
allowing users to manage projects and nodes through the terminal.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import click

from prosemark.adapters.markdown import MarkdownFileAdapter
from prosemark.storages.repositories.exceptions import ProjectExistsError, ProjectNotFoundError

if TYPE_CHECKING:  # pragma: no cover
    from click.core import Context as ClickContext

    from prosemark.domain.nodes import Node


@click.group()
@click.version_option()
@click.option(
    '--data-dir',
    default='.',
    help='Directory where project data is stored',
    type=click.Path(),
)
@click.pass_context
def cli(ctx: ClickContext, data_dir: str) -> None:
    """Prosemark - A tool for structured document creation and management.

    Prosemark helps you organize your writing projects with a hierarchical
    structure of nodes, each containing content, notes, and metadata.
    """
    # Initialize the repository and store it in the context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['repo'] = MarkdownFileAdapter(data_dir)


@cli.command()
@click.argument('name')
@click.option('--description', '-d', help='Description of the project')
@click.pass_context
def init(ctx: ClickContext, name: str, description: str | None = None) -> None:
    """Create a new project.

    NAME is the name of the new project to create.
    """
    repo = ctx.obj['repo']
    try:
        project = repo.create(name, description or '')
        click.echo(f"Project '{project.name}' created successfully.")
    except ProjectExistsError:
        click.echo('Error: A project already exists in this repository.', err=True)
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx: ClickContext) -> None:
    """Display information about the current project."""
    repo = ctx.obj['repo']
    try:
        project = repo.load()
        click.echo(f'Project: {project.name}')
        if project.description:
            click.echo(f'Description: {project.description}')
        click.echo(f'Nodes: {project.get_node_count()}')
    except ProjectNotFoundError:
        click.echo('Error: No project found. Use "init" to create a new project.', err=True)
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@cli.command()
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
    repo = ctx.obj['repo']
    try:
        project = repo.load()
        node = project.create_node(
            parent_id=parent_id,
            title=title,
            notecard=notecard,
            content=content,
            notes=notes,
            position=position,
        )
        if node is None:  # pragma: no cover
            click.echo(f'Error: Parent node with ID {parent_id} not found.', err=True)
            sys.exit(1)

        repo.save(project)
        click.echo(f"Node '{title}' added successfully with ID: {node.id}")
    except ProjectNotFoundError:
        click.echo('Error: No project found. Use "init" to create a new project.', err=True)
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@cli.command()
@click.argument('node_id')
@click.pass_context
def remove(ctx: ClickContext, node_id: str) -> None:
    """Remove a node from the project.

    NODE_ID is the ID of the node to remove.
    """
    repo = ctx.obj['repo']
    try:
        project = repo.load()
        node = project.remove_node(node_id)
        if node is None:  # pragma: no cover
            click.echo(f'Error: Node with ID {node_id} not found or is the root node.', err=True)
            sys.exit(1)

        repo.save(project)
        click.echo(f"Node '{node.title}' removed successfully.")
    except ProjectNotFoundError:
        click.echo('Error: No project found. Use "init" to create a new project.', err=True)
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@cli.command()
@click.argument('node_id')
@click.argument('new_parent_id')
@click.option('--position', '-p', type=int, help='Position to insert the node')
@click.pass_context
def move(ctx: ClickContext, node_id: str, new_parent_id: str, position: int | None = None) -> None:
    """Move a node to a new parent.

    NODE_ID is the ID of the node to move.
    NEW_PARENT_ID is the ID of the new parent node.
    """
    repo = ctx.obj['repo']
    try:
        project = repo.load()
        success = project.move_node(node_id, new_parent_id, position)
        if not success:  # pragma: no cover
            click.echo(
                'Error: Failed to move node. Check that node IDs are valid and not creating a circular reference.',
                err=True,
            )
            sys.exit(1)

        repo.save(project)
        click.echo('Node moved successfully.')
    except ProjectNotFoundError:
        click.echo('Error: No project found. Use "init" to create a new project.', err=True)
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@cli.command()
@click.argument('node_id')
@click.pass_context
def show(ctx: ClickContext, node_id: str) -> None:
    """Display node content.

    NODE_ID is the ID of the node to display.
    """
    repo = ctx.obj['repo']
    try:
        project = repo.load()
        node = project.get_node_by_id(node_id)
        if node is None:  # pragma: no cover
            click.echo(f'Error: Node with ID {node_id} not found.', err=True)
            sys.exit(1)

        click.echo(f'Title: {node.title}')
        if node.notecard:  # pragma: no branch
            click.echo('\nNotecard:')
            click.echo(f'{node.notecard}')

        if node.content:  # pragma: no branch
            click.echo('\nContent:')
            click.echo(f'{node.content}')

        if node.notes:  # pragma: no branch
            click.echo('\nNotes:')
            click.echo(f'{node.notes}')

        if node.children:  # pragma: no branch
            click.echo('\nChildren:')
            for child in node.children:
                click.echo(f'- {child.title} (ID: {child.id})')
    except ProjectNotFoundError:
        click.echo('Error: No project found. Use "init" to create a new project.', err=True)
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@cli.command()
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
    """Edit node content.

    NODE_ID is the ID of the node to edit.
    """
    repo = ctx.obj['repo']
    try:
        project = repo.load()
        node = project.get_node_by_id(node_id)
        if node is None:  # pragma: no cover
            click.echo(f'Error: Node with ID {node_id} not found.', err=True)
            sys.exit(1)

        # Edit the node using the adapter
        node = repo.update_node(node, title, notecard, content, notes)
        # If editor flag is set and no content was provided via options, open editor
        if editor and title is None and notecard is None and content is None and notes is None:  # pragma: no branch
            # Generate initial text for the editor
            initial_text = repo.generate_edit_markdown(node)

            # Open editor and get result
            edited_text = click.edit(initial_text)

            if edited_text is not None:
                # Parse the edited text
                sections = repo.parse_edit_markdown(edited_text)

                node = repo.update_node(node, **sections)

        # Save the project
        repo.save(project)
        click.echo(f"Node '{node.title}' updated successfully.")
    except ProjectNotFoundError:
        click.echo('Error: No project found. Use "init" to create a new project.', err=True)
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@cli.command()
@click.option('--node-id', '-n', help='ID of the node to start from (defaults to root)')
@click.pass_context
def structure(ctx: ClickContext, node_id: str | None = None) -> None:
    """Display the project structure.
    """
    repo = ctx.obj['repo']
    try:
        project = repo.load()

        # If node_id is provided, start from that node
        start_node = project.root_node
        if node_id:
            node = project.get_node_by_id(node_id)
            if node is None:  # pragma: no cover
                click.echo(f'Error: Node with ID {node_id} not found.', err=True)
                sys.exit(1)
            start_node = node

        # Display the structure
        click.echo(f"Structure for project '{project.name}':")
        _print_node_structure(start_node, 0)
    except ProjectNotFoundError:
        click.echo('Error: No project found. Use "init" to create a new project.', err=True)
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


def _print_node_structure(node: Node, level: int) -> None:
    """Print the node structure recursively.

    Args:
        node: The node to print.
        level: The indentation level.

    """
    indent = '  ' * level
    click.echo(f'{indent}- {node.title} (ID: {node.id})')
    for child in node.children:
        _print_node_structure(child, level + 1)


def main() -> None:
    """Run the main CLI interface."""
    cli(obj={})  # pylint: disable=no-value-for-parameter


if __name__ == '__main__':  # pragma: no cover
    main()
