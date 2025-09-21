"""Tests for DailyRepoFs adapter."""

from pathlib import Path
from unittest.mock import patch

import pytest

from prosemark.adapters.daily_repo_fs import DailyRepoFs
from prosemark.adapters.fake_clock import FakeClock
from prosemark.adapters.id_generator_uuid7 import IdGeneratorUuid7
from prosemark.exceptions import FileSystemError


class TestDailyRepoFs:
    """Test DailyRepoFs adapter methods."""

    @pytest.fixture
    def daily_dir(self, tmp_path: Path) -> Path:
        """Create a temporary daily directory."""
        daily_dir = tmp_path / 'daily'
        daily_dir.mkdir()
        return daily_dir

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        """Create a fake clock with fixed time."""
        return FakeClock('2025-09-21T12:30:00Z')

    @pytest.fixture
    def id_generator(self) -> IdGeneratorUuid7:
        """Create an ID generator."""
        return IdGeneratorUuid7()

    @pytest.fixture
    def daily_repo(
        self,
        daily_dir: Path,
        fake_clock: FakeClock,
        id_generator: IdGeneratorUuid7,
    ) -> DailyRepoFs:
        """Create a DailyRepoFs instance."""
        return DailyRepoFs(
            daily_path=daily_dir,
            clock=fake_clock,
            id_generator=id_generator,
        )

    def test_write_freeform_with_title(self, daily_repo: DailyRepoFs, daily_dir: Path) -> None:
        """Test write_freeform creates file with title."""
        # Act
        filename = daily_repo.write_freeform('Test Title')

        # Assert
        assert filename.endswith('.md')
        file_path = daily_dir / filename
        assert file_path.exists()

        # Check file content has title in frontmatter
        content = file_path.read_text(encoding='utf-8')
        assert 'title: Test Title' in content

    def test_write_freeform_without_title(self, daily_repo: DailyRepoFs, daily_dir: Path) -> None:
        """Test write_freeform creates file without title."""
        # Act
        filename = daily_repo.write_freeform()

        # Assert
        file_path = daily_dir / filename
        assert file_path.exists()

        # Check file content has no title in frontmatter
        content = file_path.read_text(encoding='utf-8')
        assert 'title:' not in content

    def test_write_freeform_handles_oserror_during_file_write(self, daily_repo: DailyRepoFs) -> None:
        """Test write_freeform raises FileSystemError when file cannot be written."""
        # Arrange - Mock Path.write_text to raise OSError
        with patch('pathlib.Path.write_text') as mock_write:
            mock_write.side_effect = OSError('Permission denied')

            # Act & Assert
            with pytest.raises(FileSystemError, match='Cannot create freeform file'):
                daily_repo.write_freeform('Test Title')

    def test_write_freeform_handles_permission_error(self, daily_repo: DailyRepoFs) -> None:
        """Test write_freeform raises FileSystemError for permission errors."""
        # Arrange - Mock Path.write_text to raise PermissionError (subclass of OSError)
        with patch('pathlib.Path.write_text') as mock_write:
            mock_write.side_effect = PermissionError('Access denied')

            # Act & Assert
            with pytest.raises(FileSystemError, match='Cannot create freeform file'):
                daily_repo.write_freeform('Test Title')

    def test_write_freeform_handles_disk_full_error(self, daily_repo: DailyRepoFs) -> None:
        """Test write_freeform raises FileSystemError for disk full errors."""
        # Arrange - Mock Path.write_text to raise OSError with disk full errno
        with patch('pathlib.Path.write_text') as mock_write:
            error = OSError('No space left on device')
            error.errno = 28  # ENOSPC - No space left on device
            mock_write.side_effect = error

            # Act & Assert
            with pytest.raises(FileSystemError, match='Cannot create freeform file'):
                daily_repo.write_freeform('Test Title')

    def test_write_freeform_successful_with_specific_filename_pattern(
        self, daily_repo: DailyRepoFs, fake_clock: FakeClock
    ) -> None:
        """Test write_freeform generates expected filename pattern."""
        # Act
        filename = daily_repo.write_freeform('Test Title')

        # Assert - Should start with timestamp from fake clock
        assert filename.startswith('20250921T1230_')
        assert filename.endswith('.md')

    def test_write_freeform_creates_valid_frontmatter(self, daily_repo: DailyRepoFs, daily_dir: Path) -> None:
        """Test write_freeform creates valid YAML frontmatter."""
        # Act
        filename = daily_repo.write_freeform('Test Title')

        # Assert
        file_path = daily_dir / filename
        content = file_path.read_text(encoding='utf-8')

        # Should start with YAML frontmatter
        assert content.startswith('---\n')
        assert 'title: Test Title' in content
        assert content.count('---') == 2  # Opening and closing frontmatter
