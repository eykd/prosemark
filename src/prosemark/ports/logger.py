"""Logger port for structured logging operations."""

from abc import ABC, abstractmethod


class Logger(ABC):
    """Abstract base class for logging operations.

    Defines the contract for logging operations throughout the system following
    Python's stdlib logging patterns. This abstract base class enables:

    * Consistent logging across all application layers with multiple log levels
    * Testable logging behavior through dependency injection and mocking
    * Support for different logging targets (console, file, structured logging services)
    * Hexagonal architecture compliance by isolating logging concerns
    * Observability for debugging, monitoring, and audit trails

    The Logger supports four standard log levels with flexible message formatting:
    - debug: Detailed diagnostic information for troubleshooting
    - info: General operational information and successful operations
    - warning: Important events that don't prevent operation but need attention
    - error: Error conditions that prevent operations from completing

    All methods follow Python's stdlib logging signature patterns, supporting
    both simple string messages and formatted messages with positional/keyword arguments.

    Examples:
        >>> class TestLogger(Logger):
        ...     def debug(self, msg: object, *args: object, **kwargs: object) -> None:
        ...         print(f'[DEBUG] {msg}', *args)
        ...
        ...     def info(self, msg: object, *args: object, **kwargs: object) -> None:
        ...         print(f'[INFO] {msg}', *args)
        ...
        ...     def warning(self, msg: object, *args: object, **kwargs: object) -> None:
        ...         print(f'[WARNING] {msg}', *args)
        ...
        ...     def error(self, msg: object, *args: object, **kwargs: object) -> None:
        ...         print(f'[ERROR] {msg}', *args)
        >>> logger = TestLogger()
        >>> logger.info('Simple message')
        [INFO] Simple message
        >>> logger.info('Formatted %s with %d args', 'message', 2)
        [INFO] Formatted message with 2 args

    """

    @abstractmethod
    def debug(self, msg: object, *args: object, **kwargs: object) -> None:
        """Log detailed diagnostic information for troubleshooting.

        Use for verbose diagnostic information that is only of interest when
        diagnosing problems. Typically disabled in production environments
        to avoid performance impact and log volume.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (implementation-specific, e.g., 'extra' for context)

        Examples:
            >>> logger.debug('Processing node %s', node_id)
            >>> logger.debug('Validation result: %s', result, extra={'node_id': node_id})

        """
        msg = 'Subclasses must implement the debug() method'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

    @abstractmethod
    def info(self, msg: object, *args: object, **kwargs: object) -> None:
        """Log general operational information.

        Use for tracking normal application flow, successful operations,
        and important state changes. This is the standard level for
        operational logging and user-facing status updates.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (implementation-specific, e.g., 'extra' for context)

        Examples:
            >>> logger.info('Created node %s', node_id)
            >>> logger.info('Project initialized at %s', project_path)
            >>> logger.info('Node added to binder', extra={'node_id': node_id, 'parent_id': parent_id})

        """
        msg = 'Subclasses must implement the info() method'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

    @abstractmethod
    def warning(self, msg: object, *args: object, **kwargs: object) -> None:
        """Log warning messages for important events that don't prevent operation.

        Use for conditions that are unexpected but don't prevent the operation
        from completing successfully. These events often indicate potential
        problems or degraded functionality that should be investigated.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (implementation-specific, e.g., 'extra' for context)

        Examples:
            >>> logger.warning('Node %s not found in binder, adding anyway', node_id)
            >>> logger.warning('Large binder detected: %d items', item_count)
            >>> logger.warning('Deprecated feature used', extra={'feature': 'old_api'})

        """
        msg = 'Subclasses must implement the warning() method'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

    @abstractmethod
    def error(self, msg: object, *args: object, **kwargs: object) -> None:
        """Log error conditions that prevent operations from completing.

        Use for error conditions, exceptions, and failures that prevent
        the requested operation from completing successfully. These indicate
        problems that require immediate attention or user intervention.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (implementation-specific, e.g., 'extra' for context)

        Examples:
            >>> logger.error('Failed to create node files: %s', error_msg)
            >>> logger.error('Binder integrity violation: duplicate node %s', node_id)
            >>> logger.error('Node creation failed', extra={'node_id': node_id, 'error': str(exc)})

        """
        msg = 'Subclasses must implement the error() method'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

    @abstractmethod
    def exception(self, msg: object, *args: object, **kwargs: object) -> None:
        """Log exception information with error level and traceback.

        Use for logging exceptions with their full traceback information.
        This is typically used in exception handlers to capture both the
        error message and the complete stack trace for debugging.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (implementation-specific, e.g., 'extra' for context)

        Examples:
            >>> try:
            ...     risky_operation()
            ... except Exception:
            ...     logger.exception('Operation failed')

        """
        msg = 'Subclasses must implement the exception() method'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover
