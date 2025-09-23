# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Binder scaffold generator for new prosemark projects.

This module provides functionality to generate initial _binder.md files
for new prosemark projects with proper structure, format, and example content.
"""

from contextlib import suppress
from pathlib import Path

from prosemark.exceptions import FileSystemError, ProsemarkFileExistsError


def generate_binder_scaffold(target_path: Path, *, create_dirs: bool = False) -> None:
    """Generate a scaffold _binder.md file for a new prosemark project.

    Creates a _binder.md file with proper structure including managed block markers,
    example content, and helpful documentation for users. The file includes HTML
    comment markers that define the managed section for prosemark to maintain
    automatically.

    Args:
        target_path: Directory where the _binder.md file should be created
        create_dirs: If True, create parent directories if they don't exist

    Raises:
        ProsemarkFileExistsError: If _binder.md already exists in the target directory
        FileSystemError: If the file cannot be created due to I/O errors,
                        permission issues, or missing parent directories

    Examples:
        >>> # Basic usage
        >>> generate_binder_scaffold(Path('/path/to/project'))

        >>> # With directory creation
        >>> generate_binder_scaffold(Path('/path/to/new/project'), create_dirs=True)

    """
    # Validate and prepare target directory
    if create_dirs:
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            msg = 'Cannot create target directory'
            raise FileSystemError(msg, str(target_path)) from exc
    elif not target_path.exists():
        msg = 'Target directory does not exist'
        raise FileSystemError(msg, str(target_path))
    elif not target_path.is_dir():
        msg = 'Target path is not a directory'
        raise FileSystemError(msg, str(target_path))

    # Check for existing binder file
    binder_file = target_path / '_binder.md'
    try:
        if binder_file.exists():
            msg = 'Binder file already exists'
            raise ProsemarkFileExistsError(msg, str(binder_file))
    except (OSError, PermissionError) as exc:
        # If we can't even check if the file exists due to permissions, we can't write either
        msg = 'Cannot access target directory'
        raise FileSystemError(msg, str(target_path)) from exc

    # Generate scaffold content
    content = _generate_scaffold_content()

    # Write the file atomically
    try:
        # Write to temporary file first, then rename for atomicity
        temp_file = binder_file.with_suffix('.tmp')
        temp_file.write_text(content, encoding='utf-8')
        temp_file.rename(binder_file)
    except OSError as exc:
        # Clean up temporary file if it exists
        if temp_file.exists():  # pragma: no cover
            with suppress(OSError):
                temp_file.unlink()

        msg = 'Cannot write binder file'
        raise FileSystemError(msg, str(binder_file)) from exc


def _generate_scaffold_content() -> str:
    """Generate the content for the scaffold _binder.md file.

    Creates the complete content including documentation, managed block
    markers, and example content that demonstrates proper binder format.

    Returns:
        Complete content string for the _binder.md file

    """
    return """# Binder

Welcome to your new prosemark project! This file serves as your project outline and table of contents.

You can write notes, introductions, and other content anywhere in this file.
Only the section between the special markers below is managed by prosemark.

## Binder (managed by Prosemark)
<!-- pmk:begin-binder -->
- [Sample Chapter](01234567.md)
- [New Placeholder]()
<!-- pmk:end-binder -->

The managed section above will be automatically updated as you add, move, and remove nodes.
"""
