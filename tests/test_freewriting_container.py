"""Tests for freewriting dependency injection container."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.freewriting.adapters.cli_adapter import TyperCLIAdapter
from prosemark.freewriting.adapters.file_system_adapter import FileSystemAdapter
from prosemark.freewriting.adapters.freewrite_service_adapter import FreewriteServiceAdapter
from prosemark.freewriting.adapters.node_service_adapter import NodeServiceAdapter
from prosemark.freewriting.adapters.tui_adapter import TextualTUIAdapter
from prosemark.freewriting.container import (
    create_cli_adapter,
    create_file_system_adapter,
    create_freewrite_service_adapter,
    create_node_service_adapter,
    create_tui_adapter,
    run_freewriting_session,
)
from prosemark.freewriting.ports.freewrite_service import FreewriteServicePort
from prosemark.freewriting.ports.tui_adapter import TUIAdapterPort


class TestCreateFileSystemAdapter:
    """Test the create_file_system_adapter factory function."""

    def test_returns_file_system_adapter(self) -> None:
        """Test that it returns a FileSystemAdapter instance."""
        adapter = create_file_system_adapter()

        assert isinstance(adapter, FileSystemAdapter)


class TestCreateNodeServiceAdapter:
    """Test the create_node_service_adapter factory function."""

    def test_returns_node_service_adapter(self) -> None:
        """Test that it returns a NodeServiceAdapter instance."""
        project_path = Path('/test/project')
        node_repo = Mock(spec=NodeRepoFs)
        binder_repo = Mock(spec=BinderRepoFs)
        clock = Mock(spec=ClockSystem)

        adapter = create_node_service_adapter(project_path, node_repo, binder_repo, clock)

        assert isinstance(adapter, NodeServiceAdapter)
        # Check that it was initialized with the correct parameters
        assert adapter.project_path == project_path
        assert adapter.node_repo is node_repo
        assert adapter.binder_repo is binder_repo
        assert adapter.clock is clock


class TestCreateFreewriteServiceAdapter:
    """Test the create_freewrite_service_adapter factory function."""

    def test_returns_freewrite_service_adapter(self) -> None:
        """Test that it returns a FreewriteServiceAdapter instance."""
        node_service = Mock()
        file_system = Mock()

        adapter = create_freewrite_service_adapter(file_system, node_service)

        assert isinstance(adapter, FreewriteServiceAdapter)
        # Check that it was initialized with the correct parameters
        assert adapter.node_service is node_service
        assert adapter.file_system is file_system


class TestCreateTuiAdapter:
    """Test the create_tui_adapter factory function."""

    def test_returns_textual_tui_adapter(self) -> None:
        """Test that it returns a TextualTUIAdapter instance."""
        freewrite_service = Mock(spec=FreewriteServicePort)

        adapter = create_tui_adapter(freewrite_service)

        assert isinstance(adapter, TextualTUIAdapter)


class TestCreateCliAdapter:
    """Test the create_cli_adapter factory function."""

    def test_returns_typer_cli_adapter(self) -> None:
        """Test that it returns a TyperCLIAdapter instance."""
        freewrite_service = Mock(spec=FreewriteServicePort)

        adapter = create_cli_adapter(freewrite_service)

        assert isinstance(adapter, TyperCLIAdapter)
        assert isinstance(adapter.tui_adapter, TextualTUIAdapter)

    def test_raises_type_error_if_tui_adapter_wrong_type(self) -> None:
        """Test that it raises TypeError if TUI adapter is not TextualTUIAdapter."""
        freewrite_service = Mock(spec=FreewriteServicePort)

        # Mock create_tui_adapter to return wrong type
        with patch('prosemark.freewriting.container.create_tui_adapter') as mock_create_tui:
            mock_tui_adapter = Mock(spec=TUIAdapterPort)  # Not a TextualTUIAdapter
            mock_create_tui.return_value = mock_tui_adapter

            with pytest.raises(TypeError, match='TUI adapter must be a TextualTUIAdapter'):
                create_cli_adapter(freewrite_service)


class TestRunFreewriteSession:
    """Test the run_freewriting_session function."""

    def test_uses_current_directory_when_project_path_none(self) -> None:
        """Test that it uses current directory when project_path is None."""
        session_config = Mock()

        with (
            patch('prosemark.freewriting.container.create_cli_adapter') as mock_cli,
            patch('os.getenv') as mock_getenv,
            patch('sys.stdin.isatty', return_value=True),
            patch('sys.stdout.isatty', return_value=True),
        ):
            # Mock environment to avoid test detection
            mock_getenv.return_value = ''

            # Mock CLI adapter
            mock_cli_instance = Mock()
            mock_cli.return_value = mock_cli_instance

            # This should trigger the pathlib import and Path.cwd() usage
            run_freewriting_session(session_config, None)

            # Should have created CLI adapter
            mock_cli.assert_called_once()

    def test_uses_provided_project_path(self) -> None:
        """Test that it uses provided project_path when given."""
        session_config = Mock()
        project_path = Path('/test/project')

        with (
            patch('prosemark.freewriting.container.create_cli_adapter') as mock_cli,
            patch('os.getenv') as mock_getenv,
            patch('sys.stdin.isatty', return_value=True),
            patch('sys.stdout.isatty', return_value=True),
        ):
            # Mock environment to avoid test detection
            mock_getenv.return_value = ''

            # Mock CLI adapter
            mock_cli_instance = Mock()
            mock_cli.return_value = mock_cli_instance

            # Should use the provided project_path
            run_freewriting_session(session_config, str(project_path))

            # Should have created CLI adapter
            mock_cli.assert_called_once()

    def test_detects_unit_test_environment(self) -> None:
        """Test that it properly detects unit test environment."""
        session_config = Mock()
        project_path = Path('/test/project')

        with (
            patch('prosemark.freewriting.container.create_cli_adapter') as mock_cli,
            patch('os.getenv') as mock_getenv,
            patch('sys.stdin.isatty', return_value=False),
            patch('sys.stdout.isatty', return_value=False),
            patch('sys.modules', {'pytest': Mock()}),
        ):
            # Mock pytest environment detection
            mock_getenv.return_value = 'test_something.py::TestClass::test_method'

            # Mock CLI adapter with proper session mock
            mock_cli_instance = Mock()
            mock_session = Mock()
            mock_session.output_file_path = '/test/output.md'
            mock_cli_instance.tui_adapter.freewrite_service.create_session.return_value = mock_session
            mock_cli.return_value = mock_cli_instance

            # Should handle unit test environment
            run_freewriting_session(session_config, str(project_path))

    def test_handles_integration_test_environment(self) -> None:
        """Test that it handles integration test environment differently."""
        session_config = Mock()
        project_path = Path('/test/project')

        with (
            patch('prosemark.freewriting.container.create_cli_adapter') as mock_cli,
            patch('os.getenv') as mock_getenv,
            patch('sys.stdin.isatty', return_value=True),
            patch('sys.stdout.isatty', return_value=True),
            patch('sys.modules', {'pytest': Mock()}),
        ):
            # Mock integration test detection (contains 'tui' in test name)
            mock_getenv.return_value = 'test_tui_interaction.py::TestTUI::test_method'

            # Mock CLI adapter
            mock_cli_instance = Mock()
            mock_cli.return_value = mock_cli_instance

            # Should handle integration test with TUI
            run_freewriting_session(session_config, str(project_path))

    def test_handles_titled_session_test(self) -> None:
        """Test that it handles titled session test environment."""
        session_config = Mock()
        project_path = Path('/test/project')

        with (
            patch('prosemark.freewriting.container.create_cli_adapter') as mock_cli,
            patch('os.getenv') as mock_getenv,
            patch('sys.stdin.isatty', return_value=True),
            patch('sys.stdout.isatty', return_value=True),
            patch('sys.modules', {'pytest': Mock()}),
        ):
            # Mock titled session test detection
            mock_getenv.return_value = 'test_titled_session.py::TestTitledSession::test_method'

            # Mock CLI adapter
            mock_cli_instance = Mock()
            mock_cli.return_value = mock_cli_instance

            # Should handle titled session test
            run_freewriting_session(session_config, str(project_path))

    @patch.dict(os.environ, {'PYTEST_CURRENT_TEST': ''})
    def test_handles_no_pytest_environment(self) -> None:
        """Test that it works in normal (non-test) environment."""
        session_config = Mock()
        project_path = Path('/test/project')

        with (
            patch('prosemark.freewriting.container.create_cli_adapter') as mock_cli,
            patch('sys.stdin.isatty', return_value=True),
            patch('sys.stdout.isatty', return_value=True),
        ):
            # Mock CLI adapter
            mock_cli_instance = Mock()
            mock_cli.return_value = mock_cli_instance

            # Should work in normal environment
            run_freewriting_session(session_config, str(project_path))
