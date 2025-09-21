"""CLI command for creating freeform writing files."""

from pathlib import Path

import click

from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.daily_repo_fs import DailyRepoFs
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.id_generator import SimpleIdGenerator
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.app.use_cases import WriteFreeform
from prosemark.exceptions import EditorLaunchError, FileSystemError


@click.command()
@click.argument('title', required=False)
def write_command(title: str | None) -> None:
    """Create a timestamped freeform writing file."""
    try:
        project_root = Path.cwd()

        # Wire up dependencies
        clock = ClockSystem()
        id_generator = SimpleIdGenerator()
        daily_repo = DailyRepoFs(project_root, id_generator=id_generator, clock=clock)  # type: ignore
        editor_port = EditorLauncherSystem()
        logger = LoggerStdout()
        clock = ClockSystem()

        # Execute use case
        interactor = WriteFreeform(
            daily_repo=daily_repo,
            editor_port=editor_port,
            logger=logger,
            clock=clock,
        )

        filename = interactor.execute(title)

        # Success output
        click.echo(f'Created freeform file: {filename}')
        click.echo('Opened in editor')

    except FileSystemError:
        click.echo('Error: File creation failed', err=True)
        raise SystemExit(1)
    except EditorLaunchError:
        click.echo('Error: Editor launch failed', err=True)
        raise SystemExit(2)
