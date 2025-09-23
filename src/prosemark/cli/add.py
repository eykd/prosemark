"""CLI command for adding nodes to the binder."""

from pathlib import Path

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.console_pretty import ConsolePretty
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.id_generator_uuid7 import IdGeneratorUuid7
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.app.use_cases import AddNode, InitProject
from prosemark.domain.models import NodeId
from prosemark.exceptions import FileSystemError, NodeNotFoundError


@click.command()
@click.argument('title')
@click.option('--parent', help='Parent node ID')
@click.option('--position', type=int, help="Position in parent's children")
@click.option('--path', '-p', type=click.Path(path_type=Path), help='Project directory')
def add_command(title: str, parent: str | None, position: int | None, path: Path | None) -> None:  # noqa: PLR0914
    """Add a new node to the binder hierarchy."""
    try:
        project_root = path or Path.cwd()

        # Auto-initialize project if it doesn't exist
        binder_path = project_root / '_binder.md'
        if not binder_path.exists():
            # Initialize empty project silently
            from prosemark.cli.init import FileSystemConfigPort

            binder_repo_init = BinderRepoFs(project_root)
            config_port = FileSystemConfigPort()
            console_port = ConsolePretty()
            logger_init = LoggerStdout()
            clock_init = ClockSystem()

            init_interactor = InitProject(
                binder_repo=binder_repo_init,
                config_port=config_port,
                console_port=console_port,
                logger=logger_init,
                clock=clock_init,
            )
            init_interactor.execute(project_root)

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor, clock)
        id_generator = IdGeneratorUuid7()
        logger = LoggerStdout()

        # Execute use case
        interactor = AddNode(
            binder_repo=binder_repo,
            node_repo=node_repo,
            id_generator=id_generator,
            logger=logger,
            clock=clock,
        )

        # Validate position if provided
        if position is not None and position < 0:
            click.echo('Error: Invalid position index', err=True)
            raise SystemExit(2)

        parent_id = None
        if parent:
            try:
                parent_id = NodeId(parent)
            except ValueError as err:
                # Invalid parent ID format, treat as "parent not found"
                click.echo('Error: Parent node not found', err=True)
                raise SystemExit(1) from err
        node_id = interactor.execute(
            title=title,
            synopsis=None,
            parent_id=parent_id,
            position=position,
        )

        # Success output
        click.echo(f'Added "{title}" ({node_id})')
        click.echo(f'Created files: {node_id}.md, {node_id}.notes.md')
        click.echo('Updated binder structure')

    except NodeNotFoundError as err:
        click.echo('Error: Parent node not found', err=True)
        raise SystemExit(1) from err
    except ValueError as err:
        click.echo('Error: Invalid position index', err=True)
        raise SystemExit(2) from err
    except FileSystemError as err:
        click.echo(f'Error: File creation failed - {err}', err=True)
        raise SystemExit(3) from err
