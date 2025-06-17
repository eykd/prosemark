"""Command discovery module for the configuration system.

This module provides functionality to discover Click commands and their options
to build inheritance relationships for configuration.
"""

from collections.abc import Iterator

import click
from click.core import Option

ClickOption = tuple[str, Option]
CommandPath = tuple[str, ...]


def discover_commands(
    cli_group: click.Group,
) -> tuple[dict[CommandPath, list[ClickOption]], dict[str, list[CommandPath]]]:
    """Discover all commands and their options to build inheritance relationships.

    Args:
        cli_group: The root Click CLI group to discover commands from.

    Returns:
        A tuple containing:
        - commands: Mapping of command paths to their options
        - shared_options: Mapping of option names to commands that use them

    """
    commands: dict[CommandPath, list[ClickOption]] = {}
    shared_options: dict[str, list[CommandPath]] = {}

    # Add the root group itself as the empty tuple path
    root_options = extract_click_options(cli_group)
    commands[()] = root_options
    for name, _ in root_options:
        if name not in shared_options:  # pragma: no branch
            shared_options[name] = []
        shared_options[name].append(())

    for path, command in walk_commands(cli_group):
        options = extract_click_options(command)
        commands[path] = options

        # Track which commands use which options for common section
        for name, _ in options:
            if name not in shared_options:
                shared_options[name] = []
            shared_options[name].append(path)

    return commands, shared_options


def extract_click_options(command: click.Command) -> list[ClickOption]:
    """Extract Click options with their types, defaults, and validation rules.

    Args:
        command: The Click command to extract options from.

    Returns:
        A list of tuples containing option names and their Click Option objects.

    """
    # Use the Python parameter name (e.g., 'output_format' for '--output-format')
    # This ensures consistency between CLI option names and config keys
    return [(param.name, param) for param in command.params if isinstance(param, click.Option) and param.name]


def walk_commands(cli_group: click.Group) -> Iterator[tuple[CommandPath, click.Command]]:
    """Recursively walk command tree yielding (path_tuple, command) pairs.

    Args:
        cli_group: The Click group to walk.

    Yields:
        Tuples of (command_path, command) where command_path is a tuple of command names.

    """
    for name, command in cli_group.commands.items():
        path = (name,)
        yield path, command

        if isinstance(command, click.Group):
            for subpath, subcmd in walk_commands(command):
                yield (name, *subpath), subcmd


def get_command_option_names(commands: dict[CommandPath, list[ClickOption]]) -> dict[CommandPath, set[str]]:
    """Get a mapping of command paths to their option names.

    Args:
        commands: Mapping of command paths to their options.

    Returns:
        A mapping of command paths to sets of option names.

    """
    return {path: {name for name, _ in options} for path, options in commands.items()}


def get_shared_options(command_options: dict[CommandPath, set[str]]) -> set[str]:
    """Find options that are shared across multiple commands.

    Args:
        command_options: Mapping of command paths to their option names.

    Returns:
        A set of option names that appear in multiple commands.

    """
    all_options: dict[str, int] = {}

    for options in command_options.values():
        for option in options:
            all_options[option] = all_options.get(option, 0) + 1

    return {option for option, count in all_options.items() if count > 1}
