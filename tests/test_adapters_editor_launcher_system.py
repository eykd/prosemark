"""Tests for EditorLauncherSystem adapter."""

import os
import subprocess  # noqa: S404
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.exceptions import EditorLaunchError, EditorNotFoundError


class TestEditorLauncherSystem:
    """Test EditorLauncherSystem adapter."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.launcher = EditorLauncherSystem()
        import tempfile

        temp_dir = tempfile.gettempdir()
        self.test_file = str(Path(temp_dir) / 'test.md')

    @patch('subprocess.run')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._find_editor')
    @patch('pathlib.Path.mkdir')
    def test_open_success(self, mock_mkdir: Mock, mock_find_editor: Mock, mock_run: Mock) -> None:
        """Test successful file opening."""
        mock_find_editor.return_value = ['nano']

        self.launcher.open(self.test_file)

        mock_mkdir.assert_called_once()
        mock_run.assert_called_once_with(['nano', str(Path(self.test_file).resolve())], check=True, shell=False)

    @patch('subprocess.run')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._find_editor')
    @patch('pathlib.Path.mkdir')
    def test_open_with_cursor_hint(self, mock_mkdir: Mock, mock_find_editor: Mock, mock_run: Mock) -> None:
        """Test file opening with cursor hint."""
        mock_find_editor.return_value = ['vim']

        self.launcher.open(self.test_file, cursor_hint='10')

        expected_cmd = ['vim', '+10', str(Path(self.test_file).resolve())]
        mock_run.assert_called_once_with(expected_cmd, check=True, shell=False)

    @patch('subprocess.run')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._find_editor')
    @patch('pathlib.Path.mkdir')
    def test_open_subprocess_called_process_error(
        self, mock_mkdir: Mock, mock_find_editor: Mock, mock_run: Mock
    ) -> None:
        """Test subprocess CalledProcessError handling."""
        mock_find_editor.return_value = ['nano']
        mock_run.side_effect = subprocess.CalledProcessError(1, 'nano')

        with pytest.raises(EditorLaunchError, match='Editor process failed with exit code 1'):
            self.launcher.open(self.test_file)

    @patch('subprocess.run')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._find_editor')
    @patch('pathlib.Path.mkdir')
    def test_open_file_not_found_error(self, mock_mkdir: Mock, mock_find_editor: Mock, mock_run: Mock) -> None:
        """Test FileNotFoundError handling."""
        mock_find_editor.return_value = ['nonexistent']
        mock_run.side_effect = FileNotFoundError('Editor not found')

        with pytest.raises(EditorNotFoundError, match='Editor executable not found: nonexistent'):
            self.launcher.open(self.test_file)

    @patch('subprocess.run')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._find_editor')
    @patch('pathlib.Path.mkdir')
    def test_open_generic_exception(self, mock_mkdir: Mock, mock_find_editor: Mock, mock_run: Mock) -> None:
        """Test generic exception handling."""
        mock_find_editor.return_value = ['nano']
        mock_run.side_effect = Exception('Unexpected error')

        with pytest.raises(EditorLaunchError, match='Failed to launch editor: Unexpected error'):
            self.launcher.open(self.test_file)

    @patch.dict(os.environ, {'EDITOR': 'vim'}, clear=True)
    def test_find_editor_with_editor_env(self) -> None:
        """Test finding editor from EDITOR environment variable."""
        result = self.launcher._find_editor()
        assert result == ['vim']

    @patch.dict(os.environ, {'VISUAL': 'emacs'}, clear=True)
    def test_find_editor_with_visual_env(self) -> None:
        """Test finding editor from VISUAL environment variable."""
        result = self.launcher._find_editor()
        assert result == ['emacs']

    @patch.dict(os.environ, {'EDITOR': 'code --wait'}, clear=True)
    def test_find_editor_with_arguments(self) -> None:
        """Test finding editor with command line arguments."""
        result = self.launcher._find_editor()
        assert result == ['code', '--wait']

    @patch.dict(os.environ, {}, clear=True)
    @patch('sys.platform', 'win32')
    def test_find_editor_windows_default(self) -> None:
        """Test finding default editor on Windows."""
        result = self.launcher._find_editor()
        assert result == ['notepad.exe']

    @patch.dict(os.environ, {}, clear=True)
    @patch('sys.platform', 'linux')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._command_exists')
    def test_find_editor_unix_nano_available(self, mock_command_exists: Mock) -> None:
        """Test finding nano on Unix systems."""
        mock_command_exists.side_effect = lambda cmd: cmd == 'nano'

        result = self.launcher._find_editor()
        assert result == ['nano']

    @patch.dict(os.environ, {}, clear=True)
    @patch('sys.platform', 'linux')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._command_exists')
    def test_find_editor_unix_vim_available(self, mock_command_exists: Mock) -> None:
        """Test finding vim on Unix systems when nano not available."""
        mock_command_exists.side_effect = lambda cmd: cmd == 'vim'

        result = self.launcher._find_editor()
        assert result == ['vim']

    @patch.dict(os.environ, {}, clear=True)
    @patch('sys.platform', 'linux')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._command_exists')
    def test_find_editor_unix_vi_available(self, mock_command_exists: Mock) -> None:
        """Test finding vi on Unix systems when nano and vim not available."""
        mock_command_exists.side_effect = lambda cmd: cmd == 'vi'

        result = self.launcher._find_editor()
        assert result == ['vi']

    @patch.dict(os.environ, {}, clear=True)
    @patch('sys.platform', 'linux')
    @patch('prosemark.adapters.editor_launcher_system.EditorLauncherSystem._command_exists')
    def test_find_editor_no_editor_found(self, mock_command_exists: Mock) -> None:
        """Test when no editor is found."""
        mock_command_exists.return_value = False

        with pytest.raises(EditorNotFoundError, match='No suitable editor found'):
            self.launcher._find_editor()

    @patch('subprocess.run')
    def test_command_exists_true(self, mock_run: Mock) -> None:
        """Test command exists check when command is found."""
        mock_run.return_value = Mock()

        result = self.launcher._command_exists('nano')
        assert result is True
        mock_run.assert_called_once_with(['which', 'nano'], check=True, capture_output=True)

    @patch('subprocess.run')
    def test_command_exists_false_called_process_error(self, mock_run: Mock) -> None:
        """Test command exists check when CalledProcessError occurs."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'which')

        result = self.launcher._command_exists('nonexistent')
        assert result is False

    @patch('subprocess.run')
    def test_command_exists_false_file_not_found_error(self, mock_run: Mock) -> None:
        """Test command exists check when FileNotFoundError occurs."""
        mock_run.side_effect = FileNotFoundError('which not found')

        result = self.launcher._command_exists('nano')
        assert result is False

    def test_build_command_without_cursor_hint(self) -> None:
        """Test building command without cursor hint."""
        result = self.launcher._build_command(['nano'], '/test.md', None)
        assert result == ['nano', '/test.md']

    def test_build_command_with_cursor_hint_supported(self) -> None:
        """Test building command with cursor hint for supported editor."""
        result = self.launcher._build_command(['vim'], '/test.md', '10')
        assert result == ['vim', '+10', '/test.md']

    def test_build_command_with_cursor_hint_unsupported(self) -> None:
        """Test building command with cursor hint for unsupported editor."""
        result = self.launcher._build_command(['notepad'], '/test.md', '10')
        assert result == ['notepad', '/test.md']

    def test_build_command_with_cursor_hint_nano_non_digit(self) -> None:
        """Test building command with non-digit cursor hint for nano."""
        result = self.launcher._build_command(['nano'], '/test.md', 'abc')
        assert result == ['nano', '/test.md']

    def test_supports_cursor_hint_vim(self) -> None:
        """Test cursor hint support detection for vim."""
        assert self.launcher._supports_cursor_hint('vim') is True
        assert self.launcher._supports_cursor_hint('/usr/bin/vim') is True

    def test_supports_cursor_hint_vi(self) -> None:
        """Test cursor hint support detection for vi."""
        assert self.launcher._supports_cursor_hint('vi') is True

    def test_supports_cursor_hint_nano(self) -> None:
        """Test cursor hint support detection for nano."""
        assert self.launcher._supports_cursor_hint('nano') is True

    def test_supports_cursor_hint_emacs(self) -> None:
        """Test cursor hint support detection for emacs."""
        assert self.launcher._supports_cursor_hint('emacs') is True

    def test_supports_cursor_hint_code(self) -> None:
        """Test cursor hint support detection for VS Code."""
        assert self.launcher._supports_cursor_hint('code') is True

    def test_supports_cursor_hint_notepad(self) -> None:
        """Test cursor hint support detection for notepad."""
        assert self.launcher._supports_cursor_hint('notepad') is False

    def test_add_cursor_hint_vim(self) -> None:
        """Test adding cursor hint for vim."""
        cmd = ['vim', '/test.md']
        result = self.launcher._add_cursor_hint(cmd, '10')
        assert result == ['vim', '+10', '/test.md']

    def test_add_cursor_hint_vi(self) -> None:
        """Test adding cursor hint for vi."""
        cmd = ['vi', '/test.md']
        result = self.launcher._add_cursor_hint(cmd, '5')
        assert result == ['vi', '+5', '/test.md']

    def test_add_cursor_hint_nano(self) -> None:
        """Test adding cursor hint for nano."""
        cmd = ['nano', '/test.md']
        result = self.launcher._add_cursor_hint(cmd, '15')
        assert result == ['nano', '+15', '/test.md']

    def test_add_cursor_hint_code(self) -> None:
        """Test adding cursor hint for VS Code."""
        cmd = ['code', '/test.md']
        result = self.launcher._add_cursor_hint(cmd, '20')
        assert result == ['code', '--goto', '20:1', '/test.md']

    def test_add_cursor_hint_non_digit(self) -> None:
        """Test adding cursor hint with non-digit value."""
        cmd = ['vim', '/test.md']
        result = self.launcher._add_cursor_hint(cmd, 'invalid')
        assert result == ['vim', '/test.md']

    def test_add_cursor_hint_unknown_editor(self) -> None:
        """Test adding cursor hint for unknown editor."""
        cmd = ['unknown', '/test.md']
        result = self.launcher._add_cursor_hint(cmd, '10')
        assert result == ['unknown', '/test.md']
