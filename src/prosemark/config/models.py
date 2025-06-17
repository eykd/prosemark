"""Pydantic model generation for configuration validation.

This module provides functionality to dynamically generate Pydantic models
from Click option definitions for configuration validation.
"""

from pathlib import Path
from typing import Any

import click
from pydantic import BaseModel, Field, create_model

from prosemark.config.discovery import ClickOption, CommandPath


def generate_pydantic_model(command_path: CommandPath, options: list[ClickOption]) -> type[BaseModel]:
    """Generate a Pydantic model for a command's options.

    Args:
        command_path: The path tuple for the command.
        options: The list of Click options for the command.

    Returns:
        A dynamically generated Pydantic model class for the command's options.

    """
    fields: dict[str, tuple[Any, Any]] = {}

    for name, option in options:
        field_type, field = click_type_to_pydantic_field(option)
        fields[name] = (field_type, field)

    # Create a dynamic model name based on the command path
    model_name = ''.join(part.capitalize() for part in command_path) + 'Config'

    result: type[BaseModel] = create_model(model_name, **fields)  # type: ignore[call-overload]
    return result


def click_type_to_pydantic_field(click_option: click.Option) -> tuple[Any, Any]:  # noqa: C901
    """Convert a Click option to a Pydantic field type and constraints.

    Args:
        click_option: The Click option to convert.

    Returns:
        A tuple of (field_type, field) where field_type is the Python type
        and field is a Pydantic Field with constraints.

    """
    param_type = click_option.type
    default = click_option.default
    required = click_option.required

    # Handle different Click types
    if isinstance(param_type, click.Choice):
        # For Choice, use str as the type (Literal with dynamic values is not supported by mypy)
        field_type: Any = str
    elif isinstance(param_type, click.Path):
        field_type = Path
    elif isinstance(param_type, click.IntRange):
        field_type = int
        min_val = getattr(param_type, 'min', None)
        max_val = getattr(param_type, 'max', None)
        field_kwargs = {}
        if min_val is not None:
            field_kwargs['ge'] = min_val
        if max_val is not None:
            field_kwargs['le'] = max_val
        return field_type, Field(default=default, **field_kwargs)
    elif param_type is click.STRING:
        field_type = str
    elif param_type is click.INT:
        field_type = int
    elif param_type is click.FLOAT:
        field_type = float
    elif param_type is click.BOOL:
        field_type = bool
    else:
        field_type = str

    # Handle multiple values (list types)
    if click_option.multiple:
        field_type = list

    # Create the field with default value
    if not required:  # pragma: no branch
        field_type = field_type | None

    field = Field(
        default=default,
        description=click_option.help or None,
    )

    return field_type, field


def create_model_cache(commands: dict[CommandPath, list[ClickOption]]) -> dict[CommandPath, type[BaseModel]]:
    """Generate and cache Pydantic models for all commands.

    Args:
        commands: Mapping of command paths to their options.

    Returns:
        A mapping of command paths to their Pydantic models.

    """
    return {path: generate_pydantic_model(path, options) for path, options in commands.items()}
