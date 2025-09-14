"""Tests for InitProject use case interactor."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from prosemark.app.use_cases import InitProject
from prosemark.domain.models import Binder
from prosemark.exceptions import BinderIntegrityError, FilesystemError


class TestInitProject:
    """Test InitProject use case interactor."""

    @pytest.fixture
    def mock_binder_repo(self) -> Mock:
        """Mock BinderRepo for testing."""
        return Mock()

    @pytest.fixture
    def mock_config_port(self) -> Mock:
        """Mock ConfigPort for testing."""
        return Mock()

    @pytest.fixture
    def mock_console_port(self) -> Mock:
        """Mock ConsolePort for testing."""
        return Mock()

    @pytest.fixture
    def mock_clock(self) -> Mock:
        """Mock Clock for testing."""
        mock_clock = Mock()
        mock_clock.now_iso.return_value = '2025-09-13T12:00:00Z'
        return mock_clock

    @pytest.fixture
    def init_project(
        self, mock_binder_repo: Mock, mock_config_port: Mock, mock_console_port: Mock, mock_clock: Mock
    ) -> InitProject:
        """InitProject instance with mocked dependencies."""
        return InitProject(
            binder_repo=mock_binder_repo,
            config_port=mock_config_port,
            console_port=mock_console_port,
            clock=mock_clock,
        )

    def test_init_project_creates_binder_and_config(
        self,
        init_project: InitProject,
        mock_binder_repo: Mock,
        mock_config_port: Mock,
        mock_console_port: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful project initialization creates required files."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()

        # Mock that no existing files exist
        project_path / '_binder.md'
        config_path = project_path / '.prosemark.yml'

        # Act
        init_project.execute(project_path)

        # Assert
        mock_binder_repo.save.assert_called_once()
        saved_binder = mock_binder_repo.save.call_args[0][0]
        assert isinstance(saved_binder, Binder)

        mock_config_port.create_default_config.assert_called_once_with(config_path)
        mock_console_port.print.assert_called_once_with(f'Initialized prosemark project at {project_path}')

    def test_init_project_detects_existing_binder(self, init_project: InitProject, tmp_path: Path) -> None:
        """Test raises BinderIntegrityError for existing _binder.md."""
        # Arrange
        project_path = tmp_path / 'existing_project'
        project_path.mkdir()
        binder_path = project_path / '_binder.md'
        binder_path.write_text('# Existing Binder')

        # Act & Assert
        with pytest.raises(BinderIntegrityError) as exc_info:
            init_project.execute(project_path)

        assert 'Project already initialized' in str(exc_info.value)
        assert str(binder_path) in str(exc_info.value)

    def test_init_project_generates_default_config(
        self, init_project: InitProject, mock_config_port: Mock, tmp_path: Path
    ) -> None:
        """Test .prosemark.yml created with expected defaults."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()
        config_path = project_path / '.prosemark.yml'

        # Act
        init_project.execute(project_path)

        # Assert
        mock_config_port.create_default_config.assert_called_once_with(config_path)

    def test_init_project_uses_injected_dependencies(
        self, mock_binder_repo: Mock, mock_config_port: Mock, mock_console_port: Mock, mock_clock: Mock, tmp_path: Path
    ) -> None:
        """Test all operations use injected ports correctly."""
        # Arrange
        init_project = InitProject(
            binder_repo=mock_binder_repo,
            config_port=mock_config_port,
            console_port=mock_console_port,
            clock=mock_clock,
        )
        project_path = tmp_path / 'test_project'
        project_path.mkdir()

        # Act
        init_project.execute(project_path)

        # Assert all dependencies were used
        mock_clock.now_iso.assert_called_once()
        mock_binder_repo.save.assert_called_once()
        mock_config_port.create_default_config.assert_called_once()
        mock_console_port.print.assert_called_once()

    def test_init_project_handles_filesystem_errors(
        self, init_project: InitProject, mock_binder_repo: Mock, tmp_path: Path
    ) -> None:
        """Test FilesystemError raised with descriptive context."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()

        # Mock filesystem failure
        mock_binder_repo.save.side_effect = FilesystemError('Cannot write file', '/path/to/binder.md')

        # Act & Assert
        with pytest.raises(FilesystemError) as exc_info:
            init_project.execute(project_path)

        assert 'Cannot write file' in str(exc_info.value)

    def test_init_project_creates_empty_binder_structure(
        self, init_project: InitProject, mock_binder_repo: Mock, tmp_path: Path
    ) -> None:
        """Test binder is created with empty root structure."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()

        # Act
        init_project.execute(project_path)

        # Assert
        mock_binder_repo.save.assert_called_once()
        saved_binder = mock_binder_repo.save.call_args[0][0]
        assert isinstance(saved_binder, Binder)
        assert saved_binder.roots == []  # Empty initial structure

    def test_init_project_validates_directory_structure(self, init_project: InitProject, tmp_path: Path) -> None:
        """Test validates project directory before initialization."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()

        # Create existing binder file
        (project_path / '_binder.md').write_text('existing content')

        # Act & Assert
        with pytest.raises(BinderIntegrityError):
            init_project.execute(project_path)
