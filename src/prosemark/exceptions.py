"""Custom exceptions for prosemark.

This module defines all domain-specific exceptions used throughout the prosemark
application. All exceptions inherit from ProsemarkError and follow these conventions:
- No custom __init__ methods
- Extra context passed as additional arguments
- No variable interpolation in error messages
"""


class ProsemarkError(Exception):
    """Base exception for all prosemark errors.

    All domain exceptions should inherit from this class to provide
    a consistent exception hierarchy for error handling.
    """


class BinderIntegrityError(ProsemarkError):
    """Error raised when binder tree integrity is violated.

    This exception indicates violations of tree invariants such as:
    - Duplicate nodes in the tree
    - Invalid parent-child relationships
    - Circular references
    - Orphaned nodes

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as node IDs, file paths, etc.

    """


class NodeIdentityError(ProsemarkError):
    """Error raised when node identity validation fails.

    This exception indicates issues with NodeID format or uniqueness:
    - Invalid UUID format
    - Non-UUIDv7 identifiers
    - Identity conflicts between nodes

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as the invalid ID value

    """


class BinderNotFoundError(ProsemarkError):
    """Error raised when the binder file is missing.

    This exception indicates that the expected _binder.md file
    cannot be found in the specified location.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as the expected file path

    """


class NodeNotFoundError(ProsemarkError):
    """Error raised when a referenced node doesn't exist.

    This exception indicates that a node referenced by ID or path
    cannot be found in the binder tree or filesystem.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as the missing node ID

    """


class FilesystemError(ProsemarkError):
    """Error raised for file system operation failures.

    This exception wraps various filesystem-related errors such as:
    - Permission denied errors
    - I/O errors
    - Path not found errors
    - Disk space errors

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as file paths and operation type

    """


class EditorLaunchError(ProsemarkError):
    """Error raised when external editor cannot be launched.

    This exception indicates failures in launching external editors such as:
    - Editor executable not found
    - Editor launch command failed
    - Editor configuration issues
    - System-specific launch failures

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as editor name, command, error details

    """


class PlaceholderNotFoundError(ProsemarkError):
    """Error raised when a placeholder cannot be found by display title.

    This exception indicates that a binder placeholder with the specified
    display title does not exist in the binder structure. Used primarily
    by MaterializeNode when attempting to materialize a non-existent placeholder.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as the display title searched for

    """


class AlreadyMaterializedError(ProsemarkError):
    """Error raised when attempting to materialize an already materialized item.

    This exception indicates that a binder item already has a NodeId assigned
    and cannot be materialized again. Used by MaterializeNode to prevent
    double-materialization of existing nodes.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as the existing NodeId

    """
