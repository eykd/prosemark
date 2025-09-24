"""Domain exceptions for the freewriting feature.

This module contains all the domain-specific exceptions that can be raised
by the freewriting business logic. These exceptions represent business rule
violations and error conditions in the domain layer.
"""

from __future__ import annotations

# Constants for error message formatting
_PREVIEW_MAX_LENGTH = 50


class FreewriteError(Exception):
    """Base exception for all freewrite domain errors.

    This is the root exception type for all freewriting-related errors.
    It provides a common base for catching any freewriting error.
    """

    def __init__(self, message: str, context: dict[str, str] | None = None) -> None:
        """Initialize the error with message and optional context.

        Args:
            message: Human-readable error description.
            context: Optional dictionary with error context details.

        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.context:
            context_str = ', '.join(f'{k}={v}' for k, v in self.context.items())
            return f'{self.message} ({context_str})'
        return self.message


class ValidationError(FreewriteError):
    """Raised when validation fails.

    This exception is raised when user input or configuration
    fails domain validation rules.
    """

    def __init__(
        self,
        field_name: str,
        field_value: str,
        validation_rule: str,
        context: dict[str, str] | None = None,
    ) -> None:
        """Initialize validation error with field details.

        Args:
            field_name: Name of the field that failed validation.
            field_value: The invalid value that was provided.
            validation_rule: Description of the validation rule that failed.
            context: Optional additional context.

        """
        message = f'Validation failed for {field_name}: {validation_rule}'
        super().__init__(message, context)
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule


class FileSystemError(FreewriteError):
    """Raised when file system operations fail.

    This exception is raised when file operations (reading, writing,
    creating directories) encounter errors.
    """

    def __init__(
        self,
        operation: str,
        file_path: str,
        system_error: str | None = None,
        context: dict[str, str] | None = None,
    ) -> None:
        """Initialize file system error with operation details.

        Args:
            operation: The file operation that failed (e.g., 'write', 'read').
            file_path: Path to the file involved in the operation.
            system_error: Optional system error message from OS.
            context: Optional additional context.

        """
        message = f'File system operation failed: {operation} on {file_path}'
        if system_error:
            message += f' ({system_error})'

        super().__init__(message, context)
        self.operation = operation
        self.file_path = file_path
        self.system_error = system_error


class NodeError(FreewriteError):
    """Raised when node operations fail.

    This exception is raised when operations on prosemark nodes
    encounter errors, such as invalid UUIDs or missing nodes.
    """

    def __init__(
        self,
        node_uuid: str | None,
        operation: str,
        reason: str,
        context: dict[str, str] | None = None,
    ) -> None:
        """Initialize node error with operation details.

        Args:
            node_uuid: UUID of the node involved (may be None for UUID validation errors).
            operation: The node operation that failed.
            reason: Reason why the operation failed.
            context: Optional additional context.

        """
        node_desc = node_uuid or 'invalid-uuid'
        message = f'Node operation failed: {operation} on {node_desc} - {reason}'

        super().__init__(message, context)
        self.node_uuid = node_uuid
        self.operation = operation
        self.reason = reason


class SessionError(FreewriteError):
    """Raised when session operations fail.

    This exception is raised when session management operations
    encounter errors, such as invalid state transitions or
    configuration problems.
    """

    def __init__(
        self,
        session_id: str | None,
        operation: str,
        reason: str,
        context: dict[str, str] | None = None,
    ) -> None:
        """Initialize session error with operation details.

        Args:
            session_id: ID of the session involved (may be None).
            operation: The session operation that failed.
            reason: Reason why the operation failed.
            context: Optional additional context.

        """
        session_desc = session_id or 'unknown-session'
        message = f'Session operation failed: {operation} on {session_desc} - {reason}'

        super().__init__(message, context)
        self.session_id = session_id
        self.operation = operation
        self.reason = reason


class TUIError(FreewriteError):
    """Raised when TUI operations fail.

    This exception is raised when terminal user interface
    operations encounter errors that cannot be recovered from
    within the TUI.
    """

    def __init__(
        self,
        component: str,
        operation: str,
        reason: str,
        recoverable: bool = True,  # noqa: FBT001, FBT002
        context: dict[str, str] | None = None,
    ) -> None:
        """Initialize TUI error with component details.

        Args:
            component: TUI component that encountered the error.
            operation: The operation that failed.
            reason: Reason why the operation failed.
            recoverable: Whether the error can be recovered from.
            context: Optional additional context.

        """
        message = f'TUI operation failed: {operation} in {component} - {reason}'

        super().__init__(message, context)
        self.component = component
        self.operation = operation
        self.reason = reason
        self.recoverable = recoverable


class CLIError(FreewriteError):
    """Raised when CLI operations fail.

    This exception is raised when command-line interface
    operations encounter errors, such as invalid arguments
    or configuration problems.
    """

    def __init__(
        self,
        command: str,
        argument: str | None,
        reason: str,
        exit_code: int = 1,
        context: dict[str, str] | None = None,
    ) -> None:
        """Initialize CLI error with command details.

        Args:
            command: CLI command that failed.
            argument: Specific argument that caused the error (may be None).
            reason: Reason why the command failed.
            exit_code: Suggested exit code for the CLI.
            context: Optional additional context.

        """
        if argument:
            message = f'CLI command failed: {command} with argument {argument} - {reason}'
        else:
            message = f'CLI command failed: {command} - {reason}'

        super().__init__(message, context)
        self.command = command
        self.argument = argument
        self.reason = reason
        self.exit_code = exit_code

    def __str__(self) -> str:
        """Return string representation of the error.

        For CLI errors, we return just the reason to maintain backward compatibility
        with the contract tests that expect simple reason strings.
        """
        return self.reason


class ConfigurationError(FreewriteError):
    """Raised when configuration is invalid.

    This exception is raised when session configuration
    or system configuration contains invalid values or
    conflicting settings.
    """

    def __init__(
        self,
        config_key: str,
        config_value: str,
        reason: str,
        context: dict[str, str] | None = None,
    ) -> None:
        """Initialize configuration error with config details.

        Args:
            config_key: Configuration key that is invalid.
            config_value: The invalid configuration value.
            reason: Reason why the configuration is invalid.
            context: Optional additional context.

        """
        message = f'Invalid configuration: {config_key}={config_value} - {reason}'

        super().__init__(message, context)
        self.config_key = config_key
        self.config_value = config_value
        self.reason = reason


class ContentError(FreewriteError):
    """Raised when content processing fails.

    This exception is raised when operations on user content
    encounter errors, such as encoding issues or content
    validation failures.
    """

    def __init__(
        self,
        operation: str,
        content_preview: str,
        reason: str,
        context: dict[str, str] | None = None,
    ) -> None:
        """Initialize content error with operation details.

        Args:
            operation: Content operation that failed.
            content_preview: First few characters of the problematic content.
            reason: Reason why the operation failed.
            context: Optional additional context.

        """
        # Limit preview to prevent huge error messages
        preview = (
            content_preview[:_PREVIEW_MAX_LENGTH] + '...'
            if len(content_preview) > _PREVIEW_MAX_LENGTH
            else content_preview
        )
        message = f'Content operation failed: {operation} on "{preview}" - {reason}'

        super().__init__(message, context)
        self.operation = operation
        self.content_preview = content_preview
        self.reason = reason


# Legacy exception aliases for backward compatibility
# These can be removed once all code uses the new exception hierarchy


class ArgumentValidationError(CLIError):
    """Legacy alias for CLI argument validation errors."""

    def __init__(self, argument: str, _value: str, reason: str) -> None:
        """Initialize with CLI error pattern."""
        super().__init__('validate', argument, reason)


class ThemeNotFoundError(CLIError):
    """Legacy alias for CLI theme not found errors."""

    def __init__(self, config_key: str, _value: str, reason: str) -> None:
        """Initialize with CLI error pattern."""
        super().__init__('configure', config_key, reason)


class DirectoryNotWritableError(CLIError):
    """Legacy alias for CLI directory not writable errors."""

    def __init__(self, operation: str, path: str, reason: str) -> None:
        """Initialize with CLI error pattern."""
        super().__init__(operation, path, reason)
