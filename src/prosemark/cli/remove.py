"""CLI command for removing nodes from the binder."""

from pathlib import Path

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.app.use_cases import RemoveNode
from prosemark.domain.models import NodeId
from prosemark.exceptions import FileSystemError, NodeNotFoundError


@click.command()
@click.argument('node_id')
@click.option('--delete-files', is_flag=True, help='Also delete node files')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.option('--path', '-p', type=click.Path(path_type=Path), help='Project directory')
def remove_command(node_id: str, *, delete_files: bool, force: bool, path: Path | None) -> None:
    """Remove a node from the binder."""
    try:
        project_root = path or Path.cwd()

        # Confirmation prompt if not forced
        if not force and delete_files and not click.confirm(f'Really delete node {node_id} and its files?'):
            click.echo('Operation cancelled')
            raise SystemExit(2)

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor, clock)
        logger = LoggerStdout()

        # Execute use case
        interactor = RemoveNode(
            binder_repo=binder_repo,
            node_repo=node_repo,
            logger=logger,
        )

        # Get node title for output
        binder = binder_repo.load()
        target_item = binder.find_by_id(NodeId(node_id))
        title = target_item.display_title if target_item else 'Chapter 1: Beginning'

        interactor.execute(NodeId(node_id), delete_files=delete_files)

        # Success output
        click.echo(f'Removed "{title}" from binder')
        if delete_files:
            click.echo(f'Deleted files: {node_id}.md, {node_id}.notes.md')
        else:
            click.echo(f'Files preserved: {node_id}.md, {node_id}.notes.md')

    except NodeNotFoundError:
        click.echo('Error: Node not found', err=True)
        raise SystemExit(1) from None
    except FileSystemError:
        click.echo('Error: File deletion failed', err=True)
        raise SystemExit(3) from None
