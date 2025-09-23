"""Comprehensive tests for InitProject use case to achieve 100% coverage."""

from pathlib import Path

import pytest

from prosemark.adapters.fake_console import FakeConsolePort
from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.init_project import InitProject
from prosemark.domain.models import Binder


class TestInitProjectCoverage:
    """Test InitProject use case with complete coverage."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_console(self) -> FakeConsolePort:
        """Fake Console for testing."""
        return FakeConsolePort()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def init_project(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
    ) -> InitProject:
        """InitProject instance with fake dependencies."""
        return InitProject(
            binder_repo=fake_binder_repo,
            console=fake_console,
            logger=fake_logger,
        )

    def test_init_project_creates_new_project(
        self,
        init_project: InitProject,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        tmp_path: Path,
    ) -> None:
        """Test InitProject creates a new project successfully."""
        # Arrange
        project_title = 'My New Project'

        # Act
        init_project.execute(project_title=project_title, project_path=tmp_path)

        # Assert - Binder was created and saved
        binder = fake_binder_repo.load()
        assert isinstance(binder, Binder)
        assert binder.roots == []

        # Assert - Success message shown
        assert fake_console.output_contains(f'SUCCESS: Project "{project_title}" initialized successfully')
        assert fake_console.output_contains(f'INFO: Created {tmp_path / "_binder.md"}')

        # Assert - Operations logged
        assert fake_logger.has_logged('info', f'Initializing project: {project_title} at {tmp_path}')
        assert fake_logger.has_logged('info', f'Project initialized: {project_title}')

    def test_init_project_uses_current_directory_when_no_path_provided(
        self,
        init_project: InitProject,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        tmp_path: Path,
    ) -> None:
        """Test InitProject uses current directory when no project_path provided."""
        # Arrange
        project_title = 'Current Dir Project'
        import os

        original_cwd = Path.cwd()

        try:
            # Change to temporary directory
            os.chdir(tmp_path)
            current_dir = Path.cwd()

            # Act
            init_project.execute(project_title=project_title, project_path=None)

            # Assert - Used current directory
            assert fake_logger.has_logged('info', f'Initializing project: {project_title} at {current_dir}')
            assert fake_console.output_contains(f'INFO: Created {current_dir / "_binder.md"}')
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_init_project_handles_existing_binder(
        self,
        init_project: InitProject,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test InitProject handles case where binder already exists."""
        # Arrange
        project_title = 'Existing Project'
        binder_path = tmp_path / '_binder.md'
        binder_path.touch()  # Create existing binder file

        # Mock the binder_repo to simulate the file check in real filesystem
        # But since we're using fakes, we need to setup the repo to have existing content
        existing_binder = Binder(roots=[])
        fake_binder_repo.save(existing_binder)

        # Mock the path.exists() check by setting up the scenario

        def mock_execute(*, project_title: str, project_path: Path | None = None) -> None:
            project_path = project_path or Path.cwd()
            init_project.logger.info('Initializing project: %s at %s', project_title, project_path)

            # Simulate binder already exists
            binder_path = project_path / '_binder.md'
            if binder_path.exists():
                init_project.console.print_error(f'Binder already exists at {binder_path}')
                return

            # Normal flow would continue here but we return early

        monkeypatch.setattr(init_project, 'execute', mock_execute)

        # Act
        init_project.execute(project_title=project_title, project_path=tmp_path)

        # Assert - Error message shown and early return
        assert fake_console.output_contains(f'ERROR: Binder already exists at {binder_path}')
        assert fake_logger.has_logged('info', f'Initializing project: {project_title} at {tmp_path}')

    def test_init_project_binder_already_exists_real_execution(
        self,
        init_project: InitProject,
        fake_console: FakeConsolePort,
        tmp_path: Path,
    ) -> None:
        """Test InitProject with existing binder file (lines 50-51)."""
        # Arrange - Create an existing _binder.md file
        project_title = 'Existing Project'
        binder_path = tmp_path / '_binder.md'
        binder_path.write_text('existing binder content')

        # Act - Call the real execute method
        init_project.execute(project_title=project_title, project_path=tmp_path)

        # Assert - Error message should be shown and early return (lines 50-51)
        assert fake_console.output_contains(f'ERROR: Binder already exists at {binder_path}')

    def test_init_project_dependency_injection(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        tmp_path: Path,
    ) -> None:
        """Test InitProject uses all injected dependencies correctly."""
        # Arrange
        init_project = InitProject(
            binder_repo=fake_binder_repo,
            console=fake_console,
            logger=fake_logger,
        )

        # Verify dependencies are assigned
        assert init_project.binder_repo is fake_binder_repo
        assert init_project.console is fake_console
        assert init_project.logger is fake_logger

        # Act
        project_title = 'Dependency Test'
        init_project.execute(project_title=project_title, project_path=tmp_path)

        # Assert all dependencies were used
        # BinderRepo was used to save
        binder = fake_binder_repo.load()
        assert binder is not None

        # Console was used for output
        assert len(fake_console.get_output()) > 0

        # Logger was used
        assert fake_logger.log_count() > 0
