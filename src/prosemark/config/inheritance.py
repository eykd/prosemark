"""Inheritance resolution for configuration.

This module provides functionality to resolve inheritance relationships
to create flat, command-specific configurations.
"""

from typing import Any

from prosemark.config.discovery import CommandPath


def resolve_inheritance(
    merged_config: dict[str, Any], command_path: CommandPath, command_options: set[str]
) -> dict[str, Any]:
    """Recursively resolve inheritance for a command path.

    Args:
        merged_config: The merged configuration from all sources.
        command_path: The path tuple for the command.
        command_options: Set of option names valid for this command.

    Returns:
        A flat dictionary with resolved configuration for the command.

    """
    resolved_config: dict[str, Any] = {}

    # Start with common section (only for options this command actually has)
    if 'common' in merged_config and isinstance(merged_config['common'], dict):
        common_section = {k: v for k, v in merged_config['common'].items() if k in command_options}
        resolved_config.update(common_section)

    # Apply parent command configurations in order
    for i in range(1, len(command_path)):
        parent_path = command_path[:i]
        parent_section = get_nested_config(merged_config, parent_path)

        if parent_section:
            parent_filtered = {k: v for k, v in parent_section.items() if k in command_options}
            resolved_config.update(parent_filtered)

    # Apply command-specific configuration last
    command_section = get_nested_config(merged_config, command_path)
    if command_section:
        command_filtered = {k: v for k, v in command_section.items() if k in command_options}
        resolved_config.update(command_filtered)

    return resolved_config


def get_nested_config(config_dict: dict[str, Any], path: CommandPath) -> dict[str, Any]:
    """Extract nested configuration for a command path.

    Args:
        config_dict: The configuration dictionary.
        path: The command path to extract configuration for.

    Returns:
        The nested configuration dictionary for the command path,
        or an empty dictionary if not found.

    """
    if not path:
        return {}

    current = config_dict
    for part in path:
        if part in current and isinstance(current[part], dict):
            current = current[part]
        else:
            return {}

    return current


def build_inheritance_cache(
    merged_config: dict[str, Any],
    commands: dict[CommandPath, set[str]],
) -> dict[CommandPath, dict[str, Any]]:
    """Build cache of resolved configurations for all commands.

    Args:
        merged_config: The merged configuration from all sources.
        commands: Mapping of command paths to their option names.

    Returns:
        A mapping of command paths to their resolved configurations.

    """
    return {path: resolve_inheritance(merged_config, path, options) for path, options in commands.items()}
