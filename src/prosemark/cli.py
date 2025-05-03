"""The main Prosemark command line interface.

This module provides the command-line interface for the Prosemark application,
allowing users to manage projects and nodes through the terminal.
"""

from __future__ import annotations

import sys

import click

from prosemark.adapters.markdown import MarkdownFileAdapter


@click.group()
@click.version_option()
@click.option(
    '--data-dir',
    default='./prosemark_data',
    help='Directory where project data is stored',
    type=click.Path(),
)
@click.pass_context
def cli(ctx: click.Context, data_dir: str) -> None:
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
def init(ctx: click.Context, name: str, description: str | None = None) -> None:
    """Create a new project.

    NAME is the name of the new project to create.
    """
    repo = ctx.obj['repo']
    try:
        project = repo.create_project(name, description or '')
        click.echo(f"Project '{project.name}' created successfully.")
    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def list(ctx: click.Context) -> None:
    """List all available projects."""
    repo = ctx.obj['repo']
    projects = repo.list_projects()

    if not projects:
        click.echo('No projects found.')
        return

    click.echo('Available projects:')
    for project in projects:
        click.echo(f"- {project['name']}")


def main() -> None:
    """Run the main CLI interface."""
    cli(obj={})  # pylint: disable=no-value-for-parameter


if __name__ == '__main__':  # pragma: no cover
    main()
