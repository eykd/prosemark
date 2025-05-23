"""Configuration manager for Prosemark.

This module provides the main ConfigManager class that handles loading,
merging, and validating configuration from multiple sources.
"""

import os
from pathlib import Path
from typing import Any

import click
import yaml

from prosemark.config.discovery import (
    CommandPath,
    discover_commands,
    get_command_option_names,
)
from prosemark.config.inheritance import build_inheritance_cache
from prosemark.config.models import create_model_cache


class ConfigManager:
    """Main configuration management class.

    This class handles loading, merging, and validating configuration from
    multiple sources according to precedence rules.

    Attributes:
        cli_group: The root Click CLI group.
        _commands: Mapping of command paths to their options.
        _command_options: Mapping of command paths to their option names.
        _models: Mapping of command paths to their Pydantic models.
        _resolved_configs: Cache of resolved configurations for all commands.

    """

    def __init__(self, cli_group: click.Group):
        """Initialize configuration system with Click CLI group.

        Args:
            cli_group: The root Click CLI group to discover commands from.

        """
        # Discover commands and their options
        commands, shared_options = discover_commands(cli_group)
        self.cli_group = cli_group
        self._commands = commands

        # Get option names for each command
        self._command_options = get_command_option_names(commands)

        # Generate Pydantic models for validation
        self._models = create_model_cache(commands)

        # Load configuration from all sources
        self._merged_config = self._load_config_layers()

        # Build cache of resolved configurations
        self._resolved_configs = build_inheritance_cache(
            self._merged_config, self._command_options
        )

    def reload(self) -> None:
        """Reload configuration from all sources."""
        self._merged_config = self._load_config_layers()
        self._resolved_configs = build_inheritance_cache(
            self._merged_config, self._command_options
        )

    def get_command_config(self, command_path: CommandPath) -> dict[str, Any]:
        """Get configuration for a command.

        Args:
            command_path: The path tuple for the command.

        Returns:
            The resolved configuration dictionary for the command.

        Raises:
            KeyError: If the command path is not found.

        """
        if command_path not in self._resolved_configs:
            raise KeyError(f'Unknown command path: {command_path}')

        return self._resolved_configs[command_path]

    def get_config_value(
        self, command_path: CommandPath, option_name: str, default: Any = None
    ) -> Any:
        """Get a specific configuration value for a command.

        Args:
            command_path: The path tuple for the command.
            option_name: The name of the option to get.
            default: The default value to return if the option is not found.

        Returns:
            The configuration value for the option, or the default if not found.

        """
        try:
            config = self.get_command_config(command_path)
            return config.get(option_name, default)
        except KeyError:
            return default

    def validate_config(self, command_path: CommandPath) -> dict[str, Any]:
        """Validate configuration for a command against its Pydantic model.

        Args:
            command_path: The path tuple for the command.

        Returns:
            The validated configuration dictionary.

        Raises:
            ValidationError: If the configuration is invalid.
            KeyError: If the command path is not found.

        """
        if command_path not in self._models:
            raise KeyError(f'Unknown command path: {command_path}')

        model = self._models[command_path]
        config = self.get_command_config(command_path)

        # Validate with Pydantic model
        validated = model(**config)

        # Convert back to dictionary
        return validated.model_dump()

    def _load_config_layers(self) -> dict[str, Any]:
        """Load and merge all configuration layers.

        Returns:
            The merged configuration dictionary from all sources.

        """
        # Start with empty configuration
        merged_config: dict[str, Any] = {}

        # Load user configuration file
        user_config_path = self._get_user_config_path()
        if user_config_path.exists():
            user_config = self._load_yaml_config(user_config_path)
            self._merge_configs(merged_config, user_config)

        # Load local project configuration file
        local_config_path = self._get_local_config_path()
        if local_config_path.exists():
            local_config = self._load_yaml_config(local_config_path)
            self._merge_configs(merged_config, local_config)

        # Apply environment variable overrides
        self._apply_env_overrides(merged_config)

        return merged_config

    def _merge_configs(self, base: dict[str, Any], overlay: dict[str, Any]) -> None:
        """Merge overlay configuration into base configuration.

        Args:
            base: The base configuration to merge into.
            overlay: The overlay configuration to merge from.

        """
        for key, value in overlay.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge dictionaries
                self._merge_configs(base[key], value)
            else:
                # Replace or add value
                base[key] = value

    def _load_yaml_config(self, file_path: Path) -> dict[str, Any]:
        """Load and parse YAML configuration file.

        Args:
            file_path: The path to the YAML configuration file.

        Returns:
            The parsed configuration dictionary.

        Raises:
            yaml.YAMLError: If the YAML file is invalid.

        """
        try:
            with open(file_path) as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            # Re-raise with more context
            raise yaml.YAMLError(f'Error parsing {file_path}: {e}') from e
        except OSError:
            # Handle file not found or permission errors
            return {}

    def _get_user_config_path(self) -> Path:
        """Get platform-appropriate user configuration file path.

        Returns:
            The path to the user configuration file.

        """
        # Check for override from environment variable
        env_config_file = os.environ.get('PMK_CONFIG_FILE')
        if env_config_file:
            return Path(env_config_file)

        # Use Click's app directory helper
        app_dir = Path(click.get_app_dir('prosemark'))
        return app_dir / 'config.yaml'

    def _get_local_config_path(self) -> Path:
        """Get local project configuration file path.

        Returns:
            The path to the local project configuration file.

        """
        return Path('.prosemark/config.yaml')

    def _apply_env_overrides(self, config: dict[str, Any]) -> None:
        """Apply environment variable overrides to configuration.

        Environment variables follow the pattern: PMK_{COMMAND}_{OPTION} (uppercase).

        Args:
            config: The configuration dictionary to apply overrides to.

        """
        prefix = 'PMK_'

        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix):].lower().split('_')

                if len(parts) < 2:
                    continue

                # Last part is the option name
                option_name = parts[-1]

                # Earlier parts form the command path
                command_parts = parts[:-1]

                # Find the right place in the config to put this value
                current = config
                for part in command_parts:
                    if part not in current:
                        current[part] = {}
                    elif not isinstance(current[part], dict):
                        # If it's not a dict, make it one (overriding previous value)
                        current[part] = {}

                    current = current[part]

                # Set the option value
                current[option_name] = value
