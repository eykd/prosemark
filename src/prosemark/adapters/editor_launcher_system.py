# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""System editor launcher implementation using environment variables and OS defaults."""

import os
import subprocess  # noqa: S404
import sys
from pathlib import Path

from prosemark.exceptions import EditorLaunchError, EditorNotFoundError
from prosemark.ports.editor_port import EditorPort


class EditorLauncherSystem(EditorPort):
    """System editor launcher using environment variables and OS detection.

    This implementation provides cross-platform editor launching with:
    - $EDITOR environment variable support (Unix/Linux tradition)
    - $VISUAL environment variable fallback
    - Platform-specific default editors
    - Proper error handling for missing editors or launch failures

    Editor precedence:
    1. $EDITOR environment variable
    2. $VISUAL environment variable
    3. Platform-specific defaults (notepad on Windows, nano on Unix)

    The adapter handles path validation, editor detection, and subprocess
    management while maintaining security and proper error reporting.
    """

    def open(self, path: str, *, cursor_hint: str | None = None) -> None:
        """Open a file in the external editor.

        Args:
            path: File path to open (will be converted to absolute path)
            cursor_hint: Optional cursor positioning hint (implementation-specific)

        Raises:
            EditorNotFoundError: When no suitable editor can be found
            EditorLaunchError: When editor fails to launch or start properly

        """
        # Convert to absolute path and validate
        abs_path = Path(path).resolve()

        # Ensure parent directory exists (editor might create the file)
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        # Find suitable editor
        editor_cmd = EditorLauncherSystem._find_editor()

        # Build command with cursor hint if supported
        cmd = EditorLauncherSystem._build_command(editor_cmd, str(abs_path), cursor_hint)

        try:
            # Launch editor as subprocess
            subprocess.run(cmd, check=True, shell=False)  # noqa: S603

        except subprocess.CalledProcessError as exc:
            msg = f'Editor process failed with exit code {exc.returncode}'
            raise EditorLaunchError(msg) from exc

        except FileNotFoundError as exc:
            msg = f'Editor executable not found: {editor_cmd[0]}'
            raise EditorNotFoundError(msg) from exc

        except Exception as exc:
            msg = f'Failed to launch editor: {exc}'
            raise EditorLaunchError(msg) from exc

    @staticmethod
    def _find_editor() -> list[str]:
        """Find suitable editor command.

        Returns:
            Command list for subprocess execution

        Raises:
            EditorNotFoundError: When no suitable editor is found

        """
        # Try environment variables first
        for env_var in ['EDITOR', 'VISUAL']:
            editor = os.environ.get(env_var)
            if editor:
                # Split command to handle editors with arguments
                return editor.split()

        # Platform-specific defaults
        if sys.platform == 'win32':
            return ['notepad.exe']
        # Unix-like systems - try common editors
        for editor in ['nano', 'vim', 'vi']:
            if EditorLauncherSystem._command_exists(editor):
                return [editor]

        msg = 'No suitable editor found. Set $EDITOR environment variable.'
        raise EditorNotFoundError(msg)

    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if a command exists in PATH.

        Args:
            command: Command name to check

        Returns:
            True if command exists, False otherwise

        """
        try:
            subprocess.run(['which', command], check=True, capture_output=True)  # noqa: S603,S607
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
        else:
            return True

    @staticmethod
    def _build_command(editor_cmd: list[str], file_path: str, cursor_hint: str | None) -> list[str]:
        """Build complete command with optional cursor positioning.

        Args:
            editor_cmd: Base editor command
            file_path: Absolute file path
            cursor_hint: Optional cursor positioning hint

        Returns:
            Complete command list for subprocess

        """
        cmd = editor_cmd.copy()
        cmd.append(file_path)

        # Add cursor hint if provided and editor supports it
        if cursor_hint and EditorLauncherSystem._supports_cursor_hint(editor_cmd[0]):
            cmd = EditorLauncherSystem._add_cursor_hint(cmd, cursor_hint)

        return cmd

    @staticmethod
    def _supports_cursor_hint(editor: str) -> bool:
        """Check if editor supports cursor positioning hints.

        Args:
            editor: Editor command name

        Returns:
            True if editor supports hints, False otherwise

        """
        # Common editors that support line number hints
        editors_with_hints = {'vim', 'vi', 'nano', 'emacs', 'code'}
        return any(known_editor in editor.lower() for known_editor in editors_with_hints)

    @staticmethod
    def _add_cursor_hint(cmd: list[str], cursor_hint: str) -> list[str]:
        """Add cursor positioning hint to command.

        Args:
            cmd: Current command list
            cursor_hint: Cursor positioning hint

        Returns:
            Modified command list with cursor hint

        """
        editor = cmd[0].lower()

        # Handle different editor cursor hint formats
        if 'vim' in editor or 'vi' in editor:
            # Vim format: +line_number
            if cursor_hint.isdigit():
                cmd.insert(-1, f'+{cursor_hint}')

        elif 'nano' in editor:
            # Nano format: +line_number
            if cursor_hint.isdigit():
                cmd.insert(-1, f'+{cursor_hint}')

        elif 'code' in editor and cursor_hint.isdigit():
            # VS Code format: --goto line:column
            cmd.insert(-1, '--goto')
            cmd.insert(-1, f'{cursor_hint}:1')

        # For other editors, cursor_hint is ignored
        return cmd
