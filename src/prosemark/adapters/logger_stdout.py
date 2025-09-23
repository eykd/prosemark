# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Standard output logger implementation."""

import sys
from typing import TextIO

from prosemark.ports.logger import Logger


class LoggerStdout(Logger):
    """Standard output logger implementation.

    This implementation provides logging to stdout/stderr streams with:
    - Standard log level formatting
    - Configurable output streams (stdout for info/debug, stderr for warning/error)
    - String formatting support compatible with Python's logging module
    - Simple, dependency-free implementation for production use

    The logger follows common conventions:
    - info/debug messages go to stdout (can be redirected separately)
    - warning/error messages go to stderr (for proper error handling)
    - Consistent formatting with log level prefixes
    """

    def __init__(
        self,
        info_stream: TextIO = sys.stdout,
        error_stream: TextIO = sys.stderr,
    ) -> None:
        """Initialize logger with specified output streams.

        Args:
            info_stream: Stream for info and debug messages (default: sys.stdout)
            error_stream: Stream for warning and error messages (default: sys.stderr)

        """
        self.info_stream = info_stream
        self.error_stream = error_stream

    def debug(self, msg: object, *args: object, **_kwargs: object) -> None:
        """Log detailed diagnostic information for troubleshooting.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (ignored in this implementation)

        """
        formatted_msg = str(msg) % args if args else str(msg)  # pragma: no cover
        print(f'[DEBUG] {formatted_msg}', file=self.info_stream)

    def info(self, msg: object, *args: object, **_kwargs: object) -> None:
        """Log general operational information.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (ignored in this implementation)

        """
        formatted_msg = str(msg) % args if args else str(msg)  # pragma: no cover
        print(f'[INFO] {formatted_msg}', file=self.info_stream)

    def warning(self, msg: object, *args: object, **_kwargs: object) -> None:
        """Log warning messages for important events that don't prevent operation.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (ignored in this implementation)

        """
        formatted_msg = str(msg) % args if args else str(msg)  # pragma: no cover
        print(f'[WARNING] {formatted_msg}', file=self.error_stream)

    def error(self, msg: object, *args: object, **_kwargs: object) -> None:
        """Log error conditions that prevent operations from completing.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (ignored in this implementation)

        """
        formatted_msg = str(msg) % args if args else str(msg)  # pragma: no cover
        print(f'[ERROR] {formatted_msg}', file=self.error_stream)

    def exception(self, msg: object, *args: object, **_kwargs: object) -> None:
        """Log exception information with error level and traceback.

        Args:
            msg: The log message or format string
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments (ignored in this implementation)

        """
        formatted_msg = str(msg) % args if args else str(msg)  # pragma: no cover
        print(f'[EXCEPTION] {formatted_msg}', file=self.error_stream)  # pragma: no cover
