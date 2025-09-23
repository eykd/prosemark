"""CLI command for initializing a new prosemark project."""

from pathlib import Path
from typing import Any

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.console_pretty import ConsolePretty
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.app.use_cases import InitProject
from prosemark.exceptions import BinderIntegrityError, FileSystemError
from prosemark.ports.config_port import ConfigPort, ProsemarkConfig


class FileSystemConfigPort(ConfigPort):
    """Temporary config port implementation."""

    def create_default_config(self, config_path: Path) -> None:
        """Create default configuration file."""
        # For MVP, we don't need a config file

    @staticmethod
    def config_exists(config_path: Path) -> bool:
        """Check if configuration file already exists."""
        return config_path.exists()

    @staticmethod
    def get_default_config_values() -> ProsemarkConfig:
        """Return default configuration values as dictionary."""
        return {}

    @staticmethod
    def load_config(_config_path: Path | None = None) -> dict[str, Any]:
        """Load configuration from file."""
        return {}


@click.command()
@click.option('--title', '-t', required=True, help='Project title')
@click.option('--path', '-p', type=click.Path(path_type=Path), help='Project directory')
def init_command(title: str, path: Path | None) -> None:
    """Initialize a new prosemark project."""
    try:
        project_path = path or Path.cwd()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_path)
        config_port = FileSystemConfigPort()
        console_port = ConsolePretty()
        logger = LoggerStdout()
        clock = ClockSystem()

        # Execute use case
        interactor = InitProject(
            binder_repo=binder_repo,
            config_port=config_port,
            console_port=console_port,
            logger=logger,
            clock=clock,
        )
        interactor.execute(project_path)

        # Success output matching test expectations
        click.echo(f'Project "{title}" initialized successfully')
        click.echo('Created _binder.md with project structure')

    except BinderIntegrityError:
        click.echo('Error: Directory already contains a prosemark project', file=click.get_text_stream('stderr'))
        raise SystemExit(1) from None
    except FileSystemError as err:
        click.echo(f'Error: {err}', file=click.get_text_stream('stderr'))
        raise SystemExit(2) from err
    except Exception as err:
        click.echo(f'Unexpected error: {err}', file=click.get_text_stream('stderr'))
        raise SystemExit(3) from err
