"""MaterializeFailure value object for failed placeholder materialization."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class MaterializeFailure:
    """Represents a failed placeholder materialization attempt.

    This value object captures information about why a placeholder
    materialization failed, providing context for error reporting and recovery.

    Args:
        display_title: Title of the placeholder that failed to materialize
        error_type: Type of error (filesystem, validation, etc.)
        error_message: Human-readable error description
        position: Position in binder hierarchy where failure occurred

    Raises:
        ValueError: If validation rules are violated during construction

    """

    display_title: str
    error_type: str
    error_message: str
    position: str | None

    # Valid error types
    VALID_ERROR_TYPES: ClassVar[set[str]] = {
        'filesystem',  # File creation, permission, disk space issues
        'validation',  # Invalid placeholder state, corrupted binder
        'already_materialized',  # Placeholder already has node_id
        'binder_integrity',  # Binder structure violations
        'id_generation',  # UUID generation failures
    }

    def __post_init__(self) -> None:
        """Validate the materialization failure after construction."""
        # Validate display_title is non-empty
        if not self.display_title or not self.display_title.strip():
            msg = 'Display title must be non-empty string'
            raise ValueError(msg)

        # Validate error_type is from predefined set
        if self.error_type not in self.VALID_ERROR_TYPES:
            msg = f"Error type must be one of {sorted(self.VALID_ERROR_TYPES)}, got '{self.error_type}'"
            raise ValueError(msg)

        # Validate error_message is non-empty and human-readable
        if not self.error_message or not self.error_message.strip():
            msg = 'Error message must be non-empty and human-readable'
            raise ValueError(msg)

        # Position validation is optional since it might not be available in all error contexts
        # but if provided, should not be empty
        if self.position is not None and not self.position.strip():
            msg = 'Position must be None or non-empty string'
            raise ValueError(msg)

    @property
    def is_retryable(self) -> bool:
        """Check if this type of error might be retryable by the user."""
        retryable_types = {'filesystem'}  # User might fix permissions, free disk space, etc.
        return self.error_type in retryable_types

    @property
    def is_critical(self) -> bool:
        """Check if this error indicates a critical system problem."""
        critical_types = {'binder_integrity', 'id_generation'}
        return self.error_type in critical_types

    @property
    def should_stop_batch(self) -> bool:
        """Check if this error should stop the entire batch operation."""
        # Critical errors should stop the batch to prevent data corruption
        return self.is_critical

    def formatted_error(self) -> str:
        """Generate formatted error message for display."""
        if self.position:
            return f"✗ Failed to materialize '{self.display_title}' at {self.position}: {self.error_message}"
        return f"✗ Failed to materialize '{self.display_title}': {self.error_message}"

    def __str__(self) -> str:
        """Generate human-readable string representation."""
        return self.formatted_error()
