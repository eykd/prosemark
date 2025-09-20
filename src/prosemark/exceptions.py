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


class BinderFormatError(ProsemarkError):
    """Error raised when binder file format is invalid.

    This exception indicates that the _binder.md file has malformed
    managed blocks or invalid structure.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as file content or line numbers

    """


class FileSystemError(ProsemarkError):
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


class ProsemarkFileExistsError(ProsemarkError):
    """Error raised when attempting to create a file that already exists.

    This exception indicates that a file creation operation was attempted
    on a path where a file already exists, and the operation does not
    permit overwriting existing files.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as the existing file path

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


class EditorNotFoundError(ProsemarkError):
    """Error raised when external editor executable cannot be found.

    This exception indicates that the configured editor is not available
    in the system PATH or at the specified location.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as editor name or path

    """


class FreeformContentValidationError(ProsemarkError):
    """Error raised when freeform content validation fails.

    This exception indicates issues with freeform content such as:
    - Invalid filename format
    - Mismatched timestamps or UUIDs
    - Invalid UUIDv7 format

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as filename or validation details

    """


class NodeValidationError(ProsemarkError):
    """Error raised when node validation fails.

    This exception indicates issues with node data such as:
    - Invalid timestamps
    - Missing required fields
    - Data consistency problems

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as node data or validation details

    """


class NodeAlreadyExistsError(ProsemarkError):
    """Error raised when attempting to create a node that already exists.

    This exception indicates that node files already exist for the
    specified NodeId and cannot be recreated.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as NodeId and file paths

    """


class FrontmatterFormatError(ProsemarkError):
    """Error raised when YAML frontmatter is malformed.

    This exception indicates that the YAML frontmatter in a node file
    cannot be parsed or contains invalid data.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as file path or YAML content

    """


class InvalidPartError(ProsemarkError):
    """Error raised when an invalid content part is specified.

    This exception indicates that an unsupported part was requested
    for node editing (valid parts: draft, notes, synopsis).

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as the invalid part name

    """


class EditorError(ProsemarkError):
    """Error raised when editor operation fails.

    This exception indicates general editor-related failures that
    don't fit into more specific error categories.

    Args:
        message: A descriptive error message without variable interpolation
        *context: Additional context such as editor details or error info

    """
