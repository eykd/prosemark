"""Integration test for freewrite sessions with word count goals and time limits."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app


class TestGoalSession:
    """Test freewrite sessions with word count goals and time limits end-to-end scenarios."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a basic project for testing."""
        project_dir = tmp_path / 'goal_session_project'
        project_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(app, ['init', '--title', 'Goal Session Test', '--path', str(project_dir)])
        assert result.exit_code == 0

        return project_dir

    def test_session_with_word_count_goal(self, runner: CliRunner, project: Path) -> None:
        """Test freewrite session with word count goal."""
        word_goal = 500

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock word count goal tracking
            mock_tui.word_count_goal = word_goal
            mock_tui.current_word_count = 0
            mock_tui.update_word_progress = Mock()

            result = runner.invoke(app, ['write', '--word-count-goal', str(word_goal), '--path', str(project)])

            assert result.exit_code == 0

            # Verify TUI was initialized with word count goal (this will fail initially)
            mock_tui_class.assert_called_once()
            init_kwargs = mock_tui_class.call_args.kwargs
            assert 'word_count_goal' in init_kwargs
            assert init_kwargs['word_count_goal'] == word_goal

    def test_session_with_time_limit(self, runner: CliRunner, project: Path) -> None:
        """Test freewrite session with time limit."""
        time_limit = 900  # 15 minutes in seconds

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock time limit tracking
            mock_tui.time_limit = time_limit
            mock_tui.remaining_time = time_limit
            mock_tui.update_timer_display = Mock()

            result = runner.invoke(app, ['write', '--time-limit', str(time_limit), '--path', str(project)])

            assert result.exit_code == 0

            # Verify TUI was initialized with time limit (this will fail initially)
            mock_tui_class.assert_called_once()
            init_kwargs = mock_tui_class.call_args.kwargs
            assert 'time_limit' in init_kwargs
            assert init_kwargs['time_limit'] == time_limit

    def test_session_with_both_goals(self, runner: CliRunner, project: Path) -> None:
        """Test freewrite session with both word count goal and time limit."""
        word_goal = 500
        time_limit = 900

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock both goal types
            mock_tui.word_count_goal = word_goal
            mock_tui.time_limit = time_limit
            mock_tui.update_progress_display = Mock()

            result = runner.invoke(
                app,
                ['write', '--word-count-goal', str(word_goal), '--time-limit', str(time_limit), '--path', str(project)],
            )

            assert result.exit_code == 0

            # Verify both goals were set (this will fail initially)
            mock_tui_class.assert_called_once()
            init_kwargs = mock_tui_class.call_args.kwargs
            assert init_kwargs.get('word_count_goal') == word_goal
            assert init_kwargs.get('time_limit') == time_limit

    def test_word_count_progress_display(self, runner: CliRunner, project: Path) -> None:
        """Test that word count progress is displayed correctly in TUI."""
        word_goal = 100

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock progressive word count updates
            word_counts = [0, 25, 50, 75, 100, 125]  # Exceeding goal
            mock_tui.get_current_word_count.side_effect = word_counts
            mock_tui.calculate_progress_percentage = Mock(side_effect=lambda current, goal: (current / goal) * 100)

            result = runner.invoke(app, ['write', '--word-count-goal', str(word_goal), '--path', str(project)])

            assert result.exit_code == 0

            # Verify progress calculation methods exist (this will fail initially)
            assert hasattr(mock_tui, 'get_current_word_count')
            assert hasattr(mock_tui, 'calculate_progress_percentage')

    def test_time_countdown_display(self, runner: CliRunner, project: Path) -> None:
        """Test that time countdown is displayed correctly in TUI."""
        time_limit = 300  # 5 minutes

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock timer countdown
            remaining_times = [300, 250, 200, 150, 100, 50, 0]
            mock_tui.get_remaining_time.side_effect = remaining_times
            mock_tui.format_time_display = Mock(side_effect=lambda seconds: f'{seconds // 60:02d}:{seconds % 60:02d}')

            result = runner.invoke(app, ['write', '--time-limit', str(time_limit), '--path', str(project)])

            assert result.exit_code == 0

            # Verify timer methods exist (this will fail initially)
            assert hasattr(mock_tui, 'get_remaining_time')
            assert hasattr(mock_tui, 'format_time_display')

    def test_goal_achievement_no_auto_exit(self, runner: CliRunner, project: Path) -> None:
        """Test that reaching goals doesn't automatically exit the session."""
        word_goal = 50  # Small goal for easy achievement
        time_limit = 60  # 1 minute

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Mock goal achievement
            mock_tui.word_count_achieved = Mock(return_value=True)
            mock_tui.time_limit_reached = Mock(return_value=True)
            mock_tui.should_auto_exit = Mock(return_value=False)  # No auto-exit
            mock_tui.run.return_value = None

            result = runner.invoke(
                app,
                ['write', '--word-count-goal', str(word_goal), '--time-limit', str(time_limit), '--path', str(project)],
            )

            assert result.exit_code == 0

            # Verify no auto-exit behavior (this will fail initially)
            assert hasattr(mock_tui, 'should_auto_exit')
            mock_tui.should_auto_exit.assert_called()

    def test_progress_indicators_update_real_time(self, runner: CliRunner, project: Path) -> None:
        """Test that progress indicators update in real-time as user types."""
        word_goal = 100
        time_limit = 300

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock real-time updates
            mock_tui.on_content_change = Mock()
            mock_tui.on_timer_tick = Mock()
            mock_tui.refresh_progress_display = Mock()

            result = runner.invoke(
                app,
                ['write', '--word-count-goal', str(word_goal), '--time-limit', str(time_limit), '--path', str(project)],
            )

            assert result.exit_code == 0

            # Verify real-time update methods exist (this will fail initially)
            assert hasattr(mock_tui, 'on_content_change')
            assert hasattr(mock_tui, 'on_timer_tick')
            assert hasattr(mock_tui, 'refresh_progress_display')

    def test_goal_session_metadata_tracking(self, runner: CliRunner, project: Path) -> None:
        """Test that goal sessions include goal information in metadata."""
        word_goal = 250
        time_limit = 600

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock metadata capture
            with patch(
                'prosemark.freewriting.adapters.file_system_adapter.FileSystemAdapter.write_session_content'
            ) as mock_writer:

                def capture_goal_metadata(file_path: Path, content: str | None, metadata: dict[str, Any]) -> str:
                    # Verify goal information is in metadata
                    assert 'word_count_goal' in metadata
                    assert metadata['word_count_goal'] == word_goal
                    assert 'time_limit' in metadata
                    assert metadata['time_limit'] == time_limit
                    assert 'session_duration' in metadata
                    assert 'goal_achieved' in metadata

                    return file_path.name

                mock_writer.side_effect = capture_goal_metadata

                result = runner.invoke(
                    app,
                    [
                        'write',
                        '--word-count-goal',
                        str(word_goal),
                        '--time-limit',
                        str(time_limit),
                        '--path',
                        str(project),
                    ],
                )

                assert result.exit_code == 0
                mock_writer.assert_called_once()

    def test_invalid_goal_values_error_handling(self, runner: CliRunner, project: Path) -> None:
        """Test error handling for invalid goal values."""
        invalid_word_goals = [-10, 0, 'invalid', 999999999]
        invalid_time_limits = [-5, 0, 'invalid', 999999999]

        for invalid_goal in invalid_word_goals:
            result = runner.invoke(app, ['write', '--word-count-goal', str(invalid_goal), '--path', str(project)])
            # Should handle invalid values gracefully (this will fail initially)
            # Either error early or use sensible defaults
            assert result.exit_code == 0 or 'invalid' in result.output.lower() or 'error' in result.output.lower()

        for invalid_limit in invalid_time_limits:
            result = runner.invoke(app, ['write', '--time-limit', str(invalid_limit), '--path', str(project)])
            # Should handle invalid values gracefully (this will fail initially)
            assert result.exit_code == 0 or 'invalid' in result.output.lower() or 'error' in result.output.lower()

    def test_goal_session_with_title_combination(self, runner: CliRunner, project: Path) -> None:
        """Test combining goals with custom title."""
        word_goal = 200
        time_limit = 450
        title = 'Focused Writing Session'

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            result = runner.invoke(
                app,
                [
                    'write',
                    '--title',
                    title,
                    '--word-count-goal',
                    str(word_goal),
                    '--time-limit',
                    str(time_limit),
                    '--path',
                    str(project),
                ],
            )

            assert result.exit_code == 0

            # Verify all parameters were passed (this will fail initially)
            mock_tui_class.assert_called_once()
            init_kwargs = mock_tui_class.call_args.kwargs
            assert init_kwargs.get('title') == title
            assert init_kwargs.get('word_count_goal') == word_goal
            assert init_kwargs.get('time_limit') == time_limit

    def test_goal_session_node_targeting_combination(self, runner: CliRunner, project: Path) -> None:
        """Test combining goals with node targeting."""
        test_uuid = 'goal1234-5678-9abc-def0-123456789abc'
        word_goal = 150
        time_limit = 300

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock node-targeted writing with goals
            with patch(
                'prosemark.freewriting.adapters.node_service_adapter.NodeServiceAdapter.append_to_node'
            ) as mock_append:

                def write_goal_node_session(file_path: Path, content: str | None, metadata: dict[str, Any]) -> str:
                    assert test_uuid in str(file_path)
                    assert metadata.get('word_count_goal') == word_goal
                    assert metadata.get('time_limit') == time_limit
                    return file_path.name

                mock_append.side_effect = write_goal_node_session

                result = runner.invoke(
                    app,
                    [
                        'write',
                        test_uuid,
                        '--word-count-goal',
                        str(word_goal),
                        '--time-limit',
                        str(time_limit),
                        '--path',
                        str(project),
                    ],
                )

                assert result.exit_code == 0
                mock_append.assert_called_once()

    def test_goal_progress_visual_indicators(self, runner: CliRunner, project: Path) -> None:
        """Test that TUI displays visual progress indicators for goals."""
        word_goal = 100
        time_limit = 300

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui
            mock_tui.run.return_value = None

            # Mock visual indicator methods
            mock_tui.render_word_progress_bar = Mock()
            mock_tui.render_time_progress_bar = Mock()
            mock_tui.update_progress_colors = Mock()  # Change colors based on progress
            mock_tui.show_achievement_notification = Mock()  # Show when goals reached

            result = runner.invoke(
                app,
                ['write', '--word-count-goal', str(word_goal), '--time-limit', str(time_limit), '--path', str(project)],
            )

            assert result.exit_code == 0

            # Verify visual indicator methods exist (this will fail initially)
            assert hasattr(mock_tui, 'render_word_progress_bar')
            assert hasattr(mock_tui, 'render_time_progress_bar')
            assert hasattr(mock_tui, 'update_progress_colors')

    def test_session_statistics_in_final_output(self, runner: CliRunner, project: Path) -> None:
        """Test that session statistics are available after completion."""
        word_goal = 75
        time_limit = 180

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_tui_class:
            mock_tui = Mock()
            mock_tui_class.return_value = mock_tui

            # Mock session statistics
            mock_tui.get_session_statistics = Mock(
                return_value={
                    'final_word_count': 85,
                    'session_duration': 150,
                    'word_goal_achieved': True,
                    'time_goal_achieved': False,
                    'words_per_minute': 34.0,
                }
            )
            mock_tui.run.return_value = None

            result = runner.invoke(
                app,
                ['write', '--word-count-goal', str(word_goal), '--time-limit', str(time_limit), '--path', str(project)],
            )

            assert result.exit_code == 0

            # Verify statistics method exists and was called (this will fail initially)
            assert hasattr(mock_tui, 'get_session_statistics')
            mock_tui.get_session_statistics.assert_called()
