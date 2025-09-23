"""Tests for WriteFreeform use case interactor."""

import pytest

from prosemark.adapters.fake_clock import FakeClock
from prosemark.adapters.fake_logger import FakeLogger
from prosemark.app.use_cases import WriteFreeform
from prosemark.exceptions import EditorLaunchError, FileSystemError
from prosemark.ports.daily_repo import DailyRepo
from prosemark.ports.editor_port import EditorPort


class FakeDailyRepo(DailyRepo):
    """Fake DailyRepo for testing."""

    def __init__(self) -> None:
        """Initialize fake with tracking attributes."""
        self.write_freeform_called = False
        self.write_freeform_title: str | None = None
        self.write_freeform_return_value = '20250911T0830_01932c5a-7f3e-7000-8000-000000000001.md'
        self.write_freeform_should_raise: Exception | None = None

    def write_freeform(self, title: str | None = None) -> str:
        """Fake write_freeform implementation."""
        self.write_freeform_called = True
        self.write_freeform_title = title

        if self.write_freeform_should_raise:
            raise self.write_freeform_should_raise

        return self.write_freeform_return_value


class FakeEditorPort(EditorPort):
    """Fake EditorPort for testing."""

    def __init__(self) -> None:
        """Initialize fake with tracking attributes."""
        self.open_called = False
        self.opened_path: str | None = None
        self.cursor_hint: str | None = None
        self.open_should_raise: Exception | None = None

    def open(self, path: str, *, cursor_hint: str | None = None) -> None:
        """Fake open implementation."""
        self.open_called = True
        self.opened_path = path
        self.cursor_hint = cursor_hint

        if self.open_should_raise:
            raise self.open_should_raise


class TestWriteFreeform:
    """Test WriteFreeform use case interactor."""

    @pytest.fixture
    def fake_daily_repo(self) -> FakeDailyRepo:
        """Create fake DailyRepo for testing."""
        return FakeDailyRepo()

    @pytest.fixture
    def fake_editor_port(self) -> FakeEditorPort:
        """Create fake EditorPort for testing."""
        return FakeEditorPort()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Create fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        """Create fake Clock for testing."""
        return FakeClock('2025-09-11T08:30:00Z')

    @pytest.fixture
    def write_freeform(
        self,
        fake_daily_repo: FakeDailyRepo,
        fake_editor_port: FakeEditorPort,
        fake_logger: FakeLogger,
        fake_clock: FakeClock,
    ) -> WriteFreeform:
        """Create WriteFreeform interactor with fake dependencies."""
        return WriteFreeform(
            daily_repo=fake_daily_repo,
            editor_port=fake_editor_port,
            logger=fake_logger,
            clock=fake_clock,
        )

    def test_write_freeform_creates_timestamped_file(
        self,
        write_freeform: WriteFreeform,
        fake_daily_repo: FakeDailyRepo,
        fake_clock: FakeClock,
    ) -> None:
        """Test that WriteFreeform creates a timestamped file."""
        # Arrange: Mock DailyRepo, EditorPort, Clock with fixed time
        expected_filename = '20250911T0830_01932c5a-7f3e-7000-8000-000000000001.md'
        fake_daily_repo.write_freeform_return_value = expected_filename

        # Act: Execute WriteFreeform with optional title
        result = write_freeform.execute(title='Test Title')

        # Assert: DailyRepo.write_freeform() called, file created with proper format
        assert fake_daily_repo.write_freeform_called
        assert fake_daily_repo.write_freeform_title == 'Test Title'
        assert result == expected_filename

    def test_write_freeform_includes_title_in_frontmatter(
        self,
        write_freeform: WriteFreeform,
        fake_daily_repo: FakeDailyRepo,
    ) -> None:
        """Test that WriteFreeform includes title in frontmatter."""
        # Arrange: Mock DailyRepo to verify title parameter
        test_title = 'My Important Thoughts'

        # Act: Execute WriteFreeform with specific title
        write_freeform.execute(title=test_title)

        # Assert: Title passed to DailyRepo for frontmatter inclusion
        assert fake_daily_repo.write_freeform_called
        assert fake_daily_repo.write_freeform_title == test_title

    def test_write_freeform_opens_file_in_editor(
        self,
        write_freeform: WriteFreeform,
        fake_daily_repo: FakeDailyRepo,
        fake_editor_port: FakeEditorPort,
    ) -> None:
        """Test that WriteFreeform opens the created file in editor."""
        # Arrange: Mock DailyRepo returning filename, mock EditorPort
        expected_filename = '20250911T0830_01932c5a-7f3e-7000-8000-000000000001.md'
        fake_daily_repo.write_freeform_return_value = expected_filename

        # Act: Execute WriteFreeform
        write_freeform.execute()

        # Assert: EditorPort.open() called with created filename
        assert fake_editor_port.open_called
        assert fake_editor_port.opened_path == expected_filename

    def test_write_freeform_handles_no_title(
        self,
        write_freeform: WriteFreeform,
        fake_daily_repo: FakeDailyRepo,
    ) -> None:
        """Test that WriteFreeform handles no title correctly."""
        # Arrange: Mock dependencies
        # Act: Execute WriteFreeform with title=None
        result = write_freeform.execute(title=None)

        # Assert: DailyRepo called with None, file created without title
        assert fake_daily_repo.write_freeform_called
        assert fake_daily_repo.write_freeform_title is None
        assert result == fake_daily_repo.write_freeform_return_value

    def test_write_freeform_returns_filename(
        self,
        write_freeform: WriteFreeform,
        fake_daily_repo: FakeDailyRepo,
    ) -> None:
        """Test that WriteFreeform returns the created filename."""
        # Arrange: Mock DailyRepo returning specific filename
        expected_filename = '20250911T1530_unique-id-here.md'
        fake_daily_repo.write_freeform_return_value = expected_filename

        # Act: Execute WriteFreeform
        result = write_freeform.execute()

        # Assert: Returns filename from DailyRepo for confirmation
        assert result == expected_filename

    def test_write_freeform_logs_creation(
        self,
        write_freeform: WriteFreeform,
        fake_logger: FakeLogger,
        fake_daily_repo: FakeDailyRepo,
    ) -> None:
        """Test that WriteFreeform logs the freewrite creation."""
        # Arrange
        expected_filename = '20250911T0830_test.md'
        fake_daily_repo.write_freeform_return_value = expected_filename

        # Act
        write_freeform.execute(title='Test')

        # Assert: Check that logger was called with relevant information
        assert any('freewrite' in msg.lower() and expected_filename in msg for msg in fake_logger.info_messages)

    def test_write_freeform_handles_filesystem_error(
        self,
        write_freeform: WriteFreeform,
        fake_daily_repo: FakeDailyRepo,
        fake_logger: FakeLogger,
    ) -> None:
        """Test that WriteFreeform handles filesystem errors appropriately."""
        # Arrange: Make DailyRepo raise FileSystemError
        fake_daily_repo.write_freeform_should_raise = FileSystemError('Disk is full', '/path/to/daily')

        # Act & Assert: Should propagate the exception
        with pytest.raises(FileSystemError, match='Disk is full'):
            write_freeform.execute()

        # Assert: Error should be logged
        all_error_msgs = fake_logger.error_messages + fake_logger.exception_messages
        assert any('error' in msg.lower() or 'failed' in msg.lower() for msg in all_error_msgs)

    def test_write_freeform_handles_editor_launch_failure(
        self,
        write_freeform: WriteFreeform,
        fake_editor_port: FakeEditorPort,
        fake_logger: FakeLogger,
    ) -> None:
        """Test that WriteFreeform handles editor launch failures gracefully."""
        # Arrange: Make EditorPort raise EditorLaunchError
        fake_editor_port.open_should_raise = EditorLaunchError('Editor not found', 'code')

        # Act: Execute should still return the filename even if editor fails
        result = write_freeform.execute()

        # Assert: Should return filename despite editor failure
        assert result == '20250911T0830_01932c5a-7f3e-7000-8000-000000000001.md'

        # Assert: Warning should be logged about editor failure
        warning_messages = [
            str(log[1]) % log[2] if log[2] else str(log[1]) for log in fake_logger.get_logs_by_level('warning')
        ]
        assert any('editor' in msg.lower() for msg in warning_messages)

    def test_write_freeform_with_title_logs_title(
        self,
        write_freeform: WriteFreeform,
        fake_logger: FakeLogger,
    ) -> None:
        """Test that WriteFreeform logs the title when provided."""
        # Arrange & Act
        write_freeform.execute(title='Morning Reflections')

        # Assert: Title should appear in logs
        all_messages = fake_logger.info_messages + fake_logger.debug_messages
        assert any('Morning Reflections' in msg for msg in all_messages)

    def test_write_freeform_default_no_title(
        self,
        write_freeform: WriteFreeform,
        fake_daily_repo: FakeDailyRepo,
    ) -> None:
        """Test that WriteFreeform defaults to no title when not provided."""
        # Act: Call execute without any arguments
        write_freeform.execute()

        # Assert: Should pass None to daily_repo
        assert fake_daily_repo.write_freeform_title is None
