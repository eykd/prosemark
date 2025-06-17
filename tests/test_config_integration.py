"""Integration tests for the configuration system with a real application."""

from pathlib import Path

import click
import pytest
import yaml
from click.testing import CliRunner

from prosemark.config.manager import ConfigManager


@pytest.fixture
def sample_app() -> click.Group:
    """Create a sample application for testing."""

    @click.group()
    @click.option('--verbose', is_flag=True, help='Enable verbose output')
    @click.option('--color', type=click.Choice(['auto', 'always', 'never']), default='auto', help='Colorize output')
    @click.pass_context
    def app(ctx: click.Context, verbose: bool, color: str) -> None:  # noqa: FBT001
        """Sample application with configuration."""
        # Store context for later use
        ctx.ensure_object(dict)
        ctx.obj['verbose'] = verbose
        ctx.obj['color'] = color

    @app.command()
    @click.option('--name', default='world', help='Name to greet')
    @click.pass_context
    def hello(ctx: click.Context, name: str) -> None:
        """Say hello to someone."""
        verbose = ctx.obj.get('verbose', False)
        if verbose:
            click.echo('Verbose mode enabled')
        click.echo(f'Hello, {name}!')

    @app.group()
    @click.option('--format', type=click.Choice(['text', 'json', 'yaml']), default='text', help='Output format')
    @click.pass_context
    def output(ctx: click.Context, output_format: str) -> None:
        """Output commands."""
        ctx.ensure_object(dict)
        ctx.obj['format'] = output_format

    @output.command()
    @click.option('--limit', type=int, default=10, help='Limit number of items')
    @click.pass_context
    def list_items(ctx: click.Context, limit: int) -> None:
        """List items."""
        format_type = ctx.obj.get('format', 'text')
        click.echo(f'Listing {limit} items in {format_type} format')

    output.add_command(list_items, name='list')

    return app


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a sample configuration file."""
    config_dir = tmp_path / '.prosemark'
    config_dir.mkdir()
    config_path = config_dir / 'config.yaml'

    config = {
        'common': {
            'verbose': True,
            'color': 'always',
        },
        'hello': {
            'name': 'configured',
        },
        'output': {
            'format': 'json',
            'list': {
                'limit': 20,
            },
        },
    }

    with config_path.open('w') as f:
        yaml.dump(config, f)

    return config_path


def test_app_with_config(config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the sample application with configuration."""

    # Create a wrapper that uses ConfigManager
    @click.group()
    @click.option('--verbose', is_flag=True, help='Enable verbose output')
    @click.option('--color', type=click.Choice(['auto', 'always', 'never']), default='auto', help='Colorize output')
    @click.pass_context
    def app_with_config(ctx: click.Context, verbose: bool, color: str) -> None:  # noqa: FBT001
        """Sample application with configuration."""
        # Override local config path BEFORE ConfigManager is created
        monkeypatch.setattr(ConfigManager, '_get_local_config_path', lambda _: config_file)
        # Initialize ConfigManager
        config_manager = ConfigManager(app_with_config)

        # Get configuration for the current command
        config = config_manager.get_command_config(())

        # Use CLI args if provided, otherwise use config
        ctx.ensure_object(dict)
        ctx.obj['config_manager'] = config_manager
        ctx.obj['verbose'] = verbose or config.get('verbose', False)
        ctx.obj['color'] = color if color != 'auto' else config.get('color', 'auto')

    @app_with_config.command()
    @click.option('--name', default='world', help='Name to greet')
    @click.pass_context
    def hello(ctx: click.Context, name: str) -> None:
        """Say hello to someone."""
        config_manager = ctx.obj['config_manager']
        if name == 'world':  # Default value
            name = config_manager.get_config_value(('hello',), 'name', default=name)
        verbose = ctx.obj.get('verbose', False)
        if verbose:
            click.echo('Verbose mode enabled')
        click.echo(f'Hello, {name}!')

    @app_with_config.group()
    @click.option('--output-format', type=click.Choice(['text', 'json', 'yaml']), default='text', help='Output format')
    @click.pass_context
    def output(ctx: click.Context, output_format: str) -> None:
        """Output commands."""
        ctx.ensure_object(dict)
        config_manager = ctx.obj['config_manager']
        if output_format == 'text':  # Default value
            output_format = config_manager.get_config_value(('output',), 'output_format', default=output_format)
        ctx.obj['format'] = output_format

    @output.command('list')
    @click.option('--limit', type=int, default=10, help='Limit number of items')
    @click.pass_context
    def list_items(ctx: click.Context, limit: int) -> None:
        """List items."""
        config_manager = ctx.obj['config_manager']
        if limit == 10:  # Default value
            limit = config_manager.get_config_value(('output', 'list'), 'limit', default=limit)
        format_type = ctx.obj.get('format', 'text')
        click.echo(f'Listing {limit} items in {format_type} format')

    # Test the application
    runner = CliRunner()
    result = runner.invoke(app_with_config, ['hello'])

    # Check that configuration was applied
    assert result.exit_code == 0
    assert 'Hello, configured!' in result.output

    # Test with CLI args overriding config
    result = runner.invoke(app_with_config, ['hello', '--name', 'override'])
    assert result.exit_code == 0
    assert 'Hello, override!' in result.output

    # Test nested command with inherited config
    result = runner.invoke(app_with_config, ['output', 'list'])
    assert result.exit_code == 0
    assert 'Listing 20 items in json format' in result.output


def test_env_var_override(sample_app: click.Group, config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test environment variable overrides."""
    # Set environment variables
    monkeypatch.setenv('PMK_HELLO_NAME', 'env_override')
    monkeypatch.setenv('PMK_OUTPUT_FORMAT', 'yaml')

    # Create ConfigManager with environment variable overrides
    config_manager = ConfigManager(sample_app)

    # Override local config path
    monkeypatch.setattr(config_manager, '_get_local_config_path', lambda: config_file)

    # Reload to apply environment variables
    config_manager.reload()

    # Check that environment variables override config file
    hello_config = config_manager.get_command_config(('hello',))
    assert hello_config['name'] == 'env_override'

    output_config = config_manager.get_command_config(('output',))
    assert output_config['format'] == 'yaml'
