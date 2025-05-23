"""Tests for the configuration system."""

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import click
import pytest
import yaml
from click.testing import CliRunner
from pydantic import ValidationError

from prosemark.config.discovery import (
    discover_commands,
    extract_click_options,
    get_command_option_names,
    walk_commands,
)
from prosemark.config.inheritance import (
    build_inheritance_cache,
    get_nested_config,
    resolve_inheritance,
)
from prosemark.config.manager import ConfigManager
from prosemark.config.models import (
    click_type_to_pydantic_field,
    create_model_cache,
    generate_pydantic_model,
)


# Test fixtures
@pytest.fixture
def sample_cli_group() -> click.Group:
    """Create a sample Click CLI group for testing."""
    @click.group()
    @click.option('--verbose', is_flag=True, help='Enable verbose output')
    def cli(verbose: bool) -> None:
        """Sample CLI group."""

    @cli.command()
    @click.option('--count', type=int, default=1, help='Number of greetings')
    def hello(count: int) -> None:
        """Say hello."""

    @cli.group()
    @click.option('--color', type=click.Choice(['red', 'green', 'blue']), default='blue')
    def nested(color: str) -> None:
        """Nested command group."""

    @nested.command()
    @click.option('--name', default='world', help='Name to greet')
    def greet(name: str) -> None:
        """Greet someone."""

    return cli


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Create a sample configuration dictionary for testing."""
    return {
        'common': {
            'verbose': True,
            'color': 'red',
        },
        'hello': {
            'count': 5,
        },
        'nested': {
            'color': 'green',
            'greet': {
                'name': 'test',
            },
        },
    }


# Discovery tests
def test_walk_commands(sample_cli_group: click.Group) -> None:
    """Test walking the command tree."""
    commands = list(walk_commands(sample_cli_group))

    # Check that we found all commands
    assert len(commands) == 3

    # Check command paths
    paths = [path for path, _ in commands]
    assert ('hello',) in paths
    assert ('nested',) in paths
    assert ('nested', 'greet') in paths


def test_extract_click_options(sample_cli_group: click.Group) -> None:
    """Test extracting Click options from a command."""
    # Get the hello command
    hello_cmd = sample_cli_group.commands['hello']
    options = extract_click_options(hello_cmd)

    # Check that we found the count option
    assert len(options) == 1
    assert options[0][0] == 'count'

    # Check option properties
    _, option = options[0]
    assert option.type == click.INT
    assert option.default == 1
    assert 'Number of greetings' in option.help


def test_discover_commands(sample_cli_group: click.Group) -> None:
    """Test discovering commands and their options."""
    commands, shared_options = discover_commands(sample_cli_group)

    # Check that we found all commands
    assert len(commands) == 3

    # Check command paths
    assert ('hello',) in commands
    assert ('nested',) in commands
    assert ('nested', 'greet') in commands

    # Check options for hello command
    hello_options = commands['hello',]
    assert len(hello_options) == 1
    assert hello_options[0][0] == 'count'

    # Check shared options
    assert 'verbose' in shared_options
    assert len(shared_options['verbose']) == 3  # All commands inherit from root


def test_get_command_option_names(sample_cli_group: click.Group) -> None:
    """Test getting option names for commands."""
    commands, _ = discover_commands(sample_cli_group)
    command_options = get_command_option_names(commands)

    # Check option names for hello command
    assert ('hello',) in command_options
    assert 'count' in command_options['hello',]

    # Check option names for nested.greet command
    assert ('nested', 'greet') in command_options
    assert 'name' in command_options['nested', 'greet']


# Inheritance tests
def test_get_nested_config(sample_config: dict[str, Any]) -> None:
    """Test getting nested configuration for a command path."""
    # Test getting root level section
    hello_config = get_nested_config(sample_config, ('hello',))
    assert hello_config == {'count': 5}

    # Test getting nested section
    greet_config = get_nested_config(sample_config, ('nested', 'greet'))
    assert greet_config == {'name': 'test'}

    # Test getting non-existent section
    missing_config = get_nested_config(sample_config, ('missing',))
    assert missing_config == {}


def test_resolve_inheritance(sample_config: dict[str, Any]) -> None:
    """Test resolving inheritance for a command path."""
    # Test resolving for hello command
    hello_options = {'count', 'verbose'}
    hello_resolved = resolve_inheritance(sample_config, ('hello',), hello_options)
    assert hello_resolved == {'count': 5, 'verbose': True}

    # Test resolving for nested.greet command
    greet_options = {'name', 'color', 'verbose'}
    greet_resolved = resolve_inheritance(sample_config, ('nested', 'greet'), greet_options)
    assert greet_resolved == {'name': 'test', 'color': 'green', 'verbose': True}


def test_build_inheritance_cache(sample_config: dict[str, Any]) -> None:
    """Test building inheritance cache for all commands."""
    command_options = {
        ('hello',): {'count', 'verbose'},
        ('nested',): {'color', 'verbose'},
        ('nested', 'greet'): {'name', 'color', 'verbose'},
    }

    cache = build_inheritance_cache(sample_config, command_options)

    # Check cache entries
    assert len(cache) == 3
    assert cache['hello',] == {'count': 5, 'verbose': True}
    assert cache['nested',] == {'color': 'green', 'verbose': True}
    assert cache['nested', 'greet'] == {'name': 'test', 'color': 'green', 'verbose': True}


# Model tests
def test_click_type_to_pydantic_field() -> None:
    """Test converting Click types to Pydantic fields."""
    # Test string type
    string_option = click.Option(['--name'], type=click.STRING, default='test')
    field_type, field = click_type_to_pydantic_field(string_option)
    assert field_type == str
    assert field.default == 'test'

    # Test int type
    int_option = click.Option(['--count'], type=click.INT, default=1)
    field_type, field = click_type_to_pydantic_field(int_option)
    assert field_type == int
    assert field.default == 1

    # Test choice type
    choice_option = click.Option(
        ['--color'], type=click.Choice(['red', 'green', 'blue']), default='blue'
    )
    field_type, _ = click_type_to_pydantic_field(choice_option)
    # Check that it's a Literal type
    assert hasattr(field_type, '__origin__') and field_type.__origin__ == Literal  # type: ignore


def test_generate_pydantic_model(sample_cli_group: click.Group) -> None:
    """Test generating a Pydantic model for a command."""
    # Get options for hello command
    commands, _ = discover_commands(sample_cli_group)
    hello_options = commands['hello',]

    # Generate model
    model = generate_pydantic_model(('hello',), hello_options)

    # Check model properties
    assert model.__name__ == 'HelloConfig'

    # Create an instance and validate
    instance = model(count=5)
    assert instance.count == 5

    # Test validation error
    with pytest.raises(ValidationError):
        model(count='invalid')  # type: ignore


def test_create_model_cache(sample_cli_group: click.Group) -> None:
    """Test creating a cache of Pydantic models for all commands."""
    commands, _ = discover_commands(sample_cli_group)
    models = create_model_cache(commands)

    # Check that we have models for all commands
    assert len(models) == 3
    assert ('hello',) in models
    assert ('nested',) in models
    assert ('nested', 'greet') in models

    # Check model names
    assert models['hello',].__name__ == 'HelloConfig'
    assert models['nested',].__name__ == 'NestedConfig'
    assert models['nested', 'greet'].__name__ == 'NestedGreetConfig'


# ConfigManager tests
@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary configuration file for testing."""
    config_path = tmp_path / 'config.yaml'
    config = {
        'common': {
            'verbose': True,
        },
        'hello': {
            'count': 5,
        },
    }

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return config_path


def test_config_manager_init(sample_cli_group: click.Group) -> None:
    """Test initializing the ConfigManager."""
    with patch('prosemark.config.manager.ConfigManager._load_config_layers') as mock_load:
        mock_load.return_value = {}
        manager = ConfigManager(sample_cli_group)

        # Check that commands were discovered
        assert len(manager._commands) == 3
        assert ('hello',) in manager._commands

        # Check that models were created
        assert len(manager._models) == 3
        assert ('hello',) in manager._models


def test_config_manager_get_command_config(
    sample_cli_group: click.Group, sample_config: dict[str, Any]
) -> None:
    """Test getting configuration for a command."""
    with patch('prosemark.config.manager.ConfigManager._load_config_layers') as mock_load:
        mock_load.return_value = sample_config
        manager = ConfigManager(sample_cli_group)

        # Get config for hello command
        hello_config = manager.get_command_config(('hello',))
        assert 'count' in hello_config
        assert hello_config['count'] == 5

        # Test error for unknown command
        with pytest.raises(KeyError):
            manager.get_command_config(('unknown',))


def test_config_manager_get_config_value(
    sample_cli_group: click.Group, sample_config: dict[str, Any]
) -> None:
    """Test getting a specific configuration value for a command."""
    with patch('prosemark.config.manager.ConfigManager._load_config_layers') as mock_load:
        mock_load.return_value = sample_config
        manager = ConfigManager(sample_cli_group)

        # Get specific value
        count = manager.get_config_value(('hello',), 'count')
        assert count == 5

        # Test default value for missing option
        missing = manager.get_config_value(('hello',), 'missing', default='default')
        assert missing == 'default'

        # Test default value for unknown command
        unknown = manager.get_config_value(('unknown',), 'option', default='default')
        assert unknown == 'default'


def test_config_manager_validate_config(
    sample_cli_group: click.Group, sample_config: dict[str, Any]
) -> None:
    """Test validating configuration for a command."""
    with patch('prosemark.config.manager.ConfigManager._load_config_layers') as mock_load:
        mock_load.return_value = sample_config
        manager = ConfigManager(sample_cli_group)

        # Validate hello config
        validated = manager.validate_config(('hello',))
        assert validated['count'] == 5

        # Test error for unknown command
        with pytest.raises(KeyError):
            manager.validate_config(('unknown',))


def test_config_manager_load_yaml_config(tmp_path: Path) -> None:
    """Test loading a YAML configuration file."""
    # Create a test YAML file
    config_path = tmp_path / 'config.yaml'
    config = {'test': {'key': 'value'}}

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    # Create a ConfigManager with a mock CLI group
    with patch('prosemark.config.manager.discover_commands') as mock_discover:
        mock_discover.return_value = ({}, {})
        manager = ConfigManager(MagicMock())

        # Test loading the YAML file
        loaded = manager._load_yaml_config(config_path)
        assert loaded == config

        # Test loading a non-existent file
        missing = manager._load_yaml_config(tmp_path / 'missing.yaml')
        assert missing == {}


def test_config_manager_get_user_config_path() -> None:
    """Test getting the user configuration file path."""
    # Create a ConfigManager with a mock CLI group
    with patch('prosemark.config.manager.discover_commands') as mock_discover:
        mock_discover.return_value = ({}, {})
        manager = ConfigManager(MagicMock())

        # Test default path
        with patch('click.get_app_dir') as mock_get_app_dir:
            mock_get_app_dir.return_value = '/app/dir'
            path = manager._get_user_config_path()
            assert path == Path('/app/dir/config.yaml')

        # Test environment variable override
        with patch.dict(os.environ, {'PMK_CONFIG_FILE': '/custom/path.yaml'}):
            path = manager._get_user_config_path()
            assert path == Path('/custom/path.yaml')


def test_config_manager_get_local_config_path() -> None:
    """Test getting the local project configuration file path."""
    # Create a ConfigManager with a mock CLI group
    with patch('prosemark.config.manager.discover_commands') as mock_discover:
        mock_discover.return_value = ({}, {})
        manager = ConfigManager(MagicMock())

        # Test path
        path = manager._get_local_config_path()
        assert path == Path('.prosemark/config.yaml')


def test_config_manager_apply_env_overrides() -> None:
    """Test applying environment variable overrides to configuration."""
    # Create a ConfigManager with a mock CLI group
    with patch('prosemark.config.manager.discover_commands') as mock_discover:
        mock_discover.return_value = ({}, {})
        manager = ConfigManager(MagicMock())

        # Test applying environment variables
        config: dict[str, Any] = {}
        with patch.dict(os.environ, {
            'PMK_HELLO_COUNT': '10',
            'PMK_NESTED_GREET_NAME': 'env',
        }):
            manager._apply_env_overrides(config)

            assert config['hello']['count'] == '10'
            assert config['nested']['greet']['name'] == 'env'


def test_config_manager_merge_configs() -> None:
    """Test merging configuration dictionaries."""
    # Create a ConfigManager with a mock CLI group
    with patch('prosemark.config.manager.discover_commands') as mock_discover:
        mock_discover.return_value = ({}, {})
        manager = ConfigManager(MagicMock())

        # Test merging dictionaries
        base = {
            'common': {
                'verbose': True,
            },
            'hello': {
                'count': 1,
            },
        }

        overlay = {
            'common': {
                'color': 'red',
            },
            'hello': {
                'count': 5,
            },
            'new': {
                'key': 'value',
            },
        }

        manager._merge_configs(base, overlay)

        # Check merged result
        assert base['common']['verbose'] is True
        assert base['common']['color'] == 'red'
        assert base['hello']['count'] == 5
        assert base['new']['key'] == 'value'


def test_config_manager_reload(sample_cli_group: click.Group) -> None:
    """Test reloading configuration."""
    with patch('prosemark.config.manager.ConfigManager._load_config_layers') as mock_load:
        # First load returns empty config
        mock_load.return_value = {}
        manager = ConfigManager(sample_cli_group)

        # Second load returns sample config
        mock_load.return_value = {'hello': {'count': 10}}
        manager.reload()

        # Check that config was reloaded
        hello_config = manager.get_command_config(('hello',))
        assert 'count' in hello_config
        assert hello_config['count'] == 10


def test_integration_with_click(sample_cli_group: click.Group, tmp_path: Path) -> None:
    """Test integration with Click commands."""
    # Create a test configuration file
    config_dir = tmp_path / '.prosemark'
    config_dir.mkdir()
    config_path = config_dir / 'config.yaml'

    config = {
        'hello': {
            'count': 5,
        },
    }

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    # Create a Click command that uses ConfigManager
    @click.command()
    @click.option('--count', type=int, default=1, help='Number of greetings')
    def hello_cmd(count: int) -> None:
        """Say hello with configuration."""
        # Use configuration value if not explicitly provided
        if count == 1:  # Default value
            with patch('prosemark.config.manager.ConfigManager._get_local_config_path') as mock_path:
                mock_path.return_value = config_path
                manager = ConfigManager(sample_cli_group)
                count = manager.get_config_value(('hello',), 'count', default=count)

        click.echo(f'Hello {count} times!')

    # Test command with configuration
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Copy config file to isolated filesystem
        os.makedirs('.prosemark')
        with open('.prosemark/config.yaml', 'w') as f:
            yaml.dump(config, f)

        # Run command without explicit count (should use config)
        result = runner.invoke(hello_cmd)
        assert result.exit_code == 0
        assert 'Hello 5 times!' in result.output

        # Run command with explicit count (should override config)
        result = runner.invoke(hello_cmd, ['--count', '3'])
        assert result.exit_code == 0
        assert 'Hello 3 times!' in result.output
