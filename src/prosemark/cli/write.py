"""CLI command for freewriting sessions.

DEPRECATED: This module is kept for backward compatibility.
The actual write command is now implemented in main.py using Typer
and the new freewriting TUI interface.
"""

from pathlib import Path

import click

from prosemark.freewriting.container import run_freewriting_session


@click.command()
@click.argument('node_uuid', required=False)
@click.option('--title', '-t', help='Session title')
@click.option('--words', '-w', type=int, help='Word count goal')
@click.option('--time', type=int, help='Time limit in minutes')
@click.option('--path', '-p', type=click.Path(path_type=Path), help='Project directory')
def write_command(
    node_uuid: str | None,
    title: str | None,
    words: int | None,
    time: int | None,
    path: Path | None,
) -> None:
    """Start a freewriting session in a distraction-free TUI."""
    try:
        project_root = path or Path.cwd()

        # Use the new freewriting container for dependency injection
        run_freewriting_session(
            node_uuid=node_uuid,
            title=title,
            word_count_goal=words,
            time_limit=time,
            project_path=project_root,
        )

    except Exception as e:
        click.echo(f'Error: {e}', err=True)
        raise SystemExit(1) from e
