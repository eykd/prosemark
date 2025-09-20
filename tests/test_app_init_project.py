"""Tests for InitProject use case interactor."""

from pathlib import Path

import pytest

from prosemark.adapters.fake_clock import FakeClock
from prosemark.adapters.fake_config import FakeConfigPort
from prosemark.adapters.fake_console import FakeConsolePort
from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.use_cases import InitProject
from prosemark.domain.models import Binder
from prosemark.exceptions import BinderIntegrityError, FileSystemError


class TestInitProject:
    """Test InitProject use case interactor."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_config_port(self) -> FakeConfigPort:
        """Fake ConfigPort for testing."""
        return FakeConfigPort()

    @pytest.fixture
    def fake_console_port(self) -> FakeConsolePort:
        """Fake ConsolePort for testing."""
        return FakeConsolePort()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        """Fake Clock for testing."""
        return FakeClock('2025-09-13T12:00:00Z')

    @pytest.fixture
    def init_project(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_config_port: FakeConfigPort,
        fake_console_port: FakeConsolePort,
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
    ) -> InitProject:
        """InitProject instance with fake dependencies."""
        return InitProject(
            binder_repo=fake_binder_repo,
            config_port=fake_config_port,
            console_port=fake_console_port,
            logger=fake_logger,
            clock=fake_clock,
        )

    def test_init_project_creates_binder_and_config(
        self,
        init_project: InitProject,
        fake_binder_repo: FakeBinderRepo,
        fake_config_port: FakeConfigPort,
        fake_console_port: FakeConsolePort,
        fake_logger: FakeLogger,
        tmp_path: Path,
    ) -> None:
        """Test successful project initialization creates required files."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()
        config_path = project_path / '.prosemark.yml'

        # Act
        init_project.execute(project_path)

        # Assert - Binder was saved
        saved_binder = fake_binder_repo.load()
        assert isinstance(saved_binder, Binder)
        assert saved_binder.roots == []

        # Assert - Config was created
        assert fake_config_port.config_exists(config_path)

        # Assert - Success message was printed to console
        assert fake_console_port.output_contains(f'Initialized prosemark project at {project_path}')

        # Assert - Operational logging occurred
        assert fake_logger.has_logged('info', 'Starting project initialization')
        assert fake_logger.has_logged('info', 'Project initialization completed successfully')
        assert fake_logger.has_logged('info', 'Initial binder structure created and saved')
        assert fake_logger.has_logged('info', 'Default configuration created')

    def test_init_project_detects_existing_binder(
        self, init_project: InitProject, fake_logger: FakeLogger, tmp_path: Path
    ) -> None:
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

        # Assert error was logged
        assert fake_logger.has_logged('error', 'Project initialization failed: project already exists')

    def test_init_project_generates_default_config(
        self, init_project: InitProject, fake_config_port: FakeConfigPort, tmp_path: Path
    ) -> None:
        """Test .prosemark.yml created with expected defaults."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()
        config_path = project_path / '.prosemark.yml'

        # Act
        init_project.execute(project_path)

        # Assert
        assert fake_config_port.config_exists(config_path)
        defaults = fake_config_port.get_default_config_values()
        assert 'editor' in defaults
        assert 'daily_dir' in defaults
        assert 'binder_file' in defaults

    def test_init_project_uses_injected_dependencies(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_config_port: FakeConfigPort,
        fake_console_port: FakeConsolePort,
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
        tmp_path: Path,
    ) -> None:
        """Test all operations use injected ports correctly."""
        # Arrange
        init_project = InitProject(
            binder_repo=fake_binder_repo,
            config_port=fake_config_port,
            console_port=fake_console_port,
            logger=fake_logger,
            clock=fake_clock,
        )
        project_path = tmp_path / 'test_project'
        project_path.mkdir()
        config_path = project_path / '.prosemark.yml'

        # Act
        init_project.execute(project_path)

        # Assert all dependencies were used
        # Clock returns the expected timestamp
        assert fake_clock.now_iso() == '2025-09-13T12:00:00Z'

        # Binder was saved
        saved_binder = fake_binder_repo.load()
        assert saved_binder.roots == []

        # Config was created
        assert fake_config_port.config_exists(config_path)

        # Console output was generated
        assert len(fake_console_port.get_output()) > 0

        # Logger was used for operational logging
        assert fake_logger.log_count() > 0
        assert fake_logger.has_logged('info', 'Starting project initialization')

    def test_init_project_handles_filesystem_errors(
        self, init_project: InitProject, fake_binder_repo: FakeBinderRepo, tmp_path: Path
    ) -> None:
        """Test FileSystemError raised with descriptive context."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()

        # Override save method to raise error
        original_save = fake_binder_repo.save

        def failing_save(binder: Binder) -> None:
            raise FileSystemError('Cannot write file', '/path/to/binder.md')

        fake_binder_repo.save = failing_save  # type: ignore[method-assign]

        # Act & Assert
        with pytest.raises(FileSystemError) as exc_info:
            init_project.execute(project_path)

        assert 'Cannot write file' in str(exc_info.value)

        # Restore original method for other tests
        fake_binder_repo.save = original_save  # type: ignore[method-assign]

    def test_init_project_creates_empty_binder_structure(
        self, init_project: InitProject, fake_binder_repo: FakeBinderRepo, tmp_path: Path
    ) -> None:
        """Test binder is created with empty root structure."""
        # Arrange
        project_path = tmp_path / 'test_project'
        project_path.mkdir()

        # Act
        init_project.execute(project_path)

        # Assert
        saved_binder = fake_binder_repo.load()
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
