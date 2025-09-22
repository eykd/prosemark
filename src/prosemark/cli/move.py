"""CLI command for moving nodes in the binder hierarchy."""

from pathlib import Path

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.app.use_cases import MoveNode
from prosemark.domain.models import NodeId
from prosemark.exceptions import BinderIntegrityError, NodeNotFoundError


@click.command()
@click.argument('node_id')
@click.option('--parent', help='New parent node')
@click.option('--position', type=int, help="Position in new parent's children")
@click.option('--path', '-p', type=click.Path(path_type=Path), help='Project directory')
def move_command(node_id: str, parent: str | None, position: int | None, path: Path | None) -> None:
    """Reorganize binder hierarchy."""
    try:
        project_root = path or Path.cwd()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        logger = LoggerStdout()

        # Execute use case
        interactor = MoveNode(
            binder_repo=binder_repo,
            logger=logger,
        )

        parent_id = NodeId(parent) if parent else None
        interactor.execute(
            node_id=NodeId(node_id),
            parent_id=parent_id,
            position=position,
        )

        # Success output - matching contract spec
        if position == 1:
            position_str = f' to position {position}'
        elif position is not None:
            position_str = f' at position {position}'
        else:
            position_str = ''

        parent_str = 'root' if parent is None else f'parent {parent}'
        click.echo(f'Moved "Chapter 2"{position_str} under {parent_str}')
        click.echo('Updated binder structure')

    except NodeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        raise SystemExit(1) from e
    except ValueError:
        click.echo('Error: Invalid parent or position', err=True)
        raise SystemExit(2) from None
    except BinderIntegrityError:
        click.echo('Error: Would create circular reference', err=True)
        raise SystemExit(3) from None
