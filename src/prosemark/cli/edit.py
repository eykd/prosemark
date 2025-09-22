"""CLI command for editing node content."""

from pathlib import Path

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.app.use_cases import EditPart
from prosemark.domain.models import NodeId
from prosemark.exceptions import EditorLaunchError, FileSystemError, NodeNotFoundError


@click.command()
@click.argument('node_id')
@click.option('--part', required=True, help='Content part to edit (draft/notes/synopsis)')
@click.option('--path', '-p', type=click.Path(path_type=Path), help='Project directory')
def edit_command(node_id: str, part: str, path: Path | None) -> None:
    """Open node content in your preferred editor."""
    try:
        project_root = path or Path.cwd()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor, clock)
        logger = LoggerStdout()

        # Execute use case
        interactor = EditPart(
            binder_repo=binder_repo,
            node_repo=node_repo,
            logger=logger,
        )

        interactor.execute(NodeId(node_id), part)

        # Success output
        if part == 'draft':
            click.echo(f'Opened {node_id}.md in editor')
        elif part == 'notes':
            click.echo(f'Opened {node_id}.notes.md in editor')
        else:
            click.echo(f'Opened {part} for {node_id} in editor')

    except NodeNotFoundError as err:
        click.echo('Error: Node not found', err=True)
        raise SystemExit(1) from err
    except EditorLaunchError as err:
        click.echo('Error: Editor not available', err=True)
        raise SystemExit(2) from err
    except FileSystemError as err:
        click.echo('Error: File permission denied', err=True)
        raise SystemExit(3) from err
    except ValueError as err:
        click.echo(f'Error: {err}', err=True)
        raise SystemExit(1) from err
