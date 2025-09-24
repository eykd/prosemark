"""Title processing utilities for freewriting feature.

This module provides utilities for processing and sanitizing titles
for use in freewriting sessions, including length handling and
character sanitization.
"""

from __future__ import annotations


def process_title(title: str, max_length: int = 50) -> str:
    """Process a title for use in freewriting sessions.

    Args:
        title: The raw title string to process.
        max_length: Maximum allowed length for the processed title.

    Returns:
        Processed title, truncated if necessary with ellipsis.

    """
    if not title:
        return title

    # Strip whitespace
    processed = title.strip()

    # Truncate if too long
    if len(processed) > max_length:
        processed = processed[: max_length - 3] + '...'

    return processed


def sanitize_title_for_filename(title: str) -> str:
    """Sanitize a title for safe use in filenames.

    Args:
        title: The title string to sanitize.

    Returns:
        Sanitized title safe for use in filenames.

    """
    # Use the FileSystemAdapter's sanitize method
    from prosemark.freewriting.adapters.file_system_adapter import FileSystemAdapter

    return FileSystemAdapter.sanitize_title(title)
