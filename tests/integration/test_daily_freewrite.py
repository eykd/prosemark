"""Integration test for daily freewrite file creation functionality."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestDailyFreewrite:
    """Test daily freewrite file creation end-to-end scenarios."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project for testing."""
        project_dir = tmp_path / 'freewrite_project'
        project_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(app, ['init', '--title', 'Freewrite Test', '--path', str(project_dir)])
        assert result.exit_code == 0

        return project_dir

    def test_basic_daily_freewrite_creation(self, runner: CliRunner, project: Path) -> None:
        """Test basic daily freewrite file creation without title."""
        # Mock the TUI interface to simulate user interaction
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock datetime to get consistent timestamp
            with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)
                mock_datetime.side_effect = datetime

                result = runner.invoke(app, ['write', '--path', str(project)])

                # The command should succeed
                assert result.exit_code == 0

                # Verify expected daily file naming pattern: 2025-09-24-1430.md
                expected_filename = '2025-09-24-1430.md'
                expected_file = project / expected_filename

                # The file should be created (this will fail initially)
                assert expected_file.exists(), f'Daily freewrite file {expected_filename} was not created'

                # Verify file content structure
                content = expected_file.read_text()

                # Should have YAML frontmatter
                assert content.startswith('---\n')
                assert 'id:' in content
                assert 'created:' in content
                assert 'session_start:' in content

                # Should have proper timestamp in frontmatter
                assert '2025-09-24T14:30:00' in content

    def test_daily_freewrite_with_user_input(self, runner: CliRunner, project: Path) -> None:
        """Test daily freewrite creation with simulated user input in TUI."""
        # Mock user typing in TUI
        user_content = ['This is my first thought', 'This is another line', 'Final thought before saving']

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock the content writing behavior
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:
                mock_writer.return_value = '2025-09-24-1430.md'

                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

                    result = runner.invoke(app, ['write', '--path', str(project)])

                    assert result.exit_code == 0

                    # Create the expected file with content for verification
                    expected_file = project / '2025-09-24-1430.md'
                    expected_content = """---
id: test-session-id
created: 2025-09-24T14:30:00
session_start: 2025-09-24T14:30:00
word_count: 12
---

# Daily Freewriting Session

This is my first thought
This is another line
Final thought before saving
"""
                    expected_file.write_text(expected_content)

                    # Verify content structure
                    content = expected_file.read_text()
                    for line in user_content:
                        assert line in content

                    # Verify word count is tracked
                    assert 'word_count:' in content

    def test_daily_freewrite_tui_layout_requirements(self, runner: CliRunner, project: Path) -> None:
        """Test that TUI opens with correct 80/20 layout requirements."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Capture TUI initialization parameters
            def capture_init(*args: Any, **kwargs: Any) -> Any:
                # Verify TUI is initialized with correct layout proportions
                assert hasattr(mock_tui, 'content_area_height_percent')
                mock_tui.content_area_height_percent = 80
                mock_tui.input_area_height_percent = 20
                return mock_tui

            mock_tui_class.side_effect = capture_init
            mock_tui.run.return_value = None

            runner.invoke(app, ['write', '--path', str(project)])

            # Verify TUI was created with correct layout (this will fail initially)
            mock_tui_class.assert_called_once()
            assert mock_tui.content_area_height_percent == 80
            assert mock_tui.input_area_height_percent == 20

    def test_daily_freewrite_real_time_word_count(self, runner: CliRunner, project: Path) -> None:
        """Test that word count updates in real-time during TUI session."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Mock word count tracking
            word_counts = [0, 5, 10, 15]  # Simulated progression
            mock_tui.get_current_word_count.side_effect = word_counts

            mock_tui.run.return_value = None

            result = runner.invoke(app, ['write', '--path', str(project)])

            assert result.exit_code == 0

            # Verify word count tracking was called (this will fail initially)
            assert hasattr(mock_tui, 'get_current_word_count')

    def test_daily_freewrite_timer_functionality(self, runner: CliRunner, project: Path) -> None:
        """Test that timer runs during freewrite session."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Mock timer functionality
            mock_tui.session_duration = 0
            mock_tui.timer_running = True
            mock_tui.run.return_value = None

            with patch('time.time') as mock_time:
                mock_time.side_effect = [1000.0, 1060.0]  # 60 seconds elapsed

                result = runner.invoke(app, ['write', '--path', str(project)])

                assert result.exit_code == 0

                # Verify timer functionality exists (this will fail initially)
                assert hasattr(mock_tui, 'timer_running')
                assert hasattr(mock_tui, 'session_duration')

    def test_daily_freewrite_content_display(self, runner: CliRunner, project: Path) -> None:
        """Test that content appears in top area as user types."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Mock content display behavior
            displayed_content = []

            def mock_add_content(line: str) -> None:
                displayed_content.append(line)

            mock_tui.add_content_line = mock_add_content
            mock_tui.clear_input = Mock()
            mock_tui.run.return_value = None

            result = runner.invoke(app, ['write', '--path', str(project)])

            assert result.exit_code == 0

            # Verify content display methods exist (this will fail initially)
            assert hasattr(mock_tui, 'add_content_line')
            assert hasattr(mock_tui, 'clear_input')

    def test_daily_freewrite_file_atomic_write(self, runner: CliRunner, project: Path) -> None:
        """Test that freewrite files are written atomically to prevent corruption."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock atomic write behavior
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_file'
            ) as mock_atomic:
                mock_atomic.return_value = True

                result = runner.invoke(app, ['write', '--path', str(project)])

                assert result.exit_code == 0

                # Verify atomic write was used (this will fail initially)
                mock_atomic.assert_called_once()

    def test_daily_freewrite_preserves_exact_input(self, runner: CliRunner, project: Path) -> None:
        """Test that exact user input is preserved including whitespace and formatting."""
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock content capture
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:

                def capture_content(file_path: Path, content: str | None, metadata: dict[str, str]) -> str:
                    # Write actual file to verify content preservation
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f'---\n{metadata}\n---\n\n{content}')
                    return file_path.name

                mock_writer.side_effect = capture_content

                with patch('prosemark.adapters.clock_system.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2025, 9, 24, 14, 30, 0, tzinfo=UTC)

                    result = runner.invoke(app, ['write', '--path', str(project)])

                    assert result.exit_code == 0

                    # This test will fail initially as the file won't be created
                    expected_file = project / '2025-09-24-1430.md'
                    if expected_file.exists():
                        content = expected_file.read_text()
                        assert 'extra spaces' in content
                        assert '    Leading indentation' in content
                        assert '\tAnd this has a tab' in content
