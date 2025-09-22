"""CLI command for materializing placeholders."""

from pathlib import Path

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.id_generator_uuid7 import IdGeneratorUuid7
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.app.use_cases import MaterializeNode
from prosemark.exceptions import AlreadyMaterializedError, FileSystemError, PlaceholderNotFoundError


@click.command()
@click.argument('title')
@click.option('--parent', '_parent', help='Parent node ID to search within')
@click.option('--path', '-p', type=click.Path(path_type=Path), help='Project directory')
def materialize_command(title: str, _parent: str | None, path: Path | None) -> None:
    """Convert a placeholder to an actual node."""
    try:
        project_root = path or Path.cwd()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor, clock)
        id_generator = IdGeneratorUuid7()
        logger = LoggerStdout()

        # Execute use case
        interactor = MaterializeNode(
            binder_repo=binder_repo,
            node_repo=node_repo,
            id_generator=id_generator,
            logger=logger,
        )

        node_id = interactor.execute(display_title=title, synopsis=None)

        # Success output
        click.echo(f'Materialized "{title}" ({node_id})')
        click.echo(f'Created files: {node_id}.md, {node_id}.notes.md')
        click.echo('Updated binder structure')

    except PlaceholderNotFoundError:
        click.echo('Error: Placeholder not found', err=True)
        raise SystemExit(1) from None
    except AlreadyMaterializedError:
        click.echo(f"Error: '{title}' is already materialized", err=True)
        raise SystemExit(1) from None
    except FileSystemError:
        click.echo('Error: File creation failed', err=True)
        raise SystemExit(2) from None
